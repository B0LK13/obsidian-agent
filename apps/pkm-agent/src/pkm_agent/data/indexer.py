"""File indexer for PKM Agent."""

import hashlib
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter

logger = logging.getLogger(__name__)


def _serialize_frontmatter(metadata: dict) -> dict:
    """Convert frontmatter metadata to JSON-serializable dict."""
    result = {}
    for key, value in metadata.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = _serialize_frontmatter(value)
        elif isinstance(value, list):
            result[key] = [
                v.isoformat() if isinstance(v, (date, datetime)) else v
                for v in value
            ]
        else:
            result[key] = value
    return result


class FileIndexer:
    """Index markdown files from PKM directory."""

    def __init__(self, pkm_root: Path, db, watch_mode: bool = False):
        self.pkm_root = Path(pkm_root)
        self.db = db
        self.watch_mode = watch_mode
        self._observer = None

    def index_all(self) -> int:
        """Index all markdown files in PKM root."""
        count = 0
        
        if not self.pkm_root.exists():
            logger.warning(f"PKM root does not exist: {self.pkm_root}")
            return 0

        for md_file in self.pkm_root.rglob("*.md"):
            try:
                self.index_file(md_file)
                count += 1
            except Exception as e:
                logger.error(f"Error indexing {md_file}: {e}")

        logger.info(f"Indexed {count} files from {self.pkm_root}")
        return count

    def index_file(self, filepath: Path) -> dict[str, Any] | None:
        """Index a single markdown file."""
        try:
            rel_path = filepath.relative_to(self.pkm_root)
            
            # Read file content
            content = filepath.read_text(encoding="utf-8")
            
            # Parse frontmatter
            post = frontmatter.loads(content)
            
            # Generate note ID from path
            note_id = hashlib.md5(str(rel_path).encode()).hexdigest()
            
            # Extract title
            title = post.get("title", filepath.stem)
            
            # Count words
            word_count = len(post.content.split())
            
            # Get file timestamps
            stat = filepath.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            note = {
                "id": note_id,
                "path": str(rel_path),
                "title": title,
                "content": post.content,
                "frontmatter": _serialize_frontmatter(dict(post.metadata)),
                "word_count": word_count,
                "created_at": created_at,
                "modified_at": modified_at,
            }
            
            # Save to database
            self.db.upsert_note(note)
            
            # Extract and save tags
            tags = post.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            
            # Extract and save links
            links = self._extract_links(post.content)
            
            logger.debug(f"Indexed: {rel_path} ({word_count} words, {len(tags)} tags, {len(links)} links)")
            
            return note
            
        except Exception as e:
            logger.error(f"Error indexing {filepath}: {e}")
            return None

    def _extract_links(self, content: str) -> list[str]:
        """Extract wiki-style links from content."""
        # Match [[link]] and [[link|alias]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        matches = re.findall(pattern, content)
        return list(set(matches))

    def start_watch_mode(self):
        """Start watching for file changes."""
        if not self.watch_mode:
            return
        
        # Create directory if it doesn't exist
        if not self.pkm_root.exists():
            self.pkm_root.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created PKM root directory: {self.pkm_root}")
            
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class Handler(FileSystemEventHandler):
                def __init__(self, indexer):
                    self.indexer = indexer
                    
                def on_created(self, event):
                    if event.src_path.endswith(".md"):
                        self.indexer.index_file(Path(event.src_path))
                        
                def on_modified(self, event):
                    if event.src_path.endswith(".md"):
                        self.indexer.index_file(Path(event.src_path))
                        
                def on_deleted(self, event):
                    if event.src_path.endswith(".md"):
                        # Handle deletion
                        pass
            
            self._observer = Observer()
            path = str(self.pkm_root)
            self._observer.schedule(Handler(self), path, recursive=True)
            try:
                self._observer.start()
                logger.info(f"Started file watcher on {self.pkm_root}")
            except OSError as exc:
                logger.warning(f"Unable to start file watcher on {self.pkm_root}: {exc}")
                self._observer = None
            
        except ImportError:
            logger.warning("watchdog not installed, file watching disabled")

    def stop_watch_mode(self):
        """Stop watching for file changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped file watcher")

    async def _on_file_created(self, path: Path):
        """Handle file creation event."""
        self.index_file(path)

    async def _on_file_modified(self, path: Path):
        """Handle file modification event."""
        self.index_file(path)

    async def _on_file_deleted(self, path: Path):
        """Handle file deletion event."""
        rel_path = path.relative_to(self.pkm_root)
        note = self.db.get_note_by_path(str(rel_path))
        if note:
            self.db.delete_note(note["id"])
