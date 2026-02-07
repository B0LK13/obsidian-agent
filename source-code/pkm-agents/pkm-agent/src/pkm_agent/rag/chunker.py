"""Text chunking for embeddings."""

import re
from dataclasses import dataclass

from pkm_agent.data.models import Chunk, Note


@dataclass
class ChunkerConfig:
    """Configuration for text chunking."""

    chunk_size: int = 512  # Target size in characters
    chunk_overlap: int = 64  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum chunk size
    respect_boundaries: bool = True  # Try to break at sentence/paragraph


class Chunker:
    """Splits text into chunks for embedding."""

    def __init__(self, config: ChunkerConfig | None = None):
        self.config = config or ChunkerConfig()

    def chunk_note(self, note: Note) -> list[Chunk]:
        """Split a note into chunks."""
        chunks = []
        text = note.content

        if not text.strip():
            return chunks

        if self.config.respect_boundaries:
            raw_chunks = self._split_by_structure(text)
        else:
            raw_chunks = self._split_by_size(text)

        for i, chunk_text in enumerate(raw_chunks):
            if len(chunk_text.strip()) < self.config.min_chunk_size:
                continue

            chunks.append(Chunk(
                id=f"{note.id}_{i}",
                note_id=note.id,
                content=chunk_text.strip(),
                index=i,
                metadata={
                    "title": note.title,
                    "path": str(note.path),
                    "tags": note.metadata.tags,
                    "area": note.metadata.area,
                }
            ))

        return chunks

    def _split_by_structure(self, text: str) -> list[str]:
        """Split text respecting markdown structure."""
        chunks = []
        current_chunk = ""

        # Split by headers first
        sections = re.split(r'(^#{1,6}\s+.+$)', text, flags=re.MULTILINE)

        for section in sections:
            if not section.strip():
                continue

            # If adding this section exceeds chunk size
            if len(current_chunk) + len(section) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)

                # If section itself is too large, split by paragraphs
                if len(section) > self.config.chunk_size:
                    para_chunks = self._split_by_paragraphs(section)
                    chunks.extend(para_chunks[:-1])
                    current_chunk = para_chunks[-1] if para_chunks else ""
                else:
                    current_chunk = section
            else:
                current_chunk += section

        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap
        return self._add_overlap(chunks)

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """Split text by paragraphs."""
        chunks = []
        current_chunk = ""

        paragraphs = re.split(r'\n\s*\n', text)

        for para in paragraphs:
            if not para.strip():
                continue

            if len(current_chunk) + len(para) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)

                # If paragraph is too large, split by sentences
                if len(para) > self.config.chunk_size:
                    sent_chunks = self._split_by_sentences(para)
                    chunks.extend(sent_chunks[:-1])
                    current_chunk = sent_chunks[-1] if sent_chunks else ""
                else:
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text by sentences."""
        chunks = []
        current_chunk = ""

        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sent in sentences:
            if len(current_chunk) + len(sent) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent
            else:
                current_chunk += " " + sent if current_chunk else sent

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_size(self, text: str) -> list[str]:
        """Simple size-based splitting."""
        chunks = []

        for i in range(0, len(text), self.config.chunk_size - self.config.chunk_overlap):
            chunk = text[i:i + self.config.chunk_size]
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between chunks for context continuity."""
        if len(chunks) <= 1:
            return chunks

        overlapped = []
        overlap_size = self.config.chunk_overlap

        for i, chunk in enumerate(chunks):
            if i > 0 and len(chunks[i-1]) >= overlap_size:
                # Add end of previous chunk to start
                prefix = chunks[i-1][-overlap_size:]
                chunk = prefix + " " + chunk

            overlapped.append(chunk)

        return overlapped
