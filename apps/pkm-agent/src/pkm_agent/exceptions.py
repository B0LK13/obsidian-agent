"""
Custom exception hierarchy for PKM Agent.

Provides structured error handling with context information and retry strategies.
"""

import traceback
from datetime import datetime
from typing import Any


class PKMAgentError(Exception):
    """Base exception for all PKM Agent errors."""

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.stack_trace = traceback.format_exc() if cause else None

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "stack_trace": self.stack_trace
        }


class RetriableError(PKMAgentError):
    """Error that can be retried with exponential backoff."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        max_retries: int = 3,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.max_retries = max_retries


class PermanentError(PKMAgentError):
    """Error that should not be retried."""
    pass


class IndexingError(PermanentError):
    """Base class for indexing errors."""
    pass


class FileIndexError(IndexingError):
    """Error indexing a specific file."""

    def __init__(self, filepath: str, message: str, **kwargs):
        super().__init__(message, context={"filepath": filepath}, **kwargs)
        self.filepath = filepath


class SearchError(PKMAgentError):
    """Base class for search errors."""
    pass


class VectorStoreError(SearchError, RetriableError):
    """Error communicating with vector store."""
    pass


class EmbeddingError(SearchError, RetriableError):
    """Error generating embeddings."""

    def __init__(self, text: str, model: str, message: str, **kwargs):
        super().__init__(
            message,
            context={"text_length": len(text), "model": model},
            **kwargs
        )


class LLMError(RetriableError):
    """Base class for LLM provider errors."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        model: str = "unknown",
        **kwargs
    ):
        super().__init__(
            message,
            context={"provider": provider, "model": model},
            **kwargs
        )
        self.provider = provider
        self.model = model


class RateLimitError(LLMError):
    """API rate limit exceeded."""
    pass


class TokenLimitError(LLMError, PermanentError):
    """Input exceeds model token limit."""
    pass


class APIError(LLMError):
    """Generic API error from LLM provider."""
    pass


class StorageError(PKMAgentError):
    """Base class for storage errors."""
    pass


class DatabaseError(StorageError, RetriableError):
    """Database operation failed."""

    def __init__(self, operation: str, message: str, **kwargs):
        super().__init__(
            message,
            context={"operation": operation},
            **kwargs
        )


class ConfigurationError(PermanentError):
    """Invalid configuration."""

    def __init__(self, config_key: str, message: str, **kwargs):
        super().__init__(
            message,
            context={"config_key": config_key},
            **kwargs
        )


class NetworkError(RetriableError):
    """Network communication error."""
    pass


class SyncError(PKMAgentError):
    """Synchronization error."""
    pass


class SyncProtocolError(SyncError, PermanentError):
    """Invalid sync protocol message."""
    pass


class ValidationError(PermanentError):
    """Input validation failed."""

    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        super().__init__(
            f"Validation failed for {field}: {reason}",
            context={"field": field, "value": value, "reason": reason},
            **kwargs
        )
