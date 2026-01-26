"""Markdown parser for Obsidian notes"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter

logger = logging.getLogger(__name__)


@dataclass
class ParsedNote:
    """Parsed note data"""
    id: str
    path: str
    title: str
    content: str
    raw_content: str
    frontmatter: Dict[str, Any]
    tags: List[str]
    links: List[str]
    embeds: List[str]
    headings: List[str]
    checksum: str
    created_at: Optional[float] = None
    modified_at: Optional[float] = None


class MarkdownParser:
    """Parser for Obsidian markdown notes"""
    
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
    TAG_PATTERN = re.compile(r'(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/-]*)')
    EMBED_PATTERN = re.compile(r'!\[\[([^\]]+)\]\]')
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
    
    def parse_file(self, file_path: Path) -> ParsedNote:
        """Parse a markdown file into a ParsedNote"""
        try:
            raw_content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            raw_content = file_path.read_text(encoding='latin-1')
        
        post = frontmatter.loads(raw_content)
        content = post.content
        fm = dict(post.metadata)
        
        rel_path = str(file_path.relative_to(self.vault_path))
        note_id = hashlib.md5(rel_path.encode()).hexdigest()
        
        title = fm.get('title') or file_path.stem
        
        tags = self._extract_tags(content, fm)
        links = self._extract_links(content)
        embeds = self._extract_embeds(content)
        headings = self._extract_headings(content)
        
        stat = file_path.stat()
        checksum = hashlib.md5(raw_content.encode()).hexdigest()
        
        return ParsedNote(
            id=note_id,
            path=rel_path,
            title=title,
            content=content,
            raw_content=raw_content,
            frontmatter=fm,
            tags=tags,
            links=links,
            embeds=embeds,
            headings=headings,
            checksum=checksum,
            created_at=stat.st_ctime,
            modified_at=stat.st_mtime,
        )
    
    def _extract_tags(self, content: str, fm: Dict[str, Any]) -> List[str]:
        """Extract tags from content and frontmatter"""
        tags = set()
        
        fm_tags = fm.get('tags', [])
        if isinstance(fm_tags, str):
            fm_tags = [t.strip() for t in fm_tags.split(',')]
        tags.update(fm_tags)
        
        inline_tags = self.TAG_PATTERN.findall(content)
        tags.update(inline_tags)
        
        return list(tags)
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract wikilinks from content"""
        return self.WIKILINK_PATTERN.findall(content)
    
    def _extract_embeds(self, content: str) -> List[str]:
        """Extract embeds from content"""
        return self.EMBED_PATTERN.findall(content)
    
    def _extract_headings(self, content: str) -> List[str]:
        """Extract headings from content"""
        matches = self.HEADING_PATTERN.findall(content)
        return [text for _, text in matches]
