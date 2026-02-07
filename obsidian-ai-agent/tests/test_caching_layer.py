"""
Unit tests for Caching and Optimization Layer (Issue #97)
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import time
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from caching_layer import (
    CacheManager,
    MemoryCacheBackend,
    SQLiteCacheBackend,
    CacheEntry,
    CacheStats,
    LLMResponseCache,
    EmbeddingCache,
    SearchResultCache,
    cached
)


class TestMemoryCacheBackend(unittest.TestCase):
    """Test in-memory cache backend."""
    
    def setUp(self):
        self.cache = MemoryCacheBackend(max_size=5, max_memory_mb=1)
    
    def test_basic_operations(self):
        """Test get, set, delete."""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=datetime.utcnow(),
            expires_at=None,
            size_bytes=100
        )
        
        self.assertTrue(self.cache.set(entry))
        
        retrieved = self.cache.get("test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.value, "value")
        
        self.assertTrue(self.cache.delete("test"))
        self.assertIsNone(self.cache.get("test"))
    
    def test_expiration(self):
        """Test TTL expiration."""
        entry = CacheEntry(
            key="expiring",
            value="value",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(milliseconds=50),
            size_bytes=100
        )
        
        self.cache.set(entry)
        self.assertIsNotNone(self.cache.get("expiring"))
        
        time.sleep(0.1)
        self.assertIsNone(self.cache.get("expiring"))
    
    def test_lru_eviction(self):
        """Test LRU eviction when max size reached."""
        for i in range(5):
            entry = CacheEntry(
                key=f"key{i}",
                value=f"value{i}",
                created_at=datetime.utcnow(),
                expires_at=None,
                size_bytes=100
            )
            self.cache.set(entry)
        
        self.assertEqual(self.cache.size(), 5)
        
        # Access key0 to make it recently used
        self.cache.get("key0")
        
        # Add one more - should evict key1 (least recently used)
        entry = CacheEntry(
            key="key6",
            value="value6",
            created_at=datetime.utcnow(),
            expires_at=None,
            size_bytes=100
        )
        self.cache.set(entry)
        
        self.assertEqual(self.cache.size(), 5)
        self.assertIsNotNone(self.cache.get("key0"))  # Recently accessed
        self.assertIsNone(self.cache.get("key1"))  # Should be evicted
    
    def test_access_counting(self):
        """Test access count tracking."""
        entry = CacheEntry(
            key="counter",
            value="value",
            created_at=datetime.utcnow(),
            expires_at=None,
            size_bytes=100
        )
        self.cache.set(entry)
        
        for _ in range(5):
            self.cache.get("counter")
        
        retrieved = self.cache.get("counter")
        self.assertGreaterEqual(retrieved.access_count, 5)


class TestSQLiteCacheBackend(unittest.TestCase):
    """Test SQLite cache backend."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "cache.db"
        self.cache = SQLiteCacheBackend(str(self.db_path))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence(self):
        """Test data survives backend recreation."""
        entry = CacheEntry(
            key="persist",
            value={"complex": "data", "number": 42},
            created_at=datetime.utcnow(),
            expires_at=None,
            size_bytes=200
        )
        
        self.cache.set(entry)
        
        # Recreate cache
        del self.cache
        self.cache = SQLiteCacheBackend(str(self.db_path))
        
        retrieved = self.cache.get("persist")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.value["number"], 42)
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        # Add expired entry
        expired = CacheEntry(
            key="expired",
            value="old",
            created_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1),
            size_bytes=100
        )
        self.cache.set(expired)
        
        # Add valid entry
        valid = CacheEntry(
            key="valid",
            value="new",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            size_bytes=100
        )
        self.cache.set(valid)
        
        self.assertEqual(self.cache.size(), 2)
        
        # Cleanup
        removed = self.cache.cleanup_expired()
        self.assertEqual(removed, 1)
        self.assertEqual(self.cache.size(), 1)
        self.assertIsNotNone(self.cache.get("valid"))


