#!/usr/bin/env python3
"""
Semantic Chunking Strategy for Note-Taking
Optimal chunking based on 2025 research with speaker segmentation and contextual enrichment
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('semantic_chunker')


@dataclass
class Chunk:
    """A semantic chunk with metadata"""
    id: str
    text: str
    start_idx: int
    end_idx: int
    chunk_type: str = "semantic"  # semantic, speaker, paragraph
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_before: str = ""
    context_after: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'text': self.text[:200] + "..." if len(self.text) > 200 else self.text,
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'chunk_type': self.chunk_type,
            'metadata': self.metadata,
            'context_length': len(self.context_before) + len(self.context_after)
        }


class SemanticChunkingStrategy:
    """
    Optimal chunking strategy for note-taking applications
    Combines multiple chunking approaches for best results
    """
    
    def __init__(self,
                 chunk_size: int = 512,      # tokens
                 overlap: int = 50,           # tokens
                 semantic_threshold: float = 0.7):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.semantic_threshold = semantic_threshold
        
        # Rough token estimate: 1 token ≈ 4 characters
        self.char_per_token = 4
    
    def chunk_document(self, text: str, doc_type: str = "generic") -> List[Chunk]:
        """
        Chunk a document using optimal strategy for its type
        """
        if doc_type == "meeting_transcript":
            return self.chunk_meeting_transcript(text)
        elif doc_type == "lecture_notes":
            return self.chunk_lecture_notes(text)
        elif doc_type == "research_paper":
            return self.chunk_research_paper(text)
        else:
            return self.chunk_generic(text)
    
    def chunk_meeting_transcript(self, transcript: str) -> List[Chunk]:
        """
        Optimal chunking for meeting transcripts (30-120 minutes)
        1. Speaker-based segmentation
        2. Semantic chunking within speakers
        3. Contextual enrichment
        """
        logger.info("Chunking meeting transcript...")
        
        # Step 1: Speaker-based segmentation
        speaker_segments = self._segment_by_speaker(transcript)
        logger.info(f"Found {len(speaker_segments)} speaker segments")
        
        # Step 2: Semantic chunking within each speaker
        all_chunks = []
        for segment in speaker_segments:
            chunks = self._semantic_chunk_segment(segment)
            all_chunks.extend(chunks)
        
        # Step 3: Contextual enrichment
        enriched_chunks = self._add_context(all_chunks, transcript)
        
        logger.info(f"Created {len(enriched_chunks)} chunks from transcript")
        return enriched_chunks
    
    def _segment_by_speaker(self, transcript: str) -> List[Dict]:
        """
        Segment transcript by speaker
        Handles common formats: "Speaker Name: text" or "[Speaker] text"
        """
        segments = []
        
        # Pattern 1: "Speaker Name: text"
        pattern1 = r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?):\s*(.*?)(?=(?:[A-Z][a-z]+(?:\s[A-Z][a-z]+)?:\s*)|$)'
        
        # Pattern 2: "[Speaker] text" or "Speaker: text"
        pattern2 = r'\[?([^\]:\n]+)\]?:\s*(.*?)(?=(?:\[?[^\]:\n]+\]?:\s*)|$)'
        
        # Try pattern 1 first
        matches = list(re.finditer(pattern1, transcript, re.DOTALL))
        
        # If no matches, try pattern 2
        if not matches:
            matches = list(re.finditer(pattern2, transcript, re.DOTALL))
        
        # If still no matches, treat as single segment
        if not matches:
            return [{
                'speaker': 'Unknown',
                'text': transcript,
                'start': 0,
                'end': len(transcript)
            }]
        
        for match in matches:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            start = match.start()
            end = match.end()
            
            segments.append({
                'speaker': speaker,
                'text': text,
                'start': start,
                'end': end
            })
        
        return segments
    
    def _semantic_chunk_segment(self, segment: Dict) -> List[Chunk]:
        """
        Create semantic chunks within a speaker segment
        Respects sentence boundaries and semantic coherence
        """
        text = segment['text']
        speaker = segment['speaker']
        base_start = segment['start']
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_start = 0
        chunk_id = 0
        
        char_offset = 0
        
        for sentence in sentences:
            sentence_length = len(sentence) // self.char_per_token
            
            # Check if adding this sentence exceeds chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    id=f"{speaker}_{chunk_id}",
                    text=chunk_text,
                    start_idx=base_start + chunk_start,
                    end_idx=base_start + char_offset,
                    chunk_type="semantic",
                    metadata={
                        'speaker': speaker,
                        'sentence_count': len(current_chunk),
                        'estimated_tokens': current_length
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk) // self.char_per_token
                chunk_start = char_offset - sum(len(s) for s in overlap_sentences)
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
            
            char_offset += len(sentence) + 1  # +1 for space
        
        # Add remaining sentences
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                id=f"{speaker}_{chunk_id}",
                text=chunk_text,
                start_idx=base_start + chunk_start,
                end_idx=base_start + char_offset,
                chunk_type="semantic",
                metadata={
                    'speaker': speaker,
                    'sentence_count': len(current_chunk),
                    'estimated_tokens': current_length
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences to include in overlap based on token count"""
        overlap = []
        overlap_length = 0
        
        # Work backwards from end of list
        for sentence in reversed(sentences):
            sentence_length = len(sentence) // self.char_per_token
            if overlap_length + sentence_length <= self.overlap:
                overlap.insert(0, sentence)
                overlap_length += sentence_length
            else:
                break
        
        return overlap
    
    def _add_context(self, chunks: List[Chunk], full_text: str) -> List[Chunk]:
        """
        Add contextual enrichment to chunks
        Includes surrounding context and meeting-level context
        """
        context_window = 200 * self.char_per_token  # 200 tokens
        
        for i, chunk in enumerate(chunks):
            # Get context before
            start_idx = max(0, chunk.start_idx - context_window)
            context_before = full_text[start_idx:chunk.start_idx]
            chunk.context_before = self._clean_context(context_before)
            
            # Get context after
            end_idx = min(len(full_text), chunk.end_idx + context_window)
            context_after = full_text[chunk.end_idx:end_idx]
            chunk.context_after = self._clean_context(context_after)
            
            # Add meeting context to metadata
            chunk.metadata['meeting_context'] = self._extract_meeting_context(full_text)
            
            # Add position info
            chunk.metadata['chunk_position'] = f"{i+1}/{len(chunks)}"
        
        return chunks
    
    def _clean_context(self, context: str) -> str:
        """Clean context text for better readability"""
        # Remove partial sentences at boundaries
        context = context.strip()
        
        # If starts mid-sentence, find start of sentence
        if context and not context[0].isupper():
            first_sentence = re.search(r'[.!?]\s+([A-Z])', context)
            if first_sentence:
                context = context[first_sentence.start() + 2:]
        
        return context
    
    def _extract_meeting_context(self, text: str) -> Dict:
        """Extract meeting-level context (topic, key entities, etc.)"""
        context = {
            'topics': [],
            'key_entities': [],
            'duration_estimate': None
        }
        
        # Extract potential topics (capitalized phrases)
        topics = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        topic_freq = {}
        for topic in topics:
            topic_freq[topic] = topic_freq.get(topic, 0) + 1
        
        # Top topics
        context['topics'] = [t for t, _ in sorted(topic_freq.items(), 
                                                   key=lambda x: x[1], 
                                                   reverse=True)[:5]]
        
        # Estimate duration from content length
        word_count = len(text.split())
        # Rough estimate: 150 words per minute for speech
        context['duration_estimate_minutes'] = word_count / 150
        
        return context
    
    def chunk_lecture_notes(self, notes: str) -> List[Chunk]:
        """
        Chunk lecture notes with section awareness
        """
        chunks = []
        
        # Split by headers
        sections = re.split(r'\n(#{1,6}\s+.*?\n)', notes)
        
        current_header = "Introduction"
        for i, section in enumerate(sections):
            if section.startswith('#'):
                current_header = section.strip('# \n')
                continue
            
            if not section.strip():
                continue
            
            # Chunk section if too long
            section_chunks = self._chunk_by_size(section, current_header)
            chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_by_size(self, text: str, section_name: str) -> List[Chunk]:
        """Chunk text by size with overlap"""
        chunks = []
        char_limit = self.chunk_size * self.char_per_token
        overlap_chars = self.overlap * self.char_per_token
        
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + char_limit
            
            # Try to end at a sentence boundary
            if end < len(text):
                # Look for sentence end within next 100 chars
                search_end = min(end + 100, len(text))
                sentence_end = text.rfind('. ', end - 100, search_end)
                if sentence_end > end - 100:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            chunk = Chunk(
                id=f"{section_name}_{chunk_id}",
                text=chunk_text,
                start_idx=start,
                end_idx=end,
                chunk_type="section",
                metadata={
                    'section': section_name,
                    'estimated_tokens': len(chunk_text) // self.char_per_token
                }
            )
            chunks.append(chunk)
            
            start = end - overlap_chars
            chunk_id += 1
        
        return chunks
    
    def chunk_research_paper(self, paper: str) -> List[Chunk]:
        """
        Chunk research paper with abstract, sections, and citations
        """
        chunks = []
        
        # Extract abstract
        abstract_match = re.search(r'Abstract[\s:]*(.+?)(?=\n\s*\n|\n#)', paper, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            chunks.append(Chunk(
                id="abstract",
                text=abstract,
                start_idx=abstract_match.start(),
                end_idx=abstract_match.end(),
                chunk_type="abstract",
                metadata={'section': 'Abstract', 'priority': 'high'}
            ))
        
        # Chunk remaining sections
        section_chunks = self.chunk_lecture_notes(paper)
        chunks.extend(section_chunks)
        
        return chunks
    
    def chunk_generic(self, text: str) -> List[Chunk]:
        """
        Generic chunking for unknown document types
        """
        # Detect if has headers
        if '#' in text:
            return self.chunk_lecture_notes(text)
        
        # Detect if has speaker patterns
        if re.search(r'[A-Z][a-z]+:\s', text):
            return self.chunk_meeting_transcript(text)
        
        # Fallback to paragraph-based chunking
        return self._chunk_by_paragraphs(text)
    
    def _chunk_by_paragraphs(self, text: str) -> List[Chunk]:
        """Chunk by paragraphs with size limits"""
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_length = 0
        start_idx = 0
        chunk_id = 0
        char_offset = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para) // self.char_per_token
            
            if current_length + para_length > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(Chunk(
                    id=f"para_{chunk_id}",
                    text=chunk_text,
                    start_idx=start_idx,
                    end_idx=char_offset,
                    chunk_type="paragraph",
                    metadata={'paragraph_count': len(current_chunk)}
                ))
                
                current_chunk = [para]
                current_length = para_length
                start_idx = char_offset
                chunk_id += 1
            else:
                current_chunk.append(para)
                current_length += para_length
            
            char_offset += len(para) + 2  # +2 for \n\n
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                id=f"para_{chunk_id}",
                text=chunk_text,
                start_idx=start_idx,
                end_idx=char_offset,
                chunk_type="paragraph",
                metadata={'paragraph_count': len(current_chunk)}
            ))
        
        return chunks
    
    def get_stats(self, chunks: List[Chunk]) -> Dict:
        """Get statistics about chunks"""
        if not chunks:
            return {}
        
        sizes = [len(c.text) // self.char_per_token for c in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(sizes) / len(sizes),
            'min_chunk_size': min(sizes),
            'max_chunk_size': max(sizes),
            'chunk_types': list(set(c.chunk_type for c in chunks)),
            'total_tokens': sum(sizes)
        }


if __name__ == '__main__':
    # Demo
    chunker = SemanticChunkingStrategy()
    
    test_transcript = """
Alice: Welcome everyone to the Q4 strategy review. Let's start with the budget discussion.
Bob: Thanks Alice. I've prepared the financial projections. We expect 15% growth.
Alice: That's great news. What about the timeline?
Bob: We can deliver by end of Q1 if we get approval this week.
Alice: Perfect, let's move to action items.
"""
    
    chunks = chunker.chunk_meeting_transcript(test_transcript)
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\n{chunk.id}: {chunk.metadata}")
        print(f"Text: {chunk.text[:100]}...")
    
    stats = chunker.get_stats(chunks)
    print(f"\nStats: {stats}")
