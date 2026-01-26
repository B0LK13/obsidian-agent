"""Semantic Duplicate and Similar Note Detection Service.

Issue #48: Detect duplicate and similar notes using semantic embeddings.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable
import hashlib
import re
import time

from ..vector_store import ChromaDBStore


class SimilarityLevel(Enum):
    EXACT_DUPLICATE = "exact_duplicate"
    NEAR_DUPLICATE = "near_duplicate"
    HIGHLY_SIMILAR = "highly_similar"
    RELATED = "related"
    DISTINCT = "distinct"


@dataclass
class DuplicateMatch:
    source_path: str
    target_path: str
    similarity_score: float
    similarity_level: SimilarityLevel
    matching_sections: list[str]
    suggested_action: str


@dataclass
class DuplicateReport:
    total_notes_scanned: int
    exact_duplicates: list[DuplicateMatch]
    near_duplicates: list[DuplicateMatch]
    highly_similar: list[DuplicateMatch]
    related_notes: list[DuplicateMatch]
    scan_duration_seconds: float


class DuplicateDetectionService:
    EXACT_THRESHOLD = 0.99
    NEAR_THRESHOLD = 0.95
    HIGH_THRESHOLD = 0.85
    RELATED_THRESHOLD = 0.70

    def __init__(self, vector_store: ChromaDBStore):
        self.vector_store = vector_store

    def _classify(self, score: float) -> SimilarityLevel:
        if score >= self.EXACT_THRESHOLD:
            return SimilarityLevel.EXACT_DUPLICATE
        if score >= self.NEAR_THRESHOLD:
            return SimilarityLevel.NEAR_DUPLICATE
        if score >= self.HIGH_THRESHOLD:
            return SimilarityLevel.HIGHLY_SIMILAR
        if score >= self.RELATED_THRESHOLD:
            return SimilarityLevel.RELATED
        return SimilarityLevel.DISTINCT

    def _action(self, level: SimilarityLevel) -> str:
        return {
            SimilarityLevel.EXACT_DUPLICATE: "Merge or delete duplicate",
            SimilarityLevel.NEAR_DUPLICATE: "Review for merge",
            SimilarityLevel.HIGHLY_SIMILAR: "Consolidate content",
            SimilarityLevel.RELATED: "Add cross-references",
            SimilarityLevel.DISTINCT: "No action",
        }[level]

    async def find_duplicates(self, path: str, content: str, threshold: float = 0.70) -> list[DuplicateMatch]:
        results = await self.vector_store.search(query_text=content, n_results=10, threshold=threshold)
        matches = []
        for r in results:
            if r.get("id") == path:
                continue
            level = self._classify(r.get("similarity", 0))
            if level != SimilarityLevel.DISTINCT:
                matches.append(DuplicateMatch(
                    source_path=path, target_path=r.get("path", r.get("id")),
                    similarity_score=r.get("similarity", 0), similarity_level=level,
                    matching_sections=[], suggested_action=self._action(level)
                ))
        return sorted(matches, key=lambda m: m.similarity_score, reverse=True)

    async def scan_vault(self, vault: Path, threshold: float = 0.85, 
                         callback: Optional[Callable] = None) -> DuplicateReport:
        start = time.time()
        exact, near, high, related = [], [], [], []
        files = list(vault.rglob("*.md"))
        seen: set = set()

        for i, f in enumerate(files):
            if callback:
                callback(i + 1, len(files), f.name)
            try:
                content = f.read_text(encoding="utf-8")
                if len(content) < 50:
                    continue
                for m in await self.find_duplicates(str(f.relative_to(vault)), content, threshold):
                    pair = tuple(sorted([m.source_path, m.target_path]))
                    if pair not in seen:
                        seen.add(pair)
                        {SimilarityLevel.EXACT_DUPLICATE: exact, SimilarityLevel.NEAR_DUPLICATE: near,
                         SimilarityLevel.HIGHLY_SIMILAR: high, SimilarityLevel.RELATED: related}[m.similarity_level].append(m)
            except Exception:
                pass

        return DuplicateReport(len(files), exact, near, high, related, time.time() - start)
