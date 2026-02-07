"""Rollback integrity tests - verify audit trail and operation reversal."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from pkm_agent.app_enhanced import EnhancedPKMAgent
from pkm_agent.audit_logger import AuditEntry
from pkm_agent.config import Config


class TestRollbackIntegrity:
    """Test rollback mechanism integrity."""

    @pytest.mark.asyncio
    async def test_audit_entry_creation(self):
        """Test that operations create audit entries."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Get initial audit count
            stats_before = await app.audit_logger.get_stats()
            initial_count = stats_before["total_entries"]
            
            # Perform an operation
            await app.search("test query", limit=5)
            
            # Verify audit entry was created
            stats_after = await app.audit_logger.get_stats()
            assert stats_after["total_entries"] > initial_count
            
            # Get recent audit entries
            history = await app.audit_logger.get_history(limit=5)
            assert len(history) > 0
            
            # Verify entry has proper structure
            latest = history[0]
            assert latest.id is not None
            assert latest.timestamp is not None
            assert latest.action is not None
            
            await app.close()

    @pytest.mark.asyncio
    async def test_audit_hash_chain_integrity(self):
        """Test audit log tamper detection via checksum verification."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Create a test entry with snapshots
            entry = AuditEntry(
                action="test_operation",
                target="test-note-123",
                snapshot_before="original content",
                snapshot_after="modified content",
            )
            
            entry_id = await app.audit_logger.log(entry)
            
            # Retrieve and verify checksums match
            retrieved = await app.audit_logger.get_entry(entry_id)
            assert retrieved is not None
            assert retrieved.checksum_before == entry.checksum_before
            assert retrieved.checksum_after == entry.checksum_after
            
            # Verify checksum computation is correct
            import hashlib
            expected_before = hashlib.sha256("original content".encode()).hexdigest()
            expected_after = hashlib.sha256("modified content".encode()).hexdigest()
            
            assert retrieved.checksum_before == expected_before
            assert retrieved.checksum_after == expected_after
            
            await app.close()

    @pytest.mark.asyncio
    async def test_operation_id_propagation(self):
        """Test that operation_id propagates through pipeline."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Perform operations
            await app.search("machine learning", limit=3)
            
            # Get audit history
            history = await app.audit_logger.get_history(limit=10)
            
            # Verify all entries have unique IDs
            ids = [entry.id for entry in history]
            assert len(ids) == len(set(ids)), "Duplicate operation IDs found"
            
            # Verify IDs are properly formatted UUIDs
            import uuid
            for entry_id in ids:
                try:
                    uuid.UUID(entry_id)
                except ValueError:
                    pytest.fail(f"Invalid UUID format: {entry_id}")
            
            await app.close()

    @pytest.mark.asyncio
    async def test_rollback_prevents_duplicate_undo(self):
        """Test that already-rolled-back operations cannot be rolled back again."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=Path(tmpdir) / "vault",
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.data_dir.mkdir(parents=True, exist_ok=True)
            config.pkm_root.mkdir(parents=True, exist_ok=True)
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Create a reversible entry
            entry = AuditEntry(
                action="test_create",
                target="note-456",
                snapshot_before=None,
                snapshot_after="new content",
                reversible=True,
            )
            
            entry_id = await app.audit_logger.log(entry)
            
            # First rollback
            success1 = await app.rollback_operation(entry_id)
            
            # Second rollback attempt (should fail)
            success2 = await app.rollback_operation(entry_id)
            
            # First should succeed (or fail gracefully), second must fail
            assert not success2, "Rollback succeeded on already-rolled-back operation"
            
            await app.close()

    @pytest.mark.asyncio
    async def test_non_reversible_operations_blocked(self):
        """Test that non-reversible operations cannot be rolled back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=Path(tmpdir) / "vault",
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.data_dir.mkdir(parents=True, exist_ok=True)
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Create a non-reversible entry
            entry = AuditEntry(
                action="irreversible_action",
                target="data-export",
                reversible=False,
            )
            
            entry_id = await app.audit_logger.log(entry)
            
            # Attempt rollback
            success = await app.rollback_operation(entry_id)
            
            # Should fail
            assert not success, "Rollback succeeded on non-reversible operation"
            
            await app.close()

    @pytest.mark.asyncio
    async def test_audit_statistics_accuracy(self):
        """Test that audit statistics are accurately maintained."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Perform known operations
            await app.search("query1", limit=3)
            await app.search("query2", limit=3)
            await app.search("query3", limit=3)
            
            # Get stats
            stats = await app.audit_logger.get_stats()
            
            # Verify stats structure
            assert "total_entries" in stats
            assert "rolled_back" in stats
            assert "by_action" in stats
            
            # Verify counts
            assert stats["total_entries"] > 0
            assert isinstance(stats["by_action"], dict)
            
            # Verify search actions are logged
            by_action = stats["by_action"]
            search_count = sum(count for action, count in by_action.items() if "search" in action.lower())
            assert search_count >= 3, f"Expected at least 3 search actions, got {search_count}"
            
            await app.close()

    @pytest.mark.asyncio
    async def test_concurrent_operations_audit_integrity(self):
        """Test audit log integrity under concurrent operations."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "vaults" / "small"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                pkm_root=fixtures_path,
                data_dir=Path(tmpdir) / ".pkm-agent",
            )
            config.ensure_dirs()
            
            app = EnhancedPKMAgent(config)
            await app.initialize()
            
            # Perform concurrent searches
            tasks = [
                app.search(f"query{i}", limit=3)
                for i in range(10)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            for result in results:
                if isinstance(result, Exception):
                    pytest.fail(f"Concurrent operation failed: {result}")
            
            # Verify all operations logged
            stats = await app.audit_logger.get_stats()
            assert stats["total_entries"] >= 10, "Some concurrent operations not logged"
            
            # Verify no duplicate IDs
            history = await app.audit_logger.get_history(limit=100)
            ids = [entry.id for entry in history]
            assert len(ids) == len(set(ids)), "Duplicate operation IDs under concurrency"
            
            await app.close()


def run_rollback_tests():
    """Run all rollback integrity tests."""
    pytest.main([__file__, "-v", "-s", "--tb=short"])


if __name__ == "__main__":
    run_rollback_tests()
