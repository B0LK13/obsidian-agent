"""
Unit tests for Vector Database Layer (Issue #96)
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from vector_database import (
    VectorDatabase,
    ChromaBackend,
    SQLiteBackend,
    EmbeddingRecord,
    SearchResult,
    create_embedding_function
)


class TestSQLiteBackend(unittest.TestCase):
    """Test SQLite fallback backend."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.backend = SQLiteBackend(str(self.db_path))
        self.embedding_dim = 384
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_and_get(self):
        """Test adding and retrieving embeddings."""
        note_id = "test/note.md"
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        metadata = {"tag": "test", "content_hash": "abc123"}
        
        success = self.backend.add(note_id, embedding, metadata)
        self.assertTrue(success)
        
        record = self.backend.get(note_id)
        self.assertIsNotNone(record)
        self.assertEqual(record.note_id, note_id)
        np.testing.assert_array_almost_equal(record.embedding, embedding)
        self.assertEqual(record.metadata["tag"], "test")
    
    def test_batch_add(self):
        """Test batch insertion."""
        from datetime import datetime
        
        records = []
        for i in range(10):
            records.append(EmbeddingRecord(
                note_id=f"note{i}.md",
                embedding=np.random.randn(self.embedding_dim).astype(np.float32),
                content_hash=f"hash{i}",
                created_at=datetime.utcnow(),
                metadata={"index": i}
            ))
        
        success = self.backend.add_batch(records)
        self.assertTrue(success)
        self.assertEqual(self.backend.count(), 10)
    
    def test_search(self):
        """Test similarity search."""
        # Add test embeddings
        for i in range(5):
            embedding = np.zeros(self.embedding_dim, dtype=np.float32)
            embedding[i] = 1.0  # Create orthogonal vectors
            self.backend.add(f"note{i}.md", embedding, {"index": i})
        
        # Search with query similar to note2
        query = np.zeros(self.embedding_dim, dtype=np.float32)
        query[2] = 1.0
        
        results = self.backend.search(query, top_k=3)
        
        self.assertEqual(len(results), 3)
        # note2 should be first (highest similarity)
        self.assertEqual(results[0].note_id, "note2.md")
        self.assertAlmostEqual(results[0].score, 1.0, places=5)
    
    def test_delete(self):
        """Test deletion."""
        self.backend.add("note1.md", np.random.randn(self.embedding_dim).astype(np.float32), {})
        self.assertEqual(self.backend.count(), 1)
        
        success = self.backend.delete("note1.md")
        self.assertTrue(success)
        self.assertEqual(self.backend.count(), 0)
        self.assertIsNone(self.backend.get("note1.md"))
    
    def test_clear(self):
        """Test clearing all data."""
        for i in range(5):
            self.backend.add(f"note{i}.md", np.random.randn(self.embedding_dim).astype(np.float32), {})
        
        self.assertEqual(self.backend.count(), 5)
        
        success = self.backend.clear()
        self.assertTrue(success)
        self.assertEqual(self.backend.count(), 0)
    
    def test_update_existing(self):
        """Test updating existing embedding."""
        note_id = "note.md"
        
        # Add initial version
        embedding1 = np.random.randn(self.embedding_dim).astype(np.float32)
        self.backend.add(note_id, embedding1, {"version": 1})
        
        # Update with new version
        embedding2 = np.random.randn(self.embedding_dim).astype(np.float32)
        self.backend.add(note_id, embedding2, {"version": 2})
        
        # Should only have one record
        self.assertEqual(self.backend.count(), 1)
        
        record = self.backend.get(note_id)
        self.assertEqual(record.metadata["version"], 2)


