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


# ============================================
# Indexing Errors
# ============================================

class IndexingError(PermanentError):
    """Base class for indexing errors."""
    pass


class FileIndexError(IndexingError):
    """Error indexing a specific file."""

    def __init__(self, filepath: str, message: str, **kwargs):
        super().__init__(message, context={"filepath": filepath}, **kwargs)
        self.filepath = filepath


class DirectoryAccessError(IndexingError):
    """Cannot access directory for indexing."""

    def __init__(self, directory: str, message: str, **kwargs):
        super().__init__(message, context={"directory": directory}, **kwargs)


class FileWatcherError(IndexingError):
    """Error in file system watcher."""
    pass


# ============================================
# Search & Retrieval Errors
# ============================================

class SearchError(PKMAgentError):
    """Base class for search errors."""
    pass


class QueryParseError(SearchError, PermanentError):
    """Invalid search query syntax."""

    def __init__(self, query: str, message: str, **kwargs):
        super().__init__(message, context={"query": query}, **kwargs)


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


# ============================================
# LLM Errors
# ============================================

class LLMError(RetriableError):
    """Base class for LLM provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str,
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

    def __init__(
        self,
        *args,
        provider: str | None = None,
        model: str | None = None,
        retry_after: float | None = None,
        message: str | None = None,
        **kwargs
    ):
        if args:
            if len(args) == 1 and provider is None and model is None and message is None:
                message = args[0]
            elif len(args) == 2 and provider is None and model is None and message is None:
                provider, model = args
            else:
                raise TypeError("RateLimitError expects (message) or (provider, model)")

        provider = provider or "unknown"
        model = model or "unknown"
        if message is None:
            message = f"Rate limit exceeded for {provider}/{model}"

        super().__init__(
            message,
            provider=provider,
            model=model,
            retry_after=retry_after,
            **kwargs
        )


class TokenLimitError(LLMError, PermanentError):
    """Input exceeds model token limit."""

    def __init__(
        self,
        provider: str,
        model: str,
        token_count: int,
        max_tokens: int,
        **kwargs
    ):
        super().__init__(
            f"Token limit exceeded: {token_count} > {max_tokens}",
            provider=provider,
            model=model,
            context={"token_count": token_count, "max_tokens": max_tokens},
            **kwargs
        )


class APIError(LLMError):
    """Generic API error from LLM provider."""

    def __init__(self, provider: str, model: str, status_code: int, **kwargs):
        super().__init__(
            f"API error: HTTP {status_code}",
            provider=provider,
            model=model,
            context={"status_code": status_code},
            **kwargs
        )


class InvalidResponseError(LLMError, PermanentError):
    """LLM returned invalid or malformed response."""
    pass


# ============================================
# Storage & Database Errors
# ============================================

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


class DatabaseConnectionError(DatabaseError):
    """Cannot connect to database."""
    pass


class DatabaseIntegrityError(DatabaseError, PermanentError):
    """Database integrity constraint violated."""
    pass


class FileSystemError(StorageError):
    """File system operation failed."""
    pass


class PermissionError(FileSystemError, PermanentError):
    """Insufficient permissions for operation."""

    def __init__(self, path: str, operation: str, **kwargs):
        super().__init__(
            f"Permission denied: {operation} on {path}",
            context={"path": path, "operation": operation},
            **kwargs
        )


class FileNotFoundError(FileSystemError, PermanentError):
    """Requested file does not exist."""

    def __init__(self, filepath: str, **kwargs):
        super().__init__(
            f"File not found: {filepath}",
            context={"filepath": filepath},
            **kwargs
        )


class FileCorruptedError(FileSystemError):
    """File is corrupted or unreadable."""

    def __init__(self, filepath: str, **kwargs):
        super().__init__(
            f"File corrupted: {filepath}",
            context={"filepath": filepath},
            **kwargs
        )


# ============================================
# Configuration Errors
# ============================================

class ConfigurationError(PermanentError):
    """Invalid configuration."""

    def __init__(self, config_key: str, message: str, **kwargs):
        super().__init__(
            message,
            context={"config_key": config_key},
            **kwargs
        )


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""

    def __init__(self, config_key: str, **kwargs):
        super().__init__(
            config_key,
            f"Missing required configuration: {config_key}",
            **kwargs
        )


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid."""

    def __init__(self, config_key: str, value: Any, expected: str, **kwargs):
        super().__init__(
            config_key,
            f"Invalid configuration for {config_key}: expected {expected}, got {value}",
            context={"value": value, "expected": expected},
            **kwargs
        )


# ============================================
# Network & Communication Errors
# ============================================

class NetworkError(RetriableError):
    """Network communication error."""
    pass


class TimeoutError(NetworkError):
    """Operation timed out."""

    def __init__(self, operation: str, timeout: float, **kwargs):
        super().__init__(
            f"Operation timed out after {timeout}s: {operation}",
            context={"operation": operation, "timeout": timeout},
            **kwargs
        )


class ConnectionError(NetworkError):
    """Cannot establish connection."""

    def __init__(self, host: str, port: int, **kwargs):
        super().__init__(
            f"Connection failed: {host}:{port}",
            context={"host": host, "port": port},
            **kwargs
        )


# ============================================
# Sync & Integration Errors
# ============================================

class SyncError(PKMAgentError):
    """Synchronization error."""
    pass


class ConflictError(SyncError):
    """Sync conflict detected."""

    def __init__(self, resource: str, local_version: str, remote_version: str, **kwargs):
        super().__init__(
            f"Sync conflict for {resource}",
            context={
                "resource": resource,
                "local_version": local_version,
                "remote_version": remote_version
            },
            **kwargs
        )


class SyncProtocolError(SyncError, PermanentError):
    """Invalid sync protocol message."""
    pass


# ============================================
# Validation Errors
# ============================================

class ValidationError(PermanentError):
    """Input validation failed."""

    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        super().__init__(
            f"Validation failed for {field}: {reason}",
            context={"field": field, "value": value, "reason": reason},
            **kwargs
        )


class SchemaValidationError(ValidationError):
    """Data does not match expected schema."""
    pass


# ============================================
# Resource Errors
# ============================================

class ResourceError(PKMAgentError):
    """Resource management error."""
    pass


class ResourceExhaustedError(ResourceError, RetriableError):
    """Resource limit exceeded."""

    def __init__(self, resource_type: str, limit: Any, current: Any, **kwargs):
        super().__init__(
            f"{resource_type} exhausted: {current}/{limit}",
            context={"resource_type": resource_type, "limit": limit, "current": current},
            **kwargs
        )


class CostLimitExceededError(ResourceError, PermanentError):
    """Cost limit exceeded."""

    def __init__(self, current_cost: float, limit: float, **kwargs):
        super().__init__(
            f"Cost limit exceeded: ${current_cost:.2f} > ${limit:.2f}",
            context={"current_cost": current_cost, "limit": limit},
            **kwargs
        )
