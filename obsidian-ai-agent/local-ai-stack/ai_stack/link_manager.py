"""
Dead Link Detection and Repair System
Issue #98: Implement Dead Link Detection and Repair

Provides comprehensive link analysis, detection of broken links,
and automated repair suggestions for Obsidian vaults.
"""

import json
import logging
import re
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class LinkType(Enum):
    """Types of links in Obsidian."""
    WIKI = "wiki"           # [[Note Name]]
    WIKI_ALIAS = "wiki_alias"  # [[Note Name|Display Text]]
    MARKDOWN = "markdown"   # [Text](path)
    EMBED = "embed"         # ![[Embedded Note]]
    TAG = "tag"             # #tag
    HEADING = "heading"     # [[Note#Heading]]
    BLOCK = "block"         # [[Note#^block-id]]


class LinkStatus(Enum):
    """Status of a link."""
    VALID = "valid"
    BROKEN = "broken"
    AMBIGUOUS = "ambiguous"  # Multiple possible targets
    EXTERNAL = "external"    # External URL
    ORPHAN = "orphan"        # Target exists but no links point to it


@dataclass
class Link:
    """Represents a single link in a note."""
    source_note: str
    target: str           # The actual link target
    display_text: str     # Display text (if different from target)
    link_type: LinkType
    line_number: int
    column_start: int
    column_end: int
    original_text: str    # The exact text as it appears
    context: str          # Surrounding text for context
    status: LinkStatus = LinkStatus.VALID
    suggestions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        return {
            'source_note': self.source_note,
            'target': self.target,
            'display_text': self.display_text,
            'link_type': self.link_type.value,
            'line_number': self.line_number,
            'column_start': self.column_start,
            'column_end': self.column_end,
            'original_text': self.original_text,
            'context': self.context,
            'status': self.status.value,
            'suggestions': self.suggestions or []
        }


@dataclass
class LinkReport:
    """Comprehensive report of link analysis."""
    total_notes: int
    total_links: int
    broken_links: List[Link]
    ambiguous_links: List[Link]
    orphan_notes: List[str]
    external_links: List[Link]
    valid_links: List[Link]
    scan_duration_ms: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'total_notes': self.total_notes,
            'total_links': self.total_links,
            'broken_count': len(self.broken_links),
            'ambiguous_count': len(self.ambiguous_links),
            'orphan_count': len(self.orphan_notes),
            'external_count': len(self.external_links),
            'valid_count': len(self.valid_links),
            'broken_links': [l.to_dict() for l in self.broken_links],
            'ambiguous_links': [l.to_dict() for l in self.ambiguous_links],
            'orphan_notes': self.orphan_notes,
            'scan_duration_ms': self.scan_duration_ms,
            'timestamp': self.timestamp.isoformat()
        }


