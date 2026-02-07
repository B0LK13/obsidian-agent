"""Data models for PKM Agent."""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NoteMetadata:
    """Metadata extracted from note frontmatter."""

    title: str | None = None
    tags: list[str] = field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None
    status: str = "active"
    area: str | None = None
    project: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "tags": _normalize_tags(self.tags),
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
            "status": self.status,
            "area": self.area,
            "project": self.project,
            "extra": _json_safe(self.extra),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NoteMetadata":
        """Create from dictionary."""
        created = data.get("created")
        modified = data.get("modified")
        return cls(
            title=data.get("title"),
            tags=_normalize_tags(data.get("tags", [])),
            created=datetime.fromisoformat(created) if created else None,
            modified=datetime.fromisoformat(modified) if modified else None,
            status=data.get("status", "active"),
            area=data.get("area"),
            project=data.get("project"),
            extra=data.get("extra", {}),
        )


@dataclass
class Note:
    """Represents a markdown note in the PKM system."""

    id: str
    path: Path
    title: str
    content: str
    metadata: NoteMetadata
    created_at: datetime
    modified_at: datetime
    word_count: int = 0
    content_hash: str = ""

    def __post_init__(self) -> None:
        """Compute derived fields."""
        if not self.content_hash:
            self.content_hash = self._compute_hash()
        if not self.word_count:
            self.word_count = len(self.content.split())

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]

    @classmethod
    def from_file(cls, filepath: Path, pkm_root: Path) -> "Note":
        """Create Note from a markdown file."""
        import frontmatter

        content = filepath.read_text(encoding="utf-8")
        try:
            post = frontmatter.loads(content)
            metadata = post.metadata if isinstance(post.metadata, dict) else {}
            body = post.content
        except Exception as exc:
            logger.warning("Failed to parse frontmatter for %s: %s", filepath, exc)
            metadata = {}
            body = content

        # Extract metadata
        meta = NoteMetadata(
            title=metadata.get("title"),
            tags=_normalize_tags(metadata.get("tags", [])),
            created=_parse_datetime(metadata.get("created")),
            modified=_parse_datetime(metadata.get("modified")),
            status=metadata.get("status", "active"),
            area=metadata.get("area"),
            project=metadata.get("project"),
            extra={k: v for k, v in metadata.items()
                   if k not in ["title", "tags", "created", "modified", "status", "area", "project"]},
        )

        # Get title from frontmatter or first heading or filename
        title = meta.title
        if not title:
            lines = body.split("\n")
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
        if not title:
            title = filepath.stem.replace("-", " ").replace("_", " ").title()

        stat = filepath.stat()
        rel_path = filepath.relative_to(pkm_root)
        note_id = hashlib.md5(str(rel_path).encode()).hexdigest()[:12]

        return cls(
            id=note_id,
            path=rel_path,
            title=title,
            content=body,
            metadata=meta,
            created_at=meta.created or datetime.fromtimestamp(stat.st_ctime),
            modified_at=meta.modified or datetime.fromtimestamp(stat.st_mtime),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "path": str(self.path),
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "word_count": self.word_count,
            "content_hash": self.content_hash,
        }


@dataclass
class Tag:
    """Represents a tag in the system."""

    id: int
    name: str
    category: str = "user"  # user, system, auto
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Link:
    """Represents a link between two notes."""

    id: int
    source_id: str
    target_id: str
    link_type: str = "reference"  # reference, related, parent, sequence
    context: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Result from a search query."""

    note_id: str
    path: str
    title: str
    score: float
    snippet: str
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "note_id": self.note_id,
            "path": self.path,
            "title": self.title,
            "score": self.score,
            "snippet": self.snippet,
            "highlights": self.highlights,
        }


@dataclass
class Chunk:
    """A chunk of text for embedding."""

    id: str
    note_id: str
    content: str
    index: int
    metadata: dict[str, Any] = field(default_factory=dict)


def _parse_datetime(value: Any) -> datetime | None:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            pass
    return None


def _normalize_tags(tags: Any) -> list[str]:
    """Normalize frontmatter tags to a list of strings."""
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, (list, tuple, set)):
        normalized = []
        for tag in tags:
            if tag is None:
                continue
            if isinstance(tag, (datetime, date)):
                normalized.append(tag.isoformat())
            else:
                normalized.append(str(tag))
        return normalized
    return [str(tags)]


def _json_safe(value: Any) -> Any:
    """Coerce values into JSON-serializable forms."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)
