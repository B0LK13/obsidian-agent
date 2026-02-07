"""Link analysis and detection for PKM notes."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pkm_agent.exceptions import ValidationError, IndexingError

logger = logging.getLogger(__name__)


class LinkType(Enum):
    """Types of links found in markdown notes."""
    WIKILINK = "wikilink"  # [[Note Title]]
    MARKDOWN = "markdown"  # [text](path)
    EMBED = "embed"  # ![[Note Title]] or ![](path)
    TAG = "tag"  # #tag


@dataclass
class Link:
    """Represents a link found in a markdown note."""
    source_path: str  # Path of note containing the link
    target: str  # The link target (note title or path)
    link_type: LinkType
    line_number: int
    column: int
    display_text: str | None = None  # For markdown links
    is_broken: bool = False

    def __str__(self) -> str:
        return f"{self.link_type.value}: {self.target} (line {self.line_number})"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "source_path": self.source_path,
            "target": self.target,
            "link_type": self.link_type.value,
            "line_number": self.line_number,
            "column": self.column,
            "display_text": self.display_text,
            "is_broken": self.is_broken,
        }


@dataclass
class LinkAnalysisResult:
    """Results of link analysis for a vault or note."""
    total_links: int
    broken_links: list[Link]
    orphan_notes: list[str]  # Notes with no incoming links
    hub_notes: list[tuple[str, int]]  # Notes with most incoming links
    link_graph: dict[str, set[str]]  # Source -> targets mapping

    def __str__(self) -> str:
        return (
            f"Link Analysis Results:\n"
            f"  Total Links: {self.total_links}\n"
            f"  Broken Links: {len(self.broken_links)}\n"
            f"  Orphan Notes: {len(self.orphan_notes)}\n"
            f"  Hub Notes: {len(self.hub_notes)}"
        )


class LinkAnalyzer:
    """Analyzes links in markdown notes."""

    # Regex patterns for different link types
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
    EMBED_PATTERN = re.compile(r'!\[\[([^\]]+)\]\]')
    MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    TAG_PATTERN = re.compile(r'(?:^|\s)#([a-zA-Z0-9_/-]+)')

    def __init__(self, vault_root: Path):
        """
        Initialize link analyzer.

        Args:
            vault_root: Root directory of the vault
        """
        if not vault_root.exists():
            raise ValidationError(f"Vault root does not exist: {vault_root}")

        self.vault_root = vault_root
        self._note_cache: dict[str, Path] = {}  # title -> path mapping
        self._build_note_cache()

    def _build_note_cache(self) -> None:
        """Build cache of note titles to paths for fast lookup."""
        try:
            for md_file in self.vault_root.rglob("*.md"):
                # Use filename without extension as title
                title = md_file.stem
                relative_path = md_file.relative_to(self.vault_root)
                self._note_cache[title] = relative_path

                # Also cache with full path for subfolders
                path_without_ext = str(relative_path.with_suffix(''))
                self._note_cache[path_without_ext] = relative_path

            logger.info(f"Built note cache with {len(self._note_cache)} entries")
        except Exception as e:
            raise IndexingError(f"Failed to build note cache: {e}", {"vault_root": str(self.vault_root)})

    def extract_links(self, file_path: Path, content: str | None = None) -> list[Link]:
        """
        Extract all links from a markdown file.

        Args:
            file_path: Path to the markdown file
            content: Optional file content (reads from disk if not provided)

        Returns:
            List of Link objects found in the file
        """
        if content is None:
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                raise IndexingError(
                    f"Failed to read file: {e}",
                    {"file_path": str(file_path)}
                )

        links: list[Link] = []
        relative_path = str(file_path.relative_to(self.vault_root))

        # Process line by line for accurate line numbers
        for line_num, line in enumerate(content.split('\n'), start=1):
            # Extract embedded links first (they contain wikilink pattern)
            for match in self.EMBED_PATTERN.finditer(line):
                target = match.group(1).split('|')[0].strip()  # Remove alias
                links.append(Link(
                    source_path=relative_path,
                    target=target,
                    link_type=LinkType.EMBED,
                    line_number=line_num,
                    column=match.start(),
                ))

            # Remove embedded links to avoid double-counting
            line_without_embeds = self.EMBED_PATTERN.sub('', line)

            # Extract wikilinks
            for match in self.WIKILINK_PATTERN.finditer(line_without_embeds):
                target = match.group(1).split('|')[0].strip()  # Remove alias
                links.append(Link(
                    source_path=relative_path,
                    target=target,
                    link_type=LinkType.WIKILINK,
                    line_number=line_num,
                    column=match.start(),
                ))

            # Extract markdown links
            for match in self.MARKDOWN_LINK_PATTERN.finditer(line):
                display_text = match.group(1)
                target = match.group(2)
                # Skip external URLs
                if not target.startswith(('http://', 'https://', 'ftp://')):
                    links.append(Link(
                        source_path=relative_path,
                        target=target,
                        link_type=LinkType.MARKDOWN,
                        line_number=line_num,
                        column=match.start(),
                        display_text=display_text,
                    ))

            # Extract tags
            for match in self.TAG_PATTERN.finditer(line):
                tag = match.group(1)
                links.append(Link(
                    source_path=relative_path,
                    target=tag,
                    link_type=LinkType.TAG,
                    line_number=line_num,
                    column=match.start(),
                ))

        return links

    def check_link_validity(self, link: Link) -> bool:
        """
        Check if a link target exists in the vault.

        Args:
            link: Link object to validate

        Returns:
            True if link target exists, False otherwise
        """
        # Tags are always valid (they don't point to files)
        if link.link_type == LinkType.TAG:
            return True

        # For wikilinks and embeds, check note cache
        if link.link_type in (LinkType.WIKILINK, LinkType.EMBED):
            # Check direct title match
            if link.target in self._note_cache:
                return True

            # Check with .md extension
            if f"{link.target}.md" in self._note_cache:
                return True

            return False

        # For markdown links, resolve relative path
        if link.link_type == LinkType.MARKDOWN:
            source_file = self.vault_root / link.source_path
            source_dir = source_file.parent

            # Resolve relative path
            target_path = (source_dir / link.target).resolve()

            # Check if within vault and exists
            try:
                target_path.relative_to(self.vault_root)
                return target_path.exists()
            except ValueError:
                # Outside vault
                return False

        return False

    def find_broken_links(self, file_path: Path | None = None) -> list[Link]:
        """
        Find all broken links in a file or entire vault.

        Args:
            file_path: Optional specific file to check (checks entire vault if None)

        Returns:
            List of broken Link objects
        """
        broken_links: list[Link] = []

        if file_path:
            files_to_check = [file_path]
        else:
            files_to_check = list(self.vault_root.rglob("*.md"))

        for md_file in files_to_check:
            try:
                links = self.extract_links(md_file)
                for link in links:
                    if not self.check_link_validity(link):
                        link.is_broken = True
                        broken_links.append(link)
            except Exception as e:
                logger.error(f"Error checking links in {md_file}: {e}")

        return broken_links

    def analyze_vault(self) -> LinkAnalysisResult:
        """
        Perform comprehensive link analysis on entire vault.

        Returns:
            LinkAnalysisResult with statistics and broken links
        """
        logger.info("Starting vault link analysis...")

        all_links: list[Link] = []
        broken_links: list[Link] = []
        link_graph: dict[str, set[str]] = {}
        incoming_links: dict[str, int] = {}

        # Analyze all markdown files
        for md_file in self.vault_root.rglob("*.md"):
            try:
                relative_path = str(md_file.relative_to(self.vault_root))
                links = self.extract_links(md_file)
                all_links.extend(links)

                # Build link graph (excluding tags)
                targets = set()
                for link in links:
                    if link.link_type != LinkType.TAG:
                        if not self.check_link_validity(link):
                            link.is_broken = True
                            broken_links.append(link)
                        else:
                            targets.add(link.target)
                            # Track incoming links
                            incoming_links[link.target] = incoming_links.get(link.target, 0) + 1

                if targets:
                    link_graph[relative_path] = targets

            except Exception as e:
                logger.error(f"Error analyzing {md_file}: {e}")

        # Find orphan notes (no incoming links)
        all_notes = set(str(p.relative_to(self.vault_root)) for p in self.vault_root.rglob("*.md"))
        linked_notes = set(incoming_links.keys())
        orphan_notes = list(all_notes - linked_notes)

        # Find hub notes (most incoming links)
        hub_notes = sorted(incoming_links.items(), key=lambda x: x[1], reverse=True)[:10]

        result = LinkAnalysisResult(
            total_links=len([l for l in all_links if l.link_type != LinkType.TAG]),
            broken_links=broken_links,
            orphan_notes=orphan_notes,
            hub_notes=hub_notes,
            link_graph=link_graph,
        )

        logger.info(f"Link analysis complete: {result}")
        return result
