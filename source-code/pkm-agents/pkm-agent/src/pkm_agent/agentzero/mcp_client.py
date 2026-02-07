"""
MCP (Model Context Protocol) Client for Obsidian integration.

This module provides a client for communicating with the Obsidian MCP server
and the PKM RAG MCP server.
"""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base MCP error."""

    pass


@dataclass
class MCPMessage:
    """MCP protocol message."""

    jsonrpc: str = "2.0"
    id: str | None = None
    method: str | None = None
    params: dict[str, Any] | None = None
    result: Any | None = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data: dict[str, Any] = {"jsonrpc": self.jsonrpc}
        if self.id:
            data["id"] = self.id
        if self.method:
            data["method"] = self.method
        if self.params is not None:
            data["params"] = self.params
        if self.result is not None:
            data["result"] = self.result
        if self.error:
            data["error"] = self.error
        return data


class MCPClientError(Exception):
    """Base exception for MCP client errors."""

    pass


class MCPConnectionError(MCPClientError):
    """Connection error."""

    pass


class MCPResponseError(MCPClientError):
    """Error response from MCP server."""

    pass


class BaseMCPClient:
    """Base MCP client implementation."""

    def __init__(self, server_url: str, timeout: int = 30):
        self.server_url = server_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: aiohttp.ClientSession | None = None
        self.request_id = 0

    async def connect(self):
        """Establish connection to MCP server."""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            logger.info(f"Connected to MCP server at {self.server_url}")

    async def disconnect(self):
        """Close connection to MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from MCP server")

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a request to the MCP server."""
        if not self.session:
            raise MCPConnectionError("Not connected to MCP server")

        self.request_id += 1
        message_id = str(self.request_id)

        message = MCPMessage(id=message_id, method=method, params=params or {})

        try:
            async with self.session.post(
                f"{self.server_url}/rpc",
                json=message.to_dict(),
                headers={"Content-Type": "application/json"},
            ) as response:
                response_data = await response.json()

                if "error" in response_data:
                    raise MCPResponseError(
                        f"MCP error: {response_data['error'].get('message', 'Unknown error')}"
                    )

                return response_data.get("result")
        except aiohttp.ClientError as e:
            raise MCPConnectionError(f"Connection error: {e}")
        except json.JSONDecodeError as e:
            raise MCPResponseError(f"Invalid JSON response: {e}")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from MCP server."""
        return await self._send_request("tools/list")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        return await self._send_request("tools/call", {"name": tool_name, "arguments": arguments})

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources from MCP server."""
        return await self._send_request("resources/list")

    async def read_resource(self, uri: str) -> str:
        """Read a resource from the MCP server."""
        result = await self._send_request("resources/read", {"uri": uri})
        return result.get("contents", "")

    async def list_prompts(self) -> list[dict[str, Any]]:
        """List available prompts from MCP server."""
        return await self._send_request("prompts/list")

    async def get_prompt(self, prompt_name: str, arguments: dict[str, Any] | None = None) -> str:
        """Get a prompt from the MCP server."""
        result = await self._send_request(
            "prompts/get", {"name": prompt_name, "arguments": arguments or {}}
        )
        return result.get("messages", [])


class ObsidianMCPClient(BaseMCPClient):
    """MCP client specifically for Obsidian vault operations."""

    def __init__(self, config: dict[str, Any]):
        base_url = config.get("base_url", "http://127.0.0.1:27123")
        api_key = config.get("api_key", "")
        self.api_key = api_key
        super().__init__(base_url)

    async def connect(self):
        """Connect to Obsidian MCP server with authentication."""
        await BaseMCPClient.connect(self)
        # Verify connection
        try:
            tools = await self.list_tools()
            logger.info(f"Obsidian MCP server available with {len(tools)} tools")
        except (MCPError, MCPClientError) as e:
            logger.error(f"Failed to connect to Obsidian MCP server: {e}")
            raise

    async def read_note(self, path: str, format: str = "markdown") -> dict[str, Any]:
        """Read a note from the vault."""
        return await self.call_tool("obsidian_read_note", {"path": path, "format": format})

    async def update_note(self, path: str, content: str, mode: str = "overwrite") -> dict[str, Any]:
        """Update a note in the vault."""
        return await self.call_tool(
            "obsidian_update_note", {"path": path, "content": content, "mode": mode}
        )

    async def search_and_replace(
        self,
        path: str,
        search: str,
        replace: str,
        use_regex: bool = False,
        case_sensitive: bool = False,
        replace_all: bool = True,
    ) -> dict[str, Any]:
        """Search and replace text in a note."""
        return await self.call_tool(
            "obsidian_search_replace",
            {
                "path": path,
                "search": search,
                "replace": replace,
                "use_regex": use_regex,
                "case_sensitive": case_sensitive,
                "replace_all": replace_all,
            },
        )

    async def global_search(
        self,
        query: str,
        use_regex: bool = False,
        path_filter: str | None = None,
        modified_after: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search across the entire vault."""
        return await self.call_tool(
            "obsidian_global_search",
            {
                "query": query,
                "use_regex": use_regex,
                "path_filter": path_filter,
                "modified_after": modified_after,
                "limit": limit,
            },
        )

    async def list_notes(
        self,
        directory: str = "/",
        extension_filter: str | None = None,
        name_regex: str | None = None,
    ) -> dict[str, Any]:
        """List notes in a directory."""
        return await self.call_tool(
            "obsidian_list_notes",
            {
                "directory": directory,
                "extension_filter": extension_filter,
                "name_regex": name_regex,
            },
        )

    async def manage_frontmatter(
        self, path: str, action: str = "get", key: str | None = None, value: Any | None = None
    ) -> dict[str, Any]:
        """Manage frontmatter of a note."""
        params: dict[str, Any] = {"path": path, "action": action}
        if key:
            params["key"] = key
        if value is not None:
            params["value"] = value

        return await self.call_tool("obsidian_manage_frontmatter", params)

    async def manage_tags(
        self, path: str, action: str = "list", tags: list[str] | None = None
    ) -> dict[str, Any]:
        """Manage tags of a note."""
        params: dict[str, Any] = {"path": path, "action": action}
        if tags:
            params["tags"] = tags

        return await self.call_tool("obsidian_manage_tags", params)

    async def delete_note(self, path: str) -> dict[str, Any]:
        """Delete a note from the vault."""
        return await self.call_tool("obsidian_delete_note", {"path": path})

    async def get_active_file(self) -> str | None:
        """Get the path of the currently active file."""
        result = await self.call_tool(
            "obsidian_update_note", {"path": "", "content": "", "mode": "get_active"}
        )
        return result.get("active_file")

    # =====================================================================
    # Extended Obsidian Operations
    # =====================================================================

    async def create_note(
        self,
        path: str,
        content: str,
        frontmatter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new note with optional frontmatter.

        Args:
            path: Path for the new note (e.g., "folder/note.md")
            content: Markdown content for the note
            frontmatter: Optional YAML frontmatter as dictionary

        Returns:
            Result with success status and created path
        """
        # Build content with frontmatter if provided
        full_content = content
        if frontmatter:
            if yaml is not None:
                fm_str = yaml.dump(frontmatter, default_flow_style=False)
            else:
                # Fallback simple YAML serialization
                fm_lines = []
                for k, v in frontmatter.items():
                    if isinstance(v, list):
                        fm_lines.append(f"{k}:")
                        for item in v:
                            fm_lines.append(f"  - {item}")
                    else:
                        fm_lines.append(f"{k}: {v}")
                fm_str = "\n".join(fm_lines)
            full_content = f"---\n{fm_str}---\n\n{content}"

        return await self.update_note(path, full_content, mode="overwrite")

    async def append_to_note(self, path: str, content: str) -> dict[str, Any]:
        """
        Append content to an existing note.

        Args:
            path: Path to the note
            content: Content to append

        Returns:
            Result with success status
        """
        return await self.update_note(path, content, mode="append")

    async def prepend_to_note(self, path: str, content: str) -> dict[str, Any]:
        """
        Prepend content to an existing note (after frontmatter).

        Args:
            path: Path to the note
            content: Content to prepend

        Returns:
            Result with success status
        """
        return await self.update_note(path, content, mode="prepend")

    async def get_periodic_note(
        self,
        period: str = "daily",
        date: str | None = None,
    ) -> dict[str, Any]:
        """
        Get a periodic note (daily, weekly, monthly, etc.).

        Args:
            period: Type of periodic note ("daily", "weekly", "monthly", "quarterly", "yearly")
            date: Optional date string (defaults to current date)

        Returns:
            Note content and metadata
        """
        # Use Obsidian's periodic notes plugin conventions
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Common periodic note path patterns
        period_formats = {
            "daily": f"Daily Notes/{date}.md",
            "weekly": f"Weekly Notes/{datetime.now().strftime('%Y-W%W')}.md",
            "monthly": f"Monthly Notes/{datetime.now().strftime('%Y-%m')}.md",
            "quarterly": f"Quarterly Notes/{datetime.now().strftime('%Y-Q')}{(datetime.now().month - 1) // 3 + 1}.md",
            "yearly": f"Yearly Notes/{datetime.now().strftime('%Y')}.md",
        }

        path = period_formats.get(period, period_formats["daily"])

        try:
            return await self.read_note(path)
        except MCPResponseError:
            # Note doesn't exist, return empty result
            return {"path": path, "content": "", "exists": False}

    async def get_active_note(self) -> dict[str, Any]:
        """
        Get the currently active note in Obsidian.

        Returns:
            Active note content and metadata, or None if no note is active
        """
        active_path = await self.get_active_file()
        if active_path:
            return await self.read_note(active_path)
        return {"path": None, "content": "", "exists": False}

    async def update_active_note(
        self,
        content: str,
        mode: str = "append",
    ) -> dict[str, Any]:
        """
        Update the currently active note.

        Args:
            content: Content to add/update
            mode: Update mode ("overwrite", "append", "prepend")

        Returns:
            Result with success status
        """
        active_path = await self.get_active_file()
        if not active_path:
            raise MCPClientError("No active file in Obsidian")
        return await self.update_note(active_path, content, mode)

    async def search_in_path(
        self,
        query: str,
        path_filter: str,
        use_regex: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search within a specific path/folder.

        Args:
            query: Search query
            path_filter: Path prefix to filter results
            use_regex: Whether to use regex matching
            limit: Maximum results to return

        Returns:
            Search results filtered by path
        """
        return await self.global_search(
            query=query,
            use_regex=use_regex,
            path_filter=path_filter,
            limit=limit,
        )

    async def get_frontmatter(self, path: str) -> dict[str, Any]:
        """
        Get all frontmatter from a note.

        Args:
            path: Path to the note

        Returns:
            Dictionary of frontmatter key-value pairs
        """
        result = await self.manage_frontmatter(path, action="get")
        return result.get("frontmatter", {})

    async def set_frontmatter_key(
        self,
        path: str,
        key: str,
        value: Any,
    ) -> dict[str, Any]:
        """
        Set a single frontmatter key.

        Args:
            path: Path to the note
            key: Frontmatter key to set
            value: Value to set

        Returns:
            Result with success status
        """
        return await self.manage_frontmatter(path, action="set", key=key, value=value)

    async def delete_frontmatter_key(self, path: str, key: str) -> dict[str, Any]:
        """
        Delete a frontmatter key.

        Args:
            path: Path to the note
            key: Frontmatter key to delete

        Returns:
            Result with success status
        """
        return await self.manage_frontmatter(path, action="delete", key=key)

    async def get_tags(self, path: str) -> list[str]:
        """
        Get all tags from a note.

        Args:
            path: Path to the note

        Returns:
            List of tags (without # prefix)
        """
        result = await self.manage_tags(path, action="list")
        return result.get("tags", [])

    async def add_tags(self, path: str, tags: list[str]) -> dict[str, Any]:
        """
        Add tags to a note.

        Args:
            path: Path to the note
            tags: List of tags to add (with or without # prefix)

        Returns:
            Result with success status
        """
        # Normalize tags (remove # if present)
        normalized_tags = [t.lstrip("#") for t in tags]
        return await self.manage_tags(path, action="add", tags=normalized_tags)

    async def remove_tags(self, path: str, tags: list[str]) -> dict[str, Any]:
        """
        Remove tags from a note.

        Args:
            path: Path to the note
            tags: List of tags to remove

        Returns:
            Result with success status
        """
        normalized_tags = [t.lstrip("#") for t in tags]
        return await self.manage_tags(path, action="remove", tags=normalized_tags)

    async def get_note_links(self, path: str) -> dict[str, list[str]]:
        """
        Get all links from a note (outgoing links).

        Args:
            path: Path to the note

        Returns:
            Dictionary with 'internal_links' and 'external_links'
        """
        note = await self.read_note(path)
        content = note.get("content", "")

        import re

        # Extract internal links [[...]]
        internal_pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
        internal_links = re.findall(internal_pattern, content)

        # Extract external links [text](url)
        external_pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
        external_matches = re.findall(external_pattern, content)
        external_links = [url for _, url in external_matches]

        return {
            "internal_links": list(set(internal_links)),
            "external_links": list(set(external_links)),
        }

    async def get_backlinks(self, path: str) -> list[dict[str, Any]]:
        """
        Get all notes that link to the specified note.

        Args:
            path: Path to the note

        Returns:
            List of notes with backlinks and context
        """
        # Extract note name without extension for link matching
        note_name = path.rsplit("/", 1)[-1].replace(".md", "")

        # Search for links to this note
        results = await self.global_search(
            query=f"[[{note_name}]]",
            use_regex=False,
            limit=100,
        )

        return results.get("results", [])

    async def batch_update_frontmatter(
        self,
        paths: list[str],
        updates: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Update frontmatter across multiple notes.

        Args:
            paths: List of note paths
            updates: Dictionary of frontmatter updates to apply

        Returns:
            List of results for each note
        """
        results = []
        for path in paths:
            try:
                for key, value in updates.items():
                    await self.set_frontmatter_key(path, key, value)
                results.append({"path": path, "success": True})
            except Exception as e:
                results.append({"path": path, "success": False, "error": str(e)})
        return results

    async def batch_add_tags(
        self,
        paths: list[str],
        tags: list[str],
    ) -> list[dict[str, Any]]:
        """
        Add tags to multiple notes.

        Args:
            paths: List of note paths
            tags: Tags to add to all notes

        Returns:
            List of results for each note
        """
        results = []
        for path in paths:
            try:
                await self.add_tags(path, tags)
                results.append({"path": path, "success": True})
            except Exception as e:
                results.append({"path": path, "success": False, "error": str(e)})
        return results


class PKMRAGMCPClient(BaseMCPClient):
    """MCP client for PKM RAG operations."""

    def __init__(self, config: dict[str, Any]):
        base_url = config.get("base_url", "http://127.0.0.1:27124")
        super().__init__(base_url)

    async def connect(self):
        """Connect to PKM RAG MCP server."""
        await BaseMCPClient.connect(self)
        try:
            tools = await self.list_tools()
            logger.info(f"PKM RAG MCP server available with {len(tools)} tools")
        except (MCPError, MCPClientError) as e:
            logger.error(f"Failed to connect to PKM RAG MCP server: {e}")
            raise

    async def search(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search the knowledge base."""
        result = await self.call_tool(
            "pkm_search", {"query": query, "limit": limit, "filters": filters or {}}
        )
        return result.get("results", [])

    async def ask(
        self, message: str, conversation_id: str | None = None, use_context: bool = True
    ) -> AsyncIterator[str]:
        """Ask a question with optional context."""
        result = await self.call_tool(
            "pkm_ask",
            {"message": message, "conversation_id": conversation_id, "use_context": use_context},
        )

        # Stream response if available
        if isinstance(result, dict) and "stream_id" in result:
            stream_id = result["stream_id"]
            while True:
                chunk_result = await self._send_request(
                    "stream/get_chunk", {"stream_id": stream_id}
                )
                if chunk_result.get("done"):
                    break
                yield chunk_result.get("content", "")
        elif isinstance(result, str):
            yield result
        else:
            yield str(result)

    async def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        return await self.call_tool("pkm_get_stats", {})

    async def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations."""
        result = await self.call_tool("pkm_list_conversations", {})
        return result.get("conversations", [])


class UnifiedMCPClient:
    """Unified client that manages multiple MCP servers."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.obsidian_client: ObsidianMCPClient | None = None
        self.pkm_rag_client: PKMRAGMCPClient | None = None

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        if "obsidian" in self.config:
            self.obsidian_client = ObsidianMCPClient(self.config["obsidian"])
            await self.obsidian_client.connect()

        if "pkm_rag" in self.config:
            self.pkm_rag_client = PKMRAGMCPClient(self.config["pkm_rag"])
            await self.pkm_rag_client.connect()

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        if self.obsidian_client:
            await self.obsidian_client.disconnect()

        if self.pkm_rag_client:
            await self.pkm_rag_client.disconnect()

    def get_obsidian_client(self) -> ObsidianMCPClient | None:
        """Get the Obsidian MCP client."""
        return self.obsidian_client

    def get_pkm_rag_client(self) -> PKMRAGMCPClient | None:
        """Get the PKM RAG MCP client."""
        return self.pkm_rag_client

    async def get_all_tools(self) -> dict[str, list[dict[str, Any]]]:
        """Get tools from all connected servers."""
        tools = {}

        if self.obsidian_client:
            tools["obsidian"] = await self.obsidian_client.list_tools()

        if self.pkm_rag_client:
            tools["pkm_rag"] = await self.pkm_rag_client.list_tools()

        return tools


async def create_unified_client(config: dict[str, Any]) -> UnifiedMCPClient:
    """Create and connect a unified MCP client."""
    client = UnifiedMCPClient(config)
    await client.connect_all()
    return client