class LinkDatabase:
    """SQLite database for storing link information."""
    
    def __init__(self, db_path: str = "links.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self):
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_note TEXT NOT NULL,
                    target TEXT NOT NULL,
                    display_text TEXT,
                    link_type TEXT NOT NULL,
                    line_number INTEGER,
                    column_start INTEGER,
                    column_end INTEGER,
                    original_text TEXT NOT NULL,
                    context TEXT,
                    status TEXT DEFAULT 'valid',
                    suggestions TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_source ON links(source_note);
                CREATE INDEX IF NOT EXISTS idx_target ON links(target);
                CREATE INDEX IF NOT EXISTS idx_status ON links(status);
                
                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    title TEXT,
                    aliases TEXT DEFAULT '[]',
                    last_modified TIMESTAMP,
                    is_orphan BOOLEAN DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_notes_path ON notes(file_path);
                
                CREATE TABLE IF NOT EXISTS link_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_notes INTEGER,
                    total_links INTEGER,
                    broken_count INTEGER,
                    duration_ms REAL
                );
            """)
    
    def add_link(self, link: Link) -> bool:
        """Add a link to the database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO links 
                    (source_note, target, display_text, link_type, line_number,
                     column_start, column_end, original_text, context, status, suggestions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    link.source_note,
                    link.target,
                    link.display_text,
                    link.link_type.value,
                    link.line_number,
                    link.column_start,
                    link.column_end,
                    link.original_text,
                    link.context,
                    link.status.value,
                    json.dumps(link.suggestions or [])
                ))
                return True
        except Exception as e:
            logger.error(f"Failed to add link: {e}")
            return False
    
    def add_note(self, note_id: str, file_path: str, title: str, 
                 aliases: List[str] = None, last_modified: datetime = None) -> bool:
        """Add or update a note in the database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO notes 
                    (note_id, file_path, title, aliases, last_modified)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    note_id,
                    file_path,
                    title,
                    json.dumps(aliases or []),
                    last_modified.isoformat() if last_modified else datetime.utcnow().isoformat()
                ))
                return True
        except Exception as e:
            logger.error(f"Failed to add note: {e}")
            return False
    
    def get_broken_links(self) -> List[Link]:
        """Get all broken links."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM links WHERE status = ?",
                (LinkStatus.BROKEN.value,)
            ).fetchall()
            return [self._row_to_link(row) for row in rows]
    
    def get_links_from_note(self, note_id: str) -> List[Link]:
        """Get all links from a specific note."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM links WHERE source_note = ?",
                (note_id,)
            ).fetchall()
            return [self._row_to_link(row) for row in rows]
    
    def get_links_to_note(self, note_id: str) -> List[Link]:
        """Get all links pointing to a specific note."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM links WHERE target = ?",
                (note_id,)
            ).fetchall()
            return [self._row_to_link(row) for row in rows]
    
    def get_orphan_notes(self) -> List[str]:
        """Get notes with no incoming links."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT n.note_id FROM notes n
                LEFT JOIN links l ON n.note_id = l.target
                WHERE l.target IS NULL
            """).fetchall()
            return [row['note_id'] for row in rows]
    
    def clear(self) -> bool:
        """Clear all link data."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM links")
                conn.execute("DELETE FROM notes")
                return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    
    def _row_to_link(self, row: sqlite3.Row) -> Link:
        """Convert database row to Link object."""
        return Link(
            source_note=row['source_note'],
            target=row['target'],
            display_text=row['display_text'] or '',
            link_type=LinkType(row['link_type']),
            line_number=row['line_number'],
            column_start=row['column_start'],
            column_end=row['column_end'],
            original_text=row['original_text'],
            context=row['context'] or '',
            status=LinkStatus(row['status']),
            suggestions=json.loads(row['suggestions'] or '[]')
        )


class LinkParser:
    """Parse links from markdown content."""
    
    # Regex patterns for different link types
    PATTERNS = {
        LinkType.WIKI: r'\[\[([^\]|#^]+)(?:#[^\]]*)?(?:\^[^\]]*)?\]\]',
        LinkType.WIKI_ALIAS: r'\[\[([^\]|]+)\|([^\]]+)\]\]',
        LinkType.MARKDOWN: r'(?<!!)\[([^\]]+)\]\(([^)]+)\)',
        LinkType.EMBED: r'!\[\[([^\]]+)\]\]',
        LinkType.TAG: r'#([a-zA-Z0-9_\-\/]+)',
        LinkType.HEADING: r'\[\[([^\]]+)#([^\]]+)\]\]',
        LinkType.BLOCK: r'\[\[([^\]]+)\^([^\]]+)\]\]',
    }
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
    
    def parse_note(self, note_path: Path) -> List[Link]:
        """Parse all links from a note."""
        links = []
        note_id = str(note_path.relative_to(self.vault_path)).replace('\\', '/')
        
        try:
            content = note_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line_links = self._parse_line(line, note_id, line_num)
                links.extend(line_links)
        except Exception as e:
            logger.warning(f"Failed to parse {note_path}: {e}")
        
        return links
    
    def _parse_line(self, line: str, note_id: str, line_num: int) -> List[Link]:
        """Parse links from a single line."""
        links = []
        
        # Wiki links with aliases [[Note|Display]]
        for match in re.finditer(self.PATTERNS[LinkType.WIKI_ALIAS], line):
            links.append(self._create_link(
                note_id=note_id,
                target=match.group(1).strip(),
                display_text=match.group(2).strip(),
                link_type=LinkType.WIKI_ALIAS,
                line_num=line_num,
                match=match,
                line=line
            ))
        
        # Remove matched alias links to avoid double-counting
        line_without_aliases = re.sub(self.PATTERNS[LinkType.WIKI_ALIAS], '', line)
        
        # Regular wiki links [[Note]]
        for match in re.finditer(self.PATTERNS[LinkType.WIKI], line_without_aliases):
            target = match.group(1).strip()
            # Skip if this looks like a heading or block reference
            if '#' in target or '^' in target:
                continue
            
            links.append(self._create_link(
                note_id=note_id,
                target=target,
                display_text=target,
                link_type=LinkType.WIKI,
                line_num=line_num,
                match=match,
                line=line
            ))
        
        # Embedded files ![[File]]
        for match in re.finditer(self.PATTERNS[LinkType.EMBED], line):
            links.append(self._create_link(
                note_id=note_id,
                target=match.group(1).strip(),
                display_text=match.group(1).strip(),
                link_type=LinkType.EMBED,
                line_num=line_num,
                match=match,
                line=line
            ))
        
        # Markdown links [Text](path)
        for match in re.finditer(self.PATTERNS[LinkType.MARKDOWN], line):
            target = match.group(2).strip()
            # Skip external URLs for now
            if target.startswith(('http://', 'https://', 'mailto:')):
                continue
            
            links.append(self._create_link(
                note_id=note_id,
                target=target,
                display_text=match.group(1).strip(),
                link_type=LinkType.MARKDOWN,
                line_num=line_num,
                match=match,
                line=line
            ))
        
        return links
    
    def _create_link(
        self,
        note_id: str,
        target: str,
        display_text: str,
        link_type: LinkType,
        line_num: int,
        match: re.Match,
        line: str
    ) -> Link:
        """Create a Link object from regex match."""
        # Get context (surrounding text)
        context_start = max(0, match.start() - 30)
        context_end = min(len(line), match.end() + 30)
        context = line[context_start:context_end]
        
        return Link(
            source_note=note_id,
            target=target,
            display_text=display_text,
            link_type=link_type,
            line_number=line_num,
            column_start=match.start(),
            column_end=match.end(),
            original_text=match.group(0),
            context=context
        )


class LinkRepairSuggester:
    """Generate repair suggestions for broken links."""
    
    def __init__(self, vault_path: str, db: LinkDatabase):
        self.vault_path = Path(vault_path)
        self.db = db
    
    def find_suggestions(self, link: Link, all_notes: Set[str]) -> List[str]:
        """Find suggestions for a broken link."""
        suggestions = []
        target_lower = link.target.lower().replace('.md', '')
        
        # Strategy 1: Case-insensitive match
        for note in all_notes:
            note_name = Path(note).stem.lower()
            if note_name == target_lower:
                suggestions.append(note)
        
        # Strategy 2: Partial match (target is substring of note)
        if len(suggestions) < 3:
            for note in all_notes:
                note_name = Path(note).stem.lower()
                if target_lower in note_name or note_name in target_lower:
                    if note not in suggestions:
                        suggestions.append(note)
        
        # Strategy 3: Similar names (Levenshtein distance would be better)
        if len(suggestions) < 3:
            for note in all_notes:
                note_name = Path(note).stem.lower()
                # Simple similarity: shared words
                target_words = set(target_lower.split())
                note_words = set(note_name.split())
                if target_words & note_words:
                    if note not in suggestions:
                        suggestions.append(note)
        
        return suggestions[:5]  # Limit to top 5


class LinkManager:
    """
    Main link management system for dead link detection and repair.
    """
    
    def __init__(self, vault_path: str, db_path: str = "links.db"):
        self.vault_path = Path(vault_path)
        self.db = LinkDatabase(db_path)
        self.parser = LinkParser(vault_path)
        self.suggester = LinkRepairSuggester(vault_path, self.db)
        self._lock = threading.RLock()
    
    def scan_vault(self) -> LinkReport:
        """
        Scan the entire vault for links and generate a report.
        """
        import time
        start_time = time.time()
        
        with self._lock:
            logger.info("Starting vault link scan...")
            
            # Clear existing data
            self.db.clear()
            
            # Find all markdown files
            all_notes = set()
            note_files = list(self.vault_path.rglob("*.md"))
            
            all_links: List[Link] = []
            valid_links: List[Link] = []
            broken_links: List[Link] = []
            ambiguous_links: List[Link] = []
            external_links: List[Link] = []
            
            # First pass: collect all notes
            for note_path in note_files:
                note_id = str(note_path.relative_to(self.vault_path)).replace('\\', '/')
                all_notes.add(note_id)
                self.db.add_note(
                    note_id=note_id,
                    file_path=str(note_path),
                    title=note_path.stem,
                    last_modified=datetime.fromtimestamp(note_path.stat().st_mtime)
                )
            
            # Second pass: parse links
            for note_path in note_files:
                links = self.parser.parse_note(note_path)
                all_links.extend(links)
                
                # Validate each link
                for link in links:
                    self._validate_link(link, all_notes)
                    
                    if link.status == LinkStatus.VALID:
                        valid_links.append(link)
                    elif link.status == LinkStatus.BROKEN:
                        broken_links.append(link)
                    elif link.status == LinkStatus.AMBIGUOUS:
                        ambiguous_links.append(link)
                    elif link.status == LinkStatus.EXTERNAL:
                        external_links.append(link)
                    
                    # Store in database
                    self.db.add_link(link)
            
            # Find orphan notes
            orphan_notes = self._find_orphans(all_notes, all_links)
            for orphan in orphan_notes:
                with self.db._get_connection() as conn:
                    conn.execute(
                        "UPDATE notes SET is_orphan = 1 WHERE note_id = ?",
                        (orphan,)
                    )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Record scan
            with self.db._get_connection() as conn:
                conn.execute("""
                    INSERT INTO link_scans (total_notes, total_links, broken_count, duration_ms)
                    VALUES (?, ?, ?, ?)
                """, (len(note_files), len(all_links), len(broken_links), duration_ms))
            
            report = LinkReport(
                total_notes=len(note_files),
                total_links=len(all_links),
                broken_links=broken_links,
                ambiguous_links=ambiguous_links,
                orphan_notes=orphan_notes,
                external_links=external_links,
                valid_links=valid_links,
                scan_duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Scan complete: {len(all_links)} links found, "
                       f"{len(broken_links)} broken, {len(orphan_notes)} orphans")
            
            return report
    
    def _validate_link(self, link: Link, all_notes: Set[str]) -> None:
        """Validate a single link against known notes."""
        target = link.target
        
        # Handle external URLs
        if target.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
            link.status = LinkStatus.EXTERNAL
            return
        
        # Normalize target
        target_normalized = target.replace('\\', '/')
        if not target_normalized.endswith('.md'):
            target_normalized += '.md'
        
        # Check for exact match
        if target_normalized in all_notes:
            link.status = LinkStatus.VALID
            return
        
        # Check case-insensitive
        matches = [n for n in all_notes if n.lower() == target_normalized.lower()]
        if len(matches) == 1:
            link.status = LinkStatus.VALID
            return
        elif len(matches) > 1:
            link.status = LinkStatus.AMBIGUOUS
            link.suggestions = matches
            return
        
        # Check if it's a partial path match
        partial_matches = [
            n for n in all_notes 
            if target_normalized.lower() in n.lower() or n.lower().endswith(target_normalized.lower())
        ]
        
        if len(partial_matches) == 1:
            link.status = LinkStatus.AMBIGUOUS
            link.suggestions = partial_matches
        elif len(partial_matches) > 1:
            link.status = LinkStatus.AMBIGUOUS
            link.suggestions = partial_matches[:5]
        else:
            # Truly broken
            link.status = LinkStatus.BROKEN
            link.suggestions = self.suggester.find_suggestions(link, all_notes)
    
    def _find_orphans(self, all_notes: Set[str], all_links: List[Link]) -> List[str]:
        """Find notes with no incoming links."""
        linked_targets = set()
        
        for link in all_links:
            if link.status in (LinkStatus.VALID, LinkStatus.AMBIGUOUS):
                target = link.target
                if not target.endswith('.md'):
                    target += '.md'
                linked_targets.add(target)
        
        # Also check without .md extension
        linked_targets_stems = {Path(t).stem.lower() for t in linked_targets}
        
        orphans = []
        for note in all_notes:
            note_stem = Path(note).stem.lower()
            if note not in linked_targets and note_stem not in linked_targets_stems:
                orphans.append(note)
        
        return sorted(orphans)
    
    def repair_link(self, link: Link, new_target: str) -> bool:
        """
        Repair a broken link by updating the note file.
        Returns True if successful.
        """
        try:
            note_path = self.vault_path / link.source_note
            content = note_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            if link.line_number < 1 or link.line_number > len(lines):
                return False
            
            line = lines[link.line_number - 1]
            
            # Replace the link
            # This is a simple replacement - more complex logic may be needed
            # for preserving formatting
            new_link_text = self._create_replacement_link(link, new_target)
            new_line = (
                line[:link.column_start] + 
                new_link_text + 
                line[link.column_end:]
            )
            
            lines[link.line_number - 1] = new_line
            note_path.write_text('\n'.join(lines), encoding='utf-8')
            
            logger.info(f"Repaired link in {link.source_note}: {link.target} -> {new_target}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to repair link: {e}")
            return False
    
    def _create_replacement_link(self, link: Link, new_target: str) -> str:
        """Create the replacement link text."""
        if link.link_type == LinkType.WIKI:
            return f"[[{new_target}]]"
        elif link.link_type == LinkType.WIKI_ALIAS:
            return f"[[{new_target}|{link.display_text}]]"
        elif link.link_type == LinkType.MARKDOWN:
            return f"[{link.display_text}]({new_target})"
        elif link.link_type == LinkType.EMBED:
            return f"![[{new_target}]]"
        else:
            return f"[[{new_target}]]"
    
    def get_broken_links(self) -> List[Link]:
        """Get all broken links from the database."""
        return self.db.get_broken_links()
    
    def get_orphan_notes(self) -> List[str]:
        """Get all orphan notes."""
        return self.db.get_orphan_notes()
    
    def export_report(self, report: LinkReport, output_path: str) -> bool:
        """Export report to JSON file."""
        try:
            Path(output_path).write_text(
                json.dumps(report.to_dict(), indent=2),
                encoding='utf-8'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create test vault
    test_vault = Path("test_link_vault")
    test_vault.mkdir(exist_ok=True)
    
    # Create test notes
    (test_vault / "Note A.md").write_text("""# Note A

