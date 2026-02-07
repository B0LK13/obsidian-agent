"""OpenAI LLM provider."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from pkm_agent.llm.base import LLMProvider, LLMResponse, Message, ToolCall, Usage

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self._model = model
        self.api_key = api_key
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                import openai

                kwargs = {}
                if self.api_key:
                    kwargs["api_key"] = self.api_key
                if self.base_url:
                    kwargs["base_url"] = self.base_url

                self._client = openai.AsyncOpenAI(**kwargs)
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")

        return self._client

    @property
    def name(self) -> str:
        return "openai"

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
        """Generate a response using OpenAI API."""
        client = self._get_client()

        # Convert messages to dict format
        msg_dicts = [m.to_dict() for m in messages]

        # Build request parameters
        params = {
            "model": self._model,
            "messages": msg_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        params.update(kwargs)

        try:
            response = await client.chat.completions.create(**params)

            # Parse response
            choice = response.choices[0]
            content = choice.message.content or ""

            # Parse tool calls
            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    tool_calls.append(ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    ))

            return LLMResponse(
                content=content,
                model=response.model,
                usage=Usage(
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                ),
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
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
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        params.update(kwargs)

        try:
            stream = await client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
