"""Multi-Level Content Summarization & Synthesis Service - Issue #50"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable
import re

from ..vector_store import ChromaDBStore


class SummaryLevel(Enum):
    BRIEF = "brief"        # 1-2 sentences
    STANDARD = "standard"  # Paragraph
    DETAILED = "detailed"  # Multiple paragraphs
    OUTLINE = "outline"    # Bullet points


@dataclass
class NoteSummary:
    note_path: str
    level: SummaryLevel
    summary: str
    key_points: list[str]
    word_count_original: int
    word_count_summary: int


@dataclass
class SynthesisResult:
    topic: str
    notes_synthesized: list[str]
    synthesis: str
    common_themes: list[str]


class SummarizationService:
    def __init__(self, vector_store: ChromaDBStore):
        self.vector_store = vector_store

    def _extract_headings(self, content: str) -> list[str]:
        return [m.group(1) for m in re.finditer(r"^#+\s+(.+)$", content, re.M)]

    def _extract_key_sentences(self, content: str, n: int = 3) -> list[str]:
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        return sentences[:n]

    def summarize_note(self, path: str, content: str, level: SummaryLevel = SummaryLevel.STANDARD) -> NoteSummary:
        headings = self._extract_headings(content)
        key_sentences = self._extract_key_sentences(content)
        words = content.split()
        
        if level == SummaryLevel.BRIEF:
            summary = key_sentences[0] if key_sentences else "No content"
        elif level == SummaryLevel.OUTLINE:
            summary = "\\n".join(f"- {h}" for h in headings) or "- " + (key_sentences[0] if key_sentences else "No headings")
        else:
            summary = " ".join(key_sentences[:3]) if key_sentences else "No summary available"
        
        return NoteSummary(
            path, level, summary, headings[:5], len(words), len(summary.split())
        )

    async def synthesize_topic(self, topic: str, vault: Path) -> SynthesisResult:
        results = await self.vector_store.search(query_text=topic, n_results=10, threshold=0.6)
        notes_used = []
        all_headings = []
        
        for r in results:
            path = r.get("path", r.get("id"))
            notes_used.append(path)
            content = r.get("content", "")
            all_headings.extend(self._extract_headings(content))
        
        themes = list(set(all_headings))[:5]
        synthesis = f"Topic: {topic}. Found {len(notes_used)} related notes. Common themes: {", ".join(themes) if themes else "None identified"}."
        
        return SynthesisResult(topic, notes_used, synthesis, themes)

    async def summarize_vault(self, vault: Path, level: SummaryLevel = SummaryLevel.STANDARD, cb: Optional[Callable] = None) -> list[NoteSummary]:
        summaries = []
        files = list(vault.rglob("*.md"))
        for i, f in enumerate(files):
            if cb: cb(i+1, len(files), f.name)
            try:
                content = f.read_text(encoding="utf-8")
                rel = str(f.relative_to(vault))
                summaries.append(self.summarize_note(rel, content, level))
            except: pass
        return summaries
