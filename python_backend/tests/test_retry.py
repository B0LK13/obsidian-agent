"""Tests for retry mechanism"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from obsidian_agent.retry import RetryConfig, retry_async, retry
from obsidian_agent.errors import ObsidianAgentError


class TestRetryConfig:
    def test_default_values(self):
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_values(self):
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.jitter is False


class TestRetryAsync:
    @pytest.mark.asyncio
    async def test_successful_call(self):
        call_count = 0

        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(successful_func)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Failed")
            return "success"

        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        result = await retry_async(fail_then_succeed, config=config)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        async def always_fail():
            raise ValueError("Always fails")

        config = RetryConfig(max_attempts=2, initial_delay=0.01, jitter=False)
        with pytest.raises(ValueError):
            await retry_async(always_fail, config=config)

    @pytest.mark.asyncio
    async def test_dont_retry_on_specific_exception(self):
        call_count = 0

        async def raise_key_error():
            nonlocal call_count
            call_count += 1
            raise KeyError("Not found")

        config = RetryConfig(max_attempts=3, jx­‰©}‘•±…äôÀ¸ÀÄ¤(€€€€€€€Ý¥Ñ ÁåÑ•ÍÐ¹á™…¥±•Ì¡-•åÉÉ½È¤è(€€€€€€€€€€€…Ý…¥ÐÉ•ÑÉå}…Íå¹Œ (€€€€€€€€€€€€€€€É…¥Í•}­•å}•ÉÉ½È°(€€€€€€€€€€€€€€€½¹™¥œõ½¹™¥œ°(€€€€€€€€€€€€€€€‘½¹Ñ}É•ÑÉå}½¸ô¡-•åÉÉ½È°¤°(€€€€€€€€€€€€¤(()±…ÍÌQ•ÍÑI•ÑÉå•½É…Ñ½Èè(€€€ÁåÑ•ÍÐ¹µ…É¬¹…Íå¹¥¼(€€€…Íå¹Œ‘•˜Ñ•ÍÑ}‘•½É…Ñ½É}ÍÕ•ÍÌ¡Í•±˜¤è(€€€€€€€É•ÑÉä¡µ…á}…ÑÑ•µÁÑÌôÈ¤(€€€€€€€…Íå¹Œ‘•˜ÍÕ••‘¥¹}™Õ¹Œ ¤è(€€€€€€€€€€€É•ÑÕÉ¸€‰½¬ˆ((€€€€€€€É•ÍÕ±Ð€ô…Ý…¥ÐÍÕ••‘¥¹}™Õ¹Œ ¤(€€€€€€€…ÍÍ•ÉÐÉ•ÍÕ±Ð€ôô€‰½¬ˆ((€€€ÁåÑ•ÍÐ¹µ…É¬¹…Íå¹¥¼(€€€…Íå¹Œ‘•˜Ñ•ÍÑ}‘•½É…Ñ½É}Ý¥Ñ¡}…ÉÕµ•¹ÑÌ¡Í•±˜¤è(€€€€€€€É•ÑÉä¡µ…á}…ÑÑ•µÁÑÌôÌ°¥¹¥Ñ¥…±}‘•±…äôÀ¸ÀÄ¤(€€€€€€€…Íå¹Œ‘•˜™Õ¹}Ý¥Ñ¡}…ÉÌ¡„°ˆôÄ¤è(€€€€€€€€€€€É•ÑÕÉ¸„€¬ˆ((€€€€€€€É•ÍÕ±Ð€ô…Ý…¥Ð™Õ¹}Ý¥Ñ¡}…ÉÌ È°ˆôÌ¤(€€€€€€€…ÍÍ•ÉÐÉ•ÍÕ±Ð€ôô€Ô