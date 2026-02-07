"""
Incremental Indexing Mechanism for Obsidian Vault
Issue #95: Implement Incremental Indexing Mechanism

Provides efficient vault indexing by only processing changed notes,
tracking file modifications via hash-based change detection.
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class IndexEntry:
    """Represents a single indexed note."""
    note_id: str
    file_path: str
    content_hash: str
    last_modified: datetime
    embedding_id: Optional[str] = None
    indexed_at: Optional[datetime] = None
    word_count: int = 0
    link_count: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.indexed_at is None:
            self.indexed_at = datetime.utcnow()


@dataclass
class ChangeReport:
    """Report of changes detected during indexing."""
    added: List[IndexEntry]
    modified: List[IndexEntry]
    deleted: List[str]  # note_ids
    unchanged: List[str]  # note_ids
    duration_ms: float
    total_scanned: int
    
    @property
    def has_changes(self) -> bool:
        return len(self.added) > 0 or len(self.modified) > 0 or len(self.deleted) > 0
    
    @property
    def change_count(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted)


class ChangeTracker:
    """
    Tracks file changes using content hashing.
    Stores state in SQLite for persistence.
    """
    
    def __init__(self, db_path: str = "index_state.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS index_state (
                    note_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    embedding_id TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    word_count INTEGER DEFAULT 0,
                    link_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]'
                );
                
                CREATE INDEX IF NOT EXISTS idx_file_path ON index_state(file_path);
                CREATE INDEX IF NOT EXISTS idx_last_modified ON index_state(last_modified);
                
                CREATE TABLE IF NOT EXISTS index_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                INSERT OR IGNORE INTO index_metadata (key, value) 
                VALUES ('version', '1.0'), ('last_full_index', 'never');
            """)
            conn.commit()
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_entry(self, note_id: str) -> Optional[IndexEntry]:
        """Get index entry for a note."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM index_state WHERE note_id = ?",
                (note_id,)
            ).fetchone()
            
            if row:
                return IndexEntry(
                    note_id=row['note_id'],
                    file_path=row['file_path'],
                    content_hash=row['content_hash'],
                    last_modified=datetime.fromisoformat(row['last_modified']),
                    embedding_id=row['embedding_id'],
                    indexed_at=datetime.fromisoformat(row['indexed_at']),
                    word_count=row['word_count'],
                    link_count=row['link_count'],
                    tags=json.loads(row['tags'])
                )
            return None
    
    def get_all_entries(self) -> Dict[str, IndexEntry]:
        """Get all tracked entries."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM index_state").fetchall()
            return {
                row['note_id']: IndexEntry(
                    note_id=row['note_id'],
                    file_path=row['file_path'],
                    content_hash=row['content_hash'],
                    last_modified=datetime.fromisoformat(row['last_modified']),
                    embedding_id=row['embedding_id'],
                    indexed_at=datetime.fromisoformat(row['indexed_at']),
                    word_count=row['word_count'],
                    link_count=row['link_count'],
                    tags=json.loads(row['tags'])
                )
                for row in rows
            }
    
    def record_change(self, entry: IndexEntry) -> None:
        """Record or update an index entry."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO index_state 
                (note_id, file_path, content_hash, last_modified, embedding_id, 
                 indexed_at, word_count, link_count, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.note_id,
                entry.file_path,
                entry.content_hash,
                entry.last_modified.isoformat(),
                entry.embedding_id,
                entry.indexed_at.isoformat(),
                entry.word_count,
                entry.link_count,
                json.dumps(entry.tags)
            ))
            conn.commit()
    
    def record_changes_batch(self, entries: List[IndexEntry]) -> None:
        """Record multiple changes efficiently."""
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO index_state 
                (note_id, file_path, content_hash, last_modified, embedding_id, 
                 indexed_at, word_count, link_count, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    e.note_id, e.file_path, e.content_hash, 
                    e.last_modified.isoformat(), e.embedding_id,
                    e.indexed_at.isoformat(), e.word_count, e.link_count,
                    json.dumps(e.tags)
                )
                for e in entries
            ])
            conn.commit()
    
    def delete_entry(self, note_id: str) -> None:
        """Remove an entry from tracking."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM index_state WHERE note_id = ?", (note_id,))
            conn.commit()
    
    def delete_entries_batch(self, note_ids: List[str]) -> None:
        """Remove multiple entries efficiently."""
        with self._get_connection() as conn:
            conn.executemany(
                "DELETE FROM index_state WHERE note_id = ?",
                [(nid,) for nid in note_ids]
            )
            conn.commit()
    
    def update_metadata(self, key: str, value: str) -> None:
        """Update index metadata."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO index_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.utcnow().isoformat()))
            conn.commit()
    
    def get_metadata(self, key: str) -> Optional[str]:
        """Get index metadata value."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM index_metadata WHERE key = ?",
                (key,)
            ).fetchone()
            return row['value'] if row else None


