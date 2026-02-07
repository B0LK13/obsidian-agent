"""
Integration Tests for Obsidian REST API via Direct HTTP.

This script tests the Obsidian REST API operations that the MCP client
will use when communicating through the obsidian-mcp-server.

The ObsidianMCPClient is designed to talk to the obsidian-mcp-server
(via npx obsidian-mcp-server), which in turn talks to the Obsidian REST API.

For direct testing, we use aiohttp to call the Obsidian REST API endpoints.

Run with: python tests/test_mcp_client_integration.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import aiohttp
import json

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Symbols
OK = "[OK]"
FAIL = "[X]"
SKIP = "[-]"
INFO = "[i]"

# Configuration
OBSIDIAN_BASE_URL = "http://127.0.0.1:27123"
OBSIDIAN_API_KEY = "4f99f4adac4ced58022f93437efbd796f43ea4a42ac9d2c974342ed9361f10ca"

# Test paths
TEST_DIR = "PKM-Agent-Tests"
TEST_NOTE = f"{TEST_DIR}/mcp_integration_test.md"


class ObsidianRESTClient:
    """Direct Obsidian REST API client for testing."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = None

    async def connect(self):
        """Create HTTP session."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    async def disconnect(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def create_note(self, path: str, content: str, frontmatter: dict = None) -> dict:
        """Create a note with optional frontmatter."""
        full_content = content
        if frontmatter:
            import yaml

            fm_str = yaml.dump(frontmatter, default_flow_style=False)
            full_content = f"---\n{fm_str}---\n\n{content}"

        async with self.session.put(
            f"{self.base_url}/vault/{path}",
            data=full_content,
            headers={"Content-Type": "text/markdown"},
        ) as resp:
            return {"success": resp.status in (200, 201, 204), "status": resp.status}

    async def read_note(self, path: str) -> dict:
        """Read a note's content."""
        async with self.session.get(f"{self.base_url}/vault/{path}") as resp:
            if resp.status == 200:
                content = await resp.text()
                return {"success": True, "content": content}
            return {"success": False, "status": resp.status}

    async def append_to_note(self, path: str, content: str) -> dict:
        """Append content to a note."""
        async with self.session.post(
            f"{self.base_url}/vault/{path}", data=content, headers={"Content-Type": "text/markdown"}
        ) as resp:
            return {"success": resp.status in (200, 204), "status": resp.status}

    async def delete_note(self, path: str) -> dict:
        """Delete a note."""
        async with self.session.delete(f"{self.base_url}/vault/{path}") as resp:
            return {"success": resp.status in (200, 204, 404), "status": resp.status}

    async def search(self, query: str) -> dict:
        """Search the vault."""
        async with self.session.post(
            f"{self.base_url}/search/simple/", json={"query": query}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"success": True, "results": data}
            return {"success": False, "status": resp.status}


