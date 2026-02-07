"""Tests for data models."""

import pytest
from datetime import datetime
from pathlib import Path
from pkm_agent.data.models import Note, NoteMetadata, Tag, Link, SearchResult


class TestNoteMetadata:
    """Tests for NoteMetadata class."""
    
    def test_default_values(self):
        """Test default values."""
        meta = NoteMetadata()
        assert meta.title is None
        assert meta.tags == []
        assert meta.created is None
        assert meta.modified is None
        assert meta.status == "active"
        assert meta.area is None
        assert meta.project is None
        assert meta.extra == {}
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        meta = NoteMetadata(
            title="Test",
            tags=["tag1", "tag2"],
            created=datetime(2024, 1, 1),
            status="archived",
        )
        d = meta.to_dict()
        assert d["title"] == "Test"
        assert d["tags"] == ["tag1", "tag2"]
        assert d["created"] == "2024-01-01T00:00:00"
        assert d["status"] == "archived"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "title": "Test",
            "tags": ["tag1", "tag2"],
            "created": "2024-01-01T00:00:00",
            "status": "archived",
        }
        meta = NoteMetadata.from_dict(d)
        assert meta.title == "Test"
        assert meta.tags == ["tag1", "tag2"]
        assert meta.created == datetime(2024, 1, 1)
        assert meta.status == "archived"


class TestNote:
    """Tests for Note class."""
    
    def test_compute_hash(self):
        """Test hash computation."""
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test",
            content="Test content",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert note.content_hash != ""
        assert len(note.content_hash) == 16
    
    def test_word_count(self):
        """Test word count calculation."""
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test",
            content="This is a test note with some words.",
            metadata=NoteMetadata(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert note.word_count > 0
    
    def test_from_file(self, temp_dir):
        """Test creating Note from file."""
        note_path = temp_dir / "test.md"
        note_path.write_text("""---
title: Test Note
tags: [test]
---

# Test Note

Content here.
""")
        
        note = Note.from_file(note_path, temp_dir)
        assert note.title == "Test Note"
        assert "# Test Note" in note.content
        assert "Content here." in note.content
        assert "test" in note.metadata.tags
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now()
        note = Note(
            id="test",
            path=Path("test.md"),
            title="Test",
            content="Content",
            metadata=NoteMetadata(title="Test"),
            created_at=now,
            modified_at=now,
        )
        d = note.to_dict()
        assert d["id"] == "test"
        assert d["title"] == "Test"
        assert d["content"] == "Content"
        assert "metadata" in d


class TestTag:
    """Tests for Tag class."""
    
    def test_defaults(self):
        """Test default values."""
        tag = Tag(id=1, name="test")
        assert tag.category == "user"
        assert tag.usage_count == 0
        assert tag.created_at is not None


class TestLink:
    """Tests for Link class."""
    
    def test_defaults(self):
        """Test default values."""
        link = Link(id=1, source_id="a", target_id="b")
        assert link.link_type == "reference"
        assert link.context is None
        assert link.created_at is not None


class TestSearchResult:
    """Tests for SearchResult class."""
    
    def test_defaults(self):
        """Test default values."""
        result = SearchResult(
            note_id="test",
            path="test.md",
            title="Test",
            score=0.5,
            snippet="Snippet",
        )
        assert result.highlights == []
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = SearchResult(
            note_id="test",
            path="test.md",
            title="Test",
            score=0.5,
            snippet="Snippet",
            highlights=["test"],
        )
        d = result.to_dict()
        assert d["note_id"] == "test"
        assert d["score"] == 0.5
        assert d["highlights"] == ["test"]
