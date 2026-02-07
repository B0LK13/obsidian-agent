"""Retriever for RAG pipeline."""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """A retrieval result."""
    
    chunk_id: str
    note_id: str
    title: str
    path: str
    content: str
    score: float
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "note_id": self.note_id,
            "title": self.title,
            "path": self.path,
            "content": self.content,
            "score": self.score,
            "snippet": self.snippet,
        }


class Retriever:
    """Retrieve relevant chunks for queries."""

    def __init__(self, db, vectorstore):
        self.db = db
        self.vectorstore = vectorstore

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
        min_score: float = 0.0,
    ) -> list[RetrievalResult]:
        """Retrieve relevant chunks for a query."""
        # Search vector store
        results = self.vectorstore.search(query, k=k * 2, filters=filters)
        
        # Filter by score and deduplicate by note
        seen_notes = set()
        filtered = []
        
        for r in results:
            if r["score"] < min_score:
                continue
                
            note_id = r["metadata"].get("note_id", r["id"].split("_")[0])
            
            # Deduplicate by note (keep highest scoring chunk per note)
            if note_id in seen_notes:
                continue
            seen_notes.add(note_id)
            
            # Create snippet
            content = r["content"]
            snippet = content[:300] + "..." if len(content) > 300 else content
            
            filtered.append(RetrievalResult(
                chunk_id=r["id"],
                note_id=note_id,
                title=r["metadata"].get("title", "Untitled"),
                path=r["metadata"].get("path", ""),
                content=content,
                score=r["score"],
                snippet=snippet,
            ))
            
            if len(filtered) >= k:
                break
        
        logger.debug(f"Retrieved {len(filtered)} results for query: {query[:50]}...")
        return filtered

    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        k: int = 5,
    ) -> str:
        """Get formatted context string for a query."""
        results = self.retrieve(query, k=k)
        
        if not results:
            return ""
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 4 chars per token
        
        for r in results:
            # Format each result
            part = f"### {r.title}\n*Path: {r.path}*\n\n{r.content}\n"
            
            if total_chars + len(part) > max_chars:
                # Truncate if needed
                remaining = max_chars - total_chars
                if remaining > 100:
                    part = part[:remaining] + "..."
                    context_parts.append(part)
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        return "\n---\n".join(context_parts)
