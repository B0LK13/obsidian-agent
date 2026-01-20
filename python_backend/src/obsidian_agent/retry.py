"""Retry mechanism with exponential backoff"""

import asyncio
import logging
import random
from functools import wraps
from typing import Callable, Tuple, Type, TypeVar

from .errors import ObsidianAgentError

T = TypeVar('T')
logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


async def retry_async(
    func: Callable,
    config: RetryConfig = None,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    dont_retry_on: Tuple[Type[Exception], ...] = ()
) -> T:
    """Retry an async function with exponential backoff"""
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func()
        except dont_retry_on:
            raise
        except retry_on as e:
            last_exception = e
            
            if isinstance(e, ObsidianAgentError) and not e.recoverable:
                logger.error(f"Non-recoverable error: {e}")
                raise
            
            if attempt == config.max_attempts - 1:
                logger.error(f"All {config.max_attempts} retry attempts failed")
                raise
            
            delay = min(
                config.initial_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            if config.jitter:
                delay = delay * (0.5 + random.random())
            
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            await asyncio.sleep(delay)
    
    raise last_exception


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    dont_retry_on: Tuple[Type[Exception], ...] = ()
):
    """Decorator for automatic retry with exponential backoff"""
    config = RetryConfig(max_attempts=max_attempts, initial_delay=initial_delay)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                lambda: func(*args, **kwargs),
                config=config,
                retry_on=retry_on,
                dont_retry_on=dont_retry_on
            )
        return wrapper
    return decorator
