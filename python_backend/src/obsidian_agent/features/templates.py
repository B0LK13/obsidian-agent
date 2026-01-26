"""Smart Template Generation - Issue #46"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable
import re
from collections import Counter
from ..vector_store import ChromaDBStore

class TemplateType(Enum):
    MEETING = "meeting"
    PROJECT = "project"
    DAILY = "daily"
    BOOK = "book"
    CUSTOM = "custom"

@dataclass
class TemplateField:
    name: str
    field_type: str
    required: bool = False

@dataclass
class GeneratedTemplate:
    name: str
    template_type: TemplateType
    content: str
    fields: list[TemplateField]
    based_on_notes: list[str]

@dataclass
class TemplateAnalysis:
    detected_patterns: dict[str, int]
    suggested_templates: list[GeneratedTemplate]

class TemplateService:
    def __init__(self, vector_store: ChromaDBStore):
        self.vector_store = vector_store
        self._patterns = {
            TemplateType.MEETING: ["attendees", "agenda", "action items"],
            TemplateType.PROJECT: ["goals", "tasks", "timeline"],
            TemplateType.DAILY: ["date", "tasks", "notes"],
            TemplateType.BOOK: ["author", "rating", "summary"],
        }

    def _detect_type(self, content: str):
        lower = content.lower()
        for ttype, pats in self._patterns.items():
            if sum(1 for p in pats if p in lower) >= 2:
                return ttype
        return None

    def _extract_headings(self, content: str):
        return re.findall(r"^#+\s+(.+)$", content, re.M)

    def generate_template(self, notes, ttype):
        sections = Counter()
        for _, c in notes:
            for h in self._extract_headings(c):
                sections[h.strip()] += 1
        common = [s for s, cnt in sections.most_common(8) if cnt >= 2]
        fields = [TemplateField(s, "text", True) for s in common[:5]]
        lines = ["# {title}", "", f"Type: {ttype.value}", ""]
        lines.extend(f"## {s}" for s in common)
        return GeneratedTemplate(f"{ttype.value.title()} Template", ttype, "\n".join(lines), fields, [p for p, _ in notes])

    async def analyze_vault(self, vault: Path, cb=None):
        by_type = {t: [] for t in TemplateType}
        for f in vault.rglob("*.md"):
            try:
                c = f.read_text(encoding="utf-8")
                rel = str(f.relative_to(vault))
                det = self._detect_type(c)
                if det:
                    by_type[det].append((rel, c))
            except:
                pass
        pats = {t.value: len(n) for t, n in by_type.items() if n}
        tmpls = [self.generate_template(n[0:10], t) for t, n in by_type.items() if len(n) >= 2]
        return TemplateAnalysis(pats, tmpls)

    def apply_template(self, tmpl, vals):
        c = tmpl.content
        for k, v in vals.items():
            c = c.replace(f"{{k}}", v)
        return c
