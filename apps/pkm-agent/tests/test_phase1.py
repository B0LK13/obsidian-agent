"""Comprehensive test suite for PKM Agent Phase 1 optimizations.

Tests:
- Audit logging system
- Cache manager
- ReAct agent
- Enhanced app integration
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from pkm_agent.audit_logger import AuditEntry, AuditLogger
from pkm_agent.cache_manager import CacheManager, LRUCache
from pkm_agent.react_agent import AgentStatus, ReActAgent, ThoughtStep, ToolResult


class TestAuditLogger:
    """Test audit logging system."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test audit logger initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path)
            
            await logger.initialize()
            assert logger._initialized
            assert db_path.exists()
            
            await logger.close()

    @pytest.mark.asyncio
    async def test_log_entry(self):
        """Test logging an audit entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path)
            await logger.initialize()
            
            entry = AuditEntry(
                action="test_action",
                target="note-123",
                snapshot_before="old content",
                snapshot_after="new content",
                user_approved=True,
            )
            
            entry_id = await logger.log(entry)
            assert entry_id == entry.id
            
            # Retrieve entry
            retrieved = await logger.get_entry(entry_id)
            assert retrieved is not None
            assert retrieved.action == "test_action"
            assert retrieved.target == "note-123"
            assert retrieved.snapshot_before == "old content"
            assert retrieved.snapshot_after == "new content"
            
            await logger.close()

    @pytest.mark.asyncio
    async def test_get_history(self):
        """Test retrieving audit history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path)
            await logger.initialize()
            
            # Log multiple entries
            for i in range(5):
                entry = AuditEntry(
                    action=f"action_{i}",
                    target=f"note-{i}",
                )
                await logger.log(entry)
            
            # Get all history
            history = await logger.get_history(limit=10)
            assert len(history) == 5
            
            # Filter by action
            history = await logger.get_history(action="action_2", limit=10)
            assert len(history) == 1
            assert history[0].action == "action_2"
            
            await logger.close()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test audit statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path)
            await logger.initialize()
            
            # Log entries
            for action in ["ingest", "normalize", "ingest", "search"]:
                entry = AuditEntry(action=action)
                await logger.log(entry)
            
            stats = await logger.get_stats()
            assert stats["total_entries"] == 4
            assert stats["by_action"]["ingest"] == 2
            assert stats["by_action"]["normalize"] == 1
            assert stats["by_action"]["search"] == 1
            
            await logger.close()


class TestCacheManager:
    """Test caching system."""

    def test_lru_cache_basic(self):
        """Test basic LRU cache operations."""
        cache = LRUCache[str](max_size=3, ttl_seconds=3600)
        
        # Set values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Get values
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # Check stats
        stats = cache.stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 0
        assert stats["size"] == 3

    def test_lru_cache_eviction(self):
        """Test LRU eviction policy."""
        cache = LRUCache[str](max_size=3, ttl_seconds=3600)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Add 4th item - should evict key1 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_cache_ttl(self):
        """Test TTL expiration."""
        import time
        
        cache = LRUCache[str](max_size=10, ttl_seconds=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        assert cache.get("key1") is None  # Expired

    def test_disk_cache(self):
        """Test disk cache operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from pkm_agent.cache_manager import DiskCache
            
            cache = DiskCache(Path(tmpdir))
            
            # Set value
            cache.set("key1", {"data": "value1"})
            
            # Get value
            result = cache.get("key1")
            assert result == {"data": "value1"}
            
            # Stats
            stats = cache.stats()
            assert stats["entries"] == 1

    def test_cache_manager_integration(self):
        """Test cache manager with multiple cache types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(Path(tmpdir), memory_cache_size=100)
            
            # Test query cache (memory)
            cache.set_query_result("test query", [{"result": 1}])
            result = cache.get_query_result("test query")
            assert result == [{"result": 1}]
            
            # Test embedding cache (disk)
            import numpy as np
            embedding = np.array([1.0, 2.0, 3.0])
            cache.set_embedding("test text", embedding)
            result = cache.get_embedding("test text")
            assert np.array_equal(result, embedding)
            
            # Stats
            stats = cache.stats()
            assert stats["query_cache"]["hits"] == 1
            assert stats["embedding_cache"]["entries"] == 1


class MockLLMProvider:
    """Mock LLM for testing."""
    
    model = "mock-model"
    
    async def chat(self, messages):
        """Mock chat method."""
        # Simple ReAct response
        return """Thought: I should search for relevant notes.
Action: search_notes
Action Input: {"query": "test topic", "top_k": 3}"""


class MockRetriever:
    """Mock retriever for testing."""
    
    async def search(self, query, k=5):
        """Mock search."""
        return [
            {"id": "note1", "content": "Content about test topic"},
            {"id": "note2", "content": "More content about test topic"},
        ]


class TestReActAgent:
    """Test ReAct agent system."""

    @pytest.mark.asyncio
    async def test_thought_step_parsing(self):
        """Test parsing LLM response into ThoughtStep."""
        from pkm_agent.react_agent import SearchNotesTool
        
        llm = MockLLMProvider()
        retriever = MockRetriever()
        tools = [SearchNotesTool(retriever)]
        
        agent = ReActAgent(
            llm_provider=llm,
            tools=tools,
            max_iterations=5,
            verbose=True,
        )
        
        response = """Thought: I need to search for information.
Action: search_notes
Action Input: {"query": "test", "top_k": 3}"""
        
        step = agent._parse_response(response, step_number=1)
        assert step.thought == "I need to search for information."
        assert step.action == "search_notes"
        assert step.action_input == {"query": "test", "top_k": 3}

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution."""
        from pkm_agent.react_agent import SearchNotesTool
        
        retriever = MockRetriever()
        tool = SearchNotesTool(retriever)
        
        result = await tool.execute(query="test", top_k=2)
        assert result.success
        assert len(result.data) == 2


class TestIntegration:
    """Integration tests for enhanced app."""

    @pytest.mark.asyncio
    async def test_enhanced_app_initialization(self):
        """Test enhanced app initialization."""
        # This would require full environment setup
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_search_with_caching(self):
        """Test search with cache integration."""
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_audit_trail_on_operations(self):
        """Test that operations create audit entries."""
        # Placeholder for integration test
        pass


def run_tests():
    """Run all tests with pytest."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
