"""Tests for error handling module"""

import pytest
from obsidian_agent.errors import (
    ErrorCode,
    ErrorSeverity,
    ObsidianAgentError,
    DatabaseError,
    DatabaseLockedError,
    VectorStoreError,
    VaultError,
    VaultNotFoundError,
    ConfigurationError,
)


class TestErrorCode:
    def test_database_error_codes(self):
        assert ErrorCode.DB_CONNECTION_FAILED.value == 100
        assert ErrorCode.DB_LOCKED.value == 101
        assert ErrorCode.DB_CORRUPTED.value == 102

    def test_vector_store_error_codes(self):
        assert ErrorCode.VECTOR_STORE_CONNECTION_FAILED.value == 200
        assert ErrorCode.EMBEDDING_GENERATION_FAILED.value == 203

    def test_vault_error_codes(self):
        assert ErrorCode.VAULT_NOT_FOUND.value == 300
        assert ErrorCode.VAULT_ACCESS_DENIED.value == 301


class TestErrorSeverity:
    def test_severity_values(self):
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestObsidianAgentError:
    def test_basic_error(self):
        error = ObsidianAgentError("Test error")
        assert error.message == "Test error"
        assert error.code == ErrorCode.UNKNOWN_ERROR
        assert error.severity == ErrorSeverity.ERROR

    def test_error_with_details(self):
        error = ObsidianAgentError(
            "Test error",
            code=ErrorCode.DB_LOCKED,
            severity=ErrorSeverity.WARNING,
            details={"path": "/test"},
            suggested_actions=["Try again"],
            recoverable=True,
        )
        assert error.code == ErrorCode.DB_LOCKED
        assert error.details["path"] == "/test"
        assert error.recoverable is True

    def test_to_dict(self):
        error = ObsidianAgentError("Test", code=ErrorCode.DB_LOCKED)
        error_dict = error.to_dict()
        assert error_dict["message"] == "Test"
        assert error_dict["code"] == 101
        assert "error" in error_dict

    def test_user_message(self):
        error = ObsidianAgentError(
            "Test error",
            suggested_actions=["Action 1", "Action 2"],
        )
        msg = error.user_message()
        assert "Test error" in msg


class TestSpecificErrors:
    def test_database_locked_error(self):
        error = DatabaseLockedError("/path/to/db")
        assert error.code == ErrorCode.DB_LOCKED
        assert error.severity == ErrorSeverity.WARNING
        assert error.recoverable is True
        assert "/path/to/db" in error.message

    def test_vault_not_found_error(self):
        error = VaultNotFoundError("/nonexistent/vault")
        assert error.code == ErrorCode.VAULT_NOT_FOUND
        assert error.recoverable is False
        assert "/nonexistent/vault" in error.message

    def test_configuration_error(self):
        error = ConfigurationError("Invalid config", config_key="api_key")
        assert error.code == ErrorCode.CONFIG_INVALID
        assert error.details["config_key"] == "api_key"


class TestExceptionHierarchy:
    def test_database_error_hierarchy(self):
        assert issubclass(DatabaseError, ObsidianAgentError)
        assert issubclass(DatabaseLockedError, DatabaseError)

    def test_vault_error_hierarchy(self):
        assert issubclass(VaultError, ObsidianAgentError)
        assert issubclass(VaultNotFoundError, VaultError)

    def test_vector_store_error_hierarchy(self):
        assert issubclass(VectorStoreError, ObsidianAgentError)
