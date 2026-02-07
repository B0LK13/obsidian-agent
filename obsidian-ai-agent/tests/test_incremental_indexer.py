"""
Unit tests for Incremental Indexer (Issue #95)
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import time
import sqlite3

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from incremental_indexer import (
    IncrementalIndexer, 
    ChangeTracker, 
    IndexEntry, 
    ChangeReport,
    get_indexer,
    set_indexer
)


class TestChangeTracker(unittest.TestCase):
    """Test the ChangeTracker class."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.tracker = ChangeTracker(str(self.db_path))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compute_hash(self):
        """Test hash computation."""
        content = "test content"
        hash1 = ChangeTracker.compute_hash(content)
        hash2 = ChangeTracker.compute_hash(content)
        hash3 = ChangeTracker.compute_hash("different content")
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex length
    
    def test_record_and_get_entry(self):
        """Test recording and retrieving entries."""
        entry = IndexEntry(
            note_id="test/note.md",
            file_path="/vault/test/note.md",
            content_hash="abc123",
            last_modified=datetime.utcnow(),
            word_count=100,
            link_count=5,
            tags=["tag1", "tag2"]
        )
        
        self.tracker.record_change(entry)
        retrieved = self.tracker.get_entry("test/note.md")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.note_id, entry.note_id)
        self.assertEqual(retrieved.content_hash, entry.content_hash)
        self.assertEqual(retrieved.word_count, 100)
        self.assertEqual(retrieved.tags, ["tag1", "tag2"])
    
    def test_delete_entry(self):
        """Test deleting entries."""
        entry = IndexEntry(
            note_id="test/note.md",
            file_path="/vault/test/note.md",
            content_hash="abc123",
            last_modified=datetime.utcnow()
        )
        
        self.tracker.record_change(entry)
        self.assertIsNotNone(self.tracker.get_entry("test/note.md"))
        
        self.tracker.delete_entry("test/note.md")
        self.assertIsNone(self.tracker.get_entry("test/note.md"))
    
    def test_batch_operations(self):
        """Test batch insert and delete."""
        entries = [
            IndexEntry(
                note_id=f"note{i}.md",
                file_path=f"/vault/note{i}.md",
                content_hash=f"hash{i}",
                last_modified=datetime.utcnow()
            )
            for i in range(10)
        ]
        
        self.tracker.record_changes_batch(entries)
        all_entries = self.tracker.get_all_entries()
        self.assertEqual(len(all_entries), 10)
        
        self.tracker.delete_entries_batch([f"note{i}.md" for i in range(5)])
        all_entries = self.tracker.get_all_entries()
        self.assertEqual(len(all_entries), 5)
    
    def test_metadata(self):
        """Test metadata storage."""
        self.tracker.update_metadata("test_key", "test_value")
        value = self.tracker.get_metadata("test_key")
        self.assertEqual(value, "test_value")
        
        # Non-existent key
        self.assertIsNone(self.tracker.get_metadata("non_existent"))


class TestIncrementalIndexer(unittest.TestCase):
    """Test the IncrementalIndexer class."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "vault"
        self.vault_path.mkdir()
        self.db_path = Path(self.temp_dir) / "index.db"
        
        self.indexer = IncrementalIndexer(
            str(self.vault_path),
            str(self.db_path)
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_note(self, path: str, content: str):
        """Helper to create a test note."""
        note_path = self.vault_path / path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content, encoding='utf-8')
        return note_path
    
    def test_detect_new_files(self):
        """Test detecting newly added files."""
        self.create_note("note1.md", "# Test\n\nContent here.")
        
        report = self.indexer.detect_changes()
        
        self.assertEqual(len(report.added), 1)
        self.assertEqual(len(report.modified), 0)
        self.assertEqual(len(report.deleted), 0)
        self.assertEqual(report.added[0].note_id, "note1.md")
    
    def test_detect_modified_files(self):
        """Test detecting modified files."""
        # Create and index initial version
        self.create_note("note1.md", "# Test\n\nOriginal content.")
        self.indexer.index_changes()
        
        # Modify the file
        time.sleep(0.1)  # Ensure different timestamp
        self.create_note("note1.md", "# Test\n\nModified content.")
        
        report = self.indexer.detect_changes()
        
        self.assertEqual(len(report.added), 0)
        self.assertEqual(len(report.modified), 1)
        self.assertEqual(len(report.deleted), 0)
        self.assertEqual(report.modified[0].note_id, "note1.md")
    
    def test_detect_deleted_files(self):
        """Test detecting deleted files."""
        # Create and index
        note_path = self.create_note("note1.md", "# Test")
        self.indexer.index_changes()
        
        # Delete the file
        note_path.unlink()
        
        report = self.indexer.detect_changes()
        
        self.assertEqual(len(report.added), 0)
        self.assertEqual(len(report.modified), 0)
        self.assertEqual(len(report.deleted), 1)
        self.assertEqual(report.deleted[0], "note1.md")
    
    def test_no_changes(self):
        """Test when no changes exist."""
        self.create_note("note1.md", "# Test")
        self.indexer.index_changes()
        
        # Detect again without changes
        report = self.indexer.detect_changes()
        
        self.assertEqual(len(report.added), 0)
        self.assertEqual(len(report.modified), 0)
        self.assertEqual(len(report.deleted), 0)
        self.assertEqual(len(report.unchanged), 1)
        self.assertFalse(report.has_changes)
    
    def test_incremental_indexing(self):
        """Test full incremental indexing workflow."""
        # Initial indexing
        self.create_note("note1.md", "# First")
        self.create_note("note2.md", "# Second")
        report = self.indexer.index_changes()
        
        self.assertEqual(len(report.added), 2)
        self.assertEqual(report.change_count, 2)
        
        # Add new file
        self.create_note("note3.md", "# Third")
        report = self.indexer.index_changes()
        
        self.assertEqual(len(report.added), 1)
        self.assertEqual(report.added[0].note_id, "note3.md")
        
        # Verify all three are tracked
        stats = self.indexer.get_index_stats()
        self.assertEqual(stats['total_notes'], 3)
    
    def test_metadata_extraction(self):
        """Test metadata extraction from content."""
        content = """# Test Note