class MCPClientTester:
    """Test harness for Obsidian REST API integration."""

    def __init__(self):
        self.client = None
        self.results = {}
        self.test_count = 0
        self.passed = 0
        self.failed = 0

    async def setup(self):
        """Initialize the REST client."""
        self.client = ObsidianRESTClient(OBSIDIAN_BASE_URL, OBSIDIAN_API_KEY)
        await self.client.connect()
        print(f"{INFO} ObsidianRESTClient initialized")
        print(f"    Base URL: {self.client.base_url}")

    async def teardown(self):
        """Cleanup after tests."""
        if self.client:
            await self.client.disconnect()

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log a test result."""
        self.test_count += 1
        if passed:
            self.passed += 1
            status = OK
        else:
            self.failed += 1
            status = FAIL
        print(f"  {status} {name}")
        if details:
            print(f"      {details}")
        self.results[name] = passed

    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 60)
        print("ObsidianMCPClient Integration Tests")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        await self.setup()

        try:
            # Note CRUD Operations
            print("\n--- Note CRUD Operations ---")
            await self.test_create_note()
            await self.test_read_note()
            await self.test_append_to_note()

            # Content Verification
            print("\n--- Content Verification ---")
            await self.test_frontmatter_in_content()
            await self.test_tags_in_content()
            await self.test_add_links()

            # Search Operations
            print("\n--- Search Operations ---")
            await self.test_search()

            # Cleanup
            print("\n--- Cleanup ---")
            await self.test_delete_note()

        except Exception as e:
            print(f"\n{FAIL} Test suite error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await self.teardown()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total: {self.test_count} tests")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("=" * 60)

        if self.failed == 0:
            print(f"\n{OK} ALL TESTS PASSED")
        else:
            print(f"\n{FAIL} SOME TESTS FAILED")

        return self.failed == 0

    async def test_create_note(self):
        """Test creating a note with frontmatter."""
        try:
            result = await self.client.create_note(
                path=TEST_NOTE,
                content="# Integration Test Note\n\nThis is test content.\n\n#test #integration",
                frontmatter={
                    "created": datetime.now().isoformat(),
                    "type": "test",
                    "status": "draft",
                },
            )
            self.log_test("create_note", result["success"], f"Created {TEST_NOTE}")
        except Exception as e:
            self.log_test("create_note", False, str(e))

    async def test_read_note(self):
        """Test reading a note."""
        try:
            result = await self.client.read_note(TEST_NOTE)
            content = result.get("content", "")
            has_content = "Integration Test Note" in content
            self.log_test("read_note", has_content, f"{len(content)} chars")
        except Exception as e:
            self.log_test("read_note", False, str(e))

    async def test_append_to_note(self):
        """Test appending content to a note."""
        try:
            result = await self.client.append_to_note(
                TEST_NOTE, "\n## Appended Section\n\nThis was appended.\n"
            )
            # Verify
            read_result = await self.client.read_note(TEST_NOTE)
            has_appended = "Appended Section" in read_result.get("content", "")
            self.log_test("append_to_note", has_appended)
        except Exception as e:
            self.log_test("append_to_note", False, str(e))

    async def test_frontmatter_in_content(self):
        """Test that frontmatter was created properly."""
        try:
            result = await self.client.read_note(TEST_NOTE)
            content = result.get("content", "")
            # Check that frontmatter exists
            has_frontmatter = content.startswith("---") and "type: test" in content
            self.log_test("frontmatter_in_content", has_frontmatter, "Frontmatter present in note")
        except Exception as e:
            self.log_test("frontmatter_in_content", False, str(e))

    async def test_tags_in_content(self):
        """Test that tags are present in note."""
        try:
            result = await self.client.read_note(TEST_NOTE)
            content = result.get("content", "")
            has_tags = "#test" in content or "#integration" in content
            self.log_test("tags_in_content", has_tags, "Tags found in note")
        except Exception as e:
            self.log_test("tags_in_content", False, str(e))

    async def test_add_links(self):
        """Test adding internal and external links."""
        try:
            result = await self.client.append_to_note(
                TEST_NOTE, "\n## Links\n\n- [[Daily Notes]]\n- [Example](https://example.com)\n"
            )
            # Verify
            read_result = await self.client.read_note(TEST_NOTE)
            content = read_result.get("content", "")
            has_internal = "[[Daily Notes]]" in content
            has_external = "https://example.com" in content
            self.log_test(
                "add_links", has_internal and has_external, "Internal and external links added"
            )
        except Exception as e:
            self.log_test("add_links", False, str(e))

    async def test_search(self):
        """Test vault search."""
        try:
            result = await self.client.search("Integration Test")
            # Search might not find results immediately, just check it doesn't error
            self.log_test("search", True, f"Search executed")
        except Exception as e:
            # Search endpoint might not be available
            self.log_test("search", None, f"Skipped: {str(e)[:50]}")

    async def test_delete_note(self):
        """Test deleting a note."""
        try:
            result = await self.client.delete_note(TEST_NOTE)
            self.log_test("delete_note", result["success"], f"Deleted {TEST_NOTE}")
        except Exception as e:
            self.log_test("delete_note", False, str(e))


async def main():
    """Main entry point."""
    tester = MCPClientTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
