"""API routes for obsidian-agent."""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException

from obsidian_agent.api.models import (
    SearchRequest, SearchResponse, SearchResult, SearchType,
    SimilarNotesRequest,
    IndexRequest, IndexResponse, IndexStatus,
    DuplicateScanRequest, DuplicateScanResponse, DuplicateMatch,
    LinkSuggestionsRequest, LinkSuggestionsResponse, LinkSuggestion,
    SummarizeRequest, SummaryResponse, SummaryLevel,
    TemplateAnalyzeRequest, TemplateResponse,
    HealthResponse, HealthStatus, ComponentHealth,
    VaultStats,
)
from obsidian_agent.api.dependencies import (
    SearchServiceDep, IndexerDep, DuplicateServiceDep,
    LinkingServiceDep, SummarizationServiceDep, TemplateServiceDep,
    HealthCheckerDep, get_settings,
)

router = APIRouter()

# Track server start time
START_TIME = datetime.now()


# ================= Health Endpoints =================

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(health_checker: HealthCheckerDep):
    """Check the health of all system components."""
    result = await health_checker.check_all()
    
    components = [
        ComponentHealth(
            name=name,
            status=HealthStatus.HEALTHY if check.get("ok") else HealthStatus.UNHEALTHY,
            message=check.get("message"),
            latency_ms=check.get("latency_ms"),
        )
        for name, check in result.items()
    ]
    
    all_healthy = all(c.status == HealthStatus.HEALTHY for c in components)
    uptime = (datetime.now() - START_TIME).total_seconds()
    
    return HealthResponse(
        status=HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED,
        version="0.1.0",
        components=components,
        uptime_seconds=uptime,
    )


@router.get("/stats", response_model=VaultStats, tags=["Health"])
async def get_vault_stats(search_service: SearchServiceDep):
    """Get vault statistics."""
    stats = await search_service.get_vault_stats()
    return VaultStats(**stats)


# ================= Search Endpoints =================

@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest, search_service: SearchServiceDep):
    """Search the vault using semantic or keyword search."""
    start = time.time()
    
    results = await search_service.search(
        query=request.query,
        limit=request.limit,
        threshold=request.threshold,
    )
    
    duration_ms = (time.time() - start) * 1000
    
    return SearchResponse(
        query=request.query,
        results=[
            SearchResult(
                note_id=r.get("id", ""),
                title=r.get("title", ""),
                path=r.get("path", ""),
                score=r.get("score", 0.0),
                snippet=r.get("snippet", ""),
                tags=r.get("tags", []),
                modified_at=r.get("modified_at"),
            )
            for r in results
        ],
        total=len(results),
        search_type=request.search_type,
        duration_ms=duration_ms,
    )


@router.post("/search/similar", response_model=SearchResponse, tags=["Search"])
async def find_similar_notes(request: SimilarNotesRequest, search_service: SearchServiceDep):
    """Find notes similar to a given note."""
    start = time.time()
    
    results = await search_service.find_similar(
        note_id=request.note_id,
        limit=request.limit,
        threshold=request.threshold,
    )
    
    duration_ms = (time.time() - start) * 1000
    
    return SearchResponse(
        query=f"similar to: {request.note_id}",
        results=[
            SearchResult(
                note_id=r.get("id", ""),
                title=r.get("title", ""),
                path=r.get("path", ""),
                score=r.get("score", 0.0),
                snippet=r.get("snippet", ""),
                tags=r.get("tags", []),
            )
            for r in results
        ],
        total=len(results),
        search_type=SearchType.SEMANTIC,
        duration_ms=duration_ms,
    )


# ================= Indexing Endpoints =================

@router.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def index_vault(request: IndexRequest, indexer: IndexerDep):
    """Index or re-index the vault."""
    start = time.time()
    
    try:
        result = await indexer.index_vault(
            full_reindex=request.full_reindex,
            paths=request.paths,
        )
        duration_ms = (time.time() - start) * 1000
        
        return IndexResponse(
            status="completed",
            notes_indexed=result.get("indexed", 0),
            notes_skipped=result.get("skipped", 0),
            errors=result.get("errors", []),
            duration_ms=duration_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/status", response_model=IndexStatus, tags=["Indexing"])
async def get_index_status(indexer: IndexerDep):
    """Get the current indexing status."""
    status = await indexer.get_status()
    return IndexStatus(**status)


# ================= Duplicate Detection Endpoints =================

@router.post("/duplicates/scan", response_model=DuplicateScanResponse, tags=["Duplicates"])
async def scan_duplicates(request: DuplicateScanRequest, duplicate_service: DuplicateServiceDep):
    """Scan for duplicate and similar notes."""
    start = time.time()
    
    matches = await duplicate_service.find_duplicates(
        threshold=request.threshold,
    )
    
    duration_ms = (time.time() - start) * 1000
    
    return DuplicateScanResponse(
        matches=[
            DuplicateMatch(
                note1_id=m.note1_id,
                note1_title=m.note1_title,
                note2_id=m.note2_id,
                note2_title=m.note2_title,
                similarity=m.similarity,
                match_type=m.level.value,
                suggested_action=m.suggested_action,
            )
            for m in matches
        ],
        total_matches=len(matches),
        scan_duration_ms=duration_ms,
    )


# ================= Link Suggestion Endpoints =================

@router.post("/links/suggest", response_model=LinkSuggestionsResponse, tags=["Linking"])
async def suggest_links(request: LinkSuggestionsRequest, linking_service: LinkingServiceDep):
    """Get link suggestions for notes."""
    suggestions = await linking_service.analyze_vault([])
    
    return LinkSuggestionsResponse(
        suggestions=[
            LinkSuggestion(
                source_note_id=s.source_note,
                target_note_id=s.target_note,
                target_title=s.target_note,
                confidence=s.confidence,
                link_type=s.link_type.value,
                reason=s.reason,
            )
            for s in suggestions.suggestions[:request.limit]
        ],
        total=len(suggestions.suggestions),
    )


# ================= Summarization Endpoints =================

@router.post("/summarize", response_model=SummaryResponse, tags=["Summarization"])
async def summarize_content(request: SummarizeRequest, summarization_service: SummarizationServiceDep):
    """Summarize a note or provided content."""
    from obsidian_agent.features.summarization import SummaryLevel as SL
    
    level_map = {
        SummaryLevel.BRIEF: SL.BRIEF,
        SummaryLevel.STANDARD: SL.STANDARD,
        SummaryLevel.DETAILED: SL.DETAILED,
        SummaryLevel.OUTLINE: SL.OUTLINE,
    }
    
    if request.content:
        result = summarization_service.summarize_note(
            "inline",
            request.content,
            level_map[request.level],
        )
    elif request.note_id:
        result = summarization_service.summarize_note(
            request.note_id,
            "",
            level_map[request.level],
        )
    else:
        raise HTTPException(status_code=400, detail="Provide note_id or content")
    
    return SummaryResponse(
        note_id=request.note_id,
        summary=result.summary,
        key_points=result.key_points,
        level=request.level,
    )


# ================= Template Endpoints =================

@router.post("/templates/analyze", response_model=list[TemplateResponse], tags=["Templates"])
async def analyze_templates(request: TemplateAnalyzeRequest, template_service: TemplateServiceDep):
    """Analyze notes and generate template suggestions."""
    templates = await template_service.analyze_patterns([])
    
    return [
        TemplateResponse(
            name=t.name,
            template_type=t.template_type.value,
            content=t.content,
            variables=t.variables,
        )
        for t in templates
    ]
