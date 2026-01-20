"""Vault indexer service"""

import logging
import time
from pathlib import Path
from typing import Callable, List, Optional, Set

from ..config import IndexingConfig, VaultConfig
from ..database import DatabaseConnection, Note, Tag
from ..errors import VaultNotFoundError, VaultError, ErrorCode, ErrorSeverity
from ..vector_store import ChromaDBStore
from .parser import MarkdownParser, ParsedNote

logger = logging.getLogger(__name__)


class VaultIndexer:
    """Service for indexing Obsidian vault"""
    
    def __init__(
        self,
        vault_config: VaultConfig,
        indexing_config: IndexingConfig,
        db: DatabaseConnection,
        vector_store: Optional[ChromaDBStore] = None,
    ):
        self.vault_config = vault_config
        self.indexing_config = indexing_config
        self.db = db
        self.vector_store = vector_store
        self.parser = MarkdownParser(vault_config.path)
        
        self._exclude_folders: Set[str] = set(vault_config.exclude_folders)
    
    def index_vault(
        self,
        incremental: bool = True,
        force: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> dict:
        """Index all notes in the vault"""
        vault_path = self.vault_config.path
        
        if not vault_path.exists():
            raise VaultNotFoundError(str(vault_path))
        
        if not vault_path.is_dir():
            raise VaultError(
                message=f"Vault path is not a directory: {vault_path}",
                code=ErrorCode.VAULT_NOT_FOUND,
            )
        
        start_time = time.time()
        md_files = self._get_markdown_files(vault_path)
        
        stats = {
            "total_files": len(md_files),
            "indexed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0,
        }
        
        existing_checksums = {}
        if incremental and not force:
            existing_checksums = self._get_existing_checksums()
        
        notes_to_index: List[ParsedNote] = []
        
        for i, file_path in enumerate(md_files):
            try:
                parsed = self.parser.parse_file(file_path)
                
                if not force and parsed.checksum in existing_checksums.values():
                    stats["skipped"] += 1
                    continue
                
                notes_to_index.append(parsed)
                
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
                stats["errors"] += 1
            
            if progress_callback:
                progress_callback(i + 1, len(md_files))
        
        if notes_to_index:
            self._save_notes_to_db(notes_to_index)
            stats["indexed"] = len(notes_to_index)
            
            if self.vector_store:
                self._index_to_vector_store(notes_to_index)
        
        stats["duration"] = time.time() - start_time
        
        logger.info(
            f"Indexing complete: {stats['indexed']} indexed, "
            f"{stats['skipped']} skipped, {stats['errors']} errors "
            f"in {stats['duration']:.2f}s"
        )
        
        return stats
    
    def _get_markdown_files(self, vault_path: Path) -> List[Path]:
        """Get all markdown files, respecting exclusions"""
        md_files = []
        
        for file_path in vault_path.rglob("*.md"):
            rel_path = file_path.relative_to(vault_path)
            parts = rel_path.parts
            
            if any(part in self._exclude_folders for part in parts):
                continue
            
            if any(file_path.match(pattern) for pattern in self.vault_config.exclude_patterns):
                continue
            
            md_files.append(file_path)
        
        return md_files
    
    def _get_existing_checksums(self) -> dict:
        """Get existing note checksums from database"""
        checksums = {}
        with self.db.get_session() as session:
            notes = session.query(Note.id, Note.checksum).all()
            checksums = {note.id: note.checksum for note in notes}
        return checksums
    
    def _save_notes_to_db(self, notes: List[ParsedNote]) -> None:
        """Save parsed notes to database"""
        with self.db.get_session() as session:
            for parsed in notes:
                note = Note(
                    id=parsed.id,
                    path=parsed.path,
                    title=parsed.title,
                    content=parsed.content,
                    created_at=parsed.created_at,
                    modified_at=parsed.modified_at,
                    indexed_at=time.time(),
                    checksum=parsed.checksum,
                    metadata=parsed.frontmatter,
                )
                
                session.merge(note)
                
                session.query(Tag).filter(Tag.note_id == parsed.id).delete()
                for tag_name in parsed.tags:
                    tag = Tag(note_id=parsed.id, tag=tag_name)
                    session.add(tag)
    
    def _index_to_vector_store(self, notes: List[ParsedNote]) -> None:
        """Index notes to vector store for semantic search"""
        batch_size = self.indexing_config.batch_size
        
        for i in range(0, len(notes), batch_size):
            batch = notes[i:i + batch_size]
            
            ids = [n.id for n in batch]
            texts = [f"{n.title}\n\n{n.content}" for n in batch]
            metadatas = [{"path": n.path, "title": n.title} for n in batch]
            
            self.vector_store.add_documents(ids, texts, metadatas)
            
            logger.debug(f"Indexed batch {i // batch_size + 1}")
