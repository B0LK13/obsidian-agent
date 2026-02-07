"""Semantic chunking strategy for better RAG performance."""

import re
from dataclasses import dataclass, field
from typing import Iterator, NamedTuple

from pkm_agent.data.models import Chunk, Note
from pkm_agent.rag.chunker import ChunkerConfig


class MarkdownSection(NamedTuple):
    """A section of markdown text."""
    level: int
    title: str
    content: str
    start_idx: int
    end_idx: int


@dataclass
class SemanticChunkerConfig(ChunkerConfig):
    """Configuration for semantic chunking."""
    include_breadcrumbs: bool = True  # Include header path in chunk content
    max_tokens: int = 500  # Target size in tokens (approx)
    preserve_code_blocks: bool = True


class SemanticChunker:
    """Splits text into chunks preserving semantic meaning."""

    def __init__(self, config: SemanticChunkerConfig | None = None):
        self.config = config or SemanticChunkerConfig()
        
        # Regex patterns
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```[\s\S]*?```')
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')

    def chunk_note(self, note: Note) -> list[Chunk]:
        """Split a note into semantic chunks."""
        text = note.content
        if not text.strip():
            return []

        chunks: list[Chunk] = []
        
        # 1. Parse markdown structure
        sections = self._parse_markdown_sections(text)
        
        # 2. Process sections into chunks
        chunk_index = 0
        
        if not sections:
            # No headers, treat as one section
            sections = [MarkdownSection(0, note.title, text, 0, len(text))]
            
        current_path: list[str] = [note.title] if note.title else []
        
        for section in sections:
            # Update path based on nesting
            # This is a simplification; a real tree parser would be better
            # but for flat list of sections, we can try to infer hierarchy
            if section.level > 0:
                # Truncate path if level goes up or stays same
                # E.g. H1 -> H2 (append), H2 -> H2 (replace last), H2 -> H1 (reset)
                # Here we just use the section title as context
                pass

            # Split section content
            section_chunks = self._chunk_text(
                section.content, 
                context_title=section.title if section.level > 0 else None
            )
            
            for content in section_chunks:
                # Add breadcrumbs if configured
                final_content = content
                if self.config.include_breadcrumbs and section.title and section.level > 0:
                    final_content = f"# {section.title}\n\n{content}"

                chunks.append(Chunk(
                    id=f"{note.id}_{chunk_index}",
                    note_id=note.id,
                    content=final_content,
                    index=chunk_index,
                    metadata={
                        "title": note.title,
                        "path": str(note.path),
                        "tags": note.metadata.tags,
                        "section": section.title,
                        "level": section.level
                    }
                ))
                chunk_index += 1

        return chunks

    def _parse_markdown_sections(self, text: str) -> list[MarkdownSection]:
        """Parse markdown into a flat list of sections."""
        matches = list(self.header_pattern.finditer(text))
        if not matches:
            return []

        sections = []
        
        # Add preamble if exists
        if matches[0].start() > 0:
            sections.append(MarkdownSection(
                level=0,
                title="Introduction",
                content=text[:matches[0].start()].strip(),
                start_idx=0,
                end_idx=matches[0].start()
            ))

        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.end()
            
            # Find end of this section (start of next header)
            if i + 1 < len(matches):
                end = matches[i+1].start()
            else:
                end = len(text)
                
            content = text[start:end].strip()
            
            if content:
                sections.append(MarkdownSection(
                    level=level,
                    title=title,
                    content=content,
                    start_idx=start,
                    end_idx=end
                ))

        return sections

    def _chunk_text(self, text: str, context_title: str | None = None) -> list[str]:
        """Split text into chunks aiming for target size."""
        if not text:
            return []

        # If text fits in one chunk, return it
        if len(text) <= self.config.chunk_size:
            return [text]

        # First, respect code blocks (don't split inside them)
        # We replace code blocks with placeholders
        code_blocks = []
        def save_code_block(match):
            code_blocks.append(match.group(0))
            return f"\x00CODE{len(code_blocks)-1}\x00"
            
        protected_text = self.code_block_pattern.sub(save_code_block, text)

        # Split by paragraphs
        paragraphs = protected_text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If paragraph itself is too big, split by sentences
            if para_size > self.config.chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split huge paragraph
                sent_chunks = self._split_huge_paragraph(para, self.config.chunk_size)
                chunks.extend(sent_chunks)
                continue

            # Check if adding fits
            if current_size + para_size + 2 > self.config.chunk_size:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for \n\n

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # Restore code blocks
        final_chunks = []
        for chunk in chunks:
            for i, code in enumerate(code_blocks):
                chunk = chunk.replace(f"\x00CODE{i}\x00", code)
            final_chunks.append(chunk)

        return final_chunks

    def _split_huge_paragraph(self, text: str, limit: int) -> list[str]:
        """Split a large paragraph by sentences."""
        sentences = self.sentence_pattern.split(text)
        chunks = []
        current = []
        current_len = 0
        
        for sent in sentences:
            if current_len + len(sent) + 1 > limit:
                if current:
                    chunks.append(" ".join(current))
                current = [sent]
                current_len = len(sent)
            else:
                current.append(sent)
                current_len += len(sent) + 1
        
        if current:
            chunks.append(" ".join(current))
            
        return chunks
