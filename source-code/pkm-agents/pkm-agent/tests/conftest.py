"""Test fixtures for PKM Agent tests."""

import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from pkm_agent.config import Config
from pkm_agent.data import Database, FileIndexer
from pkm_agent.rag import EmbeddingEngine, VectorStore, Chunker, Retriever
from pkm_agent.llm.base import Message
from pkm_agent.app import PKMAgentApp


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_pkm_root(temp_dir):
    """Create a test PKM root directory with sample notes."""
    pkm_dir = temp_dir / "pkm"
    pkm_dir.mkdir()
    
    # Create sample note
    note1 = pkm_dir / "test-note.md"
    note1.write_text("""---
title: Test Note
tags: [test, sample]
created: 2024-01-01
---

# Test Note

This is a test note for the PKM system.

It contains some content to test indexing and search.
""")
    
    note2 = pkm_dir / "another-note.md"
    note2.write_text("""---
title: Another Note
tags: [sample]
area: work
---

# Another Note

This is another test note.
It's about work-related topics.
""")
    
    return pkm_dir


@pytest.fixture
def test_config(test_pkm_root):
    """Create test configuration."""
    return Config(
        pkm_root=test_pkm_root,
        data_dir=test_pkm_root.parent / ".pkm-test",
        llm={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 100,
        },
        rag={
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_size": 512,
            "chunk_overlap": 64,
            "top_k": 5,
            "similarity_threshold": 0.7,
        },
    )


@pytest.fixture
def test_database(test_config):
    """Create test database."""
    db = Database(test_config.db_path)
    yield db
    
    # Cleanup
    if test_config.db_path.exists():
        test_config.db_path.unlink()


@pytest.fixture
def test_indexer(test_pkm_root, test_database):
    """Create test file indexer."""
    return FileIndexer(test_pkm_root, test_database)


@pytest.fixture
def test_chunker():
    """Create test chunker."""
    from pkm_agent.rag.chunker import ChunkerConfig
    return Chunker(ChunkerConfig(chunk_size=200, chunk_overlap=50))


@pytest.fixture
def test_embedding_engine(test_config):
    """Create test embedding engine."""
    return EmbeddingEngine(
        model_name=test_config.rag.embedding_model,
        cache_dir=test_config.cache_path,
    )


@pytest.fixture
def test_vectorstore(test_config, test_embedding_engine):
    """Create test vector store."""
    vs = VectorStore(test_config.chroma_path, test_embedding_engine)
    yield vs
    
    # Cleanup
    if test_config.chroma_path.exists():
        import shutil
        shutil.rmtree(test_config.chroma_path, ignore_errors=True)


@pytest.fixture
def test_retriever(test_database, test_vectorstore):
    """Create test retriever."""
    return Retriever(test_database, test_vectorstore)


@pytest.fixture
async def test_app(test_config):
    """Create test PKM application."""
    app = PKMAgentApp(test_config)
    yield app
    
    await app.close()


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="What is the capital of France?"),
    ]
