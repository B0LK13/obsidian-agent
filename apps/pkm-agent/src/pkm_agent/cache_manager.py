"""Multi-level caching system for PKM Agent.

Implements LRU cache with TTL for embeddings, query results, and processed data.
"""

import hashlib
import logging
import pickle
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LRUCache(Generic[T]):
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> T | None:
        """Get value from cache."""
        if key not in self._cache:
            self._misses += 1
            return None

        value, timestamp = self._cache[key]
        
        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return value

    def set(self, key: str, value: T) -> None:
        """Set value in cache."""
        # Remove oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._cache.popitem(last=False)

        self._cache[key] = (value, time.time())
        self._cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
        }


class DiskCache:
    """Persistent disk-based cache for expensive computations."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"

    def get(self, key: str, max_age_seconds: int | None = None) -> Any | None:
        """Get value from disk cache."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None

        # Check age if specified
        if max_age_seconds is not None:
            age = time.time() - cache_path.stat().st_mtime
            if age > max_age_seconds:
                cache_path.unlink()
                return None

        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Set value in disk cache."""
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"Failed to save cache for {key}: {e}")

    def clear(self) -> None:
        """Clear all disk cache."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "entries": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }


class CacheManager:
    """Multi-level cache manager."""

    def __init__(self, cache_dir: Path, memory_cache_size: int = 1000):
        self.query_cache = LRUCache[list](max_size=memory_cache_size, ttl_seconds=3600)
        self.embedding_cache = DiskCache(cache_dir / "embeddings")
        self.chunk_cache = DiskCache(cache_dir / "chunks")

    def get_query_result(self, query: str) -> list | None:
        """Get cached query result."""
        return self.query_cache.get(query)

    def set_query_result(self, query: str, result: list) -> None:
        """Cache query result."""
        self.query_cache.set(query, result)

    def get_embedding(self, text: str) -> Any | None:
        """Get cached embedding."""
        return self.embedding_cache.get(text, max_age_seconds=86400 * 7)  # 7 days

    def set_embedding(self, text: str, embedding: Any) -> None:
        """Cache embedding."""
        self.embedding_cache.set(text, embedding)

    def get_chunks(self, note_id: str) -> Any | None:
        """Get cached chunks for a note."""
        return self.chunk_cache.get(note_id, max_age_seconds=86400)  # 1 day

    def set_chunks(self, note_id: str, chunks: Any) -> None:
        """Cache chunks."""
        self.chunk_cache.set(note_id, chunks)

    def clear_all(self) -> None:
        """Clear all caches."""
        self.query_cache.clear()
        self.embedding_cache.clear()
        self.chunk_cache.clear()

    def stats(self) -> dict[str, Any]:
        """Get statistics for all caches."""
        return {
            "query_cache": self.query_cache.stats(),
            "embedding_cache": self.embedding_cache.stats(),
            "chunk_cache": self.chunk_cache.stats(),
        }
