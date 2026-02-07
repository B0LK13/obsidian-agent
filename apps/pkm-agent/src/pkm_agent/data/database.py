"""SQLite database for PKM Agent."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for PKM Agent."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    frontmatter TEXT,
                    word_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    modified_at TEXT,
                    indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                    UNIQUE(note_id, tag)
                );
                
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    link_text TEXT,
                    FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_notes_path ON notes(path);
                CREATE INDEX IF NOT EXISTS idx_tags_note ON tags(note_id);
                CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
                CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id);
                CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
            """)

    @contextmanager
    def _get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_action(self, category: str, action: str, metadata: dict[str, Any]):
        """Log an action to the audit log."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO audit_logs (category, action, metadata) VALUES (?, ?, ?)",
                (category, action, json.dumps(metadata))
            )

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            notes = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            tags = conn.execute("SELECT COUNT(DISTINCT tag) FROM tags").fetchone()[0]
            links = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
            words = conn.execute("SELECT COALESCE(SUM(word_count), 0) FROM notes").fetchone()[0]

        return {
            "notes": notes,
            "tags": tags,
            "links": links,
            "total_words": words,
        }

    def get_all_notes(self, limit: int = 1000) -> list[Any]:
        """Get all notes from database."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY modified_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_note_by_path(self, path: str) -> dict[str, Any] | None:
        """Get a note by its path."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE path = ?",
                (path,)
            ).fetchone()
        return dict(row) if row else None

    def upsert_note(self, note: dict[str, Any]) -> str:
        """Insert or update a note."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO notes (id, path, title, content, frontmatter, word_count, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content,
                    frontmatter = excluded.frontmatter,
                    word_count = excluded.word_count,
                    modified_at = excluded.modified_at,
                    indexed_at = CURRENT_TIMESTAMP
            """, (
                note["id"],
                note["path"],
                note["title"],
                note.get("content", ""),
                json.dumps(note.get("frontmatter", {})),
                note.get("word_count", 0),
                note.get("created_at"),
                note.get("modified_at"),
            ))
        return note["id"]

    def delete_note(self, note_id: str):
        """Delete a note by ID."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    def create_conversation(self, conversation_id: str):
        """Create a new conversation."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id) VALUES (?)",
                (conversation_id,)
            )

    def add_message(self, conversation_id: str, role: str, content: str, model: str | None = None):
        """Add a message to a conversation."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, model) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, model)
            )
            conn.execute(
                "UPDATE conversations SET message_count = message_count + 1 WHERE id = ?",
                (conversation_id,)
            )

    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get messages from a conversation."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at LIMIT ?",
                (conversation_id, limit)
            ).fetchall()
        return [dict(row) for row in rows]
