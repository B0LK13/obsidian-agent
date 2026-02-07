"""Text chunking for RAG pipeline."""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A text chunk for embedding."""
    
    id: str
    note_id: str
    content: str
    metadata: dict[str, Any]
    start_char: int = 0
    end_char: int = 0


class Chunker:
    """Split notes into chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_size: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_note(self, note: dict[str, Any]) -> list[Chunk]:
        """Split a note into chunks."""
        content = note.get("content", "")
        if not content or len(content) < self.min_chunk_size:
            return []

        note_id = note["id"]
        title = note.get("title", "")
        path = note.get("path", "")

        chunks = []
        
        # Split by paragraphs first
        paragraphs = self._split_paragraphs(content)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                # Save current chunk if it's big enough
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        id=f"{note_id}_{chunk_index}",
                        note_id=note_id,
                        content=current_chunk.strip(),
                        metadata={
                            "title": title,
                            "path": path,
                            "chunk_index": chunk_index,
                        },
                        start_char=current_start,
                        end_char=current_start + len(current_chunk),
                    ))
                    chunk_index += 1

                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_start = current_start + len(current_chunk) - len(overlap_text)
                current_chunk = overlap_text + para + "\n\n"

        # Don't forget the last chunk
        if len(current_chunk) >= self.min_chunk_size:
            chunks.append(Chunk(
                id=f"{note_id}_{chunk_index}",
                note_id=note_id,
                content=current_chunk.strip(),
                metadata={
                    "title": title,
                    "path": path,
                    "chunk_index": chunk_index,
                },
                start_char=current_start,
                end_char=current_start + len(current_chunk),
            ))

        logger.debug(f"Chunked {path}: {len(chunks)} chunks")
        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
