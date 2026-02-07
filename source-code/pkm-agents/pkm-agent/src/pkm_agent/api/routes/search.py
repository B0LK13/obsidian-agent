"""Search API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from pkm_agent.api.server import get_pkm_app
from pkm_agent.app import PKMAgentApp

router = APIRouter()

class SearchResult(BaseModel):
    note_id: str
    path: str
    title: str
    score: float
    snippet: str
    highlights: list[str]

@router.get("/", response_model=list[SearchResult])
async def search(
    q: str,
    limit: int = 20,
    area: str | None = None,
    tag: str | None = None,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Search for notes."""
    filters = {}
    if area:
        filters["area"] = area
    if tag:
        filters["tags"] = tag
        
    results = await app.search(q, limit=limit, filters=filters)
    return results
