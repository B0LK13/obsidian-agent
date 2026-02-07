"""
File system watcher for incremental indexing.

Uses watchdog library to monitor PKM directory for changes and trigger
incremental reindexing of modified files.
"""

import logging
from collections.abc import Callable
from pathlib import Path

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class MarkdownFileHandler(FileSystemEventHandler):
    """Handler for markdown file system events."""

    IGNORE_PATTERNS = {
        ".git",
        ".obsidian",
        ".pkm-agent",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".DS_Store",
        "Thumbs.db"
    }

    def __init__(
        self,
        on_created: Callable[[Path], None] | None = None,
        on_modified: Callable[[Path], None] | None = None,
        on_deleted: Callable[[Path], None] | None = None,
        ignore_patterns: set[str] | None = None,
    ):
        super().__init__()
        self.on_created_callback = on_created
        self.on_modified_callback = on_modified
        self.on_deleted_callback = on_deleted
        self._processing: set[str] = set()  # Prevent duplicate processing
        self.ignore_patterns = ignore_patterns or self.IGNORE_PATTERNS

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        # Check if any part of path matches ignore patterns
        for part in path.parts:
            if part in self.IGNORE_PATTERNS:
                return True

        # Only process markdown files
        if path.suffix != '.md':
            return True

        return False

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        if self._should_ignore(filepath):
            return

        # Prevent duplicate processing
        if filepath.as_posix() in self._processing:
            return

        try:
            self._processing.add(filepath.as_posix())
            logger.info(f"File created: {filepath}")

            if self.on_created_callback:
                self.on_created_callback(filepath)

        finally:
            self._processing.discard(filepath.as_posix())

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification event."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        if self._should_ignore(filepath):
            return

        # Prevent duplicate processing
        if filepath.as_posix() in self._processing:
            return

        try:
            self._processing.add(filepath.as_posix())
            logger.info(f"File modified: {filepath}")

            if self.on_modified_callback:
                self.on_modified_callback(filepath)

        finally:
            self._processing.discard(filepath.as_posix())

    def on_deleted(self, event: FileDeletedEvent):
        """Handle file deletion event."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        if self._should_ignore(filepath):
            return

        try:
            logger.info(f"File deleted: {filepath}")

            if self.on_deleted_callback:
                self.on_deleted_callback(filepath)

        except Exception as e:
            logger.error(f"Error handling file deletion: {e}")


class FileWatcher:
    """File system watcher for PKM directory."""

    def __init__(
        self,
        pkm_root: Path,
        on_created: Callable[[Path], None] | None = None,
        on_modified: Callable[[Path], None] | None = None,
        on_deleted: Callable[[Path], None] | None = None,
        ignore_patterns: set[str] | None = None,
    ):
        self.pkm_root = pkm_root
        self.observer = Observer()
        self.handler = MarkdownFileHandler(
            on_created=on_created,
            on_modified=on_modified,
            on_deleted=on_deleted,
            ignore_patterns=ignore_patterns,
        )
        self.running = False

    @property
    def ignore_patterns(self) -> set[str]:
        """Get ignore patterns."""
        return self.handler.ignore_patterns

    @ignore_patterns.setter
    def ignore_patterns(self, patterns: set[str]):
        """Set ignore patterns."""
        self.handler.ignore_patterns = patterns

    def start(self):
        """Start watching the PKM directory."""
        if self.running:
            logger.warning("File watcher already running")
            return

        logger.info(f"Starting file watcher for {self.pkm_root}")

        self.observer.schedule(
            self.handler,
            str(self.pkm_root),
            recursive=True
        )

        self.observer.start()
        self.running = True

        logger.info("File watcher started successfully")

    def stop(self):
        """Stop watching the PKM directory."""
        if not self.running:
            return

        logger.info("Stopping file watcher...")

        self.observer.stop()
        self.observer.join(timeout=5)
        self.running = False

        logger.info("File watcher stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
