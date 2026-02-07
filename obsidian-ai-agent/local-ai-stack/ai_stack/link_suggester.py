"""
Automated Link Suggestions System
Issue #100: Implement Automated Link Suggestions

Provides intelligent link suggestions based on content analysis,
semantic similarity, and NLP techniques to enhance note connectivity.
"""

import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import heapq
import threading

logger = logging.getLogger(__name__)


@dataclass
class LinkSuggestion:
    """Represents a suggested link."""
    source_note: str
    suggested_note: str
    confidence: float  # 0.0 to 1.0
    reason: str  # Explanation of why this link is suggested
    context: str  # The text context where the link could be added
    position: Optional[Tuple[int, int]] = None  # (line, column) if applicable
    
    def to_dict(self) -> Dict:
        return {
            'source_note': self.source_note,
            'suggested_note': self.suggested_note,
            'confidence': self.confidence,
            'reason': self.reason,
            'context': self.context,
            'position': self.position
        }


@dataclass
class SuggestionReport:
    """Report of all suggestions for analysis."""
    total_notes_analyzed: int
    total_suggestions: int
    high_confidence: List[LinkSuggestion]  # confidence >= 0.8
    medium_confidence: List[LinkSuggestion]  # confidence 0.5-0.8
    low_confidence: List[LinkSuggestion]  # confidence < 0.5
    duration_ms: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'total_notes_analyzed': self.total_notes_analyzed,
            'total_suggestions': self.total_suggestions,
            'high_confidence_count': len(self.high_confidence),
            'medium_confidence_count': len(self.medium_confidence),
            'low_confidence_count': len(self.low_confidence),
            'high_confidence': [s.to_dict() for s in self.high_confidence[:20]],
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat()
        }