This is content with #tag1 and #tag2.
Here's a [[link]] and [external](http://example.com).
"""
        self.create_note("note.md", content)
        report = self.indexer.detect_changes()
        
        entry = report.added[0]
        self.assertGreater(entry.word_count, 0)
        self.assertEqual(entry.link_count, 2)  # Both link types
        self.assertIn("tag1", entry.tags)
        self.assertIn("tag2", entry.tags)
    
    def test_full_reindex(self):
        """Test full reindex functionality."""
        self.create_note("note1.md", "# Test 1")
        self.create_note("note2.md", "# Test 2")
        self.indexer.index_changes()
        
        # Full reindex
        report = self.indexer.full_reindex()
        
        self.assertEqual(len(report.added), 2)
        stats = self.indexer.get_index_stats()
        self.assertEqual(stats['total_notes'], 2)
    
    def test_embedding_callback(self):
        """Test embedding generation callback."""
        embedding_calls = []
        
        def mock_embedder(note_id: str, content: str) -> str:
            embedding_calls.append((note_id, content))
            return f"embedding_{note_id}"
        
        indexer_with_embedder = IncrementalIndexer(
            str(self.vault_path),
            str(self.db_path).replace(".db", "_embed.db"),
            embedding_callback=mock_embedder
        )
        
        self.create_note("note1.md", "# Test")
        indexer_with_embedder.index_changes()
        
        self.assertEqual(len(embedding_calls), 1)
        self.assertEqual(embedding_calls[0][0], "note1.md")
    
    def test_nested_directories(self):
        """Test indexing nested directory structures."""
        self.create_note("folder1/note1.md", "# Nested 1")
        self.create_note("folder1/subfolder/note2.md", "# Nested 2")
        self.create_note("folder2/note3.md", "# Nested 3")
        
        report = self.indexer.detect_changes()
        
        self.assertEqual(len(report.added), 3)
        note_ids = {e.note_id for e in report.added}
        self.assertIn("folder1/note1.md", note_ids)
        self.assertIn("folder1/subfolder/note2.md", note_ids)
        self.assertIn("folder2/note3.md", note_ids)
    
    def test_stats(self):
        """Test statistics collection."""
        self.create_note("note1.md", "# Test with #tag1")
        self.create_note("note2.md", "# Test with #tag2 and #tag3")
        self.indexer.index_changes()
        
        stats = self.indexer.get_index_stats()
        
        self.assertEqual(stats['total_notes'], 2)
        self.assertIn('last_full_index', stats)
        self.assertIn('db_path', stats)
    
    def test_reset(self):
        """Test index reset."""
        self.create_note("note1.md", "# Test")
        self.indexer.index_changes()
        
        stats_before = self.indexer.get_index_stats()
        self.assertEqual(stats_before['total_notes'], 1)
        
        self.indexer.reset()
        
        stats_after = self.indexer.get_index_stats()
        self.assertEqual(stats_after['total_notes'], 0)
    
    def test_concurrent_access(self):
        """Test thread safety of change tracker."""
        import threading
        
        entries = [
            IndexEntry(
                note_id=f"note{i}.md",
                file_path=f"/vault/note{i}.md",
                content_hash=f"hash{i}",
                last_modified=datetime.utcnow()
            )
            for i in range(100)
        ]
        
        errors = []
        
        def worker(entry_batch):
            try:
                self.indexer.tracker.record_changes_batch(entry_batch)
            except Exception as e:
                errors.append(str(e))
        
        threads = [
            threading.Thread(target=worker, args=(entries[i:i+10],))
            for i in range(0, 100, 10)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)
        all_entries = self.indexer.tracker.get_all_entries()
        self.assertEqual(len(all_entries), 100)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: create, modify, delete."""
        temp_dir = tempfile.mkdtemp()
        try:
            vault_path = Path(temp_dir) / "vault"
            vault_path.mkdir()
            db_path = Path(temp_dir) / "index.db"
            
            indexer = IncrementalIndexer(str(vault_path), str(db_path))
            
            # Phase 1: Initial vault population
            (vault_path / "note1.md").write_text("# Note 1")
            (vault_path / "note2.md").write_text("# Note 2")
            report = indexer.index_changes()
            self.assertEqual(report.change_count, 2)
            
            # Phase 2: Add new note
            time.sleep(0.01)
            (vault_path / "note3.md").write_text("# Note 3")
            report = indexer.index_changes()
            self.assertEqual(report.change_count, 1)
            self.assertEqual(report.added[0].note_id, "note3.md")
            
            # Phase 3: Modify existing note
            time.sleep(0.01)
            (vault_path / "note1.md").write_text("# Note 1 Modified")
            report = indexer.index_changes()
            self.assertEqual(report.change_count, 1)
            self.assertEqual(report.modified[0].note_id, "note1.md")
            
            # Phase 4: Delete note
            (vault_path / "note2.md").unlink()
            report = indexer.index_changes()
            self.assertEqual(report.change_count, 1)
            self.assertEqual(report.deleted[0], "note2.md")
            
            # Verify final state
            stats = indexer.get_index_stats()
            self.assertEqual(stats['total_notes'], 2)  # note1, note3
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
