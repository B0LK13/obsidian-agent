"""Natural language query engine with RAG pipeline."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    async def complete(self, prompt: str, **kwargs) -> str: ...
    async def chat(self, messages: list[dict], **kwargs) -> str: ...


class QueryIntent(str, Enum):
    SEARCH = "search"
    SUMMARIZE = "summarize"
    COMPARE = "compare"
    EXPLAIN = "explain"
    CREATE = "create"
    ANSWER = "answer"


@dataclass
class QueryContext:
    """Context for a query, including retrieved documents."""
    query: str
    intent: QueryIntent
    retrieved_docs: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Result of a natural language query."""
    query: str
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    intent: QueryIntent = QueryIntent.ANSWER
    suggestions: list[str] = field(default_factory=list)


class QueryEngine:
    """Natural language query engine using RAG."""
    
    def __init__(self, search_service, llm_provider: LLMProvider | None = None):
        self.search_service = search_service
        self.llm = llm_provider
        self._system_prompt = """You are an AI assistant helping with an Obsidian knowledge base.
Answer questions based on the provided context from the user's notes.
Be concise but comprehensive. If the context doesn't contain enough information, say so.
Always cite which notes your answer is based on."""
    
    async def query(self, question: str, limit: int = 5) -> QueryResult:
        """Process a natural language query."""
        intent = self._detect_intent(question)
        context = await self._build_context(question, intent, limit)
        
        if self.llm is None:
            return self._fallback_response(context)
        
        answer = await self._generate_answer(context)
        
        return QueryResult(
            query=question,
            answer=answer,
            sources=[{"id": d.get("id"), "title": d.get("title")} for d in context.retrieved_docs],
            confidence=self._calculate_confidence(context),
            intent=intent,
            suggestions=self._generate_suggestions(context),
        )
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the intent of a query."""
        query_lower = query.lower()
        if any(w in query_lower for w in ["summarize", "summary", "tldr"]):
            return QueryIntent.SUMMARIZE
        if any(w in query_lower for w in ["compare", "difference", "vs"]):
            return QueryIntent.COMPARE
        if any(w in query_lower for w in ["explain", "how", "why"]):
            return QueryIntent.EXPLAIN
        if any(w in query_lower for w in ["create", "write", "draft"]):
            return QueryIntent.CREATE
        if any(w in query_lower for w in ["find", "search", "where"]):
            return QueryIntent.SEARCH
        return QueryIntent.ANSWER
    
    async def _build_context(self, query: str, intent: QueryIntent, limit: int) -> QueryContext:
        """Build context by retrieving relevant documents."""
        results = await self.search_service.search(query=query, limit=limit)
        return QueryContext(query=query, intent=intent, retrieved_docs=results)
    
    async def _generate_answer(self, context: QueryContext) -> str:
        """Generate an answer using the LLM."""
        docs_text = "\n\n".join([
            f"[{d.get('title', 'Untitled')}]\n{d.get('content', d.get('snippet', ''))[:1000]}"
            for d in context.retrieved_docs
        ])
        
        prompt = f"""Based on the following notes from the knowledge base:

{docs_text}

Question: {context.query}

Please provide a helpful answer based on the above context."""
        
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        return await self.llm.chat(messages)
    
    def _fallback_response(self, context: QueryContext) -> QueryResult:
        """Generate a fallback response when no LLM is available."""
        if not context.retrieved_docs:
            answer = "No relevant notes found for your query."
        else:
            titles = [d.get("title", "Untitled") for d in context.retrieved_docs[:3]]
            answer = f"Found {len(context.retrieved_docs)} relevant notes: {', '.join(titles)}"
        
        return QueryResult(
            query=context.query,
            answer=answer,
            sources=[{"id": d.get("id"), "title": d.get("title")} for d in context.retrieved_docs],
            intent=context.intent,
        )
    
    def _calculate_confidence(self, context: QueryContext) -> float:
        """Calculate confidence score based on retrieved documents."""
        if not context.retrieved_docs:
            return 0.0
        avg_score = sum(d.get("score", 0) for d in context.retrieved_docs) / len(context.retrieved_docs)
        return min(avg_score * 1.2, 1.0)
    
    def _generate_suggestions(self, context: QueryContext) -> list[str]:
        """Generate follow-up question suggestions."""
        suggestions = []
        if context.retrieved_docs:
            first_doc = context.retrieved_docs[0]
            if first_doc.get("tags"):
                suggestions.append(f"Tell me more about #{first_doc['tags'][0]}")
            suggestions.append(f"Summarize {first_doc.get('title', 'this note')}")
        return suggestions[:3]