class TextAnalyzer:
    """Analyze text to extract concepts and entities."""
    
    # Common stop words to filter out
    STOP_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'and', 'but', 'or', 'yet', 'so', 'if',
        'because', 'although', 'though', 'while', 'where', 'when', 'that',
        'which', 'who', 'whom', 'whose', 'what', 'this', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'mine',
        'yours', 'hers', 'ours', 'theirs', 'myself', 'yourself', 'himself',
        'herself', 'itself', 'ourselves', 'yourselves', 'themselves'
    }
    
    def __init__(self):
        self._word_pattern = re.compile(r'\b[A-Za-z][A-Za-z0-9_\-]{2,}\b')
    
    def extract_concepts(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract potential concept words from text.
        Returns list of lowercase words/concepts.
        """
        # Clean text
        text = re.sub(r'[#\*\[\]\(\)\|`\-]', ' ', text)
        
        # Extract words
        words = self._word_pattern.findall(text)
        
        # Filter stop words and short words
        concepts = [
            w.lower() for w in words 
            if len(w) >= min_length and w.lower() not in self.STOP_WORDS
        ]
        
        # Count frequency and return unique sorted by frequency
        from collections import Counter
        counts = Counter(concepts)
        return [word for word, _ in counts.most_common()]
    
    def extract_phrases(self, text: str, n: int = 2) -> List[str]:
        """Extract n-gram phrases from text."""
        words = self.extract_concepts(text, min_length=2)
        if len(words) < n:
            return []
        
        phrases = []
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i+n])
            phrases.append(phrase)
        
        return phrases
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple word overlap similarity between two texts.
        Returns similarity score between 0.0 and 1.0.
        """
        concepts1 = set(self.extract_concepts(text1))
        concepts2 = set(self.extract_concepts(text2))
        
        if not concepts1 or not concepts2:
            return 0.0
        
        intersection = concepts1 & concepts2
        union = concepts1 | concepts2
        
        return len(intersection) / len(union)


class SuggestionEngine:
    """
    Main engine for generating link suggestions.
    Uses multiple strategies for comprehensive coverage.
    """
    
    def __init__(self, vault_path: str, db_path: str = "suggestions.db"):
        self.vault_path = Path(vault_path)
        self.db_path = db_path
        self.analyzer = TextAnalyzer()
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize suggestion database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_note TEXT NOT NULL,
                    suggested_note TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied BOOLEAN DEFAULT 0,
                    dismissed BOOLEAN DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_source ON suggestions(source_note);
                CREATE INDEX IF NOT EXISTS idx_suggested ON suggestions(suggested_note);
                CREATE INDEX IF NOT EXISTS idx_confidence ON suggestions(confidence);
                
                CREATE TABLE IF NOT EXISTS note_index (
                    note_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    title TEXT,
                    concepts TEXT,  -- JSON array
                    aliases TEXT,   -- JSON array
                    last_modified TIMESTAMP,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def analyze_vault(self) -> SuggestionReport:
        """
        Analyze entire vault and generate link suggestions.
        """
        import time
        start_time = time.time()
        
        logger.info("Starting vault analysis for link suggestions...")
        
        # Load all notes
        notes = self._load_all_notes()
        
        # Build concept index
        self._build_concept_index(notes)
        
        # Generate suggestions using multiple strategies
        all_suggestions: List[LinkSuggestion] = []
        
        # Strategy 1: Concept overlap
        concept_suggestions = self._suggest_by_concept_overlap(notes)
        all_suggestions.extend(concept_suggestions)
        
        # Strategy 2: Title mentions in content
        mention_suggestions = self._suggest_by_title_mentions(notes)
        all_suggestions.extend(mention_suggestions)
        
        # Strategy 3: Similar titles
        title_suggestions = self._suggest_by_similar_titles(notes)
        all_suggestions.extend(title_suggestions)
        
        # Deduplicate and sort
        unique_suggestions = self._deduplicate_suggestions(all_suggestions)
        
        # Store in database
        self._store_suggestions(unique_suggestions)
        
        # Categorize by confidence
        high = [s for s in unique_suggestions if s.confidence >= 0.8]
        medium = [s for s in unique_suggestions if 0.5 <= s.confidence < 0.8]
        low = [s for s in unique_suggestions if s.confidence < 0.5]
        
        duration_ms = (time.time() - start_time) * 1000
        
        report = SuggestionReport(
            total_notes_analyzed=len(notes),
            total_suggestions=len(unique_suggestions),
            high_confidence=high,
            medium_confidence=medium,
            low_confidence=low,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Analysis complete: {len(unique_suggestions)} suggestions generated "
                   f"({len(high)} high, {len(medium)} medium, {len(low)} low confidence)")
        
        return report
    
    def _load_all_notes(self) -> Dict[str, Dict]:
        """Load all notes from vault."""
        notes = {}
        
        for note_path in self.vault_path.rglob("*.md"):
            try:
                note_id = str(note_path.relative_to(self.vault_path)).replace('\\', '/')
                content = note_path.read_text(encoding='utf-8')
                
                # Extract title (first heading or filename)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else note_path.stem
                
                # Extract aliases from frontmatter if present
                aliases = self._extract_aliases(content)
                
                notes[note_id] = {
                    'id': note_id,
                    'path': str(note_path),
                    'title': title,
                    'content': content,
                    'aliases': aliases,
                    'concepts': self.analyzer.extract_concepts(content)
                }
            except Exception as e:
                logger.warning(f"Failed to load {note_path}: {e}")
        
        return notes
    
    def _extract_aliases(self, content: str) -> List[str]:
        """Extract aliases from YAML frontmatter."""
        aliases = []
        
        # Match YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # Simple alias extraction
            alias_match = re.search(r'aliases:\s*\n((?:\s*-\s*[^\n]+\n)*)', frontmatter)
            if alias_match:
                for line in alias_match.group(1).strip().split('\n'):
                    alias = re.sub(r'^\s*-\s*', '', line).strip()
                    if alias:
                        aliases.append(alias)
        
        return aliases
    
    def _build_concept_index(self, notes: Dict[str, Dict]) -> None:
        """Build concept index in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM note_index")
            
            for note_id, note in notes.items():
                conn.execute("""
                    INSERT OR REPLACE INTO note_index 
                    (note_id, file_path, title, concepts, aliases, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    note_id,
                    note['path'],
                    note['title'],
                    json.dumps(note['concepts']),
                    json.dumps(note['aliases']),
                    datetime.utcnow().isoformat()
                ))
    
    def _suggest_by_concept_overlap(
        self, 
        notes: Dict[str, Dict]
    ) -> List[LinkSuggestion]:
        """Suggest links based on concept overlap."""
        suggestions = []
        
        note_list = list(notes.items())
        
        for i, (note_id1, note1) in enumerate(note_list):
            for note_id2, note2 in note_list[i+1:]:
                # Skip if same note
                if note_id1 == note_id2:
                    continue
                
                # Calculate concept overlap
                concepts1 = set(note1['concepts'])
                concepts2 = set(note2['concepts'])
                
                if not concepts1 or not concepts2:
                    continue
                
                overlap = concepts1 & concepts2
                
                if len(overlap) >= 3:  # Threshold
                    confidence = min(0.95, 0.5 + (len(overlap) * 0.1))
                    
                    # Suggest note2 in note1
                    context = self._find_context_for_concepts(
                        note1['content'], overlap
                    )
                    
                    suggestions.append(LinkSuggestion(
                        source_note=note_id1,
                        suggested_note=note_id2,
                        confidence=confidence,
                        reason=f"Shared concepts: {', '.join(list(overlap)[:5])}",
                        context=context
                    ))
                    
                    # Suggest note1 in note2
                    context = self._find_context_for_concepts(
                        note2['content'], overlap
                    )
                    
                    suggestions.append(LinkSuggestion(
                        source_note=note_id2,
                        suggested_note=note_id1,
                        confidence=confidence,
                        reason=f"Shared concepts: {', '.join(list(overlap)[:5])}",
                        context=context
                    ))
        
        return suggestions
    
    def _suggest_by_title_mentions(
        self, 
        notes: Dict[str, Dict]
    ) -> List[LinkSuggestion]:
        """Suggest links where note titles are mentioned in content."""
        suggestions = []
        
        for note_id, note in notes.items():
            for other_id, other_note in notes.items():
                if note_id == other_id:
                    continue
                
                # Check if other note's title is mentioned in this note
                title = other_note['title']
                title_lower = title.lower()
                
                # Look for unlinked mentions
                pattern = rf'(?<!\[\[){re.escape(title)}(?!\]\])'
                matches = list(re.finditer(pattern, note['content'], re.IGNORECASE))
                
                if matches:
                    confidence = min(0.9, 0.6 + (len(matches) * 0.05))
                    
                    # Get context from first match
                    match = matches[0]
                    context = self._get_context_around_position(
                        note['content'], match.start()
                    )
                    
                    suggestions.append(LinkSuggestion(
                        source_note=note_id,
                        suggested_note=other_id,
                        confidence=confidence,
                        reason=f"'{title}' mentioned {len(matches)} time(s) in content",
                        context=context
                    ))
                
                # Also check aliases
                for alias in other_note['aliases']:
                    alias_pattern = rf'(?<!\[\[){re.escape(alias)}(?!\]\])'
                    alias_matches = list(re.finditer(
                        alias_pattern, note['content'], re.IGNORECASE
                    ))
                    
                    if alias_matches:
                        confidence = min(0.85, 0.55 + (len(alias_matches) * 0.05))
                        match = alias_matches[0]
                        context = self._get_context_around_position(
                            note['content'], match.start()
                        )
                        
                        suggestions.append(LinkSuggestion(
                            source_note=note_id,
                            suggested_note=other_id,
                            confidence=confidence,
                            reason=f"Alias '{alias}' mentioned {len(alias_matches)} time(s)",
                            context=context
                        ))
        
        return suggestions
    
    def _suggest_by_similar_titles(
        self, 
        notes: Dict[str, Dict]
    ) -> List[LinkSuggestion]:
        """Suggest links between notes with similar titles."""
        suggestions = []
        
        note_list = list(notes.items())
        
        for i, (note_id1, note1) in enumerate(note_list):
            for note_id2, note2 in note_list[i+1:]:
                title1 = note1['title'].lower()
                title2 = note2['title'].lower()
                
                # Skip if identical
                if title1 == title2:
                    continue
                
                # Check for word overlap in titles
                words1 = set(title1.split())
                words2 = set(title2.split())
                
                common = words1 & words2
                
                if len(common) >= 2:
                    confidence = min(0.75, 0.4 + (len(common) * 0.15))
                    
                    suggestions.append(LinkSuggestion(
                        source_note=note_id1,
                        suggested_note=note_id2,
                        confidence=confidence,
                        reason=f"Similar titles: '{note1['title']}' and '{note2['title']}'",
                        context=f"Title: {note1['title']}"
                    ))
                    
                    suggestions.append(LinkSuggestion(
                        source_note=note_id2,
                        suggested_note=note_id1,
                        confidence=confidence,
                        reason=f"Similar titles: '{note2['title']}' and '{note1['title']}'",
                        context=f"Title: {note2['title']}"
                    ))
        
        return suggestions
    
    def _find_context_for_concepts(
        self, 
        content: str, 
        concepts: Set[str]
    ) -> str:
        """Find text context containing the given concepts."""
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(concept in line_lower for concept in concepts):
                return line.strip()[:200]  # Limit length
        
        return content[:200]  # Fallback to beginning
    
    def _get_context_around_position(
        self, 
        content: str, 
        position: int, 
        window: int = 100
    ) -> str:
        """Get text context around a position."""
        start = max(0, position - window)
        end = min(len(content), position + window)
        
        context = content[start:end].strip()
        # Clean up
        context = re.sub(r'\s+', ' ', context)
        
        return context[:200]
    
    def _deduplicate_suggestions(
        self, 
        suggestions: List[LinkSuggestion]
    ) -> List[LinkSuggestion]:
        """Remove duplicate suggestions, keeping highest confidence."""
        seen = {}
        
        for suggestion in suggestions:
            key = (suggestion.source_note, suggestion.suggested_note)
            
            if key not in seen:
                seen[key] = suggestion
            elif suggestion.confidence > seen[key].confidence:
                seen[key] = suggestion
        
        # Sort by confidence descending
        return sorted(seen.values(), key=lambda s: s.confidence, reverse=True)
    
    def _store_suggestions(self, suggestions: List[LinkSuggestion]) -> None:
        """Store suggestions in database."""
        with sqlite3.connect(self.db_path) as conn:
            for suggestion in suggestions:
                conn.execute("""
                    INSERT OR REPLACE INTO suggestions 
                    (source_note, suggested_note, confidence, reason, context)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    suggestion.source_note,
                    suggestion.suggested_note,
                    suggestion.confidence,
                    suggestion.reason,
                    suggestion.context
                ))
    
    def get_suggestions_for_note(
        self, 
        note_id: str, 
        min_confidence: float = 0.5
    ) -> List[LinkSuggestion]:
        """Get suggestions for a specific note."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM suggestions 
                WHERE source_note = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (note_id, min_confidence)).fetchall()
            
            return [
                LinkSuggestion(
                    source_note=row['source_note'],
                    suggested_note=row['suggested_note'],
                    confidence=row['confidence'],
                    reason=row['reason'],
                    context=row['context'] or ''
                )
                for row in rows
            ]
    
    def apply_suggestion(
        self, 
        suggestion: LinkSuggestion, 
        link_text: Optional[str] = None
    ) -> bool:
        """
        Apply a suggestion by adding the link to the source note.
        
        Args:
            suggestion: The suggestion to apply
            link_text: Optional custom link text (defaults to suggested note title)
        
        Returns:
            True if successful
        """
        try:
            note_path = self.vault_path / suggestion.source_note
            content = note_path.read_text(encoding='utf-8')
            
            # Determine link text
            if link_text is None:
                # Extract title from suggested note
                suggested_path = self.vault_path / suggestion.suggested_note
                if suggested_path.exists():
                    suggested_content = suggested_path.read_text(encoding='utf-8')
                    title_match = re.search(r'^#\s+(.+)$', suggested_content, re.MULTILINE)
                    link_text = title_match.group(1) if title_match else suggested_path.stem
                else:
                    link_text = Path(suggestion.suggested_note).stem
            
            # Create the wiki link
            wiki_link = f"[[{suggestion.suggested_note}|{link_text}]]"
            
            # Find the context and replace it with linked version
            # This is a simple implementation - more sophisticated logic could be added
            if suggestion.context and suggestion.context in content:
                # Try to link the first occurrence
                context = suggestion.context
                words = context.split()
                if words:
                    # Find a word that matches the suggested note title
                    for word in words:
                        clean_word = re.sub(r'[^\w\s]', '', word)
                        if clean_word.lower() in suggestion.suggested_note.lower():
                            new_context = context.replace(
                                word, 
                                f"[[{suggestion.suggested_note}|{clean_word}]]",
                                1
                            )
                            content = content.replace(context, new_context, 1)
                            break
                    else:
                        # If no match, append link at end
                        content = content.rstrip() + f"\n\nRelated: {wiki_link}\n"
            else:
                # Append at end
                content = content.rstrip() + f"\n\nRelated: {wiki_link}\n"
            
            note_path.write_text(content, encoding='utf-8')
            
            # Mark as applied in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE suggestions SET applied = 1
                    WHERE source_note = ? AND suggested_note = ?
                """, (suggestion.source_note, suggestion.suggested_note))
            
            logger.info(f"Applied suggestion: {suggestion.source_note} -> {suggestion.suggested_note}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply suggestion: {e}")
            return False
    
    def dismiss_suggestion(self, suggestion: LinkSuggestion) -> bool:
        """Mark a suggestion as dismissed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE suggestions SET dismissed = 1
                    WHERE source_note = ? AND suggested_note = ?
                """, (suggestion.source_note, suggestion.suggested_note))
            return True
        except Exception as e:
            logger.error(f"Failed to dismiss suggestion: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get suggestion statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM suggestions").fetchone()[0]
            applied = conn.execute(
                "SELECT COUNT(*) FROM suggestions WHERE applied = 1"
            ).fetchone()[0]
            dismissed = conn.execute(
                "SELECT COUNT(*) FROM suggestions WHERE dismissed = 1"
            ).fetchone()[0]
            high_conf = conn.execute(
                "SELECT COUNT(*) FROM suggestions WHERE confidence >= 0.8"
            ).fetchone()[0]
            
            return {
                'total_suggestions': total,
                'applied': applied,
                'dismissed': dismissed,
                'pending': total - applied - dismissed,
                'high_confidence': high_conf
            }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create test vault
    test_vault = Path("test_suggest_vault")
    test_vault.mkdir(exist_ok=True)
    
    # Create test notes
    (test_vault / "Python Programming.md").write_text("""# Python Programming

Python is a great language for AI and machine learning.
You can use it for data science and web development.

## Topics

- Variables and functions
- Object-oriented programming
""")
    
    (test_vault / "Machine Learning.md").write_text("""# Machine Learning

Machine learning is a subset of AI.
Python is commonly used for ML projects.
Popular libraries include TensorFlow and PyTorch.
""")
    
    (test_vault / "Data Science.md").write_text("""# Data Science

Data science involves statistics and machine learning.
Python is the primary language used.
Analysis and visualization are key skills.
""")
    
    (test_vault / "Web Development.md").write_text("""# Web Development

Building websites and web applications.
Can use Python with Django or Flask.
Frontend uses HTML, CSS, and JavaScript.
""")
    
    # Initialize engine and analyze
    engine = SuggestionEngine(str(test_vault), "test_suggestions.db")
    report = engine.analyze_vault()
    
    # Print report
    print(f"\n=== Suggestion Report ===")
    print(f"Notes analyzed: {report.total_notes_analyzed}")
    print(f"Total suggestions: {report.total_suggestions}")
    print(f"High confidence: {len(report.high_confidence)}")
    print(f"Medium confidence: {len(report.medium_confidence)}")
    
    if report.high_confidence:
        print("\n=== Top High Confidence Suggestions ===")
        for suggestion in report.high_confidence[:5]:
            print(f"  {suggestion.source_note} -> {suggestion.suggested_note}")
            print(f"    Confidence: {suggestion.confidence:.2f}")
            print(f"    Reason: {suggestion.reason}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_vault, ignore_errors=True)
    Path("test_suggestions.db").unlink(missing_ok=True)
    
    print("\nLink Suggester test completed successfully!")
