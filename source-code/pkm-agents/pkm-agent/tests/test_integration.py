"""Integration tests for PKM Agent."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_openai_client():
    mock_client = AsyncMock()
    
    # Setup stream
    async def mock_create(*args, **kwargs):
        async def async_gen():
            chunks = ["Hello", " world"]
            for c in chunks:
                chunk = MagicMock()
                chunk.choices = [MagicMock(delta=MagicMock(content=c))]
                yield chunk
        return async_gen()
    
    mock_client.chat.completions.create = mock_create

    with patch("pkm_agent.llm.openai_provider.OpenAIProvider._get_client", return_value=mock_client):
        yield mock_client


@pytest.mark.slow
class TestPKMIntegration:
    """Integration tests for the full PKM system."""
    
    @pytest.mark.slow
    async def test_full_indexing_flow(self, test_app, test_pkm_root):
        """Test the full indexing workflow."""
        await test_app.initialize()
        
        # Check that notes were indexed
        stats = await test_app.get_stats()
        assert stats["notes"] > 0
    
    @pytest.mark.slow
    async def test_search_functionality(self, test_app):
        """Test search functionality."""
        await test_app.initialize()
        
        # Perform a search
        results = await test_app.search("test", limit=10)
        assert isinstance(results, list)
    
    @pytest.mark.slow
    async def test_get_stats(self, test_app):
        """Test getting statistics."""
        await test_app.initialize()
        
        stats = await test_app.get_stats()
        
        assert "notes" in stats
        assert "tags" in stats
        assert "links" in stats
        assert "vector_store" in stats
        assert "llm" in stats
    
    @pytest.mark.slow
    async def test_conversation_history(self, test_app, mock_openai_client):
        """Test conversation history management."""
        await test_app.initialize()
        
        # Start a conversation
        messages = []
        async for chunk in test_app.chat("Hello"):
            messages.append(chunk)
        
        # Get history
        history = test_app.get_conversation_history()
        assert len(history) >= 2  # User + assistant
    
    @pytest.mark.slow
    async def test_list_conversations(self, test_app, mock_openai_client):
        """Test listing conversations."""
        await test_app.initialize()
        
        # Start some conversations
        async for _ in test_app.chat("Test 1"):
            pass
        
        async for _ in test_app.chat("Test 2"):
            pass
        
        # List conversations
        convs = test_app.list_conversations()
        assert len(convs) >= 2


@pytest.mark.slow
class TestAppInitialization:
    """Tests for app initialization."""
    
    @pytest.mark.slow
    async def test_app_initializes_with_config(self, test_config):
        """Test that app initializes properly with config."""
        from pkm_agent.app import PKMAgentApp
        
        app = PKMAgentApp(test_config)
        assert app.config == test_config
        assert app.db is not None
        assert app.indexer is not None
        assert app.embedding_engine is not None
        assert app.vectorstore is not None
        assert app.retriever is not None
        
        await app.close()
    
    @pytest.mark.slow
    async def test_directories_are_created(self, test_config):
        """Test that necessary directories are created."""
        from pkm_agent.app import PKMAgentApp
        
        # Ensure directories don't exist
        if test_config.data_dir.exists():
            import shutil
            shutil.rmtree(test_config.data_dir)
        
        app = PKMAgentApp(test_config)
        app.config.ensure_dirs()
        
        assert test_config.data_dir.exists()
        assert test_config.chroma_path.exists()
        assert test_config.cache_path.exists()
        
        await app.close()
