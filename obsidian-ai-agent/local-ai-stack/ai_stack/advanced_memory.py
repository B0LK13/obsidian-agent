#!/usr/bin/env python3
"""
Advanced Memory System
Features:
- Hierarchical memory (working, episodic, semantic)
- Memory compression and summarization
- Knowledge graph integration
- Temporal reasoning
- Importance scoring
- Memory decay and reinforcement
"""

import json
import logging
import hashlib
import time
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import heapq
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('advanced_memory')


@dataclass
class MemoryItem:
    """A single memory item"""
    id: str
    content: str
    memory_type: str  # working, episodic, semantic
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 1.0  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    embeddings: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    decay_factor: float = 0.95  # How fast importance decays
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'memory_type': self.memory_type,
            'timestamp': self.timestamp.isoformat(),
            'importance': self.importance,
            'access_count': self.access_count,
            'tags': list(self.tags),
            'metadata': self.metadata
        }
    
    def calculate_retrievability(self) -> float:
        """
        Calculate how retrievable this memory is
        Based on: importance, recency, frequency of access
        """
        # Time decay
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        time_decay = self.decay_factor ** age_hours
        
        # Recency boost
        hours_since_access = (datetime.now() - self.last_accessed).total_seconds() / 3600
        recency_boost = 1.0 / (1.0 + hours_since_access / 24)  # Decay over days
        
        # Frequency boost
        frequency_boost = min(1.0, self.access_count / 10)
        
        # Combined score
        retrievability = (
            self.importance * 0.4 +
            time_decay * 0.2 +
            recency_boost * 0.2 +
            frequency_boost * 0.2
        )
        
        return retrievability
    
    def access(self):
        """Record an access to this memory"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        # Slightly increase importance on access
        self.importance = min(1.0, self.importance + 0.05)


class KnowledgeGraph:
    """
    Graph-based knowledge representation
    Nodes: entities/concepts
    Edges: relationships
    """
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # entity -> properties
        self.edges: List[Dict] = []  # (source, relation, target, strength)
        self.node_embeddings: Dict[str, List[float]] = {}
    
    def add_entity(self, entity: str, entity_type: str = "concept", 
                   properties: Dict = None):
        """Add an entity to the graph"""
        if entity not in self.nodes:
            self.nodes[entity] = {
                'type': entity_type,
                'properties': properties or {},
                'first_seen': datetime.now().isoformat(),
                'mentions': 0
            }
        self.nodes[entity]['mentions'] += 1
        self.nodes[entity]['last_seen'] = datetime.now().isoformat()
    
    def add_relation(self, source: str, relation: str, target: str, 
                     strength: float = 1.0, bidirectional: bool = False):
        """Add a relationship between entities"""
        # Ensure entities exist
        self.add_entity(source)
        self.add_entity(target)
        
        edge = {
            'source': source,
            'relation': relation,
            'target': target,
            'strength': strength,
            'timestamp': datetime.now().isoformat()
        }
        self.edges.append(edge)
        
        if bidirectional:
            self.edges.append({
                'source': target,
                'relation': f"reverse_{relation}",
                'target': source,
                'strength': strength,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_related(self, entity: str, relation_type: Optional[str] = None,
                    min_strength: float = 0.0) -> List[Tuple[str, str, float]]:
        """Get entities related to given entity"""
        related = []
        
        for edge in self.edges:
            if edge['strength'] < min_strength:
                continue
            
            if relation_type and edge['relation'] != relation_type:
                continue
            
            if edge['source'] == entity:
                related.append((edge['target'], edge['relation'], edge['strength']))
            elif edge['target'] == entity:
                related.append((edge['source'], edge['relation'], edge['strength']))
        
        # Sort by strength
        related.sort(key=lambda x: x[2], reverse=True)
        return related
    
    def find_path(self, start: str, end: str, max_depth: int = 3) -> Optional[List[str]]:
        """Find path between two entities using BFS"""
        if start not in self.nodes or end not in self.nodes:
            return None
        
        visited = {start}
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end:
                return path
            
            if len(path) >= max_depth:
                continue
            
            # Get neighbors
            for edge in self.edges:
                if edge['source'] == current:
                    neighbor = edge['target']
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def get_subgraph(self, center: str, depth: int = 2) -> Dict:
        """Get subgraph around a center entity"""
        nodes = {center}
        edges_in_subgraph = []
        
        current_depth = 0
        frontier = {center}
        
        while current_depth < depth and frontier:
            new_frontier = set()
            
            for entity in frontier:
                for edge in self.edges:
                    if edge['source'] == entity and edge['target'] not in nodes:
                        nodes.add(edge['target'])
                        new_frontier.add(edge['target'])
                        edges_in_subgraph.append(edge)
                    elif edge['target'] == entity and edge['source'] not in nodes:
                        nodes.add(edge['source'])
                        new_frontier.add(edge['source'])
                        edges_in_subgraph.append(edge)
            
            frontier = new_frontier
            current_depth += 1
        
        return {
            'nodes': list(nodes),
            'edges': edges_in_subgraph,
            'center': center,
            'depth': depth
        }
    
    def extract_from_text(self, text: str):
        """Extract entities and relations from text"""
        # Simple pattern-based extraction
        # Entities: Capitalized phrases
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        for entity in entities:
            self.add_entity(entity, "named_entity")
        
        # Relations: "X is a Y", "X has Y", etc.
        is_a_pattern = r'(\w+)\s+is\s+(?:a|an)\s+(\w+)'
        for match in re.finditer(is_a_pattern, text, re.IGNORECASE):
            source, target = match.groups()
            self.add_relation(source, "is_a", target)
        
        has_pattern = r'(\w+)\s+has\s+(?:a|an)?\s*(\w+)'
        for match in re.finditer(has_pattern, text, re.IGNORECASE):
            source, target = match.groups()
            self.add_relation(source, "has", target)
    
    def query(self, query_type: str, **kwargs) -> Any:
        """Query the knowledge graph"""
        if query_type == "entity":
            entity = kwargs.get('entity')
            return self.nodes.get(entity)
        
        elif query_type == "relations":
            entity = kwargs.get('entity')
            return self.get_related(entity)
        
        elif query_type == "path":
            start = kwargs.get('start')
            end = kwargs.get('end')
            return self.find_path(start, end)
        
        elif query_type == "subgraph":
            center = kwargs.get('center')
            depth = kwargs.get('depth', 2)
            return self.get_subgraph(center, depth)
        
        return None


class MemoryCompressor:
    """
    Compress memories to save space and improve retrieval
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    def summarize(self, memories: List[MemoryItem], max_length: int = 200) -> str:
        """Summarize a list of memories"""
        if not memories:
            return ""
        
        # Combine memories
        combined_text = "\n\n".join([m.content for m in memories])
        
        if len(combined_text) <= max_length:
            return combined_text
        
        # Use LLM if available
        if self.llm:
            prompt = f"Summarize the following memories in {max_length} characters:\n\n{combined_text}"
            return self.llm.chat([{"role": "user", "content": prompt}])
        
        # Simple extraction-based summarization
        return self._extractive_summarize(combined_text, max_length)
    
    def _extractive_summarize(self, text: str, max_length: int) -> str:
        """Simple extractive summarization"""
        sentences = re.split(r'[.!?]+', text)
        
        # Score sentences by word frequency
        word_freq = defaultdict(int)
        for sentence in sentences:
            for word in sentence.lower().split():
                if len(word) > 3:
                    word_freq[word] += 1
        
        sentence_scores = []
        for sentence in sentences:
            score = sum(word_freq[w.lower()] for w in sentence.split() if len(w) > 3)
            sentence_scores.append((sentence.strip(), score))
        
        # Select top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        summary = ""
        for sentence, _ in sentence_scores:
            if len(summary) + len(sentence) < max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip()
    
    def compress_episodic_memories(self, memories: List[MemoryItem],
                                    time_window: timedelta = timedelta(hours=1)) -> List[MemoryItem]:
        """
        Compress episodic memories within a time window into a single summary memory
        """
        if len(memories) < 2:
            return memories
        
        # Group by time window
        groups = []
        current_group = [memories[0]]
        
        for memory in memories[1:]:
            if memory.timestamp - current_group[-1].timestamp <= time_window:
                current_group.append(memory)
            else:
                groups.append(current_group)
                current_group = [memory]
        
        if current_group:
            groups.append(current_group)
        
        # Compress each group
        compressed = []
        for group in groups:
            if len(group) == 1:
                compressed.append(group[0])
            else:
                summary_content = self.summarize(group)
                summary_memory = MemoryItem(
                    id=f"summary_{group[0].id}",
                    content=summary_content,
                    memory_type="episodic_summary",
                    timestamp=group[0].timestamp,
                    importance=max(m.importance for m in group),
                    metadata={
                        'summarized_count': len(group),
                        'original_ids': [m.id for m in group]
                    }
                )
                compressed.append(summary_memory)
        
        return compressed


