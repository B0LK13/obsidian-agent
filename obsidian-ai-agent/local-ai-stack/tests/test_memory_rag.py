#!/usr/bin/env python3
"""
Unit tests for Memory-Augmented RAG System
Tests all 3 memory layers: short-term, long-term, and episodic
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_stack.memory_rag import (
    MemoryEntry, Relationship,
    ShortTermMemory, LongTermMemory, EpisodicMemory,
    MemoryAugmentedRAG
)


class TestMemoryEntry(unittest.TestCase):
    """Test MemoryEntry dataclass"""
    
    def test_creation(self):
        entry = MemoryEntry(id="test1", content="Test content")
        self.assertEqual(entry.id, "test1")
        self.assertEqual(entry.content, "Test content")
        self.assertEqual(entry.memory_type, "short_term")
        self.assertIsNotNone(entry.timestamp)
    
    def test_to_dict(self):
        entry = MemoryEntry(id="test1", content="Test content")
        d = entry.to_dict()
        self.assertEqual(d['id'], "test1")
        self.assertEqual(d['content'], "Test content")
        self.assertIn('timestamp', d)
    
    def test_from_dict(self):
        original = MemoryEntry(id="test1", content="Test content")
        d = original.to_dict()
        restored = MemoryEntry.from_dict(d)
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.content, original.content)


class TestShortTermMemory(unittest.TestCase):
    """Test ShortTermMemory class"""
    
    def setUp(self):
        self.stm = ShortTermMemory(max_entries=10, ttl_minutes=60)
    
    def test_add(self):
        entry_id = self.stm.add("Test content", {"source": "test"})
        self.assertIsNotNone(entry_id)
        self.assertEqual(len(self.stm.entries), 1)
    
    def test_get(self):
        entry_id = self.stm.add("Test content")
        entry = self.stm.get(entry_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.content, "Test content")
        self.assertEqual(entry.access_count, 1)
        
        # Second access
        entry = self.stm.get(entry_id)
        self.assertEqual(entry.access_count, 2)
    
    def test_get_recent(self):
        for i in range(5):
            self.stm.add(f"Content {i}")
        
        recent = self.stm.get_recent(3)
        self.assertEqual(len(recent), 3)
        # Most recent should be last added
        self.assertEqual(recent[0].content, "Content 4")
    
    def test_eviction(self):
        # Fill to capacity
        for i in range(12):
            self.stm.add(f"Content {i}")
        
        # Should have evicted oldest
        self.assertLessEqual(len(self.stm.entries), 10)
    
    def test_ttl_expiration(self):
        # Create with very short TTL
        stm = ShortTermMemory(max_entries=10, ttl_minutes=0)
        entry_id = stm.add("Test content")
        
        # Manually set timestamp to past
        stm.entries[entry_id].timestamp = datetime.now() - timedelta(minutes=5)
        
        # Add new entry to trigger eviction
        stm.add("New content")
        
        # Old entry should be evicted
        self.assertIsNone(stm.get(entry_id))


class TestLongTermMemory(unittest.TestCase):
    """Test LongTermMemory class"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ltm = LongTermMemory(vector_store_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add(self):
        entry = MemoryEntry(id="test1", content="Docker is a container platform")
        embedding = [0.1] * 384
        
        entry_id = self.ltm.add(entry, embedding)
        self.assertEqual(entry_id, "test1")
        self.assertIn("test1", self.ltm.entries)
    
    def test_search(self):
        # Add some entries
        for i, content in enumerate([
            "Docker is a container platform",
            "Kubernetes orchestrates containers",
            "Python is a programming language"
        ]):
            entry = MemoryEntry(id=f"test{i}", content=content)
            embedding = [0.1 + i*0.01] * 384
            self.ltm.add(entry, embedding)
        
        # Search
        query_embedding = [0.12] * 384
        results = self.ltm.search(query_embedding, top_k=2)
        
        self.assertEqual(len(results), 2)
        # First result should be Docker (closest embedding)
        self.assertIn("Docker", results[0][0].content)
    
    def test_keyword_boost(self):
        entry = MemoryEntry(id="test1", content="Docker containers are lightweight")
        self.ltm.add(entry, [0.5] * 384)
        
        # Search with keyword
        results = self.ltm.search([0.1] * 384, query_text="docker containers", top_k=1)
        self.assertEqual(len(results), 1)
    
    def test_persistence(self):
        entry = MemoryEntry(id="test1", content="Persistent content")
        self.ltm.add(entry, [0.1] * 384)
        
        # Create new instance (should load from disk)
        ltm2 = LongTermMemory(vector_store_path=self.temp_dir)
        self.assertIn("test1", ltm2.entries)


