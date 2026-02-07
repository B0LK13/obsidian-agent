"""
LLM Client for AgentZero orchestrator.

This module provides a client for interacting with LLM providers
like OpenAI and Ollama.
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMConnectionError(LLMClientError):
    """Connection error."""
    pass


class LLMResponseError(LLMClientError):
    """Error response from LLM provider."""
    pass


class BaseLLMProvider:
    """Base LLM provider."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate a response."""
        raise NotImplementedError

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate a streaming response."""
        raise NotImplementedError


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self):
        """Initialize the OpenAI client."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("OpenAI LLM provider initialized")

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> str:
        """Generate a response using OpenAI API."""
        if not self.session:
            await self.initialize()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMResponseError(f"OpenAI API error: {error_text}")

                data = await response.json()
                return data["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error: {e}")

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate a streaming response using OpenAI API."""
        if not self.session:
            await self.initialize()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": True
        }

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMResponseError(f"OpenAI API error: {error_text}")

                async for line in response.content:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data == '[DONE]':
                            break

                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error: {e}")


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self):
        """Initialize the Ollama client."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=120)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("Ollama LLM provider initialized")

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> str:
        """Generate a response using Ollama API."""
        if not self.session:
            await self.initialize()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens)
            }
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMResponseError(f"Ollama API error: {error_text}")

                data = await response.json()
                return data.get("message", {}).get("content", "")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error: {e}")

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Ollama API."""
        if not self.session:
            await self.initialize()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens)
            }
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMResponseError(f"Ollama API error: {error_text}")

                async for line in response.content:
                    line_text = line.decode('utf-8').strip()
                    if line_text:
                        try:
                            data = json.loads(line_text)
                            if 'done' in data:
                                if data.get('done'):
                                    break
                                else:
                                    content = data.get('message', {}).get('content', '')
                                    if content:
                                        yield content
                        except json.JSONDecodeError:
                            continue
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error: {e}")


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        provider_type = config.get("provider", "openai").lower()

        if provider_type == "openai":
            self.provider = OpenAIProvider(config)
        elif provider_type == "ollama":
            self.provider = OllamaProvider(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_type}")

    async def initialize(self):
        """Initialize the LLM client."""
        if isinstance(self.provider, (OpenAIProvider, OllamaProvider)):
            await self.provider.initialize()

    async def cleanup(self):
        """Clean up resources."""
        if isinstance(self.provider, (OpenAIProvider, OllamaProvider)):
            await self.provider.cleanup()

    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate a response."""
        messages = [{"role": "user", "content": prompt}]
        return await self.provider.generate(messages, **kwargs)

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> str:
        """Generate a chat response."""
        return await self.provider.generate(messages, **kwargs)

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate a streaming response."""
        async for chunk in self.provider.generate_stream(messages, **kwargs):
            yield chunk


async def create_llm_client(config: dict[str, Any]) -> LLMClient:
    """Create and initialize an LLM client."""
    client = LLMClient(config)
    await client.initialize()
    return client
