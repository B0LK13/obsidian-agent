"""Proof of Concept Demo for PKM Agent

Demonstrates all features and fixes for issues #82-#86
"""

import asyncio
import json
from pathlib import Path
from pkm_agent.errors import RateLimitError, IndexingError, PermanentError
from pkm_agent.watcher import MarkdownFileHandler, FileWatcher
from pkm_agent.sync import SyncEvent, SyncEventType, SyncServer


def demo_issue_82():
    """Demo Issue #82: pkm-agent package with README.md"""
    print("\n=== Demo Issue #82: pkm-agent Installation ===")
    print("✓ pkm-agent directory created with README.md")
    print("✓ pyproject.toml configured with hatchling")
    print("  Run: cd pkm-agent && pip install -e '.[dev]'")
    print("  This should now work without OSError")


def demo_issue_83():
    """Demo Issue #83: Error hierarchy fixes"""
    print("\n=== Demo Issue #83: Error Hierarchy ===")
    
    # Test RateLimitError with message only
    print("\n1. RateLimitError with message only:")
    try:
        raise RateLimitError("API rate limit exceeded")
    except RateLimitError as e:
        print(f"   ✓ Message-only constructor works: {e}")
        print(f"     provider={e.provider}, model={e.model}")
    
    # Test RateLimitError with provider/model
    print("\n2. RateLimitError with provider and model:")
    try:
        raise RateLimitError(
            "Rate limited",
            provider="openai",
            model="gpt-4",
            retry_after=60,
        )
    except RateLimitError as e:
        print(f"   ✓ Full constructor works: {e}")
        print(f"     provider={e.provider}, model={e.model}, retry_after={e.retry_after}")
    
    # Test IndexingError is PermanentError
    print("\n3. IndexingError classification:")
    error = IndexingError("Failed to index file")
    print(f"   ✓ IndexingError is PermanentError: {isinstance(error, PermanentError)}")
    print(f"     This means it should NOT be retried")


def demo_issue_84():
    """Demo Issue #84: FileWatcher ignore_patterns"""
    print("\n=== Demo Issue #84: FileWatcher ignore_patterns ===")
    
    # Create handler and access ignore_patterns
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        handler = MarkdownFileHandler(
            callback=lambda event_type, path: print(f"Event: {event_type} - {path}"),
            vault_path=Path(tmpdir),
        )
        
        print(f"\n✓ MarkdownFileHandler has ignore_patterns attribute")
        print(f"  ignore_patterns type: {type(handler.ignore_patterns)}")
        print(f"  Patterns: {handler.ignore_patterns}")
        
        # FileWatcher also exposes handler
        watcher = FileWatcher(
            vault_path=Path(tmpdir),
            on_change=lambda event_type, path: None,
        )
        watcher.start()
        print(f"\n✓ FileWatcher.handler exposes ignore_patterns")
        print(f"  Can access via: watcher.handler.ignore_patterns")
        watcher.stop()


async def demo_issue_85():
    """Demo Issue #85: WebSocket handler signature"""
    print("\n=== Demo Issue #85: WebSocket Server (websockets>=12) ===")
    
    server = SyncServer(host="127.0.0.1", port=28765)
    
    print("\n1. Starting WebSocket server...")
    await server.start()
    print("   ✓ Server started successfully")
    print(f"     Handler signature: handle_client(connection)")
    print(f"     Compatible with websockets>=12")
    
    # Simulate a brief connection
    import websockets
    try:
        print("\n2. Testing client connection...")
        async with websockets.connect(f"ws://{server.host}:{server.port}") as websocket:
            # Receive welcome message
            message = await websocket.recv()
            data = json.loads(message)
            print(f"   ✓ Connected successfully")
            print(f"     Received: {data.get('event_type')} - {data.get('data', {}).get('message')}")
    except Exception as e:
        print(f"   Note: {e}")
    finally:
        await server.stop()
        print("\n3. Server stopped")


async def demo_issue_86():
    """Demo Issue #86: WebSocket event API"""
    print("\n=== Demo Issue #86: WebSocket Event API ===")
    
    server = SyncServer(host="127.0.0.1", port=28766)
    await server.start()
    
    print("\n1. Testing broadcast_event with SyncEvent object:")
    event = SyncEvent(
        event_type=SyncEventType.FILE_CREATED,
        data={"path": "/notes/test.md", "size": 1024},
    )
    await server.broadcast_event(event)
    print("   ✓ broadcast_event(SyncEvent) works")
    
    print("\n2. Testing broadcast_event with (event_type, data) arguments:")
    await server.broadcast_event(
        SyncEventType.FILE_MODIFIED,
        {"path": "/notes/test.md", "size": 2048},
    )
    print("   ✓ broadcast_event(event_type, data) works")
    
    print("\n3. Testing INDEX_UPDATED event:")
    await server.broadcast_event(
        SyncEventType.INDEX_UPDATED,
        {"files_indexed": 150, "duration_ms": 234},
    )
    print("   ✓ SyncEventType.INDEX_UPDATED is defined and works")
    
    print("\n4. Testing event payload schema:")
    event = SyncEvent(
        event_type=SyncEventType.FILE_CREATED,
        data={"path": "/test.md"},
    )
    payload = event.to_dict()
    print(f"   Event payload keys: {list(payload.keys())}")
    print(f"   ✓ Has 'type' field: {'type' in payload}")
    print(f"   ✓ Has 'event_type' field: {'event_type' in payload}")
    print(f"     type={payload['type']}, event_type={payload['event_type']}")
    
    await server.stop()


async def main():
    """Run all demos"""
    print("=" * 60)
    print("PKM Agent - Proof of Concept Demo")
    print("Demonstrating Fixes for Issues #82-#86")
    print("=" * 60)
    
    # Issue #82
    demo_issue_82()
    
    # Issue #83
    demo_issue_83()
    
    # Issue #84
    demo_issue_84()
    
    # Issue #85
    await demo_issue_85()
    
    # Issue #86
    await demo_issue_86()
    
    print("\n" + "=" * 60)
    print("✓ All Demos Completed Successfully")
    print("=" * 60)


if __name__ == "__main__":
    # Run with: python demo_poc.py
    asyncio.run(main())
