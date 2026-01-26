"""Specialized cache for embedding vectors."""

import hashlib
import logging
import numpy as np
from pathlib import Path
from typing import Any

from obsidian_agent.cache.cache_manager import CacheManager, CacheLevel

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Specialized cache for embedding vectors with content hashing."""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        model_name: str = "default",
        ttl_seconds: int = 86400 * 7,  # 7 days
    ):
        self.cache = cache_manager
        self.model_name = model_name
        self.ttl_seconds = ttl_seconds
        self._prefix = f"embedding:{model_name}:"
    
    def _content_hash(self, content: str) -> str:
        """Generate content hash for cache key."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _make_key(self, content: str) -> str:
        return f"{self._prefix}{self._content_hash(content)}"
    
    def get(self, content: str) -> np.ndarray | None:
        """Get cached embedding for content."""
        key = self._make_key(content)
        result = self.cache.get(key)
        
        if result is not None:
            logger.debug(f"Embedding cache hit: {key[:30]}...")
            return np.array(result)
        
        return None
    
    def set(self, content: str, embedding: np.ndarray) -> None:
        """Cache embedding for content."""
        key = self._make_key(content)
        # Store as list for JSON serialization
        self.cache.set(
            key,
            embedding.tolist(),
            ttl_seconds=self.ttl_seconds,
            level=CacheLevel.HYBRID,
        )
        logger.debug(f"Embedding cached: {key[:30]}...")
    
    def get_or_compute(
        self,
        content: str,
        compute_fn: callable,
    ) -> np.ndarray:
        """Get cached embedding or compute and cache it."""
        embedding = self.get(content)
        
        if embedding is None:
            embedding = compute_fn(content)
            self.set(content, embedding)
        
        return embedding
    
    def batch_get_or_compute(
        self,
        contents: list[str],
        compute_fn: callable,
    ) -> list[np.ndarray]:
        """Batch get/compute embeddings with caching."""
        results: list[np.ndarray | None] = []
        missing_indices: list[int] = []
        missing_contents: list[str] = []
        
        # Check cache for all contents
        for i, content in enumerate(contents):
            embedding = self.get(content)
            results.append(embedding)
            if embedding is None:
                missing_indices.append(i)
                missing_contents.append(content)
        
        # Compute missing embeddings in batch
        if missing_contents:
            computed = compute_fn(missing_contents)
            for i, (idx, embedding) in enumerate(zip(missing_indices, computed)):
                results[idx] = embedding
                self.set(contents[idx], embedding)
        
        return results
    
    def invalidate(self, content: str) -> None:
        """Remove cached embedding for content."""
        key = self._make_key(content)
        self.cache.delete(key)
    
    def clear_model_cache(self) -> None:
        """Clear all cached embeddings for this model."""
        # Note: This is a simplified version - full implementation
        # would iterate through cache keys with the model prefix
        logger.info(f"Clearing embedding cache for model: {self.model_name}")
