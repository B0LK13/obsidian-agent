"""
Integration tests for Obsidian Agent Core
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from obsidian_agent_core import (
    ObsidianAgentCore,
    AgentConfig,
    create_agent
)


class TestAgentConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AgentConfig(vault_path="/test/vault")
        
        self.assertEqual(config.vault_path, "/test/vault")
        self.assertTrue(config.enable_incremental_indexing)
        self.assertEqual(config.cache_memory_size, 1000)
        self.assertEqual(config.suggestion_min_confidence, 0.5)
    
    def test_config_serialization(self):
        """Test config save/load."""
        config = AgentConfig(
            vault_path="/test/vault",
            data_dir="/test/data",
            cache_memory_size=500
        )
        
        # Save
        temp_file = Path(tempfile.mkdtemp()) / "config.json"
        config.save(str(temp_file))
        
        # Load
        loaded = AgentConfig.from_file(str(temp_file))
        
        self.assertEqual(loaded.vault_path, config.vault_path)
        self.assertEqual(loaded.cache_memory_size, config.cache_memory_size)
        
        shutil.rmtree(temp_file.parent)


class TestObsidianAgentCore(unittest.TestCase):
    """Test core agent functionality."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault_path = self.temp_dir / "vault"
        self.vault_path.mkdir()
        self.data_dir = self.temp_dir / "data"
        
        # Create test notes
        (self.vault_path / "Note A.md").write_text(
            "# Note A\n\nContent about AI and machine learning."
        )
        (self.vault_path / "Note B.md").write_text(
            "# Note B\n\nMore about ML and AI. [[Note A]]"
        )
        
        config = AgentConfig(
            vault_path=str(self.vault_path),
            data_dir=str(self.data_dir)
        )
        
        self.agent = ObsidianAgentCore(config)
    
    def tearDown(self):
        self.agent.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test agent initialization."""
        success = self.agent.initialize()
        
        self.assertTrue(success)
        self.assertIsNotNone(self.agent.indexer)
        self.assertIsNotNone(self.agent.vector_db)
        self.assertIsNotNone(self.agent.cache)
    
    def test_index_vault(self):
        """Test vault indexing."""
        self.agent.initialize()
        
        report = self.agent.index_vault()
        
        self.assertIsNotNone(report)
        self.assertEqual(report.total_scanned, 2)
    
    def test_search_notes(self):
        """Test semantic search."""
        self.agent.initialize()
        self.agent.index_vault()
        
        results = self.agent.search_notes("artificial intelligence", top_k=5)
        
        # Should return results (even if empty due to mock embeddings)
        self.assertIsInstance(results, list)
    
    def test_scan_links(self):
        """Test link scanning."""
        self.agent.initialize()
        
        report = self.agent.scan_links()
        
        self.assertIsNotNone(report)
        self.assertEqual(report.total_notes, 2)
    
    def test_get_status(self):
        """Test status retrieval."""
        self.agent.initialize()
        
        status = self.agent.get_status()
        
        self.assertIsNotNone(status)
        self.assertIn('indexer', status.components)
        self.assertIn('vector_db', status.components)
    
    def test_get_stats_summary(self):
        """Test stats summary."""
        self.agent.initialize()
        self.agent.index_vault()
        
        stats = self.agent.get_stats_summary()
        
        self.assertIn('healthy', stats)
        self.assertIn('notes_indexed', stats)
        self.assertIn('cache_hit_rate', stats)


class TestCreateAgent(unittest.TestCase):
    """Test convenience create_agent function."""
    
    def test_create_agent(self):
        """Test agent creation with defaults."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "vault"
        vault_path.mkdir()
        (vault_path / "test.md").write_text("# Test")
        
        try:
            agent = create_agent(
                vault_path=str(vault_path),
                data_dir=str(temp_dir / "data")
            )
            
            self.assertIsInstance(agent, ObsidianAgentCore)
            self.assertTrue(agent._initialized)
            
            agent.shutdown()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in core."""
    
    def test_safe_execution_fallback(self):
        """Test that errors return fallback values."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            agent = create_agent(
                vault_path=str(temp_dir / "nonexistent"),
                data_dir=str(temp_dir / "data")
            )
            
            # This should not crash, just return None
            result = agent.index_vault()
            # Result may be None or a report depending on initialization
            
            agent.shutdown()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
