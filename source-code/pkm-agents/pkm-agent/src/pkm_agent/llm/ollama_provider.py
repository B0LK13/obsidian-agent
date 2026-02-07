"""Ollama LLM provider."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from pkm_agent.llm.base import LLMProvider, LLMResponse, Message, ToolCall, Usage

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama API provider for local LLMs."""

    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """Lazy load Ollama client."""
        if self._client is None:
            try:
                import ollama

                self._client = ollama.AsyncClient(host=self.base_url)
            except ImportError:
                raise ImportError("ollama package not installed. Install with: pip install ollama")

        return self._client

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

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

        # Convert messages to dict format
        msg_dicts = [m.to_dict() for m in messages]

        # Build request parameters
        params = {
            "model": self._model,
            "messages": msg_dicts,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        if tools:
            params["tools"] = tools

        params.update(kwargs)

        try:
            response = await client.chat(**params)

            # Parse response
            content = response.get("message", {}).get("content", "")

            # Parse tool calls (if supported by Ollama)
            tool_calls = []
            if "tool_calls" in response.get("message", {}):
                for tc in response["message"]["tool_calls"]:
                    try:
                        args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}

                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        name=tc.get("function", {}).get("name", ""),
                        arguments=args,
                    ))

            # Extract usage information if available
            usage = Usage()
            if "eval_count" in response:
                usage.completion_tokens = response.get("eval_count", 0)
            if "prompt_eval_count" in response:
                usage.prompt_tokens = response.get("prompt_eval_count", 0)
            usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

            return LLMResponse(
                content=content,
                model=self._model,
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=response.get("done_reason", "stop"),
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

        params = {
            "model": self._model,
            "messages": msg_dicts,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }

        params.update(kwargs)

        try:
            stream = await client.chat(**params)
            async for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
