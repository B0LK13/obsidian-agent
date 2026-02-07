#!/usr/bin/env python3
"""
Memory-Augmented RAG System
Based on 2025 research - multi-layer memory architecture for note-taking
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import heapq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('memory_rag')


@dataclass
class MemoryEntry:
    """A single memory entry with metadata"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    memory_type: str = "short_term"  # short_term, long_term, episodic
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'memory_type': self.memory_type,
            'relevance_score': self.relevance_score,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        entry = cls(
            id=data['id'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            memory_type=data.get('memory_type', 'short_term'),
            relevance_score=data.get('relevance_score', 1.0),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed'])
        )
        return entry


@dataclass
class Relationship:
    """Relationship between entities for episodic memory"""
    source: str
    target: str
    relation_type: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """Session-based working memory"""
    
    def __init__(self, max_entries: int = 100, ttl_minutes: int = 60):
        self.entries: Dict[str, MemoryEntry] = {}
        self.max_entries = max_entries
        self.ttl = timedelta(minutes=ttl_minutes)
        self.session_context: List[str] = []
    
    def add(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Add entry to short-term memory"""
        entry_id = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()[:12]
        
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {},
            memory_type="short_term"
        )
        
        self.entries[entry_id] = entry
        self._evict_if_needed()
        
        return entry_id
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve and update access stats"""
        entry = self.entries.get(entry_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.now()
        return entry
    
    def get_recent(self, n: int = 10) -> List[MemoryEntry]:
        """Get most recent entries"""
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_entries[:n]
    
    def get_context_window(self, max_tokens: int = 2000) -> str:
        """Get recent context as concatenated string"""
        entries = self.get_recent(20)
        context_parts = []
        total_length = 0
        
        for entry in entries:
            content = f"[{entry.timestamp.strftime('%H:%M')}] {entry.content}\n"
            if total_length + len(content) > max_tokens * 4:  # Rough token estimate
                break
            context_parts.append(content)
            total_length += len(content)
        
        return "".join(reversed(context_parts))
    
    def _evict_if_needed(self):
        """Evict oldest entries if over capacity"""
        if len(self.entries) > self.max_entries:
            # Remove expired entries first
            now = datetime.now()
            expired = [
                id for id, entry in self.entries.items()
                if now - entry.timestamp > self.ttl
            ]
            for id in expired:
                del self.entries[id]
        
        # If still over capacity, remove oldest
        if len(self.entries) > self.max_entries:
            oldest = min(self.entries.values(), key=lambda e: e.timestamp)
            del self.entries[oldest.id]
    
    def clear(self):
        """Clear all short-term memory"""
        self.entries.clear()
        self.session_context.clear()


class LongTermMemory:
    """Persistent vector-based memory"""
    
    def __init__(self, vector_store_path: str = "./data/long_term_memory"):
        self.path = Path(vector_store_path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.entries: Dict[str, MemoryEntry] = {}
        self.index = {}  # Simple inverted index
        self._load()
    
    def add(self, entry: MemoryEntry, embedding: List[float]) -> str:
        """Add entry to long-term memory"""
        entry.embedding = embedding
        entry.memory_type = "long_term"
        
        self.entries[entry.id] = entry
        
        # Update inverted index
        words = set(entry.content.lower().split())
        for word in words:
            if word not in self.index:
                self.index[word] = set()
            self.index[word].add(entry.id)
        
        self._save()
        return entry.id
    
    def search(self, query_embedding: List[float], 
               query_text: Optional[str] = None,
               top_k: int = 5) -> List[Tuple[MemoryEntry, float]]:
        """Semantic search with optional keyword boost"""
        results = []
        
        # Semantic similarity
        for entry in self.entries.values():
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                
                # Keyword boost
                if query_text:
                    keyword_boost = self._keyword_match_score(query_text, entry.content)
                    similarity = 0.7 * similarity + 0.3 * keyword_boost
                
                results.append((entry, similarity))
        
        # Return top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0
    
    def _keyword_match_score(self, query: str, content: str) -> float:
        """Calculate keyword overlap score"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0
        
        overlap = query_words & content_words
        return len(overlap) / len(query_words)
    
    def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get entry by ID"""
        return self.entries.get(entry_id)
    
    def _load(self):
        """Load from disk"""
        data_file = self.path / "memory.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data.get('entries', []):
                        entry = MemoryEntry.from_dict(entry_data)
                        self.entries[entry.id] = entry
                    self.index = data.get('index', {})
            except Exception as e:
                logger.error(f"Failed to load long-term memory: {e}")
    
    def _save(self):
        """Save to disk"""
        data_file = self.path / "memory.json"
        try:
            with open(data_file, 'w') as f:
                json.dump({
                    'entries': [e.to_dict() for e in self.entries.values()],
                    'index': {k: list(v) for k, v in self.index.items()}
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save long-term memory: {e}")


class EpisodicMemory:
    """Graph-based relationship memory"""
    
    def __init__(self, store_path: str = "./data/episodic_memory"):
        self.path = Path(store_path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.entities: Dict[str, Dict] = {}
        self.relationships: List[Relationship] = []
        self._load()
    
    def add_relationship(self, source: str, target: str, 
                         relation_type: str, strength: float = 1.0,
                         metadata: Optional[Dict] = None):
        """Add a relationship between entities"""
        # Create/update entities
        for entity in [source, target]:
            if entity not in self.entities:
                self.entities[entity] = {
                    'first_seen': datetime.now().isoformat(),
                    'mentions': 0
                }
            self.entities[entity]['mentions'] += 1
            self.entities[entity]['last_seen'] = datetime.now().isoformat()
        
        # Add relationship
        rel = Relationship(
            source=source,
            target=target,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {}
        )
        self.relationships.append(rel)
        
        self._save()
    
    def get_related(self, entity: str, relation_type: Optional[str] = None,
                    min_strength: float = 0.5) -> List[Tuple[str, float, str]]:
        """Get entities related to given entity"""
        related = []
        
        for rel in self.relationships:
            if rel.strength < min_strength:
                continue
            
            if relation_type and rel.relation_type != relation_type:
                continue
            
            if rel.source == entity:
                related.append((rel.target, rel.strength, rel.relation_type))
            elif rel.target == entity:
                related.append((rel.source, rel.strength, rel.relation_type))
        
        # Sort by strength
        related.sort(key=lambda x: x[1], reverse=True)
        return related
    
    def get_entity_context(self, entity: str, depth: int = 2) -> Dict:
        """Get contextual network around entity"""
        context = {
            'entity': entity,
            'direct_relations': [],
            'indirect_relations': [],
            'entity_info': self.entities.get(entity, {})
        }
        
        # Direct relationships
        direct = self.get_related(entity)
        context['direct_relations'] = [
            {'entity': e, 'strength': s, 'type': t}
            for e, s, t in direct[:10]
        ]
        
        # Indirect relationships (if depth > 1)
        if depth > 1:
            seen = {entity}
            for related_entity, _, _ in direct[:5]:
                if related_entity not in seen:
                    indirect = self.get_related(related_entity)
                    for e, s, t in indirect[:3]:
                        if e not in seen and e != entity:
                            context['indirect_relations'].append({
                                'via': related_entity,
                                'entity': e,
                                'strength': s,
                                'type': t
                            })
                            seen.add(e)
        
        return context
    
    def _load(self):
        """Load from disk"""
        data_file = self.path / "episodic.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.entities = data.get('entities', {})
                    self.relationships = [
                        Relationship(**rel)
                        for rel in data.get('relationships', [])
                    ]
            except Exception as e:
                logger.error(f"Failed to load episodic memory: {e}")
    
    def _save(self):
        """Save to disk"""
        data_file = self.path / "episodic.json"
        try:
            with open(data_file, 'w') as f:
                json.dump({
                    'entities': self.entities,
                    'relationships': [asdict(r) for r in self.relationships]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save episodic memory: {e}")


class MemoryAugmentedRAG:
    """
    Complete memory-augmented RAG system
    Combines short-term, long-term, and episodic memory
    """
    
    def __init__(self, data_path: str = "./data"):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(f"{data_path}/long_term_memory")
        self.episodic = EpisodicMemory(f"{data_path}/episodic_memory")
        logger.info("Memory-Augmented RAG initialized")
    
    def process_query(self, query: str, query_embedding: List[float],
                      context: Optional[Dict] = None) -> Dict:
        """
        Process a query using all memory layers
        Returns enriched context for generation
        """
        results = {
            'short_term': [],
            'long_term': [],
            'episodic': [],
            'consolidated_context': ''
        }
        
        # 1. Retrieve from short-term memory (recent context)
        recent = self.short_term.get_recent(5)
        results['short_term'] = [
            {'content': e.content, 'timestamp': e.timestamp.isoformat()}
            for e in recent
        ]
        
        # 2. Retrieve from long-term memory (semantic search)
        semantic_results = self.long_term.search(
            query_embedding, 
            query_text=query,
            top_k=5
        )
        results['long_term'] = [
            {'content': e.content, 'score': score, 'metadata': e.metadata}
            for e, score in semantic_results
        ]
        
        # 3. Extract entities and get episodic context
        # Simple entity extraction (would use NER in production)
        words = query.split()
        potential_entities = [w for w in words if len(w) > 4 and w[0].isupper()]
        
        for entity in potential_entities[:3]:
            entity_context = self.episodic.get_entity_context(entity)
            if entity_context['direct_relations']:
                results['episodic'].append(entity_context)
        
        # 4. Consolidate context for generation
        context_parts = []
        
        # Add recent context
        if results['short_term']:
            context_parts.append("Recent context:")
            for item in results['short_term']:
                context_parts.append(f"- {item['content'][:200]}")
        
        # Add semantic results
        if results['long_term']:
            context_parts.append("\nRelevant information:")
            for item in results['long_term'][:3]:
                context_parts.append(f"- {item['content'][:300]}")
        
        # Add episodic relationships
        if results['episodic']:
            context_parts.append("\nRelated concepts:")
            for entity_ctx in results['episodic']:
                rels = entity_ctx['direct_relations'][:3]
                if rels:
                    context_parts.append(
                        f"- {entity_ctx['entity']} is related to: " +
                        ", ".join([r['entity'] for r in rels])
                    )
        
        results['consolidated_context'] = "\n".join(context_parts)
        
        return results
    
    def add_to_memory(self, content: str, embedding: List[float],
                      metadata: Optional[Dict] = None,
                      relationships: Optional[List[Tuple[str, str, str]]] = None):
        """
        Add content to appropriate memory layers
        """
        # Add to short-term (always)
        stm_id = self.short_term.add(content, metadata)
        
        # Add to long-term (if significant)
        if metadata and metadata.get('significant', False):
            entry = MemoryEntry(
                id=stm_id,
                content=content,
                metadata=metadata
            )
            self.long_term.add(entry, embedding)
        
        # Add relationships to episodic memory
        if relationships:
            for source, target, rel_type in relationships:
                self.episodic.add_relationship(
                    source, target, rel_type,
                    metadata={'content_id': stm_id}
                )
    
    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        return {
            'short_term': {
                'entries': len(self.short_term.entries),
                'max_entries': self.short_term.max_entries
            },
            'long_term': {
                'entries': len(self.long_term.entries),
                'indexed_words': len(self.long_term.index)
            },
            'episodic': {
                'entities': len(self.episodic.entities),
                'relationships': len(self.episodic.relationships)
            }
        }


if __name__ == '__main__':
    # Demo
    rag = MemoryAugmentedRAG()
    
    # Add some test data
    test_embedding = [0.1] * 384
    rag.add_to_memory(
        "Docker is a containerization platform",
        test_embedding,
        {'significant': True},
        [('Docker', 'containerization', 'is_a'), ('Docker', 'platform', 'is_a')]
    )
    
    # Query
    results = rag.process_query("What is Docker?", test_embedding)
    print(json.dumps(results, indent=2))
