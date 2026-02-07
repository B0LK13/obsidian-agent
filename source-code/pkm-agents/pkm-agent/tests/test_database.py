"""Tests for database operations."""

import pytest
import sqlite3
import asyncio
from datetime import datetime
from pathlib import Path
from pkm_agent.data.database import Database
from pkm_agent.data.models import Note, NoteMetadata


class TestDatabase:
    """Tests for Database class."""
    
    def test_init_creates_tables(self, test_database):
        """Test that database initialization creates tables."""
        stats = test_database.get_stats()
        assert stats["notes"] == 0
        assert stats["tags"] == 0
        assert stats["links"] == 0
    
    def test_upsert_note(self, test_database, test_pkm_root):
        """Test inserting and updating a note."""
        note = Note(
            id="test1",
            path=Path("test.md"),
            title="Test Note",
            content="Test content",
            metadata=NoteMetadata(title="Test", tags=["tag1", "tag2"]),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        test_database.upsert_note(note)
        retrieved = test_database.get_note("test1")
        
        assert retrieved is not None
        assert retrieved.title == "Test Note"
        assert retrieved.content == "Test content"
    
    def test_get_note_by_path(self, test_database, test_pkm_root):
        """Test retrieving a note by path."""
        note = Note(
            id="test1",
            path=Path("subdir/test.md"),
            title="Test",
            content="Content",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        test_database.upsert_note(note)
        retrieved = test_database.get_note_by_path("subdir/test.md")
        
        assert retrieved is not None
        assert retrieved.id == "test1"
    
    def test_get_all_notes(self, test_database, test_pkm_root):
        """Test retrieving all notes."""
        for i in range(3):
            note = Note(
                id=f"test{i}",
                path=Path(f"test{i}.md"),
                title=f"Test {i}",
                content=f"Content {i}",
                metadata=NoteMetadata(),
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )
            test_database.upsert_note(note)
        
        notes = test_database.get_all_notes()
        assert len(notes) == 3
    
    def test_search_notes(self, test_database, test_pkm_root):
        """Test keyword search."""
        note1 = Note(
            id="test1",
            path=Path("python.md"),
            title="Python Programming",
            content="Python is a programming language",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        note2 = Note(
            id="test2",
            path=Path("javascript.md"),
            title="JavaScript Guide",
            content="JavaScript for web development",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        test_database.upsert_note(note1)
        test_database.upsert_note(note2)
        
        # Search for "Python"
        results = test_database.search_notes("Python", limit=10)
        assert len(results) >= 1
        assert "Python" in results[0].title
    
    def test_delete_note(self, test_database, test_pkm_root):
        """Test deleting a note."""
        note = Note(
            id="test1",
            path=Path("test.md"),
            title="Test",
            content="Content",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        test_database.upsert_note(note)
        assert test_database.get_note("test1") is not None
        
        deleted = test_database.delete_note("test1")
        assert deleted is True
        assert test_database.get_note("test1") is None
    
    def test_get_note_count(self, test_database, test_pkm_root):
        """Test getting note count."""
        assert test_database.get_note_count() == 0
        
        note = Note(
            id="test1",
            path=Path("test.md"),
            title="Test",
            content="Content",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        test_database.upsert_note(note)
        assert test_database.get_note_count() == 1
    
    def test_conversation_operations(self, test_database):
        """Test conversation and message operations."""
        # Create conversation
        conv_id = "test-conv"
        test_database.create_conversation(conv_id)
        
        # Add messages
        test_database.add_message(conv_id, "user", "Hello", 10, "gpt-4")
        test_database.add_message(conv_id, "assistant", "Hi there!", 15, "gpt-4")
        
        # Retrieve messages
        messages = test_database.get_conversation_messages(conv_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_tags_are_updated(self, test_database, test_pkm_root):
        """Test that tags are properly indexed."""
        note = Note(
            id="test1",
            path=Path("test.md"),
            title="Test",
            content="Content",
            metadata=NoteMetadata(tags=["python", "programming", "ai"]),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        
        test_database.upsert_note(note)
        
        stats = test_database.get_stats()
        assert stats["tags"] == 3
