"""File watching for incremental vault indexing."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Awaitable, Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class FileEventType(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """Represents a file system event."""
    event_type: FileEventType
    path: Path
    old_path: Path | None = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MarkdownEventHandler(FileSystemEventHandler):
    """Handles file events for markdown files."""
    
    def __init__(
        self,
        callback: Callable[[FileEvent], Awaitable[None]],
        loop: asyncio.AbstractEventLoop,
        debounce_ms: int = 500,
    ):
        super().__init__()
        self.callback = callback
        self.loop = loop
        self.debounce_ms = debounce_ms
        self._pending: dict[str, asyncio.TimerHandle] = {}
        self._lock = asyncio.Lock()
    
    def _is_markdown(self, path: str) -> bool:
        return path.endswith(".md")
    
    def _schedule_callback(self, event: FileEvent) -> None:
        """Schedule callback with debouncing."""
        key = str(event.path)
        
        # Cancel pending callback for same file
        if key in self._pending:
            self._pending[key].cancel()
        
        async def run_callback():
            async with self._lock:
                if key in self._pending:
                    del self._pending[key]
            try:
                await self.callback(event)
            except Exception as e:
                logger.error(f"Error in file watcher callback: {e}")
        
        # Schedule new callback
        handle = self.loop.call_later(
            self.debounce_ms / 1000,
            lambda: asyncio.run_coroutine_threadsafe(run_callback(), self.loop),
        )
        self._pending[key] = handle
    
    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.src_path):
            self._schedule_callback(FileEvent(
                event_type=FileEventType.CREATED,
                path=Path(event.src_path),
            ))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.src_path):
            self._schedule_callback(FileEvent(
                event_type=FileEventType.MODIFIED,
                path=Path(event.src_path),
            ))
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.src_path):
            self._schedule_callback(FileEvent(
                event_type=FileEventType.DELETED,
                path=Path(event.src_path),
            ))
    
    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_markdown(event.dest_path):
            self._schedule_callback(FileEvent(
                event_type=FileEventType.MOVED,
                path=Path(event.dest_path),
                old_path=Path(event.src_path),
            ))


class FileWatcher:
    """Watches vault directory for file changes and triggers incremental indexing."""
    
    def __init__(
        self,
        vault_path: Path,
        on_change: Callable[[FileEvent], Awaitable[None]],
        debounce_ms: int = 500,
        recursive: bool = True,
    ):
        self.vault_path = Path(vault_path)
        self.on_change = on_change
        self.debounce_ms = debounce_ms
        self.recursive = recursive
        self._observer: Observer | None = None
        self._running = False
        self._stats = {
            "events_processed": 0,
            "files_indexed": 0,
            "errors": 0,
            "started_at": None,
        }
    
    async def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            logger.warning("File watcher already running")
            return
        
        loop = asyncio.get_event_loop()
        handler = MarkdownEventHandler(
            callback=self._handle_event,
            loop=loop,
            debounce_ms=self.debounce_ms,
        )
        
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self.vault_path),
            recursive=self.recursive,
        )
        self._observer.start()
        self._running = True
        self._stats["started_at"] = datetime.now()
        
        logger.info(f"Started watching vault: {self.vault_path}")
    
    async def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        self._running = False
        logger.info("Stopped file watcher")
    
    async def _handle_event(self, event: FileEvent) -> None:
        """Handle a file event and trigger indexing."""
        self._stats["events_processed"] += 1
        
        try:
            await self.on_change(event)
            self._stats["files_indexed"] += 1
            logger.debug(f"Processed {event.event_type.value}: {event.path}")
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Error processing {event.path}: {e}")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def get_stats(self) -> dict[str, Any]:
        stats = self._stats.copy()
        if stats["started_at"]:
            stats["uptime_seconds"] = (datetime.now() - stats["started_at"]).total_seconds()
        return stats
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        return False
