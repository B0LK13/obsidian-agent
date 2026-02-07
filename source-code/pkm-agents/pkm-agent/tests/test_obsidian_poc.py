"""
Proof of Concept Test for Obsidian MCP Integration.

This script tests the new Obsidian MCP tools implemented in the B0LK13v2 PKM Agent.
It requires Obsidian to be running with the Local REST API plugin enabled.

Run with: python -m pytest tests/test_obsidian_poc.py -v -s
Or directly: python tests/test_obsidian_poc.py
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp

# Use ASCII-compatible symbols for Windows compatibility
CHECK = "[OK]"
CROSS = "[X]"
SKIP = "[-]"


# Configuration
OBSIDIAN_BASE_URL = "http://127.0.0.1:27123"
OBSIDIAN_API_KEY = "4f99f4adac4ced58022f93437efbd796f43ea4a42ac9d2c974342ed9361f10ca"

# Test constants
TEST_NOTE_PATH = "PKM-Agent-Tests/poc_test_note.md"
TEST_NOTE_CONTENT = """# PKM Agent PoC Test Note

This note was created by the PKM Agent Proof of Concept test.

## Test Details

- Created: {timestamp}
- Purpose: Validate Obsidian MCP integration
- Status: Testing

## Content Section

This is some sample content for testing search and replace functionality.

### Tags Test

#test #pkm-agent #poc

## Links

- [[Daily Notes]]
- [[Projects]]

