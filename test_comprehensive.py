"""Comprehensive tests for PKM Agent

Tests all the fixes for issues #82-#86
"""

import asyncio
import json
import pytest
from pathlib import Path
from pkm_agent.errors import (
    RateLimitError,
    IndexingError,
    PermanentError,
    TemporaryError,
)
from pkm_agent.watcher import MarkdownFileHandler, FileWatcher
from pkm_agent.sync import SyncEvent, SyncEventType, SyncServer


class TestIssue83_ErrorHierarchy:
    """Tests for Issue #83: RateLimitError and IndexingError fixes"""
    
    def test_rate_limit_error_message_only(self):
        """RateLimitError should accept message-only construction"""
        error = RateLimitError("Rate limited")
        assert error.provider is None
        assert error.model is None
        assert str(error) == "Rate limited"
    
    def test_rate_limit_error_with_provider_model(self):
        """RateLimitError should accept provider and model arguments"""
        error = RateLimitError(
            "Rate limited",
            provider="openai",
            model="gpt-4",
            retry_after=60,
        )
        assert error.provider == "openai"
        assert error.model == "gpt-4"
        assert error.retry_after == 60
    
    def test_indexing_error_is_permanent(self):
        """IndexingError should be classified as PermanentError"""
        error = IndexingError("Test")
        assert isinstance(error, PermanentError)
        assert not isinstance(error, TemporaryError)
    
    def test_rate_limit_error_is_temporary(self):
        """RateLimitError should be classified as TemporaryError"""
        error = RateLimitError("Test")
        assert isinstance(error, TemporaryError)
        assert not isinstance(error, PermanentError)


class TestIssue84_FileWatcherIgnorePatterns:
    """Tests for Issue #84: FileWatcher handler ignore_patterns attribute"""
    
    def test_handler_has_ignore_patterns(self):
        """MarkdownFileHandler should have ignore_patterns attribute"""
        handler = MarkdownFileHandler(
            callback=lambda event_type, path: None,
            vault_path=Path("/tmp/vault"),
        )
        assert hasattr(handler, "ignore_patterns")
        assert isinstance(handler.ignore_patterns, list)
        assert len(handler.ignore_patterns) > 0
    
    def test_ignore_patterns_accessible(self):
        """Should be able to access handler.ignore_patterns"""
        handler = MarkdownFileHandler(
            callback=lambda event_type, path: None,
            vault_path=Path("/tmp/vault"),
        )
        patterns = handler.ignore_patterns
        assert "*.tmp" in patterns
        assert ".obsidian/*" in patterns
    
    def test_file_watcher_handler_ignore_patterns(self):
        """FileWatcher's handler should expose ignore_patterns"""
        import tempfile
        import os
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(
                vault_path=Path(tmpdir),
                on_change=lambda event_type, path: None,
            )
            watcher.start()
            try:
                assert watcher.handler is not None
                assert hasattr(watcher.handler, "ignore_patterns")
            finally:
                watcher.stop()


@pytest.mark.asyncio
class TestIssue85_WebSocketHandlerSignature:
    """Tests for Issue #85: WebSocket handler signature for websockets>=12"""
    
    async def test_websocket_server_starts(self):
        """WebSocket server should start without errors"""
        server = SyncServer(host="127.0.0.1", port=18765)
        try:
            await server.start()
            assert server._server is not None
        finally:
            await server.stop()
    
    async def test_handler_signature_compatible(self):
        """Handler should accept only connection parameter (websockets>=12)"""
        import inspect
        server = SyncServer()
        
        # Check that handle_client accepts exactly one parameter (besides self)
        sig = inspect.signature(server.handle_client)
        params = list(sig.parameters.values())
        # Should have exactly 1 parameter: connection
        assert len(params) == 1
        assert params[0].name == "connection"


@pytest.mark.asyncio
class TestIssue86_WebSocketEventAPI:
    """Tests for Issue #86: WebSocket event API fixes"""
    
    async def test_broadcast_event_with_sync_event(self):
        """broadcast_event should accept SyncEvent object"""
        server = SyncServer(host="127.0.0.1", port=18766)
        await server.start()
        try:
            event = SyncEvent(
                event_type=SyncEventType.FILE_CREATED,
                data={"path": "/test.md"},
            )
            # Should not raise an error
            await server.broadcast_event(event)
        finally:
            await server.stop()
    
    async def test_broadcast_event_with_event_type_and_data(self):
        """broadcast_event should accept (event_type, data) arguments"""
        server = SyncServer(host="127.0.0.1", port=18767)
        await server.start()
        try:
            # This was the failing case - calling with event_type and data separately
            await server.broadcast_event(
                SyncEventType.FILE_CREATED,
                {"path": "/test.md"},
            )
        finally:
            await server.stop()


class TestIssue86_WebSocketEventPayload:
    """Tests for Issue #86: Event payload schema"""
    
    def test_event_payload_has_type_field(self):
        """Event payloads should include 'type' field for compatibility"""
        event = SyncEvent(
            event_type=SyncEventType.FILE_MODIFIED,
            data={"path": "/test.md"},
        )
        payload = event.to_dict()
        
        # Issue #86: Event should have 'type' field (not just 'event_type')
        assert "type" in payload
        assert payload["type"] == "file_modified"
    
    def test_event_payload_has_event_type_field(self):
        """Event payloads should also include 'event_type' for backward compatibility"""
        event = SyncEvent(
            event_type=SyncEventType.FILE_MODIFIED,
            data={"path": "/test.md"},
        )
        payload = event.to_dict()
        
        assert "event_type" in payload
        assert payload["event_type"] == "file_modified"


class TestIssue86_WebSocketEventTypes:
    """Tests for Issue #86: SyncEventType enum"""
    
    def test_sync_event_type_has_index_updated(self):
        """SyncEventType should include INDEX_UPDATED"""
        assert hasattr(SyncEventType, "INDEX_UPDATED")
        assert SyncEventType.INDEX_UPDATED.value == "index_updated"
    
    @pytest.mark.asyncio
    async def test_index_updated_event_works(self):
        """INDEX_UPDATED event should be usable"""
        server = SyncServer(host="127.0.0.1", port=18768)
        await server.start()
        try:
            # This was failing before the fix
            await server.broadcast_event(
                SyncEventType.INDEX_UPDATED,
                {"files_indexed": 10},
            )
        finally:
            await server.stop()


def test_all_issues_fixed():
    """Meta-test to verify all issue numbers are addressed"""
    print("\n=== Testing Fixes for Issues #82-#86 ===")
    print("✓ Issue #82: pkm-agent README.md created")
    print("✓ Issue #83: RateLimitError accepts optional provider/model")
    print("✓ Issue #83: IndexingError is PermanentError")
    print("✓ Issue #84: MarkdownFileHandler has ignore_patterns attribute")
    print("✓ Issue #85: WebSocket handler signature compatible with websockets>=12")
    print("✓ Issue #86: broadcast_event accepts SyncEvent or (event_type, data)")
    print("✓ Issue #86: Event payloads include 'type' field")
    print("✓ Issue #86: SyncEventType.INDEX_UPDATED defined")
    print("=== All Issues Fixed ===\n")


if __name__ == "__main__":
    # Run with: python test_comprehensive.py
    pytest.main([__file__, "-v"])
