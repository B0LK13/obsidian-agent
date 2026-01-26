"""File watching functionality for incremental indexing"""

import logging
from pathlib import Path
from typing import Callable, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class MarkdownFileHandler(FileSystemEventHandler):
    """Handles file events for markdown files
    
    Fixed for Issue #84: Added ignore_patterns instance attribute
    """
    
    # Class-level constant for patterns to ignore
    IGNORE_PATTERNS = [
        "*.tmp",
        "*.swp",
        "*~",
        ".DS_Store",
        ".obsidian/*",
        ".git/*",
        ".trash/*",
    ]
    
    def __init__(
        self,
        callback: Callable[[str, str], None],
        vault_path: Path,
        debounce_ms: int = 500,
    ):
        super().__init__()
        self.callback = callback
        self.vault_path = Path(vault_path)
        self.debounce_ms = debounce_ms
        # Fix for Issue #84: Expose ignore_patterns as instance attribute
        self.ignore_patterns = self.IGNORE_PATTERNS.copy()
    
    def _is_markdown(self, path: str) -> bool:
        """Check if file is a markdown file"""
        return path.endswith(".md")
    
    def _should_ignore(self, path: str) -> bool:
        """Check if file should be ignored based on patterns"""
        from fnmatch import fnmatch
        path_obj = Path(path)
        for pattern in self.ignore_patterns:
            if fnmatch(str(path_obj), pattern) or fnmatch(path_obj.name, pattern):
                return True
        return False
    
    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.src_path):
            if not self._should_ignore(event.src_path):
                self.callback("created", event.src_path)
    
    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.src_path):
            if not self._should_ignore(event.src_path):
                self.callback("modified", event.src_path)
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.src_path):
            if not self._should_ignore(event.src_path):
                self.callback("deleted", event.src_path)


class FileWatcher:
    """Watches vault directory for file changes"""
    
    def __init__(
        self,
        vault_path: Path,
        on_change: Callable[[str, str], None],
        debounce_ms: int = 500,
    ):
        self.vault_path = Path(vault_path)
        self.on_change = on_change
        self.debounce_ms = debounce_ms
        self._observer: Optional[Observer] = None
        self._handler: Optional[MarkdownFileHandler] = None
    
    def start(self) -> None:
        """Start watching for file changes"""
        if self._observer:
            logger.warning("File watcher already running")
            return
        
        self._handler = MarkdownFileHandler(
            callback=self.on_change,
            vault_path=self.vault_path,
            debounce_ms=self.debounce_ms,
        )
        
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(self.vault_path),
            recursive=True,
        )
        self._observer.start()
        logger.info(f"Started watching vault: {self.vault_path}")
    
    def stop(self) -> None:
        """Stop watching for file changes"""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            self._handler = None
        logger.info("Stopped file watcher")
    
    @property
    def handler(self) -> Optional[MarkdownFileHandler]:
        """Get the current handler (for accessing ignore_patterns)"""
        return self._handler
