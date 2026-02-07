"""Audit logging system for tracking all PKM Agent operations.

Provides immutable audit trail with rollback capability for all write operations.
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import aiosqlite

logger = logging.getLogger(__name__)


class AuditEntry:
    """Single audit log entry."""

    def __init__(
        self,
        action: str,
        target: str | None = None,
        snapshot_before: str | None = None,
        snapshot_after: str | None = None,
        user_approved: bool = False,
        reversible: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.action = action
        self.target = target
        self.snapshot_before = snapshot_before
        self.snapshot_after = snapshot_after
        self.user_approved = user_approved
        self.reversible = reversible
        self.metadata = metadata or {}
        
        # Compute checksums for integrity
        if snapshot_before:
            self.checksum_before = hashlib.sha256(snapshot_before.encode()).hexdigest()
        else:
            self.checksum_before = None
            
        if snapshot_after:
            self.checksum_after = hashlib.sha256(snapshot_after.encode()).hexdigest()
        else:
            self.checksum_after = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "target": self.target,
            "snapshot_before": self.snapshot_before,
            "snapshot_after": self.snapshot_after,
            "checksum_before": self.checksum_before,
            "checksum_after": self.checksum_after,
            "user_approved": self.user_approved,
            "reversible": self.reversible,
            "metadata": json.dumps(self.metadata),
        }


class RollbackHandler(Protocol):
    """Protocol for objects that can handle rollback operations."""
    
    async def rollback(self, entry: AuditEntry) -> bool:
        """Rollback the operation described in the audit entry."""
        ...


class AuditLogger:
    """Immutable append-only audit log with rollback capability."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None
        self._initialized = False

    async def initialize(self):
        """Initialize the audit database."""
        if self._initialized:
            return
            
        self._conn = await aiosqlite.connect(
            str(self.db_path),
            isolation_level=None,  # Autocommit mode
        )
        
        # Enable WAL mode for better concurrency
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA synchronous=NORMAL")
        
        # Create audit table
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                snapshot_before TEXT,
                snapshot_after TEXT,
                checksum_before TEXT,
                checksum_after TEXT,
                user_approved INTEGER NOT NULL DEFAULT 0,
                reversible INTEGER NOT NULL DEFAULT 1,
                metadata TEXT,
                rolled_back INTEGER NOT NULL DEFAULT 0,
                rollback_timestamp TEXT
            )
            """
        )
        
        # Create indices for common queries
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)"
        )
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)"
        )
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target)"
        )
        
        await self._conn.commit()
        self._initialized = True
        logger.info(f"Initialized audit log at {self.db_path}")

    async def log(self, entry: AuditEntry) -> str:
        """Append entry to audit log. Returns entry ID."""
        if not self._initialized:
            await self.initialize()
            
        data = entry.to_dict()
        
        await self._conn.execute(
            """
            INSERT INTO audit_log (
                id, timestamp, action, target,
                snapshot_before, snapshot_after,
                checksum_before, checksum_after,
                user_approved, reversible, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["timestamp"],
                data["action"],
                data["target"],
                data["snapshot_before"],
                data["snapshot_after"],
                data["checksum_before"],
                data["checksum_after"],
                1 if data["user_approved"] else 0,
                1 if data["reversible"] else 0,
                data["metadata"],
            ),
        )
        
        await self._conn.commit()
        logger.debug(f"Logged audit entry: {entry.id} ({entry.action})")
        return entry.id

    async def get_entry(self, entry_id: str) -> AuditEntry | None:
        """Retrieve an audit entry by ID."""
        if not self._initialized:
            await self.initialize()
            
        cursor = await self._conn.execute(
            "SELECT * FROM audit_log WHERE id = ?", (entry_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
            
        return self._row_to_entry(row)

    async def get_history(
        self,
        action: str | None = None,
        target: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Get audit history with optional filtering."""
        if not self._initialized:
            await self.initialize()
            
        query = "SELECT * FROM audit_log WHERE 1=1"
        params: list[Any] = []
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if target:
            query += " AND target = ?"
            params.append(target)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()
        
        return [self._row_to_entry(row) for row in rows]

    async def rollback(self, entry_id: str, handler: RollbackHandler) -> bool:
        """Rollback an operation using the provided handler."""
        entry = await self.get_entry(entry_id)
        
        if not entry:
            logger.error(f"Audit entry not found: {entry_id}")
            return False
            
        if not entry.reversible:
            logger.error(f"Entry {entry_id} is not reversible")
            return False
            
        # Check if already rolled back
        cursor = await self._conn.execute(
            "SELECT rolled_back FROM audit_log WHERE id = ?", (entry_id,)
        )
        row = await cursor.fetchone()
        
        if row and row[0]:
            logger.warning(f"Entry {entry_id} already rolled back")
            return False
        
        # Perform rollback
        success = await handler.rollback(entry)
        
        if success:
            # Mark as rolled back
            await self._conn.execute(
                """
                UPDATE audit_log 
                SET rolled_back = 1, rollback_timestamp = ? 
                WHERE id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), entry_id),
            )
            await self._conn.commit()
            logger.info(f"Rolled back operation: {entry_id}")
            
        return success

    async def get_stats(self) -> dict[str, Any]:
        """Get audit log statistics."""
        if not self._initialized:
            await self.initialize()
            
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM audit_log"
        )
        total = (await cursor.fetchone())[0]
        
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE rolled_back = 1"
        )
        rolled_back = (await cursor.fetchone())[0]
        
        cursor = await self._conn.execute(
            "SELECT action, COUNT(*) FROM audit_log GROUP BY action"
        )
        by_action = dict(await cursor.fetchall())
        
        return {
            "total_entries": total,
            "rolled_back": rolled_back,
            "by_action": by_action,
        }

    def _row_to_entry(self, row) -> AuditEntry:
        """Convert database row to AuditEntry."""
        entry = AuditEntry(
            action=row[2],
            target=row[3],
            snapshot_before=row[4],
            snapshot_after=row[5],
            user_approved=bool(row[8]),
            reversible=bool(row[9]),
            metadata=json.loads(row[10]) if row[10] else {},
        )
        entry.id = row[0]
        entry.timestamp = datetime.fromisoformat(row[1])
        entry.checksum_before = row[6]
        entry.checksum_after = row[7]
        return entry

    async def close(self):
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._initialized = False
