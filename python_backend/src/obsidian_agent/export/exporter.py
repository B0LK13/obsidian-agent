"""Export vault content to various formats."""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    CSV = "csv"


@dataclass
class ExportResult:
    format: ExportFormat
    output_path: Path
    notes_exported: int
    success: bool
    error: str | None = None


class Exporter:
    """Export vault content to various formats."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
    
    async def export(self, output_path: Path, format: ExportFormat, notes: list[str] | None = None) -> ExportResult:
        """Export notes to the specified format."""
        try:
            if format == ExportFormat.JSON:
                return await self._export_json(output_path, notes)
            elif format == ExportFormat.HTML:
                return await self._export_html(output_path, notes)
            elif format == ExportFormat.CSV:
                return await self._export_csv(output_path, notes)
            elif format == ExportFormat.MARKDOWN:
                return await self._export_markdown(output_path, notes)
            else:
                return ExportResult(format=format, output_path=output_path, notes_exported=0, success=False, error=f"Unsupported format: {format}")
        except Exception as e:
            return ExportResult(format=format, output_path=output_path, notes_exported=0, success=False, error=str(e))
    
    async def _export_json(self, output_path: Path, notes: list[str] | None) -> ExportResult:
        note_files = self._get_notes(notes)
        data = []
        for note_path in note_files:
            content = note_path.read_text(encoding="utf-8")
            data.append({"path": str(note_path.relative_to(self.vault_path)), "content": content})
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return ExportResult(format=ExportFormat.JSON, output_path=output_path, notes_exported=len(data), success=True)
    
    async def _export_html(self, output_path: Path, notes: list[str] | None) -> ExportResult:
        import markdown
        note_files = self._get_notes(notes)
        html_parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'><title>Vault Export</title></head><body>"]
        for note_path in note_files:
            content = note_path.read_text(encoding="utf-8")
            html_content = markdown.markdown(content)
            html_parts.append(f"<article><h1>{note_path.stem}</h1>{html_content}</article><hr>")
        html_parts.append("</body></html>")
        output_path.write_text("\n".join(html_parts), encoding="utf-8")
        return ExportResult(format=ExportFormat.HTML, output_path=output_path, notes_exported=len(note_files), success=True)
    
    async def _export_csv(self, output_path: Path, notes: list[str] | None) -> ExportResult:
        import csv
        note_files = self._get_notes(notes)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["path", "title", "word_count"])
            for note_path in note_files:
                content = note_path.read_text(encoding="utf-8")
                writer.writerow([str(note_path.relative_to(self.vault_path)), note_path.stem, len(content.split())])
        return ExportResult(format=ExportFormat.CSV, output_path=output_path, notes_exported=len(note_files), success=True)
    
    async def _export_markdown(self, output_path: Path, notes: list[str] | None) -> ExportResult:
        note_files = self._get_notes(notes)
        output_path.mkdir(parents=True, exist_ok=True)
        for note_path in note_files:
            dest = output_path / note_path.relative_to(self.vault_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(note_path.read_text(encoding="utf-8"), encoding="utf-8")
        return ExportResult(format=ExportFormat.MARKDOWN, output_path=output_path, notes_exported=len(note_files), success=True)
    
    def _get_notes(self, notes: list[str] | None) -> list[Path]:
        if notes:
            return [self.vault_path / n for n in notes if (self.vault_path / n).exists()]
        return list(self.vault_path.rglob("*.md"))
