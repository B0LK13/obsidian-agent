"""
Error handling utilities and retry decorators.

Provides intelligent error handling with exponential backoff and user-friendly messages.
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pkm_agent.exceptions import (
    DatabaseError,
    NetworkError,
    PermanentError,
    PKMAgentError,
    RateLimitError,
    RetriableError,
)
from pkm_agent.exceptions import (
    TimeoutError as PKMTimeoutError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


def get_user_friendly_message(error: Exception) -> str:
    """
    Convert technical exceptions to user-friendly messages.

    Args:
        error: The exception to convert

    Returns:
        User-friendly error message
    """
    if isinstance(error, RateLimitError):
        retry_msg = f" Please wait {error.retry_after}s." if error.retry_after else ""
        return f"⚠️  API rate limit reached.{retry_msg} Consider upgrading your plan or waiting before retrying."

    if isinstance(error, PKMTimeoutError):
        return f"⏱️  Operation timed out after {error.context.get('timeout')}s. The server may be slow or unreachable."

    if isinstance(error, DatabaseError):
        op = error.context.get('operation', 'database operation')
        return f"💾 Database error during {op}. Your data may not have been saved. Please try again."

    if isinstance(error, NetworkError):
        return "🌐 Network connection error. Please check your internet connection and try again."

    if isinstance(error, PKMAgentError):
        # Generic PKM Agent error with context
        return f"❌ {error.message}"

    # Fallback for unknown errors
    return f"⚠️  An unexpected error occurred: {str(error)}"


def should_retry(exception: Exception) -> bool:
    """
    Determine if an exception should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the exception can be retried
    """
    if isinstance(exception, PermanentError):
        return False

    if isinstance(exception, RetriableError):
        return True

    # Retry common transient errors
    if isinstance(exception, (
        ConnectionError,
        TimeoutError,
        OSError,
    )):
        return True

    return False


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    exceptions: tuple[type[Exception], ...] = (RetriableError, NetworkError, DatabaseError),
):
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to retry on

    Example:
        @retry_with_backoff(max_attempts=5)
        async def fetch_data():
            # ... API call that might fail ...
            pass
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def async_error_handler(
    fallback_value: Any | None = None,
    log_errors: bool = True,
    raise_on_permanent: bool = True,
):
    """
    Decorator for async functions that adds error handling and logging.

    Args:
        fallback_value: Value to return if an error occurs (None by default)
        log_errors: Whether to log errors
        raise_on_permanent: Whether to raise PermanentErrors

    Example:
        @async_error_handler(fallback_value=[])
        async def get_results():
            # ... might fail ...
            return results
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log the error
                if log_errors:
                    logger.error(
                        f"Error in {func.__name__}: {get_user_friendly_message(e)}",
                        exc_info=True,
                        extra={"function": func.__name__, "args": args, "kwargs": kwargs}
                    )

                # Raise permanent errors if configured
                if raise_on_permanent and isinstance(e, PermanentError):
                    raise

                # Return fallback value for retriable errors
                if fallback_value is not None:
                    logger.warning(f"Returning fallback value for {func.__name__}")
                    return fallback_value

                # Re-raise if no fallback
                raise

        return wrapper

    return decorator


def sync_error_handler(
    fallback_value: Any | None = None,
    log_errors: bool = True,
    raise_on_permanent: bool = True,
):
    """
    Decorator for sync functions that adds error handling and logging.

    Args:
        fallback_value: Value to return if an error occurs (None by default)
        log_errors: Whether to log errors
        raise_on_permanent: Whether to raise PermanentErrors

    Example:
        @sync_error_handler(fallback_value={})
        def parse_config():
            # ... might fail ...
            return config
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                if log_errors:
                    logger.error(
                        f"Error in {func.__name__}: {get_user_friendly_message(e)}",
                        exc_info=True,
                        extra={"function": func.__name__, "args": args, "kwargs": kwargs}
                    )

                # Raise permanent errors if configured
                if raise_on_permanent and isinstance(e, PermanentError):
                    raise

                # Return fallback value for retriable errors
                if fallback_value is not None:
                    logger.warning(f"Returning fallback value for {func.__name__}")
                    return fallback_value

                # Re-raise if no fallback
                raise

        return wrapper

    return decorator


class ErrorReporter:
    """Collect and report errors for debugging."""

    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self._errors: list[dict[str, Any]] = []

    def report(self, error: Exception, context: dict[str, Any] | None = None):
        """
        Report an error.

        Args:
            error: The exception that occurred
            context: Additional context information
        """
        error_info = {
            "timestamp": logging.Formatter().formatTime(logging.LogRecord(
                "", 0, "", 0, "", (), None
            )),
            "type": type(error).__name__,
            "message": str(error),
            "user_message": get_user_friendly_message(error),
            "context": context or {},
        }

        if isinstance(error, PKMAgentError):
            error_info.update(error.to_dict())

        self._errors.append(error_info)

        # Keep only recent errors
        if len(self._errors) > self.max_errors:
            self._errors = self._errors[-self.max_errors:]

        logger.error(f"Error reported: {error_info['user_message']}", extra=error_info)

    def get_recent_errors(self, count: int = 10) -> list[dict[str, Any]]:
        """Get recent errors."""
        return self._errors[-count:]

    def clear(self):
        """Clear all reported errors."""
        self._errors.clear()

    def has_errors(self) -> bool:
        """Check if any errors have been reported."""
        return len(self._errors) > 0


# Global error reporter instance
error_reporter = ErrorReporter()


async def with_timeout(coro, timeout: float, operation: str = "operation"):
    """
    Run a coroutine with a timeout.

    Args:
        coro: The coroutine to run
        timeout: Timeout in seconds
        operation: Description of the operation for error messages

    Returns:
        Result of the coroutine

    Raises:
        PKMTimeoutError: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        raise PKMTimeoutError(operation=operation, timeout=timeout)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division fails."""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def format_error_for_display(error: Exception) -> str:
    """
    Format an error for display in the TUI.

    Args:
        error: The exception to format

    Returns:
        Formatted error message with emoji and details
    """
    user_msg = get_user_friendly_message(error)

    details = []
    if isinstance(error, PKMAgentError) and error.context:
        for key, value in error.context.items():
            details.append(f"  • {key}: {value}")

    if details:
        return f"{user_msg}\n\nDetails:\n" + "\n".join(details)

    return user_msg
