"""File system indexer for PKM Agent."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from pkm_agent.data.database import Database
from pkm_agent.data.file_watcher import FileWatcher
from pkm_agent.data.models import Note
from pkm_agent.exceptions import FileIndexError

logger = logging.getLogger(__name__)


class FileIndexer:
    """Indexes markdown files from the PKM directory."""

    IGNORE_PATTERNS = {
        ".git",
        ".obsidian",
        ".pkm-agent",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
    }

    def __init__(
        self,
        pkm_root: Path,
        database: Database,
        on_progress: Callable[[int, int], None] | None = None,
        watch_mode: bool = False,
    ):
        self.pkm_root = pkm_root
        self.db = database
        self.on_progress = on_progress
        self._indexed_count = 0
        self.watch_mode = watch_mode
        self.watcher: FileWatcher | None = None
        self._pending_updates: asyncio.Queue = asyncio.Queue()

    def index_all(self) -> int:
        """Index all markdown files in the PKM directory."""
        logger.info(f"Starting full index of {self.pkm_root}")

        files = list(self._find_markdown_files())
        total = len(files)
        self._indexed_count = 0

        for i, filepath in enumerate(files):
            try:
                self._index_file(filepath)
                self._indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to index {filepath}: {e}")

            if self.on_progress:
                self.on_progress(i + 1, total)

        logger.info(f"Indexed {self._indexed_count}/{total} files")
        if hasattr(self.db, "log_action"):
            self.db.log_action(
                "indexer",
                "index_all",
                {"indexed": self._indexed_count, "total": total},
            )
        return self._indexed_count

    def index_file(self, filepath: Path) -> Note | None:
        """Index a single file."""
        return self._index_file(filepath)

    def _index_file(self, filepath: Path) -> Note | None:
        """Index a single markdown file."""
        if not filepath.exists():
            return None

        try:
            note = Note.from_file(filepath, self.pkm_root)
            self.db.upsert_note(note)
            logger.debug(f"Indexed: {note.path}")
            return note
        except Exception as e:
            logger.error(f"Error indexing {filepath}: {e}")
            return None

    def _find_markdown_files(self) -> list[Path]:
        """Find all markdown files in the PKM directory."""
        files = []

        for path in self.pkm_root.rglob("*.md"):
            # Skip ignored directories
            if any(part in self.IGNORE_PATTERNS for part in path.parts):
                continue

            if path.is_file():
                files.append(path)

        return sorted(files)

    def get_modified_files(self, since: datetime) -> list[Path]:
        """Get files modified since a given time."""
        modified = []

        for filepath in self._find_markdown_files():
            if datetime.fromtimestamp(filepath.stat().st_mtime) > since:
                modified.append(filepath)

        return modified

    def sync(self) -> dict:
        """Sync the index with file system changes."""
        # Get all indexed paths
        indexed_notes = self.db.get_all_notes(limit=100000)
        indexed_paths = {str(note.path) for note in indexed_notes}

        # Get all current files
        current_files = self._find_markdown_files()
        current_paths = {str(f.relative_to(self.pkm_root)) for f in current_files}

        # Find new files
        new_paths = current_paths - indexed_paths
        # Find deleted files
        deleted_paths = indexed_paths - current_paths

        stats = {"added": 0, "updated": 0, "deleted": 0}

        # Index new files
        for rel_path in new_paths:
            filepath = self.pkm_root / rel_path
            if self._index_file(filepath):
                stats["added"] += 1

        # Check for updates
        for note in indexed_notes:
            filepath = self.pkm_root / note.path
            if filepath.exists():
                current_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if current_mtime > note.modified_at:
                    if self._index_file(filepath):
                        stats["updated"] += 1

        # Remove deleted notes
        for rel_path in deleted_paths:
            note = self.db.get_note_by_path(rel_path)
            if note:
                self.db.delete_note(note.id)
                stats["deleted"] += 1

        logger.info(f"Sync complete: {stats}")
        if hasattr(self.db, "log_action"):
            self.db.log_action(
                "indexer",
                "sync",
                {"added": stats["added"], "updated": stats["updated"], "deleted": stats["deleted"]},
            )
        return stats

    def start_watch_mode(self):
        """Start file system watcher for incremental updates."""
        if self.watcher and self.watcher.running:
            logger.warning("Watch mode already started")
            return

        logger.info("Starting watch mode for incremental indexing")

        self.watcher = FileWatcher(
            pkm_root=self.pkm_root,
            on_created=self._on_file_created,
            on_modified=self._on_file_modified,
            on_deleted=self._on_file_deleted,
        )

        self.watcher.start()
        logger.info("Watch mode started successfully")

    def stop_watch_mode(self):
        """Stop file system watcher."""
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
            logger.info("Watch mode stopped")

    def _on_file_created(self, filepath: Path):
        """Handle file creation event."""
        try:
            logger.debug(f"Handling file creation: {filepath}")
            note = self._index_file(filepath)

            if note and hasattr(self.db, "log_action"):
                self.db.log_action(
                    "indexer",
                    "file_created",
                    {"filepath": str(filepath), "note_id": note.id}
                )
        except Exception as e:
            logger.error(f"Error indexing created file {filepath}: {e}")
            raise FileIndexError(str(filepath), f"Failed to index created file: {e}")

    def _on_file_modified(self, filepath: Path):
        """Handle file modification event."""
        try:
            logger.debug(f"Handling file modification: {filepath}")
            note = self._index_file(filepath)

            if note and hasattr(self.db, "log_action"):
                self.db.log_action(
                    "indexer",
                    "file_modified",
                    {"filepath": str(filepath), "note_id": note.id}
                )
        except Exception as e:
            logger.error(f"Error reindexing modified file {filepath}: {e}")
            raise FileIndexError(str(filepath), f"Failed to reindex modified file: {e}")

    def _on_file_deleted(self, filepath: Path):
        """Handle file deletion event."""
        try:
            logger.debug(f"Handling file deletion: {filepath}")

            # Get relative path
            rel_path = filepath.relative_to(self.pkm_root)

            # Find and delete note
            note = self.db.get_note_by_path(str(rel_path))
            if note:
                self.db.delete_note(note.id)

                if hasattr(self.db, "log_action"):
                    self.db.log_action(
                        "indexer",
                        "file_deleted",
                        {"filepath": str(filepath), "note_id": note.id}
                    )

                logger.info(f"Deleted note for file: {filepath}")
        except Exception as e:
            logger.error(f"Error handling file deletion {filepath}: {e}")
            # Don't raise exception for deletions as file may already be gone
