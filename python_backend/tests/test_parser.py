"""Tests for Markdown parser"""

import pytest
from pathlib import Path
import tempfile
import os

from obsidian_agent.indexing.parser import MarkdownParser, ParsedNote


class TestMarkdownParser:
    @pytest.fixture
    def temp_vault(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def parser(self, temp_vault):
        return MarkdownParser(temp_vault)

    def test_parse_simple_note(self, temp_vault, parser):
        note_path = temp_vault / "test.md"
        note_path.write_text("# Test Note\n\nThis is content.")

        result = parser.parse_file(note_path)

        assert isinstance(result, ParsedNote)
        assert result.title == "test"
        assert "Test Note" in result.headings
        assert result.path == "test.md"

    def test_extract_frontmatter(self, temp_vault, parser):
        note_path = temp_vault / "with_fm.md"
        note_path.write_text("""---
title: My Title
tags: [tag1, tag2]
date: 2024-01-01
---

# Content here
""")

        result = parser.parse_file(note_path)

        assert result.title == "My Title"
        assert result.frontmatter["date"] == "2024-01-01"
        assert "tag1" in result.tags
        assert "tag2" in result.tags

    def test_extract_wikilinks(self, temp_vault, parser):
        note_path = temp_vault / "with_links.md"
        note_path.write_text("""# Note with links

See [[Other Note]] and [[Another One|Alias]].
""")

        result = parser.parse_file(note_path)

        assert "Other Note" in result.links
        assert "Another One" in result.links

    def test_extract_inline_tags(self, temp_vault, parser):
        note_path = temp_vault / "with_tags.md"
        note_path.write_text("""# Tagged note

This has #tag1 and #tag2/nested tags.
""")

        result = parser.parse_file(note_path)

        assert "tag1" in result.tags
        assert "tag2/nested" in result.tags

    def test_extract_embeds(self, temp_vault, parser):
        note_path = temp_vault / "with_embeds.md"
        note_path.write_text("""# Embeds

![[image.png]]
![[other_note]]
""")

        result = parser.parse_file(note_path)

        assert "image.png" in result.embeds
        assert "other_note" in result.embeds

    def test_extract_headings(self, temp_vault, parser):
        note_path = temp_vault / "headings.md"
        note_path.write_text("""# Heading 1

## Heading 2

### Heading 3
""")

        result = parser.parse_file(note_path)

        assert len(result.headings) == 3
        assert "Heading 1" in result.headings
        assert "Heading 2" in result.headings
        assert "Heading 3" in result.headings

    def test_checksum_generation(self, temp_vault, parser):
        note_path = temp_vault / "checksum.md"
        note_path.write_text("Content here")

        result = parser.parse_file(note_path)

        assert result.checksum is not None
        assert len(result.checksum) == 32  # MD5 hex length

    def test_id_generation(self, temp_vault, parser):
        note_path = temp_vault / "test_id.md"
        note_path.write_text("Content")

        result = parser.parse_file(note_path)

        assert result.id is not None
        assert len(result.id) == 32  # MD5 hex length
