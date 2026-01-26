"""Error classes for PKM Agent"""

from typing import Optional


class PKMAgentError(Exception):
    """Base exception for all PKM Agent errors"""
    pass


class TemporaryError(PKMAgentError):
    """Errors that are temporary and may succeed on retry"""
    pass


class PermanentError(PKMAgentError):
    """Errors that are permanent and should not be retried"""
    pass


class RateLimitError(TemporaryError):
    """Rate limiting error from API provider
    
    Fixed for Issue #83: Now accepts optional provider/model arguments with defaults
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.retry_after = retry_after


class IndexingError(PermanentError):
    """Error during indexing operation
    
    Fixed for Issue #83: Now inherits from PermanentError instead of TemporaryError
    """
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path


class APIError(TemporaryError):
    """Generic API error"""
    pass


class ValidationError(PermanentError):
    """Data validation error"""
    pass


class ConfigurationError(PermanentError):
    """Configuration error"""
    pass
