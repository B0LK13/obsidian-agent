"""Hybrid retriever combining semantic and keyword search."""

import logging
from dataclasses import dataclass
from typing import Any

from pkm_agent.data.database import Database
from pkm_agent.data.models import SearchResult
from pkm_agent.rag.reranker import get_reranker
from pkm_agent.rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval."""

    top_k: int = 5
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    min_score: float = 0.3
    rerank: bool = True  # Enable reranking by default
    rerank_top_n: int = 20  # Rerank top N candidates


class Retriever:
    """Hybrid retriever combining semantic and keyword search."""

    def __init__(
        self,
        database: Database,
        vectorstore: VectorStore,
        config: RetrievalConfig | None = None,
    ):
        self.db = database
        self.vectorstore = vectorstore
        self.config = config or RetrievalConfig()
        self._reranker = None

        # Initialize reranker if enabled
        if self.config.rerank:
            try:
                self._reranker = get_reranker()
                logger.info("Reranking enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
                self.config.rerank = False

    def retrieve(
        self,
        query: str,
        k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Retrieve relevant documents using hybrid search."""
        k = k or self.config.top_k

        # Get more candidates if reranking
        candidate_k = self.config.rerank_top_n if self.config.rerank else k * 2

        # Get semantic results
        semantic_results = self._semantic_search(query, candidate_k, filters)

        # Get keyword results
        keyword_results = self._keyword_search(query, candidate_k)

        # Combine results using Reciprocal Rank Fusion
        combined = self._rrf_fusion(
            semantic_results,
            keyword_results,
            self.config.semantic_weight,
            self.config.keyword_weight,
        )

        # Filter by minimum score
        filtered = [r for r in combined if r.score >= self.config.min_score]

        # Apply reranking if enabled
        if self.config.rerank and self._reranker and filtered:
            logger.debug(f"Reranking {len(filtered)} candidates")
            filtered = self._reranker.rerank(query, filtered, top_k=k)
            return filtered

        # Return top k
        return filtered[:k]

    def _semantic_search(
        self,
        query: str,
        k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform semantic search using vector store."""
        try:
            return self.vectorstore.search(query, k=k, filters=filters)
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _keyword_search(self, query: str, k: int) -> list[SearchResult]:
        """Perform keyword search using database."""
        try:
            return self.db.search_notes(query, limit=k)
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _rrf_fusion(
        self,
        semantic_results: list[SearchResult],
        keyword_results: list[SearchResult],
        semantic_weight: float,
        keyword_weight: float,
        k: int = 60,
    ) -> list[SearchResult]:
        """Combine results using Reciprocal Rank Fusion."""
        scores: dict[str, float] = {}
        result_map: dict[str, SearchResult] = {}

        # Process semantic results
        for rank, result in enumerate(semantic_results):
            key = result.note_id
            rrf_score = semantic_weight * (1 / (k + rank + 1))
            scores[key] = scores.get(key, 0) + rrf_score
            result_map[key] = result

        # Process keyword results
        for rank, result in enumerate(keyword_results):
            key = result.note_id
            rrf_score = keyword_weight * (1 / (k + rank + 1))
            scores[key] = scores.get(key, 0) + rrf_score
            if key not in result_map:
                result_map[key] = result

        # Sort by combined score
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Build final results
        results = []
        for key in sorted_keys:
            result = result_map[key]
            # Normalize score to 0-1 range
            normalized_score = min(scores[key] * 100, 1.0)
            results.append(SearchResult(
                note_id=result.note_id,
                path=result.path,
                title=result.title,
                score=normalized_score,
                snippet=result.snippet,
                highlights=result.highlights,
            ))

        return results

    def get_related_notes(
        self,
        note_id: str,
        k: int = 5,
    ) -> list[SearchResult]:
        """Find notes related to a given note."""
        # Get the note content
        note = self.db.get_note(note_id)
        if not note:
            return []

        # Use the note's title and first 500 chars as query
        query = f"{note.title} {note.content[:500]}"

        # Search and filter out the source note
        results = self.retrieve(query, k=k + 1)
        return [r for r in results if r.note_id != note_id][:k]

    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
    ) -> str:
        """Get context string for LLM from retrieved documents."""
        results = self.retrieve(query)

        context_parts = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough char to token ratio

        for result in results:
            # Get full note content
            note = self.db.get_note(result.note_id)
            if not note:
                continue

            # Format context entry
            entry = f"## {note.title}\n"
            entry += f"Path: {note.path}\n"
            if note.metadata.tags:
                entry += f"Tags: {', '.join(note.metadata.tags)}\n"
            entry += f"\n{note.content}\n\n---\n\n"

            if total_chars + len(entry) > char_limit:
                # Truncate content if needed
                remaining = char_limit - total_chars
                if remaining > 200:
                    entry = entry[:remaining] + "...\n\n---\n\n"
                    context_parts.append(entry)
                break

            context_parts.append(entry)
            total_chars += len(entry)

        return "".join(context_parts)
