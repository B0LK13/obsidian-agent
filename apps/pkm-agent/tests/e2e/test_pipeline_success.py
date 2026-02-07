"""End-to-end integration tests for PKM Agent.

Tests full pipeline with real vault fixtures.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from pkm_agent.app_enhanced import EnhancedPKMAgent
from pkm_agent.config import Config


class TestE2EPipelineSuccess:
    """Test successful end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_small_vault_initialization(self):
        """Test initialization with small vault (10 notes)."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            
            # Initialize
            await app.initialize()
            
            # Verify initialization
            stats = await app.get_stats()
            assert stats["total_notes"] == 10
            assert stats["vector_store"]["total_chunks"] > 0
            
            # Verify audit log
            audit_stats = stats["audit"]
            assert audit_stats["total_entries"] > 0
            
            await app.close()

    @pytest.mark.asyncio
    async def test_successful_search_pipeline(self):
        """Test complete search workflow."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Perform search
            results = await app.search("machine learning", limit=5)
            
            # Verify results
            assert len(results) > 0
            assert len(results) <= 5
            
            # Verify result structure
            for result in results:
                assert "content" in result
                assert "metadata" in result
                assert "score" in result
            
            # Verify caching (second query should be faster)
            cache_stats_before = app.cache.stats()
            results2 = await app.search("machine learning", limit=5)
            cache_stats_after = app.cache.stats()
            
            # Cache hit should have increased
            assert cache_stats_after["query_cache"]["hits"] > cache_stats_before["query_cache"]["hits"]
            
            await app.close()

    @pytest.mark.asyncio
    async def test_medium_vault_performance(self):
        """Test with medium vault (100 notes) - performance baseline."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "medium"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            
            import time
            start = time.time()
            await app.initialize()
            init_time = time.time() - start
            
            # Initialization should complete in reasonable time (<60s for 100 notes)
            assert init_time < 60.0, f"Initialization took {init_time:.2f}s (>60s threshold)"
            
            # Search should be fast
            start = time.time()
            results = await app.search("deep learning", limit=10)
            search_time = time.time() - start
            
            # Search should complete in <2s
            assert search_time < 2.0, f"Search took {search_time:.2f}s (>2s threshold)"
            assert len(results) > 0
            
            await app.close()


class TestE2ENoResults:
    """Test handling of queries with no results."""

    @pytest.mark.asyncio
    async def test_search_no_matches(self):
        """Test search with query that has no matches."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Search for something definitely not in vault
            results = await app.search("quantum entanglement superconductivity xyzabc123", limit=5)
            
            # Should return empty results, not error
            assert isinstance(results, list)
            # May return low-scoring results or empty list
            
            await app.close()

    @pytest.mark.asyncio
    async def test_empty_vault_handling(self):
        """Test behavior with empty vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "empty_vault"
            vault_path.mkdir()
            
            config = Config(
                pkm_root=vault_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            stats = await app.get_stats()
            assert stats["total_notes"] == 0
            
            # Search on empty vault should not crash
            results = await app.search("anything", limit=5)
            assert results == []
            
            await app.close()


class TestE2EPartialFailureRecovery:
    """Test recovery from partial failures."""

    @pytest.mark.asyncio
    async def test_corrupted_note_handling(self):
        """Test handling of corrupted note files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault"
            vault_path.mkdir()
            
            # Create one valid note
            (vault_path / "valid.md").write_text(
                "---\ntitle: Valid Note\n---\n\nThis is valid content.",
                encoding="utf-8"
            )
            
            # Create one corrupted note (binary data)
            (vault_path / "corrupted.md").write_bytes(b"\x00\x01\x02\xff")
            
            # Create one with invalid front matter
            (vault_path / "invalid-fm.md").write_text(
                "---\ninvalid yaml: [ unclosed\n---\n\nContent here.",
                encoding="utf-8"
            )
            
            config = Config(
                pkm_root=vault_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            
            # Should not crash, should skip corrupted files
            await app.initialize()
            
            stats = await app.get_stats()
            # Should have indexed at least the valid note
            assert stats["total_notes"] >= 1
            
            await app.close()

    @pytest.mark.asyncio
    async def test_indexing_retry_on_error(self):
        """Test that indexing continues after encountering errors."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy small vault
            import shutil
            vault_path = Path(tmpdir) / "vault"
            shutil.copytree(fixtures_path, vault_path)
            
            # Add a problematic file
            (vault_path / "problematic.md").write_text(
                "---\ntitle: Test\n---\n\n" + ("x" * 1000000),  # Very large file
                encoding="utf-8"
            )
            
            config = Config(
                pkm_root=vault_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            
            # Should complete even if large file causes issues
            await app.initialize()
            
            stats = await app.get_stats()
            # Should have indexed at least the original 10 notes
            assert stats["total_notes"] >= 10
            
            await app.close()


def run_e2e_tests():
    """Run all E2E tests."""
    pytest.main([__file__, "-v", "-s", "--tb=short"])


if __name__ == "__main__":
    run_e2e_tests()
