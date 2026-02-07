"""
Comprehensive Test Suite for PKM-Agent Phase 1 & 2 Implementation
Run this script to verify all implementations are working correctly.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import json

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg: str):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg: str):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_header(msg: str):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{RESET}\n")


class TestRunner:
    """Runs all tests and tracks results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results: List[Dict[str, Any]] = []
    
    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Run a test and track result."""
        print(f"\n{BLUE}Testing: {name}{RESET}")
        try:
            result = func(*args, **kwargs)
            if result:
                print_success(f"{name} - PASSED")
                self.passed += 1
                self.results.append({"name": name, "status": "PASSED"})
                return True
            else:
                print_error(f"{name} - FAILED")
                self.failed += 1
                self.results.append({"name": name, "status": "FAILED"})
                return False
        except Exception as e:
            print_error(f"{name} - ERROR: {e}")
            self.failed += 1
            self.results.append({"name": name, "status": "ERROR", "error": str(e)})
            return False
    
    def warn(self, msg: str):
        """Track a warning."""
        self.warnings += 1
        print_warning(msg)
    
    def summary(self):
        """Print test summary."""
        print_header("TEST SUMMARY")
        total = self.passed + self.failed
        print(f"Total Tests: {total}")
        print_success(f"Passed: {self.passed}")
        if self.failed > 0:
            print_error(f"Failed: {self.failed}")
        if self.warnings > 0:
            print_warning(f"Warnings: {self.warnings}")
        
        if self.failed == 0:
            print(f"\n{GREEN}{'🎉 ALL TESTS PASSED! 🎉':^60}{RESET}\n")
        else:
            print(f"\n{RED}{'⚠️  SOME TESTS FAILED  ⚠️':^60}{RESET}\n")
        
        return self.failed == 0


def test_imports() -> bool:
    """Test that all new modules can be imported."""
    try:
        from pkm_agent.exceptions import (
            PKMAgentError, RetriableError, PermanentError,
            IndexingError, SearchError, LLMError, RateLimitError
        )
        print_info("Exception hierarchy imported successfully")
        
        from pkm_agent.data.file_watcher import FileWatcher
        print_info("FileWatcher imported successfully")
        
        from pkm_agent.websocket_sync import SyncServer, SyncEvent, SyncEventType
        print_info("Sync server imported successfully")
        
        from pkm_agent.data.link_analyzer import LinkAnalyzer, Link, LinkType
        print_info("LinkAnalyzer imported successfully")
        
        from pkm_agent.data.link_healer import LinkValidator, LinkHealer, LinkSuggestion
        print_info("LinkHealer imported successfully")
        
        return True
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False


def test_exception_hierarchy() -> bool:
    """Test exception hierarchy functionality."""
    from pkm_agent.exceptions import (
        PKMAgentError, RetriableError, PermanentError,
        IndexingError, RateLimitError
    )
    
    # Test basic exception creation
    error = IndexingError("Test error", {"file": "test.md"})
    assert error.message == "Test error"
    assert error.context["file"] == "test.md"
    print_info(f"Created exception: {error}")
    
    # Test retriable vs permanent
    assert isinstance(RateLimitError("Test"), RetriableError)
    assert isinstance(IndexingError("Test"), PermanentError)
    print_info("Exception types correctly classified")
    
    # Test to_dict()
    error_dict = error.to_dict()
    assert "error_type" in error_dict
    assert "message" in error_dict
    assert "context" in error_dict
    print_info(f"Exception serialization: {error_dict}")
    
    return True


def test_link_analyzer() -> bool:
    """Test link analyzer with sample data."""
    from pkm_agent.data.link_analyzer import LinkAnalyzer, LinkType
    from pathlib import Path
    import tempfile
    import shutil
    
    # Create temporary vault
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir)
        
        # Create test notes
        (vault_root / "Note1.md").write_text("""# Note 1
