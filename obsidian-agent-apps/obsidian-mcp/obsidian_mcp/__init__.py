"""
Obsidian MCP Server - Comprehensive note management through Model Context Protocol.

This package provides 46+ tools for managing Obsidian vaults via MCP:
- Note CRUD operations
- Link and graph analysis
- Tag management
- Search and query
- Templates and automation
"""

__version__ = "1.0.0"
__author__ = "Obsidian MCP Team"

from obsidian_mcp.client import ObsidianClient
from obsidian_mcp.exceptions import ObsidianError, NoteNotFoundError, APIError

__all__ = [
    "ObsidianClient",
    "ObsidianError",
    "NoteNotFoundError",
    "APIError",
]
