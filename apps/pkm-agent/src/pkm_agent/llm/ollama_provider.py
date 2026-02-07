"""Ollama LLM provider for local models."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from pkm_agent.llm.base import LLMProvider, LLMResponse, Message, Usage

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """Lazy load Ollama client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
            except ImportError:
                raise ImportError("httpx package not installed. Install with: pip install httpx")
        return self._client

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_tools(self) -> bool:
        return False

    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response using Ollama API."""
        client = self._get_client()

        msg_dicts = [m.to_dict() for m in messages]

        payload = {
            "model": self._model,
            "messages": msg_dicts,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            content = data.get("message", {}).get("content", "")

            return LLMResponse(
                content=content,
                model=self._model,
                usage=Usage(
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                ),
                finish_reason="stop",
            )

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate a streaming response."""
        client = self._get_client()

        msg_dicts = [m.to_dict() for m in messages]

        payload = {
            "model": self._model,
            "messages": msg_dicts,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
