"""Multi-level caching system for obsidian-agent."""

import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar, Callable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheLevel(str, Enum):
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


@dataclass
class CacheEntry(Generic[T]):
    key: str
    value: T
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = datetime.now()


class LRUCache(Generic[T]):
    """In-memory LRU cache with size limit."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100):
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._current_memory = 0
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> T | None:
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        if entry.is_expired():
            self.delete(key)
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.touch()
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: T, ttl_seconds: int | None = None) -> None:
        # Calculate entry size
        size = len(pickle.dumps(value))
        
        # Evict if needed
        while self._current_memory + size > self.max_memory_bytes and self._cache:
            self._evict_oldest()
        while len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        entry = CacheEntry(key=key, value=value, expires_at=expires_at, size_bytes=size)
        self._cache[key] = entry
        self._current_memory += size
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            self._current_memory -= self._cache[key].size_bytes
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        self._cache.clear()
        self._current_memory = 0
    
    def _evict_oldest(self) -> None:
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size_bytes
    
    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "memory_mb": self._current_memory / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }


class DiskCache(Generic[T]):
    """Disk-based cache with optional compression."""
    
    def __init__(self, cache_dir: Path, max_size_mb: float = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self._index_path = self.cache_dir / "_index.json"
        self._index: dict[str, dict] = self._load_index()
    
    def _load_index(self) -> dict[str, dict]:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text())
            except Exception:
                return {}
        return {}
    
    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index))
    
    def _key_to_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{h[:2]}" / f"{h}.pkl"
    
    def get(self, key: str) -> T | None:
        if key not in self._index:
            return None
        
        meta = self._index[key]
        if meta.get("expires_at") and datetime.fromisoformat(meta["expires_at"]) < datetime.now():
            self.delete(key)
            return None
        
        path = self._key_to_path(key)
        if not path.exists():
            del self._index[key]
            return None
        
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache entry: {e}")
            return None
    
    def set(self, key: str, value: T, ttl_seconds: int | None = None) -> None:
        path = self._key_to_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            pickle.dump(value, f)
        
        expires_at = None
        if ttl_seconds:
            expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
        
        self._index[key] = {
            "path": str(path),
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "size": path.stat().st_size,
        }
        self._save_index()
    
    def delete(self, key: str) -> bool:
        if key in self._index:
            path = Path(self._index[key]["path"])
            if path.exists():
                path.unlink()
            del self._index[key]
            self._save_index()
            return True
        return False
    
    def clear(self) -> None:
        import shutil
        for d in self.cache_dir.iterdir():
            if d.is_dir() and d.name != "_index.json":
                shutil.rmtree(d)
        self._index = {}
        self._save_index()


class CacheManager:
    """Unified cache manager with multiple levels."""
    
    def __init__(
        self,
        cache_dir: Path | None = None,
        memory_max_size: int = 1000,
        memory_max_mb: float = 100,
        disk_max_mb: float = 500,
        default_level: CacheLevel = CacheLevel.HYBRID,
    ):
        self.memory_cache = LRUCache[Any](memory_max_size, memory_max_mb)
        self.disk_cache = DiskCache[Any](cache_dir, disk_max_mb) if cache_dir else None
        self.default_level = default_level
    
    def get(self, key: str, level: CacheLevel | None = None) -> Any | None:
        level = level or self.default_level
        
        # Try memory first
        if level in (CacheLevel.MEMORY, CacheLevel.HYBRID):
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        # Try disk
        if level in (CacheLevel.DISK, CacheLevel.HYBRID) and self.disk_cache:
            value = self.disk_cache.get(key)
            if value is not None:
                # Promote to memory cache
                if level == CacheLevel.HYBRID:
                    self.memory_cache.set(key, value)
                return value
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        level: CacheLevel | None = None,
    ) -> None:
        level = level or self.default_level
        
        if level in (CacheLevel.MEMORY, CacheLevel.HYBRID):
            self.memory_cache.set(key, value, ttl_seconds)
        
        if level in (CacheLevel.DISK, CacheLevel.HYBRID) and self.disk_cache:
            self.disk_cache.set(key, value, ttl_seconds)
    
    def delete(self, key: str) -> None:
        self.memory_cache.delete(key)
        if self.disk_cache:
            self.disk_cache.delete(key)
    
    def clear(self) -> None:
        self.memory_cache.clear()
        if self.disk_cache:
            self.disk_cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "memory": self.memory_cache.get_stats(),
            "disk": {"enabled": self.disk_cache is not None},
            "default_level": self.default_level.value,
        }
    
    def cached(
        self,
        ttl_seconds: int | None = None,
        level: CacheLevel | None = None,
        key_func: Callable[..., str] | None = None,
    ):
        """Decorator for caching function results."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args, **kwargs) -> T:
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = f"{func.__name__}:{hash((args, tuple(kwargs.items())))}"
                
                result = self.get(key, level)
                if result is not None:
                    return result
                
                result = func(*args, **kwargs)
                self.set(key, result, ttl_seconds, level)
                return result
            return wrapper
        return decorator
