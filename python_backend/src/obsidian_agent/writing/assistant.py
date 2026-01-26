"""AI-powered writing assistant for note creation and improvement."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    async def complete(self, prompt: str, **kwargs) -> str: ...
    async def chat(self, messages: list[dict], **kwargs) -> str: ...


class SuggestionType(str, Enum):
    CONTINUATION = "continuation"
    IMPROVEMENT = "improvement"
    EXPANSION = "expansion"
    SUMMARY = "summary"
    OUTLINE = "outline"
    QUESTION = "question"


@dataclass
class WritingSuggestion:
    """A writing suggestion from the assistant."""
    suggestion_type: SuggestionType
    content: str
    confidence: float = 0.0
    context: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class WritingAssistant:
    """AI-powered writing assistant for Obsidian notes."""
    
    def __init__(self, llm_provider: LLMProvider | None = None, search_service=None):
        self.llm = llm_provider
        self.search = search_service
        self._prompts = {
            SuggestionType.CONTINUATION: "Continue writing the following note naturally:",
            SuggestionType.IMPROVEMENT: "Improve the clarity and flow of this text:",
            SuggestionType.EXPANSION: "Expand on the following ideas with more detail:",
            SuggestionType.SUMMARY: "Summarize the key points of this note:",
            SuggestionType.OUTLINE: "Create an outline for a note about:",
            SuggestionType.QUESTION: "Generate thought-provoking questions about:",
        }
    
    async def suggest(self, text: str, suggestion_type: SuggestionType, context: str = "") -> WritingSuggestion:
        """Generate a writing suggestion."""
        if self.llm is None:
            return self._fallback_suggestion(text, suggestion_type)
        
        prompt = self._build_prompt(text, suggestion_type, context)
        response = await self.llm.complete(prompt)
        
        return WritingSuggestion(
            suggestion_type=suggestion_type,
            content=response,
            confidence=0.8,
            context=context,
        )
    
    async def continue_writing(self, text: str, max_tokens: int = 200) -> str:
        """Continue writing from the given text."""
        suggestion = await self.suggest(text, SuggestionType.CONTINUATION)
        return suggestion.content
    
    async def improve_text(self, text: str) -> str:
        """Improve the given text."""
        suggestion = await self.suggest(text, SuggestionType.IMPROVEMENT)
        return suggestion.content
    
    async def expand_ideas(self, text: str) -> str:
        """Expand on the ideas in the text."""
        suggestion = await self.suggest(text, SuggestionType.EXPANSION)
        return suggestion.content
    
    async def generate_outline(self, topic: str) -> list[str]:
        """Generate an outline for a topic."""
        suggestion = await self.suggest(topic, SuggestionType.OUTLINE)
        lines = suggestion.content.strip().split("\n")
        return [line.strip() for line in lines if line.strip()]
    
    async def generate_questions(self, text: str, count: int = 5) -> list[str]:
        """Generate questions about the text."""
        suggestion = await self.suggest(text, SuggestionType.QUESTION)
        lines = suggestion.content.strip().split("\n")
        questions = [line.strip() for line in lines if line.strip() and "?" in line]
        return questions[:count]
    
    async def suggest_related_notes(self, text: str, limit: int = 5) -> list[dict]:
        """Suggest related notes based on content."""
        if self.search is None:
            return []
        results = await self.search.search(query=text[:500], limit=limit)
        return results
    
    async def auto_complete(self, text: str, cursor_position: int) -> list[str]:
        """Provide auto-completion suggestions at cursor position."""
        context = text[:cursor_position]
        last_line = context.split("\n")[-1] if context else ""
        
        if last_line.startswith("[["):
            return await self._suggest_links(last_line[2:])
        elif last_line.startswith("#"):
            return await self._suggest_tags(last_line[1:])
        else:
            suggestion = await self.suggest(context, SuggestionType.CONTINUATION)
            return [suggestion.content[:100]]
    
    async def _suggest_links(self, partial: str) -> list[str]:
        """Suggest note links."""
        if self.search is None:
            return []
        results = await self.search.search(query=partial, limit=5)
        return [f"[[{r.get('title', '')}]]" for r in results]
    
    async def _suggest_tags(self, partial: str) -> list[str]:
        """Suggest tags."""
        return [f"#{partial}"]
    
    def _build_prompt(self, text: str, suggestion_type: SuggestionType, context: str) -> str:
        base_prompt = self._prompts.get(suggestion_type, "")
        full_prompt = f"{base_prompt}\n\n{text}"
        if context:
            full_prompt = f"Context: {context}\n\n{full_prompt}"
        return full_prompt
    
    def _fallback_suggestion(self, text: str, suggestion_type: SuggestionType) -> WritingSuggestion:
        fallback_content = {
            SuggestionType.CONTINUATION: "...",
            SuggestionType.IMPROVEMENT: text,
            SuggestionType.EXPANSION: f"{text}\n\n[Expand with more details here]",
            SuggestionType.SUMMARY: f"Summary of: {text[:50]}...",
            SuggestionType.OUTLINE: "1. Introduction\n2. Main Points\n3. Conclusion",
            SuggestionType.QUESTION: "What are the key takeaways?\nHow does this relate to other topics?",
        }
        return WritingSuggestion(
            suggestion_type=suggestion_type,
            content=fallback_content.get(suggestion_type, ""),
            confidence=0.0,
        )