[[Note2]]
[[Broken Link]]
![[Image.png]]
[External Link](https://example.com)
#tag1 #tag2
""")
        
        (vault_root / "Note2.md").write_text("""# Note 2
[[Note1]]
""")
        
        # Initialize analyzer
        analyzer = LinkAnalyzer(vault_root)
        print_info(f"Initialized analyzer with {len(analyzer._note_cache)} notes")
        
        # Extract links from Note1
        note1_path = vault_root / "Note1.md"
        links = analyzer.extract_links(note1_path)
        print_info(f"Extracted {len(links)} links from Note1.md")
        
        # Check link types
        wikilinks = [l for l in links if l.link_type == LinkType.WIKILINK]
        embeds = [l for l in links if l.link_type == LinkType.EMBED]
        tags = [l for l in links if l.link_type == LinkType.TAG]
        
        print_info(f"  - {len(wikilinks)} wikilinks")
        print_info(f"  - {len(embeds)} embeds")
        print_info(f"  - {len(tags)} tags")
        
        assert len(wikilinks) == 2  # [[Note2]], [[Broken Link]]
        assert len(embeds) == 1     # ![[Image.png]]
        assert len(tags) == 2       # #tag1, #tag2
        
        # Find broken links
        broken = analyzer.find_broken_links()
        print_info(f"Found {len(broken)} broken links")
        
        assert len(broken) >= 2  # [[Broken Link]], ![[Image.png]]
        
        # Analyze vault
        result = analyzer.analyze_vault()
        print_info(f"Vault analysis: {result.total_links} total links, "
                  f"{len(result.broken_links)} broken")
        
        return True


def test_link_validator() -> bool:
    """Test link validation and fuzzy matching."""
    from pkm_agent.data.link_analyzer import LinkAnalyzer, Link, LinkType
    from pkm_agent.data.link_healer import LinkValidator
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir)
        
        # Create notes
        (vault_root / "Machine Learning.md").write_text("# ML")
        (vault_root / "Deep Learning Basics.md").write_text("# DL")
        (vault_root / "test.md").write_text("[[Machin Learning]]\n[[Deep Lerning]]")
        
        # Initialize
        analyzer = LinkAnalyzer(vault_root)
        validator = LinkValidator(analyzer, min_confidence=0.7)
        
        # Create broken links
        broken1 = Link(
            source_path="test.md",
            target="Machin Learning",
            link_type=LinkType.WIKILINK,
            line_number=1,
            column=0,
            is_broken=True
        )
        
        broken2 = Link(
            source_path="test.md",
            target="Deep Lerning",
            link_type=LinkType.WIKILINK,
            line_number=2,
            column=0,
            is_broken=True
        )
        
        # Get suggestions
        suggestion1 = validator.suggest_fix(broken1)
        suggestion2 = validator.suggest_fix(broken2)
        
        assert suggestion1 is not None
        assert suggestion2 is not None
        
        print_info(f"Suggestion 1: '{broken1.target}' → '{suggestion1.suggested_target}' "
                  f"({suggestion1.confidence:.1%})")
        print_info(f"Suggestion 2: '{broken2.target}' → '{suggestion2.suggested_target}' "
                  f"({suggestion2.confidence:.1%})")
        
        assert suggestion1.confidence >= 0.7
        assert suggestion2.confidence >= 0.7
        
        return True


def test_link_healer() -> bool:
    """Test link healing (dry run)."""
    from pkm_agent.data.link_analyzer import LinkAnalyzer
    from pkm_agent.data.link_healer import LinkValidator, LinkHealer
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir)
        
        # Create notes
        (vault_root / "Target Note.md").write_text("# Target")
        test_file = vault_root / "test.md"
        test_file.write_text("# Test\n[[Targt Note]]\n")
        
        # Initialize
        analyzer = LinkAnalyzer(vault_root)
        validator = LinkValidator(analyzer, min_confidence=0.7)
        healer = LinkHealer(validator, dry_run=True)
        
        # Heal broken links (dry run)
        results = healer.heal_file(test_file)
        
        print_info(f"Healing results: {len(results)} links processed")
        for r in results:
            print_info(f"  - {r.action}: {r.link.target}")
            if r.suggestion:
                print_info(f"    → {r.suggestion.suggested_target} "
                          f"({r.suggestion.confidence:.1%})")
        
        # Verify file not changed (dry run)
        content_after = test_file.read_text()
        assert "Targt Note" in content_after  # Original text preserved
        
        # Now test real healing
        healer_real = LinkHealer(validator, dry_run=False)
        results_real = healer_real.heal_file(test_file)
        
        # Verify file changed
        content_fixed = test_file.read_text()
        print_info(f"Fixed content: {content_fixed}")
        assert "Target Note" in content_fixed  # Fixed text
        assert "Targt Note" not in content_fixed  # Original removed
        
        return True


def test_file_watcher_basic() -> bool:
    """Test file watcher initialization."""
    from pkm_agent.data.file_watcher import FileWatcher
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir)
        
        events = []
        
        def on_created(path):
            events.append(("created", path))
        
        def on_modified(path):
            events.append(("modified", path))
        
        def on_deleted(path):
            events.append(("deleted", path))
        
        # Initialize watcher
        watcher = FileWatcher(
            vault_root,
            on_created=on_created,
            on_modified=on_modified,
            on_deleted=on_deleted
        )
        
        print_info(f"FileWatcher initialized for {vault_root}")
        print_info(f"Ignore patterns: {len(watcher.handler.ignore_patterns)} patterns")
        
        # Start watching
        watcher.start()
        print_info("FileWatcher started")
        
        # Give it a moment
        time.sleep(0.5)
        
        # Create a file
        (vault_root / "test.md").write_text("# Test")
        time.sleep(0.5)
        
        # Modify the file
        (vault_root / "test.md").write_text("# Test Modified")
        time.sleep(0.5)
        
        # Stop watcher
        watcher.stop()
        print_info("FileWatcher stopped")
        
        print_info(f"Captured {len(events)} events")
        for event_type, path in events:
            print_info(f"  - {event_type}: {path}")
        
        # We should have captured at least create and modify events
        # (delete not tested to avoid file system race conditions)
        assert len(events) >= 1
        
        return True


async def test_sync_server() -> bool:
    """Test WebSocket sync server."""
    from pkm_agent.websocket_sync import SyncServer, SyncEventType
    import websockets
    
    # Create server
    server = SyncServer(host="127.0.0.1", port=27126)  # Use different port for testing
    
    # Start server in background
    server_task = asyncio.create_task(server.start())
    print_info("Sync server started on ws://127.0.0.1:27126")
    
    # Give server time to start
    await asyncio.sleep(1)
    
    try:
        # Connect client
        async with websockets.connect('ws://127.0.0.1:27126') as ws:
            print_info("Client connected to sync server")
            
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            print_info("Sent ping")
            
            # Receive response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            print_info(f"Received: {data.get('type')}")
            
            assert data.get('type') == 'pong'
            
            # Test broadcast
            await server.broadcast_event(SyncEventType.FILE_CREATED, {"path": "test.md"})
            print_info("Broadcasted file_created event")
            
            # Receive broadcast
            broadcast = await asyncio.wait_for(ws.recv(), timeout=5)
            broadcast_data = json.loads(broadcast)
            event_type = broadcast_data.get('type') or broadcast_data.get('event_type')
            print_info(f"Received broadcast: {event_type}")
            
            assert event_type == 'file_created'
            assert broadcast_data.get('data', {}).get('path') == 'test.md'
    
    finally:
        # Stop server
        await server.stop()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print_info("Sync server stopped")
    
    return True


async def test_app_integration() -> bool:
    """Test PKMAgentApp with new features."""
    from pkm_agent.config import Config
    from pkm_agent.app import PKMAgentApp
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir)
        
        # Create test vault
        (vault_root / "test.md").write_text("# Test Note\n\nContent here.")
        
        # Create config
        config = Config()
        config.pkm_root = vault_root
        
        # Initialize app
        app = PKMAgentApp(config)
        print_info("PKMAgentApp initialized")
        
        # Check that sync server exists
        assert hasattr(app, 'sync_server')
        assert app.sync_server is not None
        print_info("Sync server configured")
        
        # Check that indexer has watch mode
        assert hasattr(app.indexer, 'watch_mode')
        print_info(f"Indexer watch mode: {app.indexer.watch_mode}")
        
        # Initialize (this starts sync server and file watcher)
        try:
            await app.initialize()
            print_info("App initialized successfully")
            
            # Give it a moment
            await asyncio.sleep(1)
            
            # Check sync server is running
            assert app._sync_server_task is not None
            print_info("Sync server task running")
            
            # Clean up
            await app.close()
            print_info("App closed cleanly")
            
        except Exception as e:
            print_error(f"App initialization failed: {e}")
            await app.close()
            raise
    
    return True


def run_sync_tests():
    """Run async tests."""
    print_header("ASYNC TESTS")
    
    runner = TestRunner()
    
    # Test sync server
    try:
        result = asyncio.run(test_sync_server())
        if result:
            runner.passed += 1
            print_success("WebSocket Sync Server - PASSED")
        else:
            runner.failed += 1
            print_error("WebSocket Sync Server - FAILED")
    except Exception as e:
        runner.failed += 1
        print_error(f"WebSocket Sync Server - ERROR: {e}")
    
    # Test app integration
    try:
        result = asyncio.run(test_app_integration())
        if result:
            runner.passed += 1
            print_success("App Integration - PASSED")
        else:
            runner.failed += 1
            print_error("App Integration - FAILED")
    except Exception as e:
        runner.failed += 1
        print_error(f"App Integration - ERROR: {e}")
    
    return runner


def main():
    """Run all tests."""
    print_header("PKM-AGENT COMPREHENSIVE TEST SUITE")
    print("Testing Phase 1 & 2 Implementations\n")
    
    runner = TestRunner()
    
    # Test 1: Imports
    print_header("TEST 1: MODULE IMPORTS")
    runner.test("Import all new modules", test_imports)
    
    # Test 2: Exception Hierarchy
    print_header("TEST 2: EXCEPTION HIERARCHY")
    runner.test("Exception hierarchy functionality", test_exception_hierarchy)
    
    # Test 3: Link Analyzer
    print_header("TEST 3: LINK ANALYZER")
    runner.test("Link analyzer with sample vault", test_link_analyzer)
    
    # Test 4: Link Validator
    print_header("TEST 4: LINK VALIDATOR")
    runner.test("Link validator fuzzy matching", test_link_validator)
    
    # Test 5: Link Healer
    print_header("TEST 5: LINK HEALER")
    runner.test("Link healer (dry run and real)", test_link_healer)
    
    # Test 6: File Watcher
    print_header("TEST 6: FILE WATCHER")
    runner.test("File watcher event detection", test_file_watcher_basic)
    
    # Run async tests
    async_runner = run_sync_tests()
    runner.passed += async_runner.passed
    runner.failed += async_runner.failed
    runner.warnings += async_runner.warnings
    
    # Summary
    success = runner.summary()
    
    # Save results
    results_file = Path("test_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "passed": runner.passed,
            "failed": runner.failed,
            "warnings": runner.warnings,
            "results": runner.results
        }, f, indent=2)
    
    print_info(f"Results saved to {results_file}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
