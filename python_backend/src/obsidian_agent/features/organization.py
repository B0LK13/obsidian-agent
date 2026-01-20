"""AI-Powered Auto-Organization & Tagging Service - Issue #49"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable
import re
from collections import Counter

from ..vector_store import ChromaDBStore


class OrganizationType(Enum):
    TAG = "tag"
    FOLDER = "folder"
    MOC = "moc"


@dataclass
class OrganizationSuggestion:
    note_path: str
    suggestion_type: OrganizationType
    value: str
    confidence: float
    reason: str


@dataclass
class TagAnalysis:
    tag: str
    count: int
    related_tags: list[str]


@dataclass
class OrganizationReport:
    total_notes: int
    suggestions: list[OrganizationSuggestion]
    tag_analysis: list[TagAnalysis]
    folder_suggestions: dict[str, list[str]]


class AutoOrganizationService:
    def __init__(self, vector_store: ChromaDBStore):
        self.vector_store = vector_store
        self._topics = ["meeting", "project", "idea", "todo", "reference", "journal", "research"]

    def _extract_tags(self, content: str) -> list[str]:
        return re.findall(r"#([a-zA-Z][a-zA-Z0-9_/-]*)", content)

    async def suggest_tags(self, path: str, content: str) -> list[OrganizationSuggestion]:
        suggestions = []
        existing = set(self._extract_tags(content))
        for topic in self._topics:
            if topic in content.lower() and topic not in existing:
                suggestions.append(OrganizationSuggestion(
                    path, OrganizationType.TAG, f"#{topic}", 0.7, f"Contains {topic}"
                ))
        return suggestions

    async def analyze_vault(self, vault: Path, cb: Optional[Callable] = None) -> OrganizationReport:
        notes, all_tags = {}, Counter()
        for f in vault.rglob("*.md"):
            try:
                rel = str(f.relative_to(vault))
                content = f.read_text(encoding="utf-8")
                notes[rel] = content
                for tag in self._extract_tags(content):
                    all_tags[tag] += 1
            except: pass
        
        suggestions = []
        for path, content in notes.items():
            suggestions.extend(await self.suggest_tags(path, content))
        
        analysis = [TagAnalysis(t, c, []) for t, c in all_tags.most_common(20)]
        return OrganizationReport(len(notes), suggestions[:100], analysis, {})