class TestCacheManager(unittest.TestCase):
    """Test high-level cache manager."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CacheManager(
            memory_cache_size=10,
            disk_cache_path=str(Path(self.temp_dir) / "cache.db"),
            default_ttl_seconds=3600
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_two_tier_cache(self):
        """Test L1 and L2 cache interaction."""
        # Set in cache
        self.cache.set("ns", "key", "value")
        
        # Should be in L1
        hit, value = self.cache.get("ns", "key")
        self.assertTrue(hit)
        self.assertEqual(value, "value")
        
        # Clear L1 only (simulate eviction)
        self.cache.l1_cache.clear()
        
        # Should still be in L2
        hit, value = self.cache.get("ns", "key")
        self.assertTrue(hit)
        self.assertEqual(value, "value")
        
        # Should be promoted back to L1
        entry = self.cache.l1_cache.get(self.cache._compute_key("ns", "key"))
        self.assertIsNotNone(entry)
    
    def test_statistics(self):
        """Test cache statistics."""
        # Generate hits and misses
        for i in range(10):
            self.cache.set("test", f"key{i}", f"value{i}")
        
        for i in range(10):
            self.cache.get("test", f"key{i}")  # hits
        
        for i in range(10, 20):
            self.cache.get("test", f"key{i}")  # misses
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 10)
        self.assertEqual(stats['misses'], 10)
        self.assertEqual(stats['hit_rate'], 0.5)
    
    def test_custom_ttl(self):
        """Test per-entry TTL."""
        self.cache.set("test", "short", "value", ttl_seconds=1)
        self.cache.set("test", "long", "value", ttl_seconds=3600)
        
        time.sleep(1.5)
        
        hit_short, _ = self.cache.get("test", "short")
        hit_long, _ = self.cache.get("test", "long")
        
        self.assertFalse(hit_short)
        self.assertTrue(hit_long)


class TestSpecializedCaches(unittest.TestCase):
    """Test specialized cache implementations."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CacheManager(
            memory_cache_size=10,
            disk_cache_path=str(Path(self.temp_dir) / "cache.db")
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_llm_response_cache(self):
        """Test LLM response caching."""
        llm_cache = LLMResponseCache(self.manager, ttl_seconds=3600)
        
        # Cache response
        llm_cache.set("What is AI?", "gpt-4", {"text": "AI is artificial intelligence"}, temperature=0.7)
        
        # Retrieve
        hit, response = llm_cache.get("What is AI?", "gpt-4", temperature=0.7)
        self.assertTrue(hit)
        self.assertEqual(response["text"], "AI is artificial intelligence")
        
        # Different temperature should miss
        hit, _ = llm_cache.get("What is AI?", "gpt-4", temperature=0.5)
        self.assertFalse(hit)
    
    def test_embedding_cache(self):
        """Test embedding caching with numpy arrays."""
        emb_cache = EmbeddingCache(self.manager)
        
        embedding = np.random.randn(384).astype(np.float32)
        
        emb_cache.set("test text", "model-v1", embedding)
        
        hit, retrieved = emb_cache.get("test text", "model-v1")
        self.assertTrue(hit)
        np.testing.assert_array_almost_equal(embedding, retrieved)
    
    def test_search_result_cache(self):
        """Test search result caching."""
        search_cache = SearchResultCache(self.manager, ttl_seconds=300)
        
        results = [
            {"note_id": "note1", "score": 0.9},
            {"note_id": "note2", "score": 0.8}
        ]
        
        search_cache.set("query", 5, results, filters={"tag": "ai"})
        
        hit, cached_results = search_cache.get("query", 5, filters={"tag": "ai"})
        self.assertTrue(hit)
        self.assertEqual(len(cached_results), 2)
        
        # Different filters should miss
        hit, _ = search_cache.get("query", 5, filters={"tag": "programming"})
        self.assertFalse(hit)


class TestCacheDecorator(unittest.TestCase):
    """Test caching decorator."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CacheManager(
            memory_cache_size=10,
            disk_cache_path=str(Path(self.temp_dir) / "cache.db")
        )
        self.call_count = 0
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cached_decorator(self):
        """Test @cached decorator."""
        @cached(self.cache, "test_ns", ttl_seconds=3600)
        def expensive_function(x, y):
            self.call_count += 1
            return x * y
        
        # First call
        result1 = expensive_function(5, 10)
        self.assertEqual(result1, 50)
        self.assertEqual(self.call_count, 1)
        
        # Second call with same args - should use cache
        result2 = expensive_function(5, 10)
        self.assertEqual(result2, 50)
        self.assertEqual(self.call_count, 1)  # Not called again
        
        # Different args - should compute
        result3 = expensive_function(3, 4)
        self.assertEqual(result3, 12)
        self.assertEqual(self.call_count, 2)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_workflow(self):
        """Test complete caching workflow."""
        temp_dir = tempfile.mkdtemp()
        try:
            cache = CacheManager(
                memory_cache_size=100,
                disk_cache_path=str(Path(temp_dir) / "cache.db"),
                default_ttl_seconds=3600
            )
            
            # Phase 1: Cache various data types
            cache.set("strings", "key", "value")
            cache.set("numbers", "key", 42)
            cache.set("lists", "key", [1, 2, 3])
            cache.set("dicts", "key", {"nested": "data"})
            
            # Phase 2: Verify retrieval
            for ns in ["strings", "numbers", "lists", "dicts"]:
                hit, value = cache.get(ns, "key")
                self.assertTrue(hit, f"Failed for {ns}")
                self.assertIsNotNone(value)
            
            # Phase 3: Check stats
            stats = cache.get_stats()
            self.assertEqual(stats['hits'], 4)
            self.assertEqual(stats['hit_rate'], 1.0)
            
            # Phase 4: Cleanup and verify
            cache.cleanup()
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
