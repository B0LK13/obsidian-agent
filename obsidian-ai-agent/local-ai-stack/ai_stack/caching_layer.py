"""
Caching and Optimization Layer
Issue #97: Implement Caching and Optimization Layer

Provides intelligent caching for LLM responses, embeddings, and vector search results
with TTL management, LRU eviction, and cache warming capabilities.
"""

import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Set
import heapq

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def touch(self):
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_rate: float = 0.0
    avg_lookup_time_ms: float = 0.0
    
    def update_hit_rate(self):
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        pass
    
    @abstractmethod
    def set(self, entry: CacheEntry) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        pass
    
    @abstractmethod
    def keys(self) -> List[str]:
        pass
    
    @abstractmethod
    def size(self) -> int:
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory LRU cache with size limits."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._access_order: List[Tuple[float, str]] = []  # (timestamp, key) for LRU
        self._current_memory = 0
    
    def get(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            entry.touch()
            return entry
    
    def set(self, entry: CacheEntry) -> bool:
        with self._lock:
            # Check if we need to evict
            while (len(self._cache) >= self.max_size or 
                   (self._current_memory + entry.size_bytes > self.max_memory_bytes)):
                if not self._evict_lru():
                    break
            
            # Remove old entry if exists
            if entry.key in self._cache:
                self._current_memory -= self._cache[entry.key].size_bytes
            
            self._cache[entry.key] = entry
            self._current_memory += entry.size_bytes
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            return self._remove_entry(key)
    
    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._current_memory = 0
            return True
    
    def keys(self) -> List[str]:
        with self._lock:
            return list(self._cache.keys())
    
    def size(self) -> int:
        with self._lock:
            return len(self._cache)
    
    def _remove_entry(self, key: str) -> bool:
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size_bytes
            return True
        return False
    
    def _evict_lru(self) -> bool:
        """Evict least recently used entry."""
        if not self._cache:
            return False
        
        # Find LRU entry
        lru_key = None
        lru_time = float('inf')
        
        for key, entry in self._cache.items():
            access_time = entry.last_accessed or entry.created_at
            if access_time.timestamp() < lru_time:
                lru_time = access_time.timestamp()
                lru_key = key
        
        if lru_key:
            self._remove_entry(lru_key)
            return True
        return False
    
    def get_memory_usage(self) -> Dict:
        """Get memory usage statistics."""
        with self._lock:
            return {
                'current_bytes': self._current_memory,
                'max_bytes': self.max_memory_bytes,
                'entry_count': len(self._cache),
                'max_entries': self.max_size,
                'utilization_percent': (self._current_memory / self.max_memory_bytes) * 100
            }


class SQLiteCacheBackend(CacheBackend):
    """Persistent SQLite-based cache."""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self):
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path)
        return self._local.connection
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    size_bytes INTEGER DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at);
                CREATE INDEX IF NOT EXISTS idx_accessed ON cache(last_accessed);
            """)
    
    def get(self, key: str) -> Optional[CacheEntry]:
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM cache WHERE key = ?",
                    (key,)
                ).fetchone()
                
                if row:
                    entry = CacheEntry(
                        key=row[0],
                        value=pickle.loads(row[1]),
                        created_at=datetime.fromisoformat(row[2]),
                        expires_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        access_count=row[4],
                        last_accessed=datetime.fromisoformat(row[5]) if row[5] else None,
                        size_bytes=row[6]
                    )
                    
                    if entry.is_expired():
                        self.delete(key)
                        return None
                    
                    # Update access stats
                    conn.execute(
                        """UPDATE cache SET access_count = access_count + 1,
                            last_accessed = ? WHERE key = ?""",
                        (datetime.utcnow().isoformat(), key)
                    )
                    
                    return entry
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
        return None
    
    def set(self, entry: CacheEntry) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache 
                    (key, value, created_at, expires_at, access_count, last_accessed, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key,
                    pickle.dumps(entry.value),
                    entry.created_at.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                    entry.access_count,
                    entry.last_accessed.isoformat() if entry.last_accessed else None,
                    entry.size_bytes
                ))
                return True
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                return True
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False
    
    def clear(self) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM cache")
                return True
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False
    
    def keys(self) -> List[str]:
        try:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT key FROM cache").fetchall()
                return [r[0] for r in rows]
        except Exception as e:
            logger.error(f"Cache keys failed: {e}")
            return []
    
    def size(self) -> int:
        try:
            with self._get_connection() as conn:
                row = conn.execute("SELECT COUNT(*) FROM cache").fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Cache size failed: {e}")
            return 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE expires_at < ?",
                    (datetime.utcnow().isoformat(),)
                )
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return 0


class CacheManager:
    """
    High-level cache manager with tiered caching (L1: memory, L2: disk)
    and intelligent cache warming.
    """
    
    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_cache_mb: float = 50,
        disk_cache_path: str = "cache.db",
        default_ttl_seconds: Optional[int] = 3600
    ):
        self.l1_cache = MemoryCacheBackend(memory_cache_size, memory_cache_mb)
        self.l2_cache = SQLiteCacheBackend(disk_cache_path)
        self.default_ttl = timedelta(seconds=default_ttl_seconds) if default_ttl_seconds else None
        self.stats = CacheStats()
        self._lock = threading.RLock()
    
    def _compute_key(self, namespace: str, data: Any) -> str:
        """Compute cache key from data."""
        key_data = f"{namespace}:{json.dumps(data, sort_keys=True, default=str)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        try:
            return len(pickle.dumps(value))
        except:
            return 0
    
    def get(self, namespace: str, key_data: Any) -> Tuple[bool, Any]:
        """
        Get value from cache. Checks L1 first, then L2.
        Returns (hit, value).
        """
        key = self._compute_key(namespace, key_data)
        start_time = time.time()
        
        with self._lock:
            # Check L1 (memory)
            entry = self.l1_cache.get(key)
            if entry:
                self.stats.hits += 1
                self.stats.update_hit_rate()
                self.stats.avg_lookup_time_ms = (time.time() - start_time) * 1000
                return True, entry.value
            
            # Check L2 (disk)
            entry = self.l2_cache.get(key)
            if entry:
                # Promote to L1
                self.l1_cache.set(entry)
                self.stats.hits += 1
                self.stats.update_hit_rate()
                self.stats.avg_lookup_time_ms = (time.time() - start_time) * 1000
                return True, entry.value
            
            self.stats.misses += 1
            self.stats.update_hit_rate()
            self.stats.avg_lookup_time_ms = (time.time() - start_time) * 1000
            return False, None
    
    def set(
        self, 
        namespace: str, 
        key_data: Any, 
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        key = self._compute_key(namespace, key_data)
        
        expires = None
        if ttl_seconds is not None:
            expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        elif self.default_ttl:
            expires = datetime.utcnow() + self.default_ttl
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=expires,
            size_bytes=self._get_size(value)
        )
        
        with self._lock:
            # Set in both caches
            l1_success = self.l1_cache.set(entry)
            l2_success = self.l2_cache.set(entry)
            
            if l1_success or l2_success:
                self.stats.total_entries = self.l1_cache.size() + self.l2_cache.size()
                self.stats.total_size_bytes = (
                    self.l1_cache.get_memory_usage()['current_bytes'] +
                    self._get_disk_size()
                )
                return True
            return False
    
    def delete(self, namespace: str, key_data: Any) -> bool:
        """Delete from both cache levels."""
        key = self._compute_key(namespace, key_data)
        
        with self._lock:
            l1_success = self.l1_cache.delete(key)
            l2_success = self.l2_cache.delete(key)
            return l1_success or l2_success
    
    def clear(self) -> bool:
        """Clear all caches."""
        with self._lock:
            self.l1_cache.clear()
            self.l2_cache.clear()
            self.stats = CacheStats()
            return True
    
    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics."""
        with self._lock:
            l1_stats = self.l1_cache.get_memory_usage()
            
            return {
                'l1_memory': l1_stats,
                'l2_disk_entries': self.l2_cache.size(),
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'hit_rate': self.stats.hit_rate,
                'avg_lookup_time_ms': self.stats.avg_lookup_time_ms,
                'total_entries': self.stats.total_entries,
                'evictions': self.stats.evictions
            }
    
    def _get_disk_size(self) -> int:
        """Get approximate disk usage."""
        # This is a rough estimate
        return self.l2_cache.size() * 1024  # Assume 1KB per entry average
    
    def cleanup(self) -> Dict:
        """Cleanup expired entries and return stats."""
        with self._lock:
            expired_l2 = self.l2_cache.cleanup_expired()
            
            # For L1, just remove expired on next access
            return {
                'expired_removed_l2': expired_l2
            }


