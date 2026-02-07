"""
Type definitions for PKM Agent vault operations.

This module provides data classes and enums for structured vault operations
including notes, frontmatter, tags, attachments, links, and batch operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PeriodicNoteType(Enum):
    """Types of periodic notes supported by Obsidian."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class UpdateMode(Enum):
    """Modes for updating note content."""

    APPEND = "append"
    PREPEND = "prepend"
    OVERWRITE = "overwrite"


class FrontmatterAction(Enum):
    """Actions for frontmatter management."""

    GET = "get"
    SET = "set"
    DELETE = "delete"


class TagAction(Enum):
    """Actions for tag management."""

    ADD = "add"
    REMOVE = "remove"
    LIST = "list"


class BatchOperationType(Enum):
    """Types of batch operations."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    FRONTMATTER = "frontmatter"
    TAGS = "tags"
    SEARCH_REPLACE = "search_replace"


@dataclass
class NoteSpec:
    """Specification for creating a new note."""

    path: str
    content: str
    frontmatter: dict[str, Any] | None = None
    tags: list[str] | None = None
    template: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "content": self.content,
            "frontmatter": self.frontmatter,
            "tags": self.tags,
            "template": self.template,
        }


@dataclass
class NoteResult:
    """Result of a note operation."""

    path: str
    success: bool
    content: str | None = None
    error: str | None = None
    created: bool = False
    modified: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "created": self.created,
            "modified": self.modified,
        }


@dataclass
class SearchResult:
    """Result from a vault search."""

    path: str
    content: str
    score: float = 0.0
    matches: list[str] = field(default_factory=list)
    line_number: int | None = None
    context: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "content": self.content,
            "score": self.score,
            "matches": self.matches,
            "line_number": self.line_number,
            "context": self.context,
        }


@dataclass
class FrontmatterUpdate:
    """Specification for a frontmatter update operation."""

    path: str
    key: str
    value: Any = None
    action: FrontmatterAction = FrontmatterAction.SET

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "key": self.key,
            "value": self.value,
            "action": self.action.value,
        }


@dataclass
class TagUpdate:
    """Specification for a tag update operation."""

    path: str
    tags: list[str]
    action: TagAction = TagAction.ADD

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"path": self.path, "tags": self.tags, "action": self.action.value}


@dataclass
class SearchReplaceSpec:
    """Specification for a search and replace operation."""

    path: str
    search: str
    replace: str
    use_regex: bool = False
    case_sensitive: bool = False
    replace_all: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "search": self.search,
            "replace": self.replace,
            "use_regex": self.use_regex,
            "case_sensitive": self.case_sensitive,
            "replace_all": self.replace_all,
        }


@dataclass
class BatchOperation:
    """Specification for a batch operation."""

    operation: BatchOperationType
    params: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"operation": self.operation.value, "params": self.params}


@dataclass
class Attachment:
    """Represents an attachment in the vault."""

    path: str
    name: str
    size: int = 0
    mime_type: str = ""
    created: datetime | None = None
    modified: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "mime_type": self.mime_type,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
        }


@dataclass
class Link:
    """Represents a wikilink between notes."""

    source_path: str
    target_path: str
    link_text: str
    is_embed: bool = False
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_path": self.source_path,
            "target_path": self.target_path,
            "link_text": self.link_text,
            "is_embed": self.is_embed,
            "line_number": self.line_number,
        }


@dataclass
class TemplateSpec:
    """Specification for a note template."""

    name: str
    path: str
    variables: list[str] = field(default_factory=list)
    content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "variables": self.variables,
            "content": self.content,
        }


@dataclass
class PeriodicNoteSpec:
    """Specification for a periodic note."""

    period: PeriodicNoteType
    date: datetime | None = None
    template: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period": self.period.value,
            "date": self.date.isoformat() if self.date else None,
            "template": self.template,
        }


@dataclass
class VaultStats:
    """Statistics about the vault."""

    total_notes: int = 0
    total_attachments: int = 0
    total_tags: int = 0
    total_links: int = 0
    broken_links: int = 0
    orphan_notes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_notes": self.total_notes,
            "total_attachments": self.total_attachments,
            "total_tags": self.total_tags,
            "total_links": self.total_links,
            "broken_links": self.broken_links,
            "orphan_notes": self.orphan_notes,
        }
