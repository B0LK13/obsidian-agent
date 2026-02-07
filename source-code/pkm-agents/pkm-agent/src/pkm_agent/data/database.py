"""SQLite database operations for PKM Agent."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from pkm_agent.data.models import Note, NoteMetadata, SearchResult, _json_safe


class Database:
    """SQLite database manager for PKM Agent."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript("""
                -- Notes table
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    content TEXT,
                    content_hash TEXT,
                    metadata JSON,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    word_count INTEGER DEFAULT 0,
                    embedding_id TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_notes_path ON notes(path);
                CREATE INDEX IF NOT EXISTS idx_notes_modified ON notes(modified_at DESC);

                -- Tags table
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT DEFAULT 'user',
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Note-Tag junction
                CREATE TABLE IF NOT EXISTS note_tags (
                    note_id TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'user',
                    PRIMARY KEY (note_id, tag_id),
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                );

                -- Links table
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    link_type TEXT DEFAULT 'reference',
                    context TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES notes(id) ON DELETE CASCADE,
                    UNIQUE(source_id, target_id, link_type)
                );

                CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id);
                CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_id);

                -- Conversations table
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    message_count INTEGER DEFAULT 0,
                    summary TEXT
                );

                -- Messages table
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tokens_used INTEGER,
                    model TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);

                -- Audit log table
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    metadata JSON,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);
            """)

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Note operations
    def upsert_note(self, note: Note) -> None:
        """Insert or update a note."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO notes (id, path, title, content, content_hash, metadata,
                                   created_at, modified_at, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    path = excluded.path,
                    title = excluded.title,
                    content = excluded.content,
                    content_hash = excluded.content_hash,
                    metadata = excluded.metadata,
                    modified_at = excluded.modified_at,
                    word_count = excluded.word_count
            """, (
                note.id,
                str(note.path),
                note.title,
                note.content,
                note.content_hash,
                json.dumps(note.metadata.to_dict()),
                note.created_at.isoformat(),
                note.modified_at.isoformat(),
                note.word_count,
            ))

            # Update tags
            self._update_note_tags(conn, note)

    def _update_note_tags(self, conn: sqlite3.Connection, note: Note) -> None:
        """Update tags for a note."""
        # Remove existing tags
        conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note.id,))

        # Add new tags
        for tag_name in note.metadata.tags:
            # Ensure tag exists
            conn.execute("""
                INSERT OR IGNORE INTO tags (name) VALUES (?)
            """, (tag_name,))

            # Get tag id
            result = conn.execute(
                "SELECT id FROM tags WHERE name = ?", (tag_name,)
            ).fetchone()

            if result:
                conn.execute("""
                    INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)
                """, (note.id, result["id"]))

                # Update usage count
                conn.execute("""
                    UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?
                """, (result["id"],))

    def get_note(self, note_id: str) -> Note | None:
        """Get a note by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()

            if row:
                return self._row_to_note(row)
        return None

    def get_note_by_path(self, path: str) -> Note | None:
        """Get a note by path."""
        normalized_path = str(Path(path))
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE path = ?", (normalized_path,)
            ).fetchone()

            if row:
                return self._row_to_note(row)
        return None

    def get_all_notes(self, limit: int = 1000) -> list[Note]:
        """Get all notes."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY modified_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_to_note(row) for row in rows]

    def search_notes(
        self,
        query: str,
        limit: int = 20
    ) -> list[SearchResult]:
        """Simple keyword search in notes."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, path, title, content,
                       (CASE
                           WHEN title LIKE ? THEN 10
                           WHEN content LIKE ? THEN 5
                           ELSE 1
                       END) as score
                FROM notes
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY score DESC, modified_at DESC
                LIMIT ?
            """, (
                f"%{query}%", f"%{query}%",
                f"%{query}%", f"%{query}%",
                limit
            )).fetchall()

            results = []
            for row in rows:
                # Extract snippet around match
                content = row["content"] or ""
                idx = content.lower().find(query.lower())
                if idx >= 0:
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(query) + 50)
                    snippet = content[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet = snippet + "..."
                else:
                    snippet = content[:100] + "..." if len(content) > 100 else content

                results.append(SearchResult(
                    note_id=row["id"],
                    path=row["path"],
                    title=row["title"],
                    score=row["score"] / 10.0,
                    snippet=snippet,
                    highlights=[query],
                ))

            return results

    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID."""
        with self._get_connection() as conn:
            result = conn.execute(
                "DELETE FROM notes WHERE id = ?", (note_id,)
            )
            return result.rowcount > 0

    def get_note_count(self) -> int:
        """Get total number of notes."""
        with self._get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM notes").fetchone()
            return result[0] if result else 0

    def _row_to_note(self, row: sqlite3.Row) -> Note:
        """Convert database row to Note object."""
        metadata_dict = json.loads(row["metadata"]) if row["metadata"] else {}
        metadata = NoteMetadata.from_dict(metadata_dict)

        return Note(
            id=row["id"],
            path=Path(row["path"]),
            title=row["title"],
            content=row["content"] or "",
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
            word_count=row["word_count"],
            content_hash=row["content_hash"] or "",
        )

    # Audit logging
    def log_action(self, category: str, action: str, metadata: dict[str, Any] | None = None) -> None:
        """Persist an audit log entry."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (category, action, metadata, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    category,
                    action,
                    json.dumps(_json_safe(metadata or {})),
                    datetime.now().isoformat(),
                ),
            )

    def get_audit_logs(
        self,
        limit: int = 50,
        category: str | None = None,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent audit log entries."""
        where = []
        params: list[Any] = []

        if category:
            where.append("category = ?")
            params.append(category)
        if action:
            where.append("action = ?")
            params.append(action)

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT category, action, metadata, created_at
                FROM audit_logs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "category": row["category"],
                        "action": row["action"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "created_at": row["created_at"],
                    }
                )

            return results

    # Conversation operations
    def create_conversation(self, conv_id: str) -> None:
        """Create a new conversation."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO conversations (id, started_at)
                VALUES (?, ?)
            """, (conv_id, datetime.now().isoformat()))
        self.log_action("conversation", "create", {"conversation_id": conv_id})

    def add_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        tokens: int = 0,
        model: str = ""
    ) -> None:
        """Add a message to a conversation."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO messages (conversation_id, role, content, timestamp, tokens_used, model)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (conv_id, role, content, datetime.now().isoformat(), tokens, model))

            conn.execute("""
                UPDATE conversations
                SET message_count = message_count + 1
                WHERE id = ?
            """, (conv_id,))
        self.log_action("conversation", "message", {"conversation_id": conv_id, "role": role})

    def get_conversation_messages(
        self,
        conv_id: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get messages from a conversation."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT role, content, timestamp, model
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conv_id, limit)).fetchall()

            return [dict(row) for row in reversed(rows)]

    # Stats
    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            note_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            tag_count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
            link_count = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
            word_count = conn.execute("SELECT SUM(word_count) FROM notes").fetchone()[0] or 0

            return {
                "notes": note_count,
                "tags": tag_count,
                "links": link_count,
                "total_words": word_count,
            }