# Decorator for automatic caching
def cached(
    cache_manager: CacheManager,
    namespace: str,
    ttl_seconds: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for automatic function result caching.
    
    Args:
        cache_manager: CacheManager instance
        namespace: Cache namespace
        ttl_seconds: Time-to-live in seconds
        key_func: Optional function to generate cache key from arguments
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key_data = key_func(*args, **kwargs)
            else:
                key_data = {'args': args, 'kwargs': kwargs}
            
            # Try cache
            hit, value = cache_manager.get(namespace, key_data)
            if hit:
                logger.debug(f"Cache hit for {func.__name__}")
                return value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(namespace, key_data, result, ttl_seconds)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        # Attach cache bypass method
        wrapper.cache_manager = cache_manager
        wrapper.namespace = namespace
        
        return wrapper
    return decorator


# Specialized caches for different use cases

class LLMResponseCache:
    """Specialized cache for LLM responses with prompt-aware keying."""
    
    def __init__(self, cache_manager: CacheManager, ttl_seconds: int = 3600):
        self.cache = cache_manager
        self.namespace = "llm_response"
        self.ttl = ttl_seconds
    
    def _make_key(self, prompt: str, model: str, temperature: float, **kwargs) -> Dict:
        """Create cache key from LLM parameters."""
        return {
            'prompt': prompt.strip(),
            'model': model,
            'temperature': temperature,
            'params': kwargs
        }
    
    def get(self, prompt: str, model: str, temperature: float = 0.7, **kwargs) -> Tuple[bool, Any]:
        """Get cached LLM response."""
        key = self._make_key(prompt, model, temperature, **kwargs)
        return self.cache.get(self.namespace, key)
    
    def set(self, prompt: str, model: str, response: Any, temperature: float = 0.7, **kwargs) -> bool:
        """Cache LLM response."""
        key = self._make_key(prompt, model, temperature, **kwargs)
        return self.cache.set(self.namespace, key, response, self.ttl)


class EmbeddingCache:
    """Specialized cache for text embeddings."""
    
    def __init__(self, cache_manager: CacheManager, ttl_seconds: Optional[int] = None):
        self.cache = cache_manager
        self.namespace = "embeddings"
        self.ttl = ttl_seconds
    
    def get(self, text: str, model: str) -> Tuple[bool, Optional[np.ndarray]]:
        """Get cached embedding."""
        key = {'text': text, 'model': model}
        hit, value = self.cache.get(self.namespace, key)
        if hit and isinstance(value, list):
            return True, np.array(value)
        return hit, value
    
    def set(self, text: str, model: str, embedding: np.ndarray) -> bool:
        """Cache embedding."""
        key = {'text': text, 'model': model}
        return self.cache.set(self.namespace, key, embedding.tolist(), self.ttl)


class SearchResultCache:
    """Specialized cache for vector search results."""
    
    def __init__(self, cache_manager: CacheManager, ttl_seconds: int = 300):
        self.cache = cache_manager
        self.namespace = "search_results"
        self.ttl = ttl_seconds
    
    def get(self, query: str, top_k: int, filters: Optional[Dict] = None) -> Tuple[bool, Any]:
        """Get cached search results."""
        key = {'query': query, 'top_k': top_k, 'filters': filters}
        return self.cache.get(self.namespace, key)
    
    def set(self, query: str, top_k: int, results: Any, filters: Optional[Dict] = None) -> bool:
        """Cache search results."""
        key = {'query': query, 'top_k': top_k, 'filters': filters}
        return self.cache.set(self.namespace, key, results, self.ttl)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize cache manager
    cache = CacheManager(
        memory_cache_size=100,
        memory_cache_mb=10,
        disk_cache_path="test_cache.db",
        default_ttl_seconds=3600
    )
    
    # Test basic operations
    print("Testing basic cache operations...")
    
    cache.set("test", "key1", "value1")
    hit, value = cache.get("test", "key1")
    print(f"Cache hit: {hit}, value: {value}")
    
    # Test specialized caches
    llm_cache = LLMResponseCache(cache)
    llm_cache.set("What is AI?", "gpt-4", {"text": "AI is..."})
    hit, response = llm_cache.get("What is AI?", "gpt-4")
    print(f"LLM cache hit: {hit}")
    
    embedding_cache = EmbeddingCache(cache)
    test_embedding = np.random.randn(384).astype(np.float32)
    embedding_cache.set("test text", "model-v1", test_embedding)
    hit, emb = embedding_cache.get("test text", "model-v1")
    print(f"Embedding cache hit: {hit}")
    
    # Stats
    print(f"\nCache stats: {cache.get_stats()}")
    
    # Cleanup
    cache.clear()
    Path("test_cache.db").unlink(missing_ok=True)
    
    print("\nCaching Layer test completed successfully!")
