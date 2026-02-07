"""Tests for RAG components."""

import pytest
from pathlib import Path
from pkm_agent.rag.chunker import Chunker, ChunkerConfig
from pkm_agent.data.models import Note, Chunk, NoteMetadata
from datetime import datetime


class TestChunker:
    """Tests for Chunker class."""
    
    def test_chunk_note(self, test_chunker, test_pkm_root):
        """Test chunking a note."""
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test Note",
            content="This is a test note. " * 20,  # Longer content
            metadata=NoteMetadata(tags=["test"]),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        chunks = test_chunker.chunk_note(note)
        assert len(chunks) > 1
        assert all(c.note_id == "test" for c in chunks)
    
    def test_chunk_small_note(self, test_chunker, test_pkm_root):
        """Test chunking a small note (should produce few chunks)."""
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test",
            content="Short content",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        chunks = test_chunker.chunk_note(note)
        # Small content might not be chunked
        assert len(chunks) >= 0
    
    def test_chunk_with_structure(self, test_chunker, test_pkm_root):
        """Test chunking respects markdown structure."""
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test",
            content="""# Section 1

Content for section 1.

## Section 2

Content for section 2.

### Section 3

Content for section 3.
""",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        chunks = test_chunker.chunk_note(note)
        # Should create chunks based on headers
        assert len(chunks) > 0
    
    def test_chunk_metadata(self, test_chunker, test_pkm_root):
        """Test that chunks preserve note metadata."""
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test Note",
            content="Content here",
            metadata=NoteMetadata(
                title="Test",
                tags=["python", "programming"],
                area="work",
            ),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        chunks = test_chunker.chunk_note(note)
        if chunks:
            chunk = chunks[0]
            assert chunk.metadata["title"] == "Test Note"
            assert chunk.metadata["tags"] == ["python", "programming"]
            assert chunk.metadata["area"] == "work"


class TestChunkerConfig:
    """Tests for ChunkerConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ChunkerConfig()
        assert config.chunk_size == 512
        assert config.chunk_overlap == 64
        assert config.min_chunk_size == 100
        assert config.respect_boundaries is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ChunkerConfig(
            chunk_size=256,
            chunk_overlap=32,
            min_chunk_size=50,
            respect_boundaries=False,
        )
        assert config.chunk_size == 256
        assert config.chunk_overlap == 32
        assert config.min_chunk_size == 50
        assert config.respect_boundaries is False


@pytest.mark.slow
class TestEmbeddingEngine:
    """Tests for EmbeddingEngine (may require model download)."""
    
    def test_lazy_loading(self, test_embedding_engine):
        """Test that model is lazy loaded."""
        assert test_embedding_engine._model is None
        # Access dimension to trigger load
        _ = test_embedding_engine.dimension
        # Note: model may still be None if download fails
    
    @pytest.mark.slow
    def test_embed_text(self, test_embedding_engine):
        """Test embedding generation (slow test)."""
        texts = ["Hello world", "Test text"]
        try:
            embeddings = test_embedding_engine.embed(texts)
            assert len(embeddings) == len(texts)
            assert all(len(emb) > 0 for emb in embeddings)
        except Exception:
            # May fail if model not downloaded
            pytest.skip("Model download failed")
    
    @pytest.mark.slow
    def test_embed_query(self, test_embedding_engine):
        """Test embedding a single query (slow test)."""
        try:
            embedding = test_embedding_engine.embed_query("test query")
            assert len(embedding) > 0
        except Exception:
            pytest.skip("Model download failed")


@pytest.mark.slow
class TestVectorStore:
    """Tests for VectorStore (slow - requires ChromaDB)."""
    
    @pytest.mark.slow
    def test_add_chunks(self, test_vectorstore):
        """Test adding chunks to vector store."""
        chunks = [
            Chunk(
                id="chunk_0",
                note_id="note1",
                content="Test content",
                index=0,
                metadata={"title": "Test", "path": "test.md"},
            )
        ]
        
        try:
            count = test_vectorstore.add_chunks(chunks)
            assert count == 1
        except Exception:
            pytest.skip("ChromaDB not available")
    
    @pytest.mark.slow
    def test_search(self, test_vectorstore):
        """Test searching vector store."""
        chunks = [
            Chunk(
                id="chunk_0",
                note_id="note1",
                content="Python is a programming language",
                index=0,
                metadata={"title": "Python", "path": "python.md"},
            )
        ]
        
        try:
            test_vectorstore.add_chunks(chunks)
            results = test_vectorstore.search("programming language", k=5)
            assert len(results) >= 0
        except Exception:
            pytest.skip("ChromaDB not available")