class TestEpisodicMemory(unittest.TestCase):
    """Test EpisodicMemory class"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.em = EpisodicMemory(store_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_relationship(self):
        self.em.add_relationship("Docker", "container", "is_a", strength=0.9)
        
        self.assertIn("Docker", self.em.entities)
        self.assertIn("container", self.em.entities)
        self.assertEqual(len(self.em.relationships), 1)
    
    def test_get_related(self):
        self.em.add_relationship("Docker", "Kubernetes", "related_to", 0.8)
        self.em.add_relationship("Docker", "container", "is_a", 0.9)
        
        related = self.em.get_related("Docker")
        self.assertEqual(len(related), 2)
        
        # Check sorted by strength
        self.assertEqual(related[0][0], "container")  # 0.9 strength
    
    def test_get_entity_context(self):
        self.em.add_relationship("Docker", "Kubernetes", "orchestrates", 0.8)
        self.em.add_relationship("Kubernetes", "Pod", "manages", 0.7)
        
        context = self.em.get_entity_context("Docker", depth=2)
        
        self.assertEqual(context['entity'], "Docker")
        self.assertTrue(len(context['direct_relations']) > 0)


class TestMemoryAugmentedRAG(unittest.TestCase):
    """Test integrated MemoryAugmentedRAG system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rag = MemoryAugmentedRAG(data_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_to_memory(self):
        embedding = [0.1] * 384
        
        self.rag.add_to_memory(
            content="Test content",
            embedding=embedding,
            metadata={"significant": True},
            relationships=[("A", "B", "rel")]
        )
        
        self.assertEqual(len(self.rag.short_term.entries), 1)
        self.assertEqual(len(self.rag.long_term.entries), 1)
        self.assertEqual(len(self.rag.episodic.relationships), 1)
    
    def test_process_query(self):
        # Add test data
        embedding = [0.1] * 384
        self.rag.add_to_memory(
            content="Docker is a containerization platform",
            embedding=embedding,
            metadata={"significant": True}
        )
        
        # Query
        results = self.rag.process_query("What is Docker?", embedding)
        
        self.assertIn('short_term', results)
        self.assertIn('long_term', results)
        self.assertIn('consolidated_context', results)
        self.assertTrue(len(results['consolidated_context']) > 0)
    
    def test_get_stats(self):
        self.rag.add_to_memory("Test", [0.1] * 384, {"significant": True})
        stats = self.rag.get_stats()
        
        self.assertIn('short_term', stats)
        self.assertIn('long_term', stats)
        self.assertIn('episodic', stats)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rag = MemoryAugmentedRAG(data_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_knowledge_base_workflow(self):
        """Test complete knowledge base workflow"""
        # Add knowledge
        docs = [
            ("Python is a high-level programming language", [0.1] * 384),
            ("JavaScript runs in web browsers", [0.2] * 384),
            ("Docker containers package applications", [0.3] * 384),
        ]
        
        for content, emb in docs:
            self.rag.add_to_memory(
                content=content,
                embedding=emb,
                metadata={"significant": True, "topic": "tech"},
                relationships=[
                    (content.split()[0], "technology", "is")
                ]
            )
        
        # Query
        query_emb = [0.15] * 384
        results = self.rag.process_query("Tell me about programming", query_emb)
        
        self.assertTrue(len(results['long_term']) > 0)
        self.assertIn("consolidated_context", results)
    
    def test_session_context_workflow(self):
        """Test session-based context tracking"""
        # Simulate conversation
        messages = [
            "What is machine learning?",
            "How does neural networks work?",
            "Explain deep learning"
        ]
        
        for msg in messages:
            self.rag.short_term.add(msg, {"type": "user_query"})
        
        context = self.rag.short_term.get_context_window()
        
        self.assertIn("What is machine learning?", context)
        self.assertIn("How does neural networks work?", context)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
