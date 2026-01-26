"""Tests for AI-powered features"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, AsyncMock

from obsidian_agent.features.duplicates import (
    DuplicateDetectionService,
    SimilarityLevel,
    DuplicateMatch,
)
from obsidian_agent.features.linking import (
    AutoLinkingService,
    LinkType,
    LinkSuggestion,
)
from obsidian_agent.features.organization import (
    AutoOrganizationService,
    OrganizationType,
)
from obsidian_agent.features.summarization import (
    SummarizationService,
    SummaryLevel,
)
from obsidian_agent.features.templates import (
    TemplateService,
    TemplateType,
)


class TestSimilarityLevel:
    def test_level_values(self):
        assert SimilarityLevel.EXACT_DUPLICATE.value == "exact"
        assert SimilarityLevel.NEAR_DUPLICATE.value == "near"
        assert SimilarityLevel.HIGHLY_SIMILAR.value == "high"
        assert SimilarityLevel.RELATED.value == "related"


class TestLinkType:
    def test_link_type_values(self):
        assert LinkType.SEMANTIC.value == "semantic"
        assert LinkType.ENTITY_MENTION.value == "entity"
        assert LinkType.TOPIC.value == "topic"


class TestOrganizationType:
    def test_org_type_values(self):
        assert OrganizationType.TAG.value == "tag"
        assert OrganizationType.FOLDER.value == "folder"
        assert OrganizationType.MOC.value == "moc"


class TestSummaryLevel:
    def test_summary_level_values(self):
        assert SummaryLevel.BRIEF.value == "brief"
        assert SummaryLevel.STANDARD.value == "standard"
        assert SummaryLevel.DETAILED.value == "detailed"
        assert SummaryLevel.OUTLINE.value == "outline"


class TestTemplateType:
    def test_template_type_values(self):
        assert TemplateType.MEETING.value == "meeting"
        assert TemplateType.PROJECT.value == "project"
        assert TemplateType.DAILY.value == "daily"
        assert TemplateType.BOOK.value == "book"


class TestDuplicateDetectionService:
    @pytest.fixture
    def mock_vector_store(self):
        store = Mock()
        store.search = AsyncMock(return_value=[])
        return store

    def test_initialization(self, mock_vector_store):
        service = DuplicateDetectionService(mock_vector_store)
        assert service.vector_store is mock_vector_store

    def test_similarity_thresholds(self, mock_vector_store):
        service = DuplicateDetectionService(mock_vector_store)
        assert service._thresholds[SimilarityLevel.EXACT_DUPLICATE] == 0.99
        assert service._thresholds[SimilarityLevel.NEAR_DUPLICATE] == 0.95


class TestAutoLinkingService:
    @pytest.fixture
    def mock_vector_store(self):
        store = Mock()
        store.search = AsyncMock(return_value=[])
        return store

    def test_initialization(self, mock_vector_store):
        service = AutoLinkingService(mock_vector_store)
        assert service.vector_store is mock_vector_store

    def test_extract_title_from_heading(self, mock_vector_store):
        service = AutoLinkingService(mock_vector_store)
        content = "# My Title\n\nSome content here."
        title = service._extract_title("test.md", content)
        assert title == "My Title"

    def test_extract_title_from_filename(self, mock_vector_store):
        service = AutoLinkingService(mock_vector_store)
        content = "No heading here."
        title = service._extract_title("my_note.md", content)
        assert title == "my_note"


class TestAutoOrganizationService:
    @pytest.fixture
    def mock_vector_store(self):
        store = Mock()
        store.search = AsyncMock(return_value=[])
        return store

    def test_initialization(self, mock_vector_store):
        service = AutoOrganizationService(mock_vector_store)
        assert service.vector_store is mock_vector_store

    def test_extract_tags(self, mock_vector_store):
        service = AutoOrganizationService(mock_vector_store)
        content = "This has #tag1 and #tag2/nested tags."
        tags = service._extract_tags(content)
        assert "tag1" in tags
        assert "tag2/nested" in tags


class TestSummarizationService:
    @pytest.fixture
    def mock_vector_store(self):
        store = Mock()
        store.search = AsyncMock(return_value=[])
        return store

    def test_initialization(self, mock_vector_store):
        service = SummarizationService(mock_vector_store)
        assert service.vector_store is mock_vector_store

    def test_extract_headings(self, mock_vector_store):
        service = SummarizationService(mock_vector_store)
        content = "# Heading 1\n\n## Heading 2\n\n### Heading 3"
        headings = service._extract_headings(content)
        assert len(headings) == 3

    def test_summarize_note_brief(self, mock_vector_store):
        service = SummarizationService(mock_vector_store)
        content = "This is a long sentence that should be used. Another sentence here."
        result = service.summarize_note("test.md", content, SummaryLevel.BRIEF)
        assert result.level == SummaryLevel.BRIEF
        assert result.note_path == "test.md"


class TestTemplateService:
    @pytest.fixture
    def mock_vector_store(self):
        store = Mock()
        return store

    def test_initialization(self, mock_vector_store):
        service = TemplateService(mock_vector_store)
        assert service.vector_store is mock_vector_store

    def test_detect_meeting_type(self, mock_vector_store):
        service = TemplateService(mock_vector_store)
        content = "# Meeting\n\nAttendees: John, Jane\n\nAgenda:\n- Item 1\n- Item 2"
        detected = service._detect_type(content)
        assert detected == TemplateType.MEETING

    def test_detect_project_type(self, mock_vector_store):
        service = TemplateService(mock_vector_store)
        content = "# Project\n\nGoals:\n- Goal 1\n\nTasks:\n- Task 1"
        detected = service._detect_type(content)
        assert detected == TemplateType.PROJECT 