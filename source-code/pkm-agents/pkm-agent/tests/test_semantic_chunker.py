"""Tests for SemanticChunker."""

import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pkm_agent.data.models import Note, NoteMetadata
from pkm_agent.rag.semantic_chunker import SemanticChunker, SemanticChunkerConfig


@pytest.fixture
def sample_note():
    content = """# Main Title

Introduction text here.

## Section 1

This is section 1 content.
It has multiple paragraphs.

Here is a code block:
```python
def hello():
    print("world")
```

## Section 2

Short section.

### Subsection 2.1

Deeply nested content.
"""
    meta = NoteMetadata(title="Main Title")
    return Note(
        id="test_note",
        path=Path("test.md"),
        title="Main Title",
        content=content,
        metadata=meta,
        created_at=datetime.datetime.now(),
        modified_at=datetime.datetime.now()
    )


def test_chunk_splitting(sample_note):
    chunker = SemanticChunker()
    chunks = chunker.chunk_note(sample_note)

    assert len(chunks) > 0
    
    # Check that Introduction is captured
    assert "Introduction text here" in chunks[0].content
    
    # Check Section 1
    sec1_chunks = [c for c in chunks if c.metadata.get("section") == "Section 1"]
    assert len(sec1_chunks) > 0
    assert "This is section 1 content" in sec1_chunks[0].content
    
    # Check Code Block preservation
    code_chunk = [c for c in chunks if "def hello():" in c.content][0]
    assert "```python" in code_chunk.content
    assert "print(\"world\")" in code_chunk.content
    assert "```" in code_chunk.content

    # Check Subsection
    sub_chunks = [c for c in chunks if c.metadata.get("section") == "Subsection 2.1"]
    assert len(sub_chunks) > 0
    assert "Deeply nested content" in sub_chunks[0].content


def test_chunk_size_limits():
    config = SemanticChunkerConfig(chunk_size=50)  # Very small size to force splits
    chunker = SemanticChunker(config)
    
    content = "A" * 30 + "\n\n" + "B" * 30 + "\n\n" + "C" * 30
    note = Note(
        id="test_size",
        path=Path("size.md"),
        title="Size Test",
        content=content,
        metadata=NoteMetadata(),
        created_at=datetime.datetime.now(),
        modified_at=datetime.datetime.now()
    )
    
    chunks = chunker.chunk_note(note)
    # Should be at least 3 chunks because 30+30 > 50
    assert len(chunks) >= 3
    for chunk in chunks:
        # Check that no chunk is massively oversized (allow some buffer for metadata/overhead)
        assert len(chunk.content) < 100 