This links to [[Note B]] and [[Missing Note]].
Also see [[Note C|Display Text]].
""")
    
    (test_vault / "Note B.md").write_text("""# Note B

Links back to [[Note A]].
""")
    
    (test_vault / "Note C.md").write_text("""# Note C

No links here - will be orphan.
""")
    
    (test_vault / "orphan.md").write_text("""# Orphan Note

This note has no incoming links.
""")
    
    # Initialize manager and scan
    manager = LinkManager(str(test_vault), "test_links.db")
    report = manager.scan_vault()
    
    # Print report
    print(f"\n=== Link Report ===")
    print(f"Total notes: {report.total_notes}")
    print(f"Total links: {report.total_links}")
    print(f"Valid: {len(report.valid_links)}")
    print(f"Broken: {len(report.broken_links)}")
    print(f"Orphans: {len(report.orphan_notes)}")
    
    if report.broken_links:
        print("\n=== Broken Links ===")
        for link in report.broken_links:
            print(f"  {link.source_note}:{link.line_number} -> {link.target}")
            if link.suggestions:
                print(f"    Suggestions: {link.suggestions}")
    
    if report.orphan_notes:
        print("\n=== Orphan Notes ===")
        for note in report.orphan_notes:
            print(f"  {note}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_vault, ignore_errors=True)
    Path("test_links.db").unlink(missing_ok=True)
    
    print("\nLink Manager test completed successfully!")
