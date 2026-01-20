"""Auto-Linking Service - Issue #47"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable
import re

from ..vector_store import ChromaDBStore


class LinkType(Enum):
    SEMANTIC = "semantic"
    ENTITY_MENTION = "entity"
    TOPIC = "topic"


@dataclass
class LinkSuggestion:
    source_path: str
    target_path: str
    link_type: LinkType
    confidence: float
    context: str
    suggested_text: str


@dataclass
class LinkDiscoveryReport:
    total_notes_analyzed: int
    suggestions: list[LinkSuggestion]
    missing_backlinks: list[tuple[str, str]]
    orphan_notes: list[str]


class AutoLinkingService:
    def __init__(self, vector_store: ChromaDBStore):
        self.vector_store = vector_store

    def _extract_title(self, path: str, content: str) -> str:
        for line in content.strip().split('\n')[:5]:
            if line.startswith('# '):
                return line[2:].strip()
        return Path(path).stem

    def _find_existing_links(self, content: str) -> set[str]:
        return {m.group(1).lower() for m in re.finditer(r'\[\[([^\]|]+)', content)}

    async def suggest_links(self, path: str, content: str, notes: dict, thresh: float = 0.75) -> list[LinkSuggestion]:
        suggestions = []
        existing = self._find_existing_links(content)
        titles = {p: self._extract_title(p, c) for p, c in notes.items() if p != path}
        
        for t_path, title in titles.items():
            if len(title) >= 3 and title.lower() not in existing:
                if re.search(rf'\b{re.escape(title)}\b', content, re.I):
                    suggestions.append(LinkSuggestion(
                        path, t_path, LinkType.ENTITY_MENTION, 0.95, title, f'[[{Path(t_path).stem}]]'
                    ))
        
        for r in await self.vector_store.search(query_text=content, n_results=5, threshold=thresh):
            target = r.get('path', r.get('id'))
            if target != path and Path(target).stem.lower() not in existing:
                suggestions.append(LinkSuggestion(
                    path, target, LinkType.SEMANTIC, r.get('similarity', 0), 'Related', f'[[{Path(target).stem}]]'
                ))
        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)

    async def find_orphans(self, notes: dict) -> list[str]:
        links, with_out = set(), set()
        for p, c in notes.items():
            found = re.findall(r'\[\[([^\]|]+)', c)
            if found:
                with_out.add(p)
                links.update(l.lower() for l in found)
        return [p for p in notes if Path(p).stem.lower() not in links and p not in with_out]

    async def analyze_vault(self, vault: Path, cb: Optional[Callable] = None) -> LinkDiscoveryReport:
        notes = {}
        for f in vault.rglob('*.md'):
            try: notes[str(f.relative_to(vault))] = f.read_text(encoding='utf-8')
            except: pass
        sugg = []
        for p, c in notes.items():
            sugg.extend(await self.suggest_links(p, c, notes))
        return LinkDiscoveryReport(len(notes), sugg[:100], [], await self.find_orphans(notes))