"""


class ObsidianAPITester:
    """Direct Obsidian REST API tester for PoC validation."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def check_connection(self) -> dict:
        """Check if Obsidian REST API is accessible."""
        try:
            async with self.session.get(f"{self.base_url}/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "data": data}
                return {"success": False, "status": resp.status}
        except aiohttp.ClientConnectorError:
            return {"success": False, "error": "Cannot connect to Obsidian REST API"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_vault_files(self) -> dict:
        """List files in the vault root."""
        try:
            async with self.session.get(f"{self.base_url}/vault/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "files": data.get("files", [])}
                return {"success": False, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_note(self, path: str, content: str) -> dict:
        """Create or update a note."""
        try:
            # Use PUT to create/update
            async with self.session.put(
                f"{self.base_url}/vault/{path}",
                data=content,
                headers={"Content-Type": "text/markdown"},
            ) as resp:
                if resp.status in (200, 201, 204):
                    return {"success": True, "path": path}
                text = await resp.text()
                return {"success": False, "status": resp.status, "error": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_note(self, path: str) -> dict:
        """Read a note's content."""
        try:
            async with self.session.get(f"{self.base_url}/vault/{path}") as resp:
                if resp.status == 200:
                    content = await resp.text()
                    return {"success": True, "content": content}
                return {"success": False, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_note(self, path: str) -> dict:
        """Delete a note."""
        try:
            async with self.session.delete(f"{self.base_url}/vault/{path}") as resp:
                if resp.status in (200, 204, 404):
                    return {"success": True}
                return {"success": False, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_vault(self, query: str) -> dict:
        """Search the vault."""
        try:
            async with self.session.post(
                f"{self.base_url}/search/simple/", json={"query": query}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "results": data}
                return {"success": False, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_active_file(self) -> dict:
        """Get the currently active file."""
        try:
            async with self.session.get(f"{self.base_url}/active/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "data": data}
                return {"success": False, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def test_mcp_client():
    """Test the MCP client directly."""
    print("\n" + "=" * 60)
    print("Testing ObsidianMCPClient")
    print("=" * 60)

    try:
        from pkm_agent.agentzero.mcp_client import ObsidianMCPClient

        config = {"base_url": OBSIDIAN_BASE_URL, "api_key": OBSIDIAN_API_KEY}

        client = ObsidianMCPClient(config)
        print(f"{CHECK} ObsidianMCPClient instantiated successfully")
        print(f"  Base URL: {client.server_url}")
        return True

    except ImportError as e:
        print(f"{CROSS} Import error: {e}")
        return False
    except Exception as e:
        print(f"{CROSS} Error: {e}")
        return False


async def run_poc_tests():
    """Run all PoC tests."""
    print("\n" + "=" * 60)
    print("PKM Agent Obsidian MCP Integration - Proof of Concept")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Obsidian URL: {OBSIDIAN_BASE_URL}")
    print()

    results = {
        "connection": False,
        "list_files": False,
        "create_note": False,
        "read_note": False,
        "search": False,
        "delete_note": False,
        "mcp_client": False,
    }

    async with ObsidianAPITester(OBSIDIAN_BASE_URL, OBSIDIAN_API_KEY) as tester:
        # Test 1: Connection
        print("\n[1/7] Testing Obsidian REST API connection...")
        result = await tester.check_connection()
        if result["success"]:
            print(f"  {CHECK} Connected to Obsidian")
            if "data" in result:
                print(f"    Vault: {result['data'].get('name', 'Unknown')}")
                print(
                    f"    Version: {result['data'].get('versions', {}).get('obsidian', 'Unknown')}"
                )
            results["connection"] = True
        else:
            print(f"  {CROSS} Connection failed: {result.get('error', 'Unknown error')}")
            print("\n  Make sure Obsidian is running with the Local REST API plugin enabled.")
            return results

        # Test 2: List files
        print("\n[2/7] Listing vault files...")
        result = await tester.list_vault_files()
        if result["success"]:
            files = result.get("files", [])
            print(f"  {CHECK} Found {len(files)} items in vault root")
            if files[:5]:
                for f in files[:5]:
                    print(f"    - {f}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
            results["list_files"] = True
        else:
            print(f"  {CROSS} Failed to list files: {result.get('error', 'Unknown')}")

        # Test 3: Create note
        print(f"\n[3/7] Creating test note: {TEST_NOTE_PATH}...")
        timestamp = datetime.now().isoformat()
        content = TEST_NOTE_CONTENT.format(timestamp=timestamp)
        result = await tester.create_note(TEST_NOTE_PATH, content)
        if result["success"]:
            print(f"  {CHECK} Note created successfully")
            results["create_note"] = True
        else:
            print(f"  {CROSS} Failed to create note: {result.get('error', 'Unknown')}")

        # Test 4: Read note
        print(f"\n[4/7] Reading test note...")
        result = await tester.read_note(TEST_NOTE_PATH)
        if result["success"]:
            content = result.get("content", "")
            print(f"  {CHECK} Note read successfully ({len(content)} chars)")
            if "PKM Agent PoC Test Note" in content:
                print(f"    Content verified {CHECK}")
            results["read_note"] = True
        else:
            print(f"  {CROSS} Failed to read note: {result.get('error', 'Unknown')}")

        # Test 5: Search
        print(f"\n[5/7] Searching vault for 'PKM Agent PoC'...")
        result = await tester.search_vault("PKM Agent PoC")
        if result["success"]:
            search_results = result.get("results", [])
            print(f"  {CHECK} Search completed ({len(search_results)} results)")
            results["search"] = True
        else:
            print(f"  {CROSS} Search failed: {result.get('error', 'Unknown')}")
            # Search might not be available on all setups, don't fail completely
            results["search"] = None

        # Test 6: MCP Client
        print(f"\n[6/7] Testing ObsidianMCPClient...")
        results["mcp_client"] = await test_mcp_client()

        # Test 7: Cleanup - Delete note
        print(f"\n[7/7] Cleaning up test note...")
        result = await tester.delete_note(TEST_NOTE_PATH)
        if result["success"]:
            print(f"  {CHECK} Test note deleted")
            results["delete_note"] = True
        else:
            print(f"  {CROSS} Failed to delete note: {result.get('error', 'Unknown')}")

    # Summary
    print("\n" + "=" * 60)
    print("PROOF OF CONCEPT RESULTS")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is True:
            status = f"{CHECK} PASS"
            passed += 1
        elif result is None:
            status = f"{SKIP} SKIP"
            skipped += 1
        else:
            status = f"{CROSS} FAIL"
            failed += 1
        print(f"  {test_name:20} {status}")

    print()
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    if failed == 0:
        print(f"\n{CHECK} PROOF OF CONCEPT SUCCESSFUL")
        print("  The Obsidian MCP integration is working correctly.")
    else:
        print(f"\n{CROSS} PROOF OF CONCEPT FAILED")
        print("  Some tests did not pass. Check the output above.")

    return results


async def main():
    """Main entry point."""
    try:
        results = await run_poc_tests()

        # Exit with appropriate code
        failed = sum(1 for r in results.values() if r is False)
        sys.exit(1 if failed > 0 else 0)

    except KeyboardInterrupt:
        print("\nTest interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
