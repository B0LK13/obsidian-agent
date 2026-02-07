"""Re-ranking module for improving search relevance."""

import logging
from dataclasses import dataclass

from pkm_agent.data.models import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class RerankerConfig:
    """Configuration for reranker."""

    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    batch_size: int = 32
    use_cache: bool = True
    cache_size: int = 1000


class CrossEncoderReranker:
    """Rerank search results using a cross-encoder model."""

    def __init__(self, config: RerankerConfig | None = None):
        self.config = config or RerankerConfig()
        self._model = None
        self._cache = {} if self.config.use_cache else None

    def _load_model(self):
        """Lazy load the cross-encoder model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading reranker model: {self.config.model_name}")
            self._model = CrossEncoder(self.config.model_name)
            logger.info("Reranker model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed, reranking disabled")
            self._model = None

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """
        Rerank search results using cross-encoder.

        Args:
            query: Search query
            results: Initial search results
            top_k: Number of results to return (None = return all)

        Returns:
            Reranked search results with updated scores
        """
        if not results:
            return []

        # Check cache
        cache_key = None
        if self._cache is not None:
            result_ids = tuple(r.note_id for r in results)
            cache_key = (query, result_ids)
            if cache_key in self._cache:
                logger.debug("Reranking cache hit")
                cached_results = self._cache[cache_key]
                return cached_results[:top_k] if top_k else cached_results

        # Load model if not loaded
        self._load_model()

        # If model not available, return original results
        if self._model is None:
            logger.debug("Reranker model not available, returning original results")
            return results[:top_k] if top_k else results

        # Prepare query-document pairs
        pairs = []
        for result in results:
            # Use snippet or truncate content for reranking
            text = result.snippet if result.snippet else ""
            if not text and hasattr(result, 'content'):
                text = result.content[:500]

            pairs.append([query, text])

        # Get reranking scores
        try:
            scores = self._model.predict(pairs)

            # Create new results with updated scores
            reranked = []
            for result, score in zip(results, scores):
                reranked.append(SearchResult(
                    note_id=result.note_id,
                    path=result.path,
                    title=result.title,
                    score=float(score),  # Use cross-encoder score
                    snippet=result.snippet,
                    highlights=result.highlights,
                ))

            # Sort by new score
            reranked.sort(key=lambda x: x.score, reverse=True)

            # Update cache
            if self._cache is not None:
                # Implement LRU-like caching
                if len(self._cache) >= self.config.cache_size:
                    # Remove oldest entry (first key)
                    self._cache.pop(next(iter(self._cache)))
                self._cache[cache_key] = reranked

            logger.debug(f"Reranked {len(results)} results")
            return reranked[:top_k] if top_k else reranked

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:top_k] if top_k else results

    def clear_cache(self):
        """Clear the reranking cache."""
        if self._cache is not None:
            self._cache.clear()
            logger.debug("Reranking cache cleared")


# Global reranker instance
_reranker: CrossEncoderReranker | None = None


def get_reranker(config: RerankerConfig | None = None) -> CrossEncoderReranker:
    """Get or create global reranker instance."""
    global _reranker

    if _reranker is None:
        _reranker = CrossEncoderReranker(config)

    return _reranker
