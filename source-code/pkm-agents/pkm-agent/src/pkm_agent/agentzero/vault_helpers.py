"""
Advanced helper utilities for Obsidian vault operations.

This module provides high-level utilities for:
- Daily note integration
- Template support
- Backlink management
- Attachment handling
- Batch operations
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .mcp_client import ObsidianMCPClient

from .types import (
    Attachment,
    BatchOperation,
    BatchOperationType,
    FrontmatterUpdate,
    Link,
    NoteResult,
    NoteSpec,
    PeriodicNoteType,
    TemplateSpec,
)

logger = logging.getLogger(__name__)


class VaultHelpers:
    """Advanced helper utilities for Obsidian vault operations."""

    def __init__(self, client: "ObsidianMCPClient"):
        """Initialize vault helpers with an Obsidian MCP client."""
        self.client = client
        self._templates_cache: dict[str, TemplateSpec] = {}
        self._daily_note_format = "%Y-%m-%d"
        self._daily_note_folder = "Daily Notes"
        self._templates_folder = "Templates"
        self._attachments_folder = "attachments"

    def configure(
        self,
        daily_note_format: str = "%Y-%m-%d",
        daily_note_folder: str = "Daily Notes",
        templates_folder: str = "Templates",
        attachments_folder: str = "attachments",
    ):
        """Configure vault helper settings."""
        self._daily_note_format = daily_note_format
        self._daily_note_folder = daily_note_folder
        self._templates_folder = templates_folder
        self._attachments_folder = attachments_folder

    # =========================================================================
    # Daily Note Integration
    # =========================================================================

    def get_daily_note_path(self, date: datetime | None = None) -> str:
        """Get the path for a daily note."""
        if date is None:
            date = datetime.now()
        filename = date.strftime(self._daily_note_format)
        return f"{self._daily_note_folder}/{filename}.md"

    async def ensure_daily_note(
        self, date: datetime | None = None, template: str | None = None
    ) -> NoteResult:
        """Get or create today's daily note."""
        path = self.get_daily_note_path(date)

        try:
            # Try to read existing note
            result = await self.client.read_note(path)
            return NoteResult(
                path=path,
                success=True,
                content=result.get("content", ""),
                created=False,
                modified=False,
            )
        except Exception:
            # Note doesn't exist, create it
            content = ""
            if template:
                template_content = await self.get_template(template)
                if template_content:
                    # Substitute date variables
                    target_date = date or datetime.now()
                    content = self._substitute_date_variables(template_content, target_date)

            if not content:
                # Default daily note content
                target_date = date or datetime.now()
                content = f"# {target_date.strftime('%A, %B %d, %Y')}\n\n## Tasks\n\n- [ ] \n\n## Notes\n\n"

            try:
                await self.client.create_note(path, content)
                return NoteResult(
                    path=path, success=True, content=content, created=True, modified=False
                )
            except Exception as e:
                return NoteResult(path=path, success=False, error=str(e))

    async def get_periodic_note(
        self, period: PeriodicNoteType, date: datetime | None = None
    ) -> NoteResult:
        """Get a periodic note (daily, weekly, monthly, etc.)."""
        if date is None:
            date = datetime.now()

        # Determine path based on period type
        if period == PeriodicNoteType.DAILY:
            path = self.get_daily_note_path(date)
        elif period == PeriodicNoteType.WEEKLY:
            week_num = date.isocalendar()[1]
            path = f"Weekly Notes/{date.year}-W{week_num:02d}.md"
        elif period == PeriodicNoteType.MONTHLY:
            path = f"Monthly Notes/{date.strftime('%Y-%m')}.md"
        elif period == PeriodicNoteType.QUARTERLY:
            quarter = (date.month - 1) // 3 + 1
            path = f"Quarterly Notes/{date.year}-Q{quarter}.md"
        elif period == PeriodicNoteType.YEARLY:
            path = f"Yearly Notes/{date.year}.md"
        else:
            return NoteResult(path="", success=False, error=f"Unknown period type: {period}")

        try:
            result = await self.client.read_note(path)
            return NoteResult(path=path, success=True, content=result.get("content", ""))
        except Exception as e:
            return NoteResult(path=path, success=False, error=str(e))

    def _substitute_date_variables(self, content: str, date: datetime) -> str:
        """Substitute date-related template variables."""
        replacements = {
            "{{date}}": date.strftime("%Y-%m-%d"),
            "{{time}}": date.strftime("%H:%M"),
            "{{datetime}}": date.strftime("%Y-%m-%d %H:%M"),
            "{{title}}": date.strftime("%A, %B %d, %Y"),
            "{{year}}": str(date.year),
            "{{month}}": date.strftime("%B"),
            "{{day}}": str(date.day),
            "{{weekday}}": date.strftime("%A"),
            "{{week}}": str(date.isocalendar()[1]),
        }
        for var, value in replacements.items():
            content = content.replace(var, value)
        return content

    # =========================================================================
    # Template Support
    # =========================================================================

    async def list_templates(self, directory: str | None = None) -> list[TemplateSpec]:
        """List available note templates."""
        template_dir = directory or self._templates_folder
        templates = []

        try:
            result = await self.client.list_notes(template_dir, extension_filter=".md")
            notes = result.get("files", [])

            for note in notes:
                path = note.get("path", "")
                name = Path(path).stem

                # Try to extract variables from template
                try:
                    content_result = await self.client.read_note(path)
                    content = content_result.get("content", "")
                    variables = self._extract_template_variables(content)
                except Exception:
                    variables = []

                template = TemplateSpec(name=name, path=path, variables=variables)
                templates.append(template)
                self._templates_cache[name] = template

            return templates
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []

    async def get_template(self, name: str) -> str | None:
        """Get template content by name."""
        # Check cache first
        if name in self._templates_cache and self._templates_cache[name].content:
            return self._templates_cache[name].content

        # Try to find template
        path = f"{self._templates_folder}/{name}.md"
        try:
            result = await self.client.read_note(path)
            content = result.get("content", "")

            # Update cache
            if name not in self._templates_cache:
                self._templates_cache[name] = TemplateSpec(
                    name=name,
                    path=path,
                    variables=self._extract_template_variables(content),
                    content=content,
                )
            else:
                self._templates_cache[name].content = content

            return content
        except Exception as e:
            logger.error(f"Error getting template {name}: {e}")
            return None

    def _extract_template_variables(self, content: str) -> list[str]:
        """Extract template variables from content."""
        # Match {{variable}} patterns
        pattern = r"\{\{(\w+)\}\}"
        matches = re.findall(pattern, content)
        return list(set(matches))

    async def render_template(self, template: str, variables: dict[str, Any]) -> str:
        """Render a template with variable substitution."""
        content = await self.get_template(template)
        if not content:
            return ""

        # Substitute variables
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        # Also substitute date variables
        content = self._substitute_date_variables(content, datetime.now())

        return content

    async def create_from_template(
        self, template_name: str, target_path: str, variables: dict[str, Any] | None = None
    ) -> NoteResult:
        """Create a new note from a template."""
        content = await self.render_template(template_name, variables or {})

        if not content:
            return NoteResult(
                path=target_path,
                success=False,
                error=f"Template '{template_name}' not found or empty",
            )

        try:
            await self.client.create_note(target_path, content)
            return NoteResult(path=target_path, success=True, content=content, created=True)
        except Exception as e:
            return NoteResult(path=target_path, success=False, error=str(e))

    # =========================================================================
    # Backlink Management
    # =========================================================================

    async def get_backlinks(self, path: str) -> list[Link]:
        """Get all notes that link to the specified note."""
        backlinks = []
        note_name = Path(path).stem

        # Search for wikilinks to this note
        search_patterns = [
            f"[[{note_name}]]",
            f"[[{note_name}|",
            f"![[{note_name}]]",
            f"![[{note_name}|",
        ]

        for pattern in search_patterns:
            try:
                result = await self.client.global_search(pattern, use_regex=False)
                matches = result.get("matches", [])

                for match in matches:
                    source_path = match.get("path", "")
                    if source_path and source_path != path:
                        is_embed = pattern.startswith("!")
                        link = Link(
                            source_path=source_path,
                            target_path=path,
                            link_text=note_name,
                            is_embed=is_embed,
                            line_number=match.get("line"),
                        )
                        # Avoid duplicates
                        if not any(l.source_path == link.source_path for l in backlinks):
                            backlinks.append(link)
            except Exception as e:
                logger.error(f"Error searching for backlinks with pattern '{pattern}': {e}")

        return backlinks

    async def get_outgoing_links(self, path: str) -> list[Link]:
        """Get all links in a note."""
        links = []

        try:
            result = await self.client.read_note(path)
            content = result.get("content", "")

            # Find all wikilinks
            pattern = r"(!?)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"
            matches = re.finditer(pattern, content)

            for match in matches:
                is_embed = match.group(1) == "!"
                target = match.group(2)
                display_text = match.group(3) or target

                link = Link(
                    source_path=path, target_path=target, link_text=display_text, is_embed=is_embed
                )
                links.append(link)

            return links
        except Exception as e:
            logger.error(f"Error getting outgoing links: {e}")
            return []

    async def update_wikilinks(self, old_name: str, new_name: str) -> int:
        """Update all wikilinks when a note is renamed."""
        updated_count = 0

        # Find all notes linking to the old name
        try:
            result = await self.client.global_search(f"[[{old_name}", use_regex=False)
            matches = result.get("matches", [])

            for match in matches:
                source_path = match.get("path", "")
                if source_path:
                    try:
                        # Replace old links with new
                        await self.client.search_and_replace(
                            source_path,
                            f"[[{old_name}",
                            f"[[{new_name}",
                            use_regex=False,
                            replace_all=True,
                        )
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"Error updating links in {source_path}: {e}")

            return updated_count
        except Exception as e:
            logger.error(f"Error updating wikilinks: {e}")
            return 0

    async def find_broken_links(self) -> list[Link]:
        """Find all broken wikilinks in the vault."""
        broken_links = []

        try:
            # Get all notes
            result = await self.client.list_notes("/", extension_filter=".md")
            all_notes = {Path(n.get("path", "")).stem for n in result.get("files", [])}

            for note in result.get("files", []):
                path = note.get("path", "")
                links = await self.get_outgoing_links(path)

                for link in links:
                    target_name = Path(link.target_path).stem
                    if target_name not in all_notes:
                        broken_links.append(link)

            return broken_links
        except Exception as e:
            logger.error(f"Error finding broken links: {e}")
            return []

    async def find_orphan_notes(self) -> list[str]:
        """Find notes with no incoming or outgoing links."""
        orphans = []

        try:
            result = await self.client.list_notes("/", extension_filter=".md")
            all_notes = result.get("files", [])

            for note in all_notes:
                path = note.get("path", "")

                # Check outgoing links
                outgoing = await self.get_outgoing_links(path)

                # Check incoming links (backlinks)
                backlinks = await self.get_backlinks(path)

                if not outgoing and not backlinks:
                    orphans.append(path)

            return orphans
        except Exception as e:
            logger.error(f"Error finding orphan notes: {e}")
            return []

    # =========================================================================
    # Attachment Handling
    # =========================================================================

    async def list_attachments(
        self, directory: str | None = None, filter_ext: str | None = None
    ) -> list[Attachment]:
        """List all attachments in the vault."""
        attachments = []
        attach_dir = directory or self._attachments_folder

        try:
            result = await self.client.list_notes(attach_dir)
            files = result.get("files", [])

            for file_info in files:
                path = file_info.get("path", "")
                name = Path(path).name
                ext = Path(path).suffix.lower()

                # Skip markdown files
                if ext == ".md":
                    continue

                # Apply filter if specified
                if filter_ext:
                    filter_exts = [f".{e.strip('.')}" for e in filter_ext.split(",")]
                    if ext not in filter_exts:
                        continue

                # Determine mime type
                mime_types = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".svg": "image/svg+xml",
                    ".pdf": "application/pdf",
                    ".mp3": "audio/mpeg",
                    ".mp4": "video/mp4",
                    ".webm": "video/webm",
                }

                attachment = Attachment(
                    path=path,
                    name=name,
                    size=file_info.get("size", 0),
                    mime_type=mime_types.get(ext, "application/octet-stream"),
                )
                attachments.append(attachment)

            return attachments
        except Exception as e:
            logger.error(f"Error listing attachments: {e}")
            return []

    async def get_attachments_for_note(self, path: str) -> list[Attachment]:
        """Get all attachments referenced in a note."""
        attachments = []

        try:
            result = await self.client.read_note(path)
            content = result.get("content", "")

            # Find embedded attachments
            pattern = r"!\[\[([^\]]+)\]\]"
            matches = re.findall(pattern, content)

            for match in matches:
                # Extract path from match
                attach_path = match.split("|")[0]  # Handle aliases
                if not attach_path.endswith(".md"):
                    attachment = Attachment(path=attach_path, name=Path(attach_path).name)
                    attachments.append(attachment)

            return attachments
        except Exception as e:
            logger.error(f"Error getting attachments for note: {e}")
            return []

    async def find_unused_attachments(self) -> list[Attachment]:
        """Find attachments not referenced by any note."""
        unused = []

        try:
            # Get all attachments
            all_attachments = await self.list_attachments()

            # Get all notes and their referenced attachments
            referenced = set()
            result = await self.client.list_notes("/", extension_filter=".md")

            for note in result.get("files", []):
                path = note.get("path", "")
                note_attachments = await self.get_attachments_for_note(path)
                for attach in note_attachments:
                    referenced.add(attach.name)

            # Find unused
            for attachment in all_attachments:
                if attachment.name not in referenced:
                    unused.append(attachment)

            return unused
        except Exception as e:
            logger.error(f"Error finding unused attachments: {e}")
            return []

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_create_notes(self, notes: list[NoteSpec]) -> list[NoteResult]:
        """Create multiple notes in one operation."""
        results = []

        for note in notes:
            try:
                await self.client.create_note(note.path, note.content, note.frontmatter)
                results.append(NoteResult(path=note.path, success=True, created=True))
            except Exception as e:
                results.append(NoteResult(path=note.path, success=False, error=str(e)))

        return results

    async def batch_update_notes(self, updates: list[dict[str, Any]]) -> list[NoteResult]:
        """Update multiple notes in one operation."""
        results = []

        for update in updates:
            path = update.get("path", "")
            content = update.get("content", "")
            mode = update.get("mode", "append")

            try:
                await self.client.update_note(path, content, mode)
                results.append(NoteResult(path=path, success=True, modified=True))
            except Exception as e:
                results.append(NoteResult(path=path, success=False, error=str(e)))

        return results

    async def batch_update_frontmatter(self, updates: list[FrontmatterUpdate]) -> list[NoteResult]:
        """Update frontmatter on multiple notes."""
        results = []

        for update in updates:
            try:
                await self.client.manage_frontmatter(
                    update.path, update.action.value, update.key, update.value
                )
                results.append(NoteResult(path=update.path, success=True, modified=True))
            except Exception as e:
                results.append(NoteResult(path=update.path, success=False, error=str(e)))

        return results

    async def batch_add_tags(self, notes: list[str], tags: list[str]) -> list[NoteResult]:
        """Add tags to multiple notes."""
        results = []

        for path in notes:
            try:
                await self.client.add_tags(path, tags)
                results.append(NoteResult(path=path, success=True, modified=True))
            except Exception as e:
                results.append(NoteResult(path=path, success=False, error=str(e)))

        return results

    async def batch_operations(self, operations: list[BatchOperation]) -> list[NoteResult]:
        """Execute multiple operations atomically."""
        results = []

        for op in operations:
            try:
                if op.operation == BatchOperationType.CREATE:
                    spec = NoteSpec(**op.params)
                    await self.client.create_note(spec.path, spec.content, spec.frontmatter)
                    results.append(NoteResult(path=spec.path, success=True, created=True))

                elif op.operation == BatchOperationType.UPDATE:
                    path = op.params.get("path", "")
                    content = op.params.get("content", "")
                    mode = op.params.get("mode", "append")
                    await self.client.update_note(path, content, mode)
                    results.append(NoteResult(path=path, success=True, modified=True))

                elif op.operation == BatchOperationType.DELETE:
                    path = op.params.get("path", "")
                    await self.client.delete_note(path)
                    results.append(NoteResult(path=path, success=True))

                elif op.operation == BatchOperationType.FRONTMATTER:
                    path = op.params.get("path", "")
                    action = op.params.get("action", "set")
                    key = op.params.get("key", "")
                    value = op.params.get("value")
                    await self.client.manage_frontmatter(path, action, key, value)
                    results.append(NoteResult(path=path, success=True, modified=True))

                elif op.operation == BatchOperationType.TAGS:
                    path = op.params.get("path", "")
                    action = op.params.get("action", "add")
                    tags = op.params.get("tags", [])
                    await self.client.manage_tags(path, action, tags)
                    results.append(NoteResult(path=path, success=True, modified=True))

                elif op.operation == BatchOperationType.SEARCH_REPLACE:
                    path = op.params.get("path", "")
                    search = op.params.get("search", "")
                    replace = op.params.get("replace", "")
                    use_regex = op.params.get("use_regex", False)
                    await self.client.search_and_replace(path, search, replace, use_regex)
                    results.append(NoteResult(path=path, success=True, modified=True))

                else:
                    results.append(
                        NoteResult(
                            path="", success=False, error=f"Unknown operation: {op.operation}"
                        )
                    )

            except Exception as e:
                path = op.params.get("path", "unknown")
                results.append(NoteResult(path=path, success=False, error=str(e)))

        return results

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def create_note_with_options(
        self,
        path: str,
        content: str,
        frontmatter: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        template: str | None = None,
    ) -> NoteResult:
        """Create a note with all optional parameters."""
        try:
            # If template specified, use it
            if template:
                result = await self.create_from_template(template, path, frontmatter or {})
                if not result.success:
                    return result

                # If additional content provided, append it
                if content:
                    await self.client.append_to_note(path, f"\n{content}")
            else:
                # Create note with content and frontmatter
                await self.client.create_note(path, content, frontmatter)

            # Add tags if specified
            if tags:
                await self.client.add_tags(path, tags)

            return NoteResult(path=path, success=True, created=True)
        except Exception as e:
            return NoteResult(path=path, success=False, error=str(e))
