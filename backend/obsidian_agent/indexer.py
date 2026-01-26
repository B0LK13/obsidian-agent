"""
Vault indexer module for Obsidian Agent
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import And, Term
import frontmatter


class VaultIndexer:
    """Indexes markdown files in an Obsidian vault for fast searching"""
    
    def __init__(self, vault_path: str, index_dir: Optional[str] = None):
        self.vault_path = Path(vault_path).resolve()
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        
        # Default index directory inside vault's .obsidian folder
        if index_dir is None:
            index_dir = self.vault_path / ".obsidian" / "agent-index"
        else:
            index_dir = Path(index_dir)
        
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Define schema for indexed documents
        self.schema = Schema(
            path=ID(stored=True, unique=True),
            title=TEXT(stored=True),
            content=TEXT(stored=True),
            tags=TEXT(stored=True),
            modified=DATETIME(stored=True)
        )
        
        # Create or open the index
        if not exists_in(str(self.index_dir)):
            self.index = create_in(str(self.index_dir), self.schema)
        else:
            self.index = open_dir(str(self.index_dir))
    
    def extract_metadata(self, file_path: Path) -> Dict:
        """Extract metadata and content from a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
            # Extract title from frontmatter or filename
            title = post.get('title', file_path.stem)
            
            # Extract tags
            tags = post.get('tags', [])
            if isinstance(tags, list):
                tags = ' '.join(str(tag) for tag in tags)
            else:
                tags = str(tags)
            
            # Get file modification time
            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            return {
                'path': str(file_path.relative_to(self.vault_path)),
                'title': title,
                'content': post.content,
                'tags': tags,
                'modified': modified
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def index_vault(self, force: bool = False) -> Dict[str, int]:
        """Index all markdown files in the vault"""
        writer = self.index.writer()
        stats = {'indexed': 0, 'skipped': 0, 'errors': 0}
        
        try:
            # Find all markdown files
            md_files = list(self.vault_path.rglob("*.md"))
            
            for md_file in md_files:
                # Skip hidden files and .obsidian folder
                if any(part.startswith('.') for part in md_file.parts):
                    stats['skipped'] += 1
                    continue
                
                metadata = self.extract_metadata(md_file)
                if metadata:
                    try:
                        writer.update_document(**metadata)
                        stats['indexed'] += 1
                    except Exception as e:
                        print(f"Error indexing {md_file}: {e}")
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
            
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise Exception(f"Failed to index vault: {e}")
        
        return stats
    
    def get_stats(self) -> Dict:
        """Get statistics about the indexed vault"""
        with self.index.searcher() as searcher:
            doc_count = searcher.doc_count_all()
            
        vault_files = sum(1 for _ in self.vault_path.rglob("*.md") 
                         if not any(part.startswith('.') for part in _.parts))
        
        return {
            'indexed_documents': doc_count,
            'vault_files': vault_files,
            'vault_path': str(self.vault_path),
            'index_path': str(self.index_dir)
        }
