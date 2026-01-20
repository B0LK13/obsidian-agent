"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ================= Enums =================

class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class SummaryLevel(str, Enum):
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"
    OUTLINE = "outline"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ================= Search =================

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    search_type: SearchType = Field(default=SearchType.SEMANTIC)
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    filter_tags: list[str] | None = None
    filter_folders: list[str] | None = None


class SearchResult(BaseModel):
    note_id: str
    title: str
    path: str
    score: float
    snippet: str
    tags: list[str] = []
    modified_at: datetime | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    search_type: SearchType
    duration_ms: float


class SimilarNotesRequest(BaseModel):
    note_id: str = Field(..., description="Note ID to find similar notes for")
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.5)


# ================= Indexing =================

class IndexRequest(BaseModel):
    full_reindex: bool = Field(default=False)
    paths: list[str] | None = None


class IndexStatus(BaseModel):
    is_indexing: bool
    total_notes: int
    indexed_notes: int
    last_indexed_at: datetime | None
    progress_percent: float


class IndexResponse(BaseModel):
    status: str
    notes_indexed: int
    notes_skipped: int
    errors: list[str] = []
    duration_ms: float


# ================= Duplicates =================

class DuplicateMatch(BaseModel):
    note1_id: str
    note1_title: str
    note2_id: str
    note2_title: str
    similarity: float
    match_type: str
    suggested_action: str


class DuplicateScanRequest(BaseModel):
    threshold: float = Field(default=0.9, ge=0.5, le=1.0)
    include_similar: bool = Field(default=True)


class DuplicateScanResponse(BaseModel):
    matches: list[DuplicateMatch]
    total_matches: int
    scan_duration_ms: float


# ================= Linking =================

class LinkSuggestion(BaseModel):
    source_note_id: str
    target_note_id: str
    target_title: str
    confidence: float
    link_type: str
    reason: str


class LinkSuggestionsRequest(BaseModel):
    note_id: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class LinkSuggestionsResponse(BaseModel):
    suggestions: list[LinkSuggestion]
    total: int


# ================= Summarization =================

class SummarizeRequest(BaseModel):
    note_id: str | None = None
    content: str | None = None
    level: SummaryLevel = Field(default=SummaryLevel.STANDARD)


class SummaryResponse(BaseModel):
    note_id: str | None
    summary: str
    key_points: list[str]
    level: SummaryLevel


# ================= Templates =================

class TemplateAnalyzeRequest(BaseModel):
    note_ids: list[str] | None = None
    count: int = Field(default=50)


class TemplateResponse(BaseModel):
    name: str
    template_type: str
    content: str
    variables: list[str]


# ================= Health =================

class ComponentHealth(BaseModel):
    name: str
    status: HealthStatus
    message: str | None = None
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: HealthStatus
    version: str
    components: list[ComponentHealth]
    uptime_seconds: float


# ================= Stats =================

class VaultStats(BaseModel):
    total_notes: int
    total_words: int
    total_links: int
    total_tags: int
    avg_words_per_note: float
    avg_links_per_note: float
    orphan_notes: int
    most_linked_notes: list[dict[str, Any]]
    top_tags: list[dict[str, Any]]
