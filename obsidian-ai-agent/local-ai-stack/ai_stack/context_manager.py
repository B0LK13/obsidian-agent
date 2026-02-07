#!/usr/bin/env python3
"""
Context Management System
Optimizes token usage and manages context window efficiently:
- Sliding window with overlap
- Hierarchical summarization
- Token counting and budget management
- Priority-based context selection
- Dynamic context injection
"""

import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('context_manager')


class Tokenizer:
    """Simple tokenizer for counting tokens"""
    
    # Rough approximation: 1 token ≈ 4 characters for English
    CHARS_PER_TOKEN = 4
    
    @classmethod
    def count(cls, text: str) -> int:
        """Estimate token count"""
        return max(1, len(text) // cls.CHARS_PER_TOKEN)
    
    @classmethod
    def truncate(cls, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        max_chars = max_tokens * cls.CHARS_PER_TOKEN
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."


class ContextPriority(Enum):
    CRITICAL = 4    # System prompt, instructions
    HIGH = 3        # Recent conversation, key facts
    MEDIUM = 2      # Retrieved documents
    LOW = 1         # Older context, supplementary info


@dataclass
class ContextChunk:
    """A chunk of context with metadata"""
    content: str
    priority: ContextPriority
    source: str  # e.g., "system", "user", "retrieval", "summary"
    timestamp: float = field(default_factory=lambda: logging.time.time())
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = Tokenizer.count(self.content)


class SlidingWindowManager:
    """
    Manages sliding window of conversation history
    """
    
    def __init__(self, max_tokens: int = 4000, overlap_tokens: int = 200):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.chunks: List[ContextChunk] = []
        self.total_tokens = 0
    
    def add(self, content: str, source: str, priority: ContextPriority = ContextPriority.MEDIUM):
        """Add a new chunk to the window"""
        chunk = ContextChunk(
            content=content,
            priority=priority,
            source=source
        )
        
        self.chunks.append(chunk)
        self.total_tokens += chunk.token_count
        
        # Prune if over budget
        self._prune()
    
    def _prune(self):
        """Remove low-priority chunks to fit within token budget"""
        while self.total_tokens > self.max_tokens and len(self.chunks) > 1:
            # Find lowest priority chunk
            lowest_priority = min(self.chunks, key=lambda c: (c.priority.value, c.timestamp))
            
            # If it's critical, we have a problem
            if lowest_priority.priority == ContextPriority.CRITICAL:
                # Truncate instead of remove
                excess = self.total_tokens - self.max_tokens
                lowest_priority.content = Tokenizer.truncate(
                    lowest_priority.content, 
                    lowest_priority.token_count - excess
                )
                lowest_priority.token_count = Tokenizer.count(lowest_priority.content)
                break
            
            self.total_tokens -= lowest_priority.token_count
            self.chunks.remove(lowest_priority)
    
    def get_context(self) -> str:
        """Get current context as a single string"""
        # Sort by priority (high to low) then timestamp
        sorted_chunks = sorted(
            self.chunks,
            key=lambda c: (-c.priority.value, c.timestamp)
        )
        
        return "\n\n".join([c.content for c in sorted_chunks])
    
    def get_messages_format(self) -> List[Dict[str, str]]:
        """Get context in chat message format"""
        messages = []
        
        for chunk in self.chunks:
            role = chunk.metadata.get('role', 'system')
            messages.append({
                'role': role,
                'content': chunk.content
            })
        
        return messages


class HierarchicalSummarizer:
    """
    Hierarchical summarization for long documents
    - Level 0: Original chunks
    - Level 1: Summaries of chunks
    - Level 2: Summary of summaries
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.levels: Dict[int, List[ContextChunk]] = {}
    
    def add_document(self, doc_id: str, content: str, chunk_size: int = 1000):
        """Add a document and create hierarchical summary"""
        # Split into chunks
        chunks = self._split_into_chunks(content, chunk_size)
        
        level_0 = []
        for i, chunk_text in enumerate(chunks):
            chunk = ContextChunk(
                content=chunk_text,
                priority=ContextPriority.MEDIUM,
                source=f"doc:{doc_id}:chunk:{i}",
                metadata={'doc_id': doc_id, 'level': 0, 'chunk_idx': i}
            )
            level_0.append(chunk)
        
        self.levels[0] = level_0
        
        # Create higher levels
        self._build_hierarchy()
    
    def _split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks with sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _build_hierarchy(self):
        """Build summary hierarchy"""
        current_level = 0
        
        while len(self.levels.get(current_level, [])) > 1:
            current_chunks = self.levels[current_level]
            next_level_chunks = []
            
            # Group chunks and summarize
            group_size = 3  # Summarize 3 chunks at a time
            for i in range(0, len(current_chunks), group_size):
                group = current_chunks[i:i+group_size]
                combined = "\n\n".join([c.content for c in group])
                
                summary = self._summarize(combined, max_length=200)
                
                chunk = ContextChunk(
                    content=summary,
                    priority=ContextPriority(current_chunks[0].priority.value - 1),
                    source=f"summary:level:{current_level+1}:group:{i//group_size}",
                    metadata={
                        'level': current_level + 1,
                        'source_chunks': [c.metadata.get('chunk_idx', i) for c in group]
                    }
                )
                next_level_chunks.append(chunk)
            
            self.levels[current_level + 1] = next_level_chunks
            current_level += 1
    
    def _summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize text"""
        if self.llm:
            prompt = f"Summarize the following text in {max_length} characters:\n\n{text}"
            return self.llm.chat([{"role": "user", "content": prompt}])
        
        # Fallback: extract first and last sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 2:
            return text
        return sentences[0] + " " + sentences[-1]
    
    def get_summary_at_level(self, level: int) -> List[ContextChunk]:
        """Get all chunks at a specific summary level"""
        return self.levels.get(level, [])
    
    def get_adaptive_summary(self, token_budget: int) -> str:
        """
        Get best summary given token budget
        Uses higher level summaries if budget is tight
        """
        # Try levels from highest to lowest
        for level in sorted(self.levels.keys(), reverse=True):
            chunks = self.levels[level]
            total_tokens = sum(c.token_count for c in chunks)
            
            if total_tokens <= token_budget:
                return "\n\n".join([c.content for c in chunks])
        
        # If nothing fits, truncate highest level
        chunks = self.levels[max(self.levels.keys())]
        result = ""
        for chunk in chunks:
            if Tokenizer.count(result) + chunk.token_count <= token_budget:
                result += chunk.content + "\n\n"
            else:
                break
        
        return result.strip()


class ContextInjector:
    """
    Dynamically injects relevant context based on query
    """
    
    def __init__(self, retriever=None):
        self.retriever = retriever
        self.injection_rules: List[Dict] = []
    
    def add_rule(self, pattern: str, context: str, priority: ContextPriority = ContextPriority.HIGH):
        """Add an injection rule"""
        self.injection_rules.append({
            'pattern': re.compile(pattern, re.IGNORECASE),
            'context': context,
            'priority': priority
        })
    
    def inject(self, query: str, base_context: str, max_tokens: int = 1000) -> str:
        """
        Inject relevant context based on query
        """
        injected_contexts = []
        
        # Check rules
        for rule in self.injection_rules:
            if rule['pattern'].search(query):
                injected_contexts.append((rule['context'], rule['priority']))
        
        # Retrieve relevant context if retriever available
        if self.retriever:
            retrieved = self.retriever.retrieve(query, top_k=3)
            for item in retrieved:
                injected_contexts.append((item.content, ContextPriority.MEDIUM))
        
        # Sort by priority
        injected_contexts.sort(key=lambda x: x[1].value, reverse=True)
        
        # Build final context within token budget
        result_parts = []
        current_tokens = Tokenizer.count(base_context)
        
        for context, priority in injected_contexts:
            context_tokens = Tokenizer.count(context)
            if current_tokens + context_tokens <= max_tokens:
                result_parts.append(context)
                current_tokens += context_tokens
            else:
                break
        
        # Combine: injected context first, then base
        return "\n\n".join(result_parts + [base_context])


class SmartContextBuilder:
    """
    Intelligent context building for LLM requests
    Combines all context management techniques
    """
    
    def __init__(self, llm_client=None, max_context_tokens: int = 6000):
        self.llm = llm_client
        self.max_tokens = max_context_tokens
        
        self.sliding_window = SlidingWindowManager(
            max_tokens=max_context_tokens * 0.6,
            overlap_tokens=200
        )
        self.summarizer = HierarchicalSummarizer(llm_client)
        self.injector = ContextInjector()
        
        # Token budget allocation
        self.budget = {
            'system': int(max_context_tokens * 0.1),
            'conversation': int(max_context_tokens * 0.3),
            'retrieved': int(max_context_tokens * 0.4),
            'injected': int(max_context_tokens * 0.2)
        }
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt"""
        truncated = Tokenizer.truncate(prompt, self.budget['system'])
        self.sliding_window.add(
            truncated,
            source="system",
            priority=ContextPriority.CRITICAL,
        )
    
    def add_user_message(self, message: str):
        """Add user message to context"""
        chunk = ContextChunk(
            content=message,
            priority=ContextPriority.HIGH,
            source="user",
            metadata={'role': 'user'}
        )
        
        # Truncate if needed
        if chunk.token_count > self.budget['conversation'] // 4:
            chunk.content = Tokenizer.truncate(
                chunk.content, 
                self.budget['conversation'] // 4
            )
            chunk.token_count = Tokenizer.count(chunk.content)
        
        self.sliding_window.chunks.append(chunk)
        self.sliding_window.total_tokens += chunk.token_count
        self.sliding_window._prune()
    
    def add_retrieved_context(self, documents: List[Dict]):
        """Add retrieved documents to context"""
        for doc in documents:
            content = doc.get('content', '')
            source = doc.get('source', 'retrieval')
            
            chunk = ContextChunk(
                content=f"[{source}]\n{content}",
                priority=ContextPriority.MEDIUM,
                source=source,
                metadata={'doc_id': doc.get('id', 'unknown')}
            )
            
            self.sliding_window.chunks.append(chunk)
            self.sliding_window.total_tokens += chunk.token_count
        
        self.sliding_window._prune()
    
    def build_context(self, query: str = "") -> List[Dict[str, str]]:
        """
        Build final context for LLM
        Returns in chat message format
        """
        # Get base context from sliding window
        base_messages = self.sliding_window.get_messages_format()
        
        # Inject relevant context if query provided
        if query:
            user_content = base_messages[-1]['content'] if base_messages else ""
            enhanced_content = self.injector.inject(
                query, 
                user_content, 
                max_tokens=self.budget['injected']
            )
            if base_messages:
                base_messages[-1]['content'] = enhanced_content
        
        return base_messages
    
    def get_token_stats(self) -> Dict:
        """Get token usage statistics"""
        return {
            'total_budget': self.max_tokens,
            'used': self.sliding_window.total_tokens,
            'remaining': self.max_tokens - self.sliding_window.total_tokens,
            'budget_allocation': self.budget,
            'chunks': len(self.sliding_window.chunks)
        }


# Example usage
if __name__ == '__main__':
    # Mock LLM
    class MockLLM:
        def chat(self, messages):
            return "Summary of the text"
    
    llm = MockLLM()
    
    # Test context manager
    builder = SmartContextBuilder(llm, max_context_tokens=4000)
    
    # Set system prompt
    builder.set_system_prompt("You are a helpful assistant.")
    
    # Add conversation
    builder.add_user_message("Tell me about machine learning.")
    
    # Add retrieved context
    docs = [
        {'id': '1', 'content': 'ML is a subset of AI...', 'source': 'wiki'},
        {'id': '2', 'content': 'Deep learning uses neural networks...', 'source': 'article'}
    ]
    builder.add_retrieved_context(docs)
    
    # Build context
    context = builder.build_context("machine learning")
    
    print("Built Context:")
    for msg in context:
        print(f"[{msg['role']}] {msg['content'][:100]}...")
    
    print("\nToken Stats:", builder.get_token_stats())