class AdvancedMemorySystem:
    """
    Complete memory system combining all components
    """
    
    def __init__(self, data_path: str = "./data", llm_client=None):
        self.data_path = data_path
        self.llm = llm_client
        
        # Memory stores
        self.working_memory: Dict[str, MemoryItem] = {}
        self.episodic_memory: Dict[str, MemoryItem] = {}
        self.semantic_memory: Dict[str, MemoryItem] = {}
        
        # Knowledge graph
        self.kg = KnowledgeGraph()
        
        # Compressor
        self.compressor = MemoryCompressor(llm_client)
        
        # Configuration
        self.max_working_memory = 10
        self.episodic_compression_threshold = 50
        
        logger.info("Advanced Memory System initialized")
    
    def store(self, content: str, memory_type: str = "episodic",
              importance: float = 1.0, metadata: Dict = None,
              tags: Set[str] = None) -> str:
        """
        Store a new memory
        """
        # Generate ID
        memory_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        
        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {},
            tags=tags or set()
        )
        
        # Store in appropriate memory type
        if memory_type == "working":
            self._store_working(memory)
        elif memory_type == "episodic":
            self.episodic_memory[memory_id] = memory
        elif memory_type == "semantic":
            self.semantic_memory[memory_id] = memory
        
        # Extract to knowledge graph
        self.kg.extract_from_text(content)
        
        # Check if compression needed
        if len(self.episodic_memory) > self.episodic_compression_threshold:
            self._compress_episodic()
        
        return memory_id
    
    def _store_working(self, memory: MemoryItem):
        """Store in working memory with capacity limit"""
        if len(self.working_memory) >= self.max_working_memory:
            # Remove least important
            least_important = min(self.working_memory.values(), 
                                  key=lambda m: m.calculate_retrievability())
            # Move to episodic
            least_important.memory_type = "episodic"
            self.episodic_memory[least_important.id] = least_important
            del self.working_memory[least_important.id]
        
        self.working_memory[memory.id] = memory
    
    def retrieve(self, query: str, query_embedding: Optional[List[float]] = None,
                 memory_types: List[str] = None, top_k: int = 5) -> List[MemoryItem]:
        """
        Retrieve relevant memories
        """
        memory_types = memory_types or ["working", "episodic", "semantic"]
        
        candidates = []
        
        # Collect from specified memory types
        if "working" in memory_types:
            candidates.extend(self.working_memory.values())
        if "episodic" in memory_types:
            candidates.extend(self.episodic_memory.values())
        if "semantic" in memory_types:
            candidates.extend(self.semantic_memory.values())
        
        # Score each memory
        scored = []
        for memory in candidates:
            score = memory.calculate_retrievability()
            
            # Boost for keyword match
            if any(word in memory.content.lower() for word in query.lower().split()):
                score += 0.2
            
            scored.append((memory, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Access top memories
        top_memories = []
        for memory, score in scored[:top_k]:
            memory.access()
            top_memories.append(memory)
        
        return top_memories
    
    def get_context_window(self, max_items: int = 5) -> str:
        """Get recent working memory as context"""
        recent = sorted(self.working_memory.values(), 
                       key=lambda m: m.last_accessed, reverse=True)[:max_items]
        
        return "\n\n".join([f"- {m.content}" for m in recent])
    
    def _compress_episodic(self):
        """Compress episodic memories"""
        logger.info("Compressing episodic memories...")
        
        memories = list(self.episodic_memory.values())
        compressed = self.compressor.compress_episodic_memories(memories)
        
        # Replace with compressed
        self.episodic_memory = {m.id: m for m in compressed}
        
        logger.info(f"Compressed {len(memories)} memories into {len(compressed)}")
    
    def query_knowledge_graph(self, query_type: str, **kwargs) -> Any:
        """Query the knowledge graph"""
        return self.kg.query(query_type, **kwargs)
    
    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        return {
            'working_memory': {
                'count': len(self.working_memory),
                'capacity': self.max_working_memory
            },
            'episodic_memory': {
                'count': len(self.episodic_memory),
                'compression_threshold': self.episodic_compression_threshold
            },
            'semantic_memory': {
                'count': len(self.semantic_memory)
            },
            'knowledge_graph': {
                'entities': len(self.kg.nodes),
                'relations': len(self.kg.edges)
            }
        }


# Example usage
if __name__ == '__main__':
    memory = AdvancedMemorySystem()
    
    # Store some memories
    memory.store("Met with Alice to discuss the project", "episodic", importance=0.8)
    memory.store("The project deadline is next Friday", "semantic", importance=0.9)
    memory.store("Need to review the documentation", "working", importance=0.7)
    
    # Retrieve
    results = memory.retrieve("project deadline")
    print("Retrieved memories:")
    for m in results:
        print(f"  - {m.content} (importance: {m.importance})")
    
    # Query knowledge graph
    print("\nKnowledge Graph Stats:", memory.get_stats())
