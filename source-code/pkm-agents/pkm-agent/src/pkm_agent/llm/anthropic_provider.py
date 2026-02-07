"""Anthropic LLM Provider."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from pkm_agent.llm.base import LLMProvider, LLMResponse, Message, Role, ToolCall, Usage

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        model: str = "claude-3-opus-20240229",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package not found. Install with: pip install anthropic")

        self._model = model
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
        )

    @property
    def name(self) -> str:
        return "anthropic"

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
        """Generate response."""
        
        # Convert messages to Anthropic format
        system_prompt = ""
        anthropic_msgs = []
        
        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_prompt = msg.content
            else:
                anthropic_msgs.append({
                    "role": msg.role,
                    "content": msg.content
                })

        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": anthropic_msgs,
        }

        if tools:
            # Convert OpenAI-style tool defs to Anthropic format
            # OpenAI: {"type": "function", "function": {name, desc, params}}
            # Anthropic: {name, description, input_schema}
            anthropic_tools = []
            for t in tools:
                if t.get("type") == "function":
                    f = t["function"]
                    anthropic_tools.append({
                        "name": f["name"],
                        "description": f.get("description"),
                        "input_schema": f.get("parameters")
                    })
            params["tools"] = anthropic_tools

        response = await self.client.messages.create(**params)
        
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))
        
        return LLMResponse(
            content=content,
            model=response.model,
            usage=Usage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            ),
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "stop"
        )

    async def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate streaming response."""
        
        system_prompt = ""
        anthropic_msgs = []
        
        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_prompt = msg.content
            else:
                anthropic_msgs.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        async with self.client.messages.stream(
            max_tokens=max_tokens,
            messages=anthropic_msgs,
            model=self.model,
            system=system_prompt,
            temperature=temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text
