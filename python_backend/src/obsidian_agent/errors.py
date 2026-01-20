"""Comprehensive error handling for Obsidian Agent"""

from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorCode(Enum):
    """Error codes for different error types"""
    DB_CONNECTION_FAILED = 100
    DB_LOCKED = 101
    DB_CORRUPTED = 102
    DB_MIGRATION_FAILED = 103
    VECTOR_STORE_CONNECTION_FAILED = 200
    VECTOR_STORE_INDEX_FAILED = 201
    VECTOR_STORE_SEARCH_FAILED = 202
    EMBEDDING_GENERATION_FAILED = 203
    VAULT_NOT_FOUND = 300
    VAULT_ACCESS_DENIED = 301
    FILE_READ_ERROR = 302
    FILE_PARSE_ERROR = 303
    API_CONNECTION_FAILED = 400
    API_AUTHENTICATION_FAILED = 401
    API_RATE_LIMITED = 402
    API_TIMEOUT = 403
    CONFIG_INVALID = 500
    CONFIG_MISSING = 501
    UNKNOWN_ERROR = 999


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ObsidianAgentError(Exception):
    """Base exception for all Obsidian Agent errors"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        suggested_actions: Optional[List[str]] = None,
        help_url: Optional[str] = None,
        recoverable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.severity = severity
        self.details = details or {}
        self.suggested_actions = suggested_actions or []
        self.help_url = help_url
        self.recoverable = recoverable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code.value,
            "severity": self.severity.value,
            "details": self.details,
            "suggested_actions": self.suggested_actions,
            "help_url": self.help_url,
            "recoverable": self.recoverable,
        }
    
    def user_message(self) -> str:
        msg = f"Error: {self.message}"
        if self.suggested_actions:
            msg += "\n\nSuggested actions:\n"
            for action in self.suggested_actions:
                msg += f"  - {action}\n"
        return msg


class DatabaseError(ObsidianAgentError):
    """Base database error"""
    pass


class DatabaseLockedError(DatabaseError):
    def __init__(self, db_path: str):
        super().__init__(
            message=f"Database is locked: {db_path}",
            code=ErrorCode.DB_LOCKED,
            severity=ErrorSeverity.WARNING,
            details={"db_path": db_path},
            suggested_actions=["Wait and try again", "Close other applications"],
            recoverable=True,
        )


class VectorStoreError(ObsidianAgentError):
    """Base vector store error"""
    pass


class VaultError(ObsidianAgentError):
    """Base vault error"""
    pass


class VaultNotFoundError(VaultError):
    def __init__(self, vault_path: str):
        super().__init__(
            message=f"Vault not found: {vault_path}",
            code=ErrorCode.VAULT_NOT_FOUND,
            severity=ErrorSeverity.ERROR,
            details={"vault_path": vault_path},
            suggested_actions=["Check if the vault path is correct"],
            recoverable=False,
        )


class ConfigurationError(ObsidianAgentError):
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFIG_INVALID,
            severity=ErrorSeverity.ERROR,
            details={"config_key": config_key},
            suggested_actions=["Check configuration file"],
            recoverable=False,
        )
