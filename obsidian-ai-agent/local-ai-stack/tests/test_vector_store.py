#!/usr/bin/env python3
"""
Unit tests for Vector Store (both original and optimized)
Tests HNSW indexing, lazy loading, and batch operations
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_stack.vector_server import LocalVectorStore, Document
from ai_stack.vector_server_optimized import OptimizedVectorStore, HNSWIndex


class TestHNSWIndex(unittest.TestCase):
    """Test HNSW index implementation"""
    
    def setUp(self):
        self.index = HNSWIndex(dim=128, max_elements=1000)
    
    def test_add_and_query(self):
        """Test basic add and query operations"""
        embeddings = [[0.1] * 128, [0.2] * 128, [0.3] * 128]
        ids = ["doc1", "doc2", "doc3"]
        
        self.index.add_items(embeddings, ids)
        
        results, distances = self.index.knn_query([0.15] * 128, k=2)
        
        self.assertEqual(len(results), 2)
        # doc1 (0.1) should be closest to query (0.15)
        self.assertEqual(results[0], "doc1")
    
    def test_save_and_load(self):
        """Test index persistence"""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Add items
            self.index.add_items([[0.1] * 128], ["doc1"])
            
            # Save
            self.index.save(temp_dir)
            
            # Load in new index
            new_index = HNSWIndex(dim=128)
            new_index.load(temp_dir)
            
            # Query should work
            results, _ = new_index.knn_query([0.1] * 128, k=1)
            self.assertEqual(results[0], "doc1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestOptimizedVectorStore(unittest.TestCase):
    """Test optimized vector store"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = OptimizedVectorStore(data_path=self.temp_dir, embedding_dim=128)
    
    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_single(self):
        """Test adding a single document"""
        docs = [
            Document(id="test1", content="Test content", metadata={"key": "value"}, embedding=[0.1] * 128)
        ]
        
        self.store.add(docs)
        self.assertEqual(self.store.count(), 1)
    
    def test_add_batch(self):
        """Test batch add operation"""
        docs = [
            Document(id=f"doc{i}", content=f"Content {i}", metadata={}, embedding=[i/10.0] * 128)
            for i in range(100)
        ]
        
        self.store.add(docs, batch_size=25)
        self.assertEqual(self.store.count(), 100)
    
    def test_query(self):
        """Test similarity search"""
        # Add documents
        docs = [
            Document(id="doc1", content="Python programming", metadata={}, embedding=[0.1] * 128),
            Document(id="doc2", content="JavaScript coding", metadata={}, embedding=[0.5] * 128),
            Document(id="doc3", content="Docker containers", metadata={}, embedding=[0.9] * 128),
        ]
        self.store.add(docs)
        
        # Query
        results = self.store.query([0.15] * 128, n_results=2)
        
        self.assertEqual(len(results), 2)
        # doc1 should be first (closest to 0.15)
        self.assertEqual(results[0]['id'], "doc1")
        self.assertIn('score', results[0])
        self.assertIn('distance', results[0])
    
    def test_query_with_filter(self):
        """Test filtered search"""
        docs = [
            Document(id="doc1", content="Python", metadata={"category": "programming"}, embedding=[0.1] * 128),
            Document(id="doc2", content="Cooking", metadata={"category": "food"}, embedding=[0.1] * 128),
        ]
        self.store.add(docs)
        
        # Query with filter
        results = self.store.query([0.1] * 128, n_results=5, filter_metadata={"category": "programming"})
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "doc1")
    
    def test_get(self):
        """Test document retrieval"""
        doc = Document(id="test1", content="Test", metadata={"key": "val"}, embedding=[0.1] * 128)
        self.store.add([doc])
        
        retrieved = self.store.get("test1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "test1")
        self.assertEqual(retrieved.content, "Test")
    
    def test_delete(self):
        """Test document deletion"""
        doc = Document(id="test1", content="Test", metadata={}, embedding=[0.1] * 128)
        self.store.add([doc])
        
        result = self.store.delete("test1")
        self.assertTrue(result)
        self.assertEqual(self.store.count(), 0)
        
        # Delete non-existent
        result = self.store.delete("nonexistent")
        self.assertFalse(result)
    
    def test_persistence(self):
        """Test data persistence across instances"""
        doc = Document(id="persist1", content="Persistent", metadata={}, embedding=[0.1] * 128)
        self.store.add([doc])
        self.store._save_data(force=True)
        
        # Create new instance
        store2 = OptimizedVectorStore(data_path=self.temp_dir, embedding_dim=128)
        
        self.assertEqual(store2.count(), 1)
        retrieved = store2.get("persist1")
        self.assertIsNotNone(retrieved)
        store2.close()
    
    def test_query_performance(self):
        """Test query performance (should be fast with HNSW)"""
        # Add many documents
        docs = [
            Document(id=f"doc{i}", content=f"Content {i}", metadata={}, embedding=[i/1000.0] * 128)
            for i in range(500)
        ]
        self.store.add(docs)
        
        # Time queries
        start = time.time()
        for _ in range(100):
            results = self.store.query([0.5] * 128, n_results=5)
        elapsed = time.time() - start
        
        # Should be fast (less than 1 second for 100 queries)
        self.assertLess(elapsed, 1.0)
        
        # Check stats
        stats = self.store.get_stats()
        self.assertIn('avg_query_time_ms', stats)
        self.assertIn('documents', stats)
    
    def test_stats(self):
        """Test statistics reporting"""
        self.store.add([Document(id="d1", content="Test", metadata={}, embedding=[0.1] * 128)])
        
        stats = self.store.get_stats()
        
        self.assertEqual(stats['documents'], 1)
        self.assertIn('queries', stats)
        self.assertIn('using_hnsw', stats)


class TestOriginalVectorStore(unittest.TestCase):
    """Test original vector store for compatibility"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = LocalVectorStore(data_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_operations(self):
        """Test basic CRUD operations"""
        doc = Document(id="test1", content="Test content", metadata={"key": "value"})
        doc.embedding = [0.1, 0.2, 0.3]
        
        # Add
        self.store.add([doc])
        self.assertEqual(self.store.count(), 1)
        
        # Query
        results = self.store.query([0.1, 0.2, 0.3], n_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "test1")
        
        # Get
        retrieved = self.store.get("test1")
        self.assertIsNotNone(retrieved)
        
        # Delete
        self.assertTrue(self.store.delete("test1"))
        self.assertEqual(self.store.count(), 0)


class TestComparison(unittest.TestCase):
    """Compare original vs optimized implementations"""
    
    def test_query_accuracy(self):
        """Ensure both implementations return similar results"""
        temp1 = tempfile.mkdtemp()
        temp2 = tempfile.mkdtemp()
        
        try:
            original = LocalVectorStore(data_path=temp1)
            optimized = OptimizedVectorStore(data_path=temp2, embedding_dim=3)
            
            # Add same documents
            docs = [
                Document(id="d1", content="A", metadata={}, embedding=[1.0, 0.0, 0.0]),
                Document(id="d2", content="B", metadata={}, embedding=[0.0, 1.0, 0.0]),
                Document(id="d3", content="C", metadata={}, embedding=[0.0, 0.0, 1.0]),
            ]
            original.add(docs)
            optimized.add(docs)
            
            # Query
            orig_results = original.query([1.0, 0.1, 0.1], n_results=2)
            opt_results = optimized.query([1.0, 0.1, 0.1], n_results=2)
            
            # Both should return d1 as top result
            self.assertEqual(orig_results[0]['id'], "d1")
            self.assertEqual(opt_results[0]['id'], "d1")
            
            optimized.close()
        finally:
            shutil.rmtree(temp1, ignore_errors=True)
            shutil.rmtree(temp2, ignore_errors=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