class TestVectorDatabase(unittest.TestCase):
    """Test high-level VectorDatabase interface."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.embedding_dim = 384
        
        # Create a simple test embedding function
        def embed(text: str) -> np.ndarray:
            np.random.seed(hash(text) % 2**32)
            return np.random.randn(self.embedding_dim).astype(np.float32)
        
        self.embed = embed
        
        self.db = VectorDatabase(
            backend="sqlite",
            persist_dir=self.temp_dir,
            embedding_function=embed
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_note(self):
        """Test adding a single note."""
        success = self.db.add_note(
            "note1.md",
            "This is test content about AI.",
            {"tag": "ai"}
        )
        
        self.assertTrue(success)
        self.assertEqual(self.db.count(), 1)
    
    def test_add_notes_batch(self):
        """Test batch note addition."""
        notes = [
            (f"note{i}.md", f"Content for note {i}", {"index": i})
            for i in range(10)
        ]
        
        success_count, failure_count = self.db.add_notes_batch(notes)
        
        self.assertEqual(success_count, 10)
        self.assertEqual(failure_count, 0)
        self.assertEqual(self.db.count(), 10)
    
    def test_search(self):
        """Test semantic search."""
        # Add notes
        self.db.add_note("ai.md", "Machine learning and artificial intelligence", {"category": "tech"})
        self.db.add_note("cooking.md", "Recipes and cooking techniques", {"category": "food"})
        self.db.add_note("python.md", "Python programming language", {"category": "tech"})
        
        # Search
        results = self.db.search("programming", top_k=2)
        
        self.assertGreaterEqual(len(results), 1)
        # Results should have scores (cosine similarity: -1 to 1)
        for r in results:
            self.assertIsInstance(r.score, float)
            self.assertGreaterEqual(r.score, -1.0)
            self.assertLessEqual(r.score, 1.0)
    
    def test_search_by_embedding(self):
        """Test search with pre-computed embedding."""
        self.db.add_note("note1.md", "Content here", {})
        
        query_embedding = self.embed("test query")
        results = self.db.search_by_embedding(query_embedding, top_k=1)
        
        self.assertEqual(len(results), 1)
    
    def test_delete_and_get(self):
        """Test note deletion and retrieval."""
        self.db.add_note("note1.md", "Content", {"key": "value"})
        
        record = self.db.get_note("note1.md")
        self.assertIsNotNone(record)
        self.assertEqual(record.metadata["key"], "value")
        
        self.db.delete_note("note1.md")
        self.assertIsNone(self.db.get_note("note1.md"))
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        self.db.add_note("note1.md", "Content 1", {})
        self.db.add_note("note2.md", "Content 2", {})
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_notes'], 2)
        self.assertEqual(stats['backend'], 'SQLiteBackend')
        self.assertTrue(stats['has_embedding_function'])
    
    def test_clear_database(self):
        """Test clearing entire database."""
        for i in range(5):
            self.db.add_note(f"note{i}.md", f"Content {i}", {})
        
        self.assertEqual(self.db.count(), 5)
        
        success = self.db.clear()
        self.assertTrue(success)
        self.assertEqual(self.db.count(), 0)
    
    def test_no_embedding_function_error(self):
        """Test error handling when no embedding function."""
        db_no_embed = VectorDatabase(backend="sqlite", persist_dir=self.temp_dir)
        
        success = db_no_embed.add_note("note.md", "content", {})
        self.assertFalse(success)
        
        results = db_no_embed.search("query")
        self.assertEqual(len(results), 0)


class TestEmbeddingFunction(unittest.TestCase):
    """Test embedding function factory."""
    
    def test_fallback_embedding(self):
        """Test fallback embedding when sentence-transformers not available."""
        embed = create_embedding_function()
        
        # Should return a vector
        vec1 = embed("test text")
        self.assertIsInstance(vec1, np.ndarray)
        self.assertEqual(vec1.dtype, np.float32)
        
        # Same text should produce same embedding (deterministic)
        vec2 = embed("test text")
        np.testing.assert_array_equal(vec1, vec2)
        
        # Different text should produce different embedding
        vec3 = embed("different text")
        self.assertFalse(np.array_equal(vec1, vec3))


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: add, search, update, delete."""
        temp_dir = tempfile.mkdtemp()
        try:
            def embed(text: str) -> np.ndarray:
                np.random.seed(hash(text) % 2**32)
                return np.random.randn(384).astype(np.float32)
            
            db = VectorDatabase(
                backend="sqlite",
                persist_dir=temp_dir,
                embedding_function=embed
            )
            
            # Phase 1: Add notes
            db.add_note("ai_basics.md", "Introduction to AI and ML", {"level": "beginner"})
            db.add_note("deep_learning.md", "Neural networks and deep learning", {"level": "advanced"})
            db.add_note("cooking.md", "Italian cuisine recipes", {"level": "beginner"})
            
            self.assertEqual(db.count(), 3)
            
            # Phase 2: Search
            results = db.search("neural networks", top_k=2)
            self.assertGreaterEqual(len(results), 1)
            
            # Phase 3: Update existing
            db.add_note("ai_basics.md", "Updated AI introduction with examples", {"level": "beginner", "updated": True})
            record = db.get_note("ai_basics.md")
            self.assertTrue(record.metadata.get("updated"))
            self.assertEqual(db.count(), 3)  # Still 3, not 4
            
            # Phase 4: Delete
            db.delete_note("cooking.md")
            self.assertEqual(db.count(), 2)
            
            # Verify deletion
            self.assertIsNone(db.get_note("cooking.md"))
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