class IncrementalIndexer:
    """
    Main incremental indexing engine.
    Scans vault, detects changes, and triggers re-indexing only for modified content.
    """
    
    def __init__(
        self,
        vault_path: str,
        state_db_path: str = "index_state.db",
        embedding_callback: Optional[Callable[[str, str], str]] = None
    ):
        self.vault_path = Path(vault_path)
        self.tracker = ChangeTracker(state_db_path)
        self.embedding_callback = embedding_callback
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        
        # Supported markdown extensions
        self.markdown_extensions = {'.md', '.markdown'}
    
    def _extract_note_metadata(self, content: str) -> Dict:
        """Extract metadata from note content."""
        lines = content.split('\n')
        
        # Count words (excluding markdown syntax)
        import re
        text_only = re.sub(r'[#\*\[\]\(\)\|`\-]', ' ', content)
        word_count = len([w for w in text_only.split() if w.strip()])
        
        # Count links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)|\[\[([^\]]+)\]\]'
        link_count = len(re.findall(link_pattern, content))
        
        # Extract tags
        tag_pattern = r'#([a-zA-Z0-9_\-\/]+)'
        tags = list(set(re.findall(tag_pattern, content)))
        
        return {
            'word_count': word_count,
            'link_count': link_count,
            'tags': tags
        }
    
    def _scan_vault(self) -> Dict[str, Tuple[Path, str, datetime]]:
        """Scan vault for all markdown files and their metadata."""
        current_files = {}
        
        for file_path in self.vault_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.markdown_extensions:
                try:
                    stat = file_path.stat()
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    note_id = str(file_path.relative_to(self.vault_path)).replace('\\', '/')
                    current_files[note_id] = (file_path, note_id, modified_time)
                except (OSError, ValueError) as e:
                    logger.warning(f"Could not stat {file_path}: {e}")
        
        return current_files
    
    def _read_note_content(self, file_path: Path) -> Optional[str]:
        """Safely read note content."""
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None
    
    def detect_changes(self) -> ChangeReport:
        """
        Detect all changes in the vault without performing indexing.
        Returns a report of what would be indexed.
        """
        import time
        start_time = time.time()
        
        current_files = self._scan_vault()
        tracked_entries = self.tracker.get_all_entries()
        tracked_ids = set(tracked_entries.keys())
        current_ids = set(current_files.keys())
        
        added = []
        modified = []
        deleted = []
        unchanged = []
        
        # Check for new and modified files
        for note_id, (file_path, _, modified_time) in current_files.items():
            content = self._read_note_content(file_path)
            if content is None:
                continue
            
            current_hash = self.tracker.compute_hash(content)
            
            if note_id not in tracked_entries:
                # New file
                metadata = self._extract_note_metadata(content)
                entry = IndexEntry(
                    note_id=note_id,
                    file_path=str(file_path),
                    content_hash=current_hash,
                    last_modified=modified_time,
                    word_count=metadata['word_count'],
                    link_count=metadata['link_count'],
                    tags=metadata['tags']
                )
                added.append(entry)
            elif tracked_entries[note_id].content_hash != current_hash:
                # Modified file
                metadata = self._extract_note_metadata(content)
                entry = IndexEntry(
                    note_id=note_id,
                    file_path=str(file_path),
                    content_hash=current_hash,
                    last_modified=modified_time,
                    embedding_id=tracked_entries[note_id].embedding_id,
                    word_count=metadata['word_count'],
                    link_count=metadata['link_count'],
                    tags=metadata['tags']
                )
                modified.append(entry)
            else:
                unchanged.append(note_id)
        
        # Check for deleted files
        for note_id in tracked_ids - current_ids:
            deleted.append(note_id)
        
        duration_ms = (time.time() - start_time) * 1000
        
        return ChangeReport(
            added=added,
            modified=modified,
            deleted=deleted,
            unchanged=unchanged,
            duration_ms=duration_ms,
            total_scanned=len(current_files)
        )
    
    def index_changes(self, report: Optional[ChangeReport] = None) -> ChangeReport:
        """
        Perform incremental indexing based on change detection.
        Updates embeddings only for changed content.
        """
        with self._lock:
            if report is None:
                report = self.detect_changes()
            
            if not report.has_changes:
                logger.info(f"No changes detected. Scanned {report.total_scanned} files in {report.duration_ms:.1f}ms")
                return report
            
            logger.info(f"Indexing {report.change_count} changes: "
                       f"{len(report.added)} added, {len(report.modified)} modified, "
                       f"{len(report.deleted)} deleted")
            
            # Process additions
            for entry in report.added:
                if self._stop_event.is_set():
                    break
                self._index_entry(entry)
            
            # Process modifications
            for entry in report.modified:
                if self._stop_event.is_set():
                    break
                self._index_entry(entry)
            
            # Process deletions
            if report.deleted and not self._stop_event.is_set():
                self.tracker.delete_entries_batch(report.deleted)
                logger.info(f"Removed {len(report.deleted)} deleted notes from index")
            
            # Update metadata
            self.tracker.update_metadata('last_incremental_index', datetime.utcnow().isoformat())
            
            logger.info(f"Incremental indexing complete in {report.duration_ms:.1f}ms")
            return report
    
    def _index_entry(self, entry: IndexEntry) -> None:
        """Index a single entry, generating embedding if callback provided."""
        try:
            if self.embedding_callback:
                content = self._read_note_content(Path(entry.file_path))
                if content:
                    embedding_id = self.embedding_callback(entry.note_id, content)
                    entry.embedding_id = embedding_id
            
            self.tracker.record_change(entry)
            logger.debug(f"Indexed: {entry.note_id}")
        except Exception as e:
            logger.error(f"Failed to index {entry.note_id}: {e}")
    
    def full_reindex(self) -> ChangeReport:
        """
        Force full reindex of the vault.
        Clears existing state and re-indexes everything.
        """
        with self._lock:
            logger.info("Starting full vault reindex...")
            
            # Clear existing state
            with self.tracker._get_connection() as conn:
                conn.execute("DELETE FROM index_state")
                conn.commit()
            
            self.tracker.update_metadata('last_full_index', datetime.utcnow().isoformat())
            
            # Reindex everything
            current_files = self._scan_vault()
            all_entries = []
            
            for note_id, (file_path, _, modified_time) in current_files.items():
                if self._stop_event.is_set():
                    break
                
                content = self._read_note_content(file_path)
                if content is None:
                    continue
                
                metadata = self._extract_note_metadata(content)
                entry = IndexEntry(
                    note_id=note_id,
                    file_path=str(file_path),
                    content_hash=self.tracker.compute_hash(content),
                    last_modified=modified_time,
                    word_count=metadata['word_count'],
                    link_count=metadata['link_count'],
                    tags=metadata['tags']
                )
                
                if self.embedding_callback and content:
                    try:
                        entry.embedding_id = self.embedding_callback(note_id, content)
                    except Exception as e:
                        logger.error(f"Embedding failed for {note_id}: {e}")
                
                all_entries.append(entry)
            
            # Batch insert
            if all_entries:
                self.tracker.record_changes_batch(all_entries)
            
            logger.info(f"Full reindex complete: {len(all_entries)} notes indexed")
            
            return ChangeReport(
                added=all_entries,
                modified=[],
                deleted=[],
                unchanged=[],
                duration_ms=0,
                total_scanned=len(all_entries)
            )
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the current index."""
        entries = self.tracker.get_all_entries()
        
        total_words = sum(e.word_count for e in entries.values())
        total_links = sum(e.link_count for e in entries.values())
        all_tags = set()
        for e in entries.values():
            all_tags.update(e.tags)
        
        return {
            'total_notes': len(entries),
            'total_words': total_words,
            'total_links': total_links,
            'unique_tags': len(all_tags),
            'last_full_index': self.tracker.get_metadata('last_full_index'),
            'last_incremental_index': self.tracker.get_metadata('last_incremental_index'),
            'db_path': self.tracker.db_path
        }
    
    def stop(self) -> None:
        """Signal the indexer to stop current operations."""
        self._stop_event.set()
    
    def reset(self) -> None:
        """Clear all index state."""
        with self._lock:
            with self.tracker._get_connection() as conn:
                conn.execute("DELETE FROM index_state")
                conn.execute("DELETE FROM index_metadata")
                conn.commit()
            logger.info("Index state reset")


# Singleton instance for application-wide use
_indexer_instance: Optional[IncrementalIndexer] = None


def get_indexer(vault_path: Optional[str] = None, **kwargs) -> IncrementalIndexer:
    """Get or create the global indexer instance."""
    global _indexer_instance
    if _indexer_instance is None:
        if vault_path is None:
            raise ValueError("vault_path required for first initialization")
        _indexer_instance = IncrementalIndexer(vault_path, **kwargs)
    return _indexer_instance


def set_indexer(indexer: IncrementalIndexer) -> None:
    """Set the global indexer instance."""
    global _indexer_instance
    _indexer_instance = indexer


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create test vault
    test_vault = Path("test_vault")
    test_vault.mkdir(exist_ok=True)
    
    # Create test note
    (test_vault / "note1.md").write_text("# Test Note\n\nThis is a test. #tag1 #tag2")
    (test_vault / "note2.md").write_text("# Another Note\n\nWith a [[link]] to another note.")
    
    # Initialize indexer
    indexer = IncrementalIndexer(str(test_vault), "test_index.db")
    
    # Detect changes
    report = indexer.detect_changes()
    print(f"Changes detected: {report.change_count}")
    print(f"Added: {len(report.added)}")
    print(f"Modified: {len(report.modified)}")
    print(f"Deleted: {len(report.deleted)}")
    
    # Index changes
    indexer.index_changes(report)
    
    # Get stats
    stats = indexer.get_index_stats()
    print(f"\nIndex stats: {stats}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_vault, ignore_errors=True)
    Path("test_index.db").unlink(missing_ok=True)
    
    print("\nIncremental Indexer test completed successfully!")
