"""Intelligent text chunking for RAG pipeline."""

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ChunkingStrategy(str, Enum):
    """Chunking strategy options."""

    FIXED = "fixed"  # Fixed size chunks
    SEMANTIC = "semantic"  # Semantic boundary-aware
    SENTENCE = "sentence"  # Sentence-based
    PARAGRAPH = "paragraph"  # Paragraph-based
    MARKDOWN = "markdown"  # Markdown structure-aware


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""

    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    chunk_size: int = 512  # Target chunk size in characters
    chunk_overlap: int = 50  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum chunk size
    max_chunk_size: int = 1000  # Maximum chunk size
    respect_boundaries: bool = True  # Don't split mid-sentence


class TextChunker:
    """Intelligent text chunking with multiple strategies."""

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()

    def chunk_text(self, text: str, metadata: dict = None) -> list[dict]:
        """
        Chunk text using configured strategy.

        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or len(text) < self.config.min_chunk_size:
            return [{"content": text, "metadata": metadata or {}}]

        # Select chunking method based on strategy
        if self.config.strategy == ChunkingStrategy.MARKDOWN:
            chunks = list(self._chunk_markdown(text))
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            chunks = list(self._chunk_by_paragraphs(text))
        elif self.config.strategy == ChunkingStrategy.SENTENCE:
            chunks = list(self._chunk_by_sentences(text))
        elif self.config.strategy == ChunkingStrategy.SEMANTIC:
            chunks = list(self._chunk_semantic(text))
        else:  # FIXED
            chunks = list(self._chunk_fixed(text))

        # Add metadata to all chunks
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_meta = (metadata or {}).copy()
            chunk_meta["chunk_index"] = i
            chunk_meta["total_chunks"] = len(chunks)
            result.append({
                "content": chunk_text,
                "metadata": chunk_meta,
            })

        logger.debug(f"Chunked text into {len(result)} chunks using {self.config.strategy} strategy")
        return result

    def _chunk_fixed(self, text: str) -> Iterator[str]:
        """Fixed-size chunking with overlap."""
        pos = 0
        text_len = len(text)

        while pos < text_len:
            end = min(pos + self.config.chunk_size, text_len)

            # If respect_boundaries, try to find sentence boundary
            if self.config.respect_boundaries and end < text_len:
                # Look for sentence end in last 100 chars
                search_start = max(pos, end - 100)
                boundary = self._find_sentence_boundary(text[search_start:end])
                if boundary != -1:
                    end = search_start + boundary

            chunk = text[pos:end].strip()
            if len(chunk) >= self.config.min_chunk_size:
                yield chunk

            pos = end - self.config.chunk_overlap if end < text_len else text_len

    def _chunk_semantic(self, text: str) -> Iterator[str]:
        """Semantic chunking - tries to keep related content together."""
        # First split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\n+', text)

        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            # If adding this paragraph would exceed max size, yield current chunk
            if current_size + para_size > self.config.max_chunk_size and current_chunk:
                yield ' '.join(current_chunk)

                # Start new chunk with overlap (last paragraph)
                if self.config.chunk_overlap > 0 and len(current_chunk) > 1:
                    current_chunk = [current_chunk[-1], para]
                    current_size = len(current_chunk[-1]) + para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

            # If chunk is big enough, yield it
            if current_size >= self.config.chunk_size:
                yield ' '.join(current_chunk)
                current_chunk = []
                current_size = 0

        # Yield remaining chunk
        if current_chunk:
            yield ' '.join(current_chunk)

    def _chunk_by_paragraphs(self, text: str) -> Iterator[str]:
        """Chunk by paragraphs, combining small ones."""
        paragraphs = re.split(r'\n\n+', text)

        current = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            if current_size + para_size > self.config.max_chunk_size and current:
                yield '\n\n'.join(current)
                current = [para]
                current_size = para_size
            else:
                current.append(para)
                current_size += para_size

        if current:
            yield '\n\n'.join(current)

    def _chunk_by_sentences(self, text: str) -> Iterator[str]:
        """Chunk by sentences, combining to target size."""
        sentences = self._split_sentences(text)

        current = []
        current_size = 0

        for sentence in sentences:
            sent_size = len(sentence)

            if current_size + sent_size > self.config.max_chunk_size and current:
                yield ' '.join(current)
                current = [sentence]
                current_size = sent_size
            else:
                current.append(sentence)
                current_size += sent_size

        if current:
            yield ' '.join(current)

    def _chunk_markdown(self, text: str) -> Iterator[str]:
        """Markdown-aware chunking that respects document structure."""
        # Split by headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split('\n')

        current_section = []
        current_size = 0
        current_level = 0

        for line in lines:
            header_match = re.match(header_pattern, line, re.MULTILINE)

            if header_match:
                level = len(header_match.group(1))

                # If we have content and hit same/higher level header, yield chunk
                if current_section and level <= current_level:
                    chunk = '\n'.join(current_section)
                    if len(chunk) >= self.config.min_chunk_size:
                        yield chunk
                    current_section = []
                    current_size = 0

                current_level = level

            current_section.append(line)
            current_size += len(line)

            # If chunk is too large, yield it
            if current_size > self.config.max_chunk_size:
                chunk = '\n'.join(current_section)
                if len(chunk) >= self.config.min_chunk_size:
                    yield chunk
                current_section = []
                current_size = 0

        # Yield remaining content
        if current_section:
            chunk = '\n'.join(current_section)
            if len(chunk) >= self.config.min_chunk_size:
                yield chunk

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be improved with NLTK/spaCy)
        sentence_endings = re.compile(r'([.!?]+[\s\n]+|[\n]{2,})')
        parts = sentence_endings.split(text)

        sentences = []
        for i in range(0, len(parts)-1, 2):
            sentence = parts[i] + (parts[i+1] if i+1 < len(parts) else '')
            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

        # Add last part if not captured
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1].strip())

        return sentences

    def _find_sentence_boundary(self, text: str) -> int:
        """Find the last sentence boundary in text."""
        # Look for sentence endings from the end
        for pattern in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            pos = text.rfind(pattern)
            if pos != -1:
                return pos + len(pattern)
        return -1


def optimize_chunk_size(
    corpus_sample: list[str],
    target_chunks: int = 3,
    min_size: int = 200,
    max_size: int = 1000,
) -> int:
    """
    Analyze corpus to determine optimal chunk size.

    Args:
        corpus_sample: Sample documents to analyze
        target_chunks: Target number of chunks per document
        min_size: Minimum chunk size to consider
        max_size: Maximum chunk size to consider

    Returns:
        Recommended chunk size
    """
    if not corpus_sample:
        return 512  # Default

    # Calculate average document length
    avg_length = sum(len(doc) for doc in corpus_sample) / len(corpus_sample)

    # Calculate ideal chunk size
    ideal_size = int(avg_length / target_chunks)

    # Clamp to bounds
    recommended = max(min_size, min(ideal_size, max_size))

    logger.info(
        f"Analyzed {len(corpus_sample)} documents. "
        f"Avg length: {avg_length:.0f}, "
        f"Recommended chunk size: {recommended}"
    )

    return recommended
