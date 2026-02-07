"""Tests for file indexer."""

import pytest
from pathlib import Path
from pkm_agent.data import FileIndexer
from pkm_agent.data.models import Note


class TestFileIndexer:
    """Tests for FileIndexer class."""
    
    def test_find_markdown_files(self, test_indexer, test_pkm_root):
        """Test finding markdown files."""
        files = test_indexer._find_markdown_files()
        assert len(files) > 0
        assert all(f.suffix == ".md" for f in files)
    
    def test_index_file(self, test_indexer, test_pkm_root):
        """Test indexing a single file."""
        new_note = test_pkm_root / "new-note.md"
        new_note.write_text("""---
title: New Note
tags: [new]
---

# New Note

Content.
""")
        
        note = test_indexer.index_file(new_note)
        assert note is not None
        assert note.title == "New Note"
        assert "new" in note.metadata.tags
    
    def test_index_all(self, test_indexer, test_database):
        """Test indexing all files."""
        count = test_indexer.index_all()
        assert count > 0
        
        # Check that notes are in database
        notes = test_database.get_all_notes()
        assert len(notes) >= count
    
    def test_sync_new_files(self, test_indexer, test_pkm_root, test_database):
        """Test syncing detects new files."""
        # Index existing files
        test_indexer.index_all()
        initial_count = test_database.get_note_count()
        
        # Add new file
        new_note = test_pkm_root / "sync-test.md"
        new_note.write_text("# Sync Test\nContent")
        
        # Sync
        stats = test_indexer.sync()
        assert stats["added"] >= 1
        assert test_database.get_note_count() >= initial_count + 1
    
    def test_get_modified_files(self, test_indexer, test_pkm_root, temp_dir):
        """Test getting modified files."""
        from datetime import datetime, timedelta
        
        # Create a file
        test_file = test_pkm_root / "mod-test.md"
        test_file.write_text("# Test\nContent")
        
        # Get files modified since yesterday
        since = datetime.now() - timedelta(days=1)
        modified = test_indexer.get_modified_files(since)
        
        assert len(modified) > 0
        assert test_file in modified
    
    def test_ignores_patterns(self, test_indexer, temp_dir):
        """Test that certain directories are ignored."""
        pkm_root = temp_dir / "pkm-test"
        pkm_root.mkdir()
        
        # Create directories that should be ignored
        (pkm_root / ".git").mkdir()
        (pkm_root / ".obsidian").mkdir()
        (pkm_root / "node_modules").mkdir()
        
        # Create files in ignored directories
        (pkm_root / ".git" / "test.md").write_text("test")
        (pkm_root / ".obsidian" / "test.md").write_text("test")
        (pkm_root / "node_modules" / "test.md").write_text("test")
        
        # Create file that should not be ignored
        (pkm_root / "regular.md").write_text("test")
        
        indexer = FileIndexer(pkm_root, test_indexer.db)
        files = indexer._find_markdown_files()
        
        assert len(files) == 1
        assert files[0].name == "regular.md"
