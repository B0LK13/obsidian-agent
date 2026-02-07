"""Obsidian MCP Server - 46+ tools for note management."""

import asyncio
import json
from typing import Any, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import structlog

from obsidian_mcp.config import get_settings
from obsidian_mcp import tools as obsidian_tools

logger = structlog.get_logger()


def create_server() -> Server:
    """Create and configure the Obsidian MCP server."""
    settings = get_settings()
    
    server = Server(settings.server_name)
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available tools."""
        return [
            # Note Management (12 tools)
            Tool(
                name="create_note",
                description="Create a new note in the Obsidian vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Note path (e.g., 'Projects/Idea')"},
                        "content": {"type": "string", "description": "Note content in Markdown"},
                        "folder": {"type": "string", "description": "Optional folder path"},
                    },
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name="read_note",
                description="Read a note's content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="update_note",
                description="Update an existing note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                        "content": {"type": "string", "description": "New content"},
                    },
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name="delete_note",
                description="Delete a note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="list_notes",
                description="List all notes in the vault or a folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "description": "Optional folder to list"},
                        "extension": {"type": "string", "description": "File extension filter", "default": ".md"},
                    },
                },
            ),
            Tool(
                name="search_notes",
                description="Search for notes containing specific text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_by_tag",
                description="Search for notes with a specific tag",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tag": {"type": "string", "description": "Tag to search for"},
                    },
                    "required": ["tag"],
                },
            ),
            Tool(
                name="get_note_metadata",
                description="Get metadata about a note (tags, links, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="append_to_note",
                description="Append content to an existing note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                        "content": {"type": "string", "description": "Content to append"},
                        "prepend_newline": {"type": "boolean", "description": "Add newline before content", "default": True},
                    },
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name="create_daily_note",
                description="Create a daily note for a specific date",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format (default: today)"},
                        "content": {"type": "string", "description": "Optional content"},
                    },
                },
            ),
            Tool(
                name="get_daily_note",
                description="Get a daily note for a specific date",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format (default: today)"},
                    },
                },
            ),
            Tool(
                name="get_note_links",
                description="Get all links in a note (incoming and outgoing)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            
            # Link & Graph Analysis (8 tools)
            Tool(
                name="get_backlinks",
                description="Get all notes that link to this note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="get_forward_links",
                description="Get all notes that this note links to",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="get_orphan_notes",
                description="Find all notes with no connections",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_hub_notes",
                description="Find the most connected notes (hubs)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of hubs to return", "default": 10},
                    },
                },
            ),
            Tool(
                name="get_shortest_path",
                description="Find shortest path between two notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_path": {"type": "string", "description": "Starting note"},
                        "to_path": {"type": "string", "description": "Target note"},
                    },
                    "required": ["from_path", "to_path"],
                },
            ),
            Tool(
                name="get_connected_notes",
                description="Get all notes connected to a note within a depth",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Starting note"},
                        "depth": {"type": "integer", "description": "Connection depth (1-3)", "default": 1},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="analyze_graph",
                description="Analyze the vault graph structure",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="suggest_links",
                description="Suggest potential links for a note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                    },
                    "required": ["path"],
                },
            ),
            
            # Tag Management (5 tools)
            Tool(
                name="list_all_tags",
                description="List all tags in the vault",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_tag_statistics",
                description="Get statistics about tag usage",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="rename_tag",
                description="Rename a tag across all notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "old_tag": {"type": "string", "description": "Current tag name"},
                        "new_tag": {"type": "string", "description": "New tag name"},
                    },
                    "required": ["old_tag", "new_tag"],
                },
            ),
            Tool(
                name="get_related_tags",
                description="Find tags that appear together with a given tag",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tag": {"type": "string", "description": "Tag to analyze"},
                    },
                    "required": ["tag"],
                },
            ),
            
            # Folder Management (6 tools)
            Tool(
                name="list_folders",
                description="List all folders in the vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Parent folder path"},
                    },
                },
            ),
            Tool(
                name="create_folder",
                description="Create a new folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path to create"},
                    },
                    "required": ["folder_path"],
                },
            ),
            Tool(
                name="move_note",
                description="Move a note to a different folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_path": {"type": "string", "description": "Current note path"},
                        "to_folder": {"type": "string", "description": "Target folder"},
                    },
                    "required": ["from_path", "to_folder"],
                },
            ),
            Tool(
                name="rename_note",
                description="Rename a note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "old_path": {"type": "string", "description": "Current path"},
                        "new_name": {"type": "string", "description": "New name (no extension)"},
                    },
                    "required": ["old_path", "new_name"],
                },
            ),
            Tool(
                name="get_folder_notes",
                description="Get all notes in a folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path"},
                    },
                    "required": ["folder_path"],
                },
            ),
            Tool(
                name="get_vault_statistics",
                description="Get vault statistics",
                inputSchema={"type": "object", "properties": {}},
            ),
            
            # Search Tools (5 tools)
            Tool(
                name="advanced_search",
                description="Advanced search with filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "use_regex": {"type": "boolean", "default": False},
                        "case_sensitive": {"type": "boolean", "default": False},
                        "in_title": {"type": "boolean", "default": False},
                        "in_content": {"type": "boolean", "default": True},
                        "folder": {"type": "string"},
                        "tag": {"type": "string"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_by_date",
                description="Search notes by date range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "date_format": {"type": "string", "enum": ["created", "modified"], "default": "modified"},
                    },
                },
            ),
            Tool(
                name="search_recent",
                description="Get recently modified notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Days to look back", "default": 7},
                    },
                },
            ),
            Tool(
                name="find_duplicates",
                description="Find potentially duplicate notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "threshold": {"type": "number", "description": "Similarity threshold (0-1)", "default": 0.8},
                    },
                },
            ),
            Tool(
                name="search_untagged",
                description="Find notes without tags",
                inputSchema={"type": "object", "properties": {}},
            ),
            
            # Template Tools (4 tools)
            Tool(
                name="apply_template",
                description="Apply a template to an existing note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note_path": {"type": "string"},
                        "template_name": {"type": "string", "enum": ["daily", "project", "meeting", "research"]},
                        "variables": {"type": "object"},
                    },
                    "required": ["note_path", "template_name"],
                },
            ),
            Tool(
                name="create_from_template",
                description="Create a new note from a template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note_path": {"type": "string"},
                        "template_name": {"type": "string", "enum": ["daily", "project", "meeting", "research"]},
                        "variables": {"type": "object"},
                    },
                    "required": ["note_path", "template_name"],
                },
            ),
            Tool(
                name="list_templates",
                description="List available templates",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="batch_create_notes",
                description="Create multiple notes at once",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "notes": {"type": "array", "description": "List of note definitions"},
                        "template_name": {"type": "string"},
                    },
                    "required": ["notes"],
                },
            ),
            
            # Canvas Tools (3 tools)
            Tool(
                name="list_canvases",
                description="List all canvas files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="read_canvas",
                description="Read a canvas file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "canvas_path": {"type": "string"},
                    },
                    "required": ["canvas_path"],
                },
            ),
            Tool(
                name="create_canvas",
                description="Create a new canvas",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "canvas_path": {"type": "string"},
                        "title": {"type": "string", "default": "New Canvas"},
                    },
                    "required": ["canvas_path"],
                },
            ),
            
            # External Tools (3 tools)
            Tool(
                name="extract_urls",
                description="Extract all URLs from the vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain_filter": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="get_external_links",
                description="Get external links from a note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note_path": {"type": "string"},
                    },
                    "required": ["note_path"],
                },
            ),
            Tool(
                name="create_bibliography",
                description="Create bibliography from source notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tag": {"type": "string", "default": "source"},
                    },
                },
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Execute a tool."""
        logger.info("Tool called", tool=name, arguments=arguments)
        
        try:
            # Map tool names to functions
            tool_map = {
                # Note tools
                "create_note": obsidian_tools.create_note,
                "read_note": obsidian_tools.read_note,
                "update_note": obsidian_tools.update_note,
                "delete_note": obsidian_tools.delete_note,
                "list_notes": obsidian_tools.list_notes,
                "search_notes": obsidian_tools.search_notes,
                "search_by_tag": obsidian_tools.search_by_tag,
                "get_note_metadata": obsidian_tools.get_note_metadata,
                "append_to_note": obsidian_tools.append_to_note,
                "create_daily_note": obsidian_tools.create_daily_note,
                "get_daily_note": obsidian_tools.get_daily_note,
                "get_note_links": obsidian_tools.get_note_links,
                
                # Link tools
                "get_backlinks": obsidian_tools.get_backlinks,
                "get_forward_links": obsidian_tools.get_forward_links,
                "get_orphan_notes": obsidian_tools.get_orphan_notes,
                "get_hub_notes": obsidian_tools.get_hub_notes,
                "get_shortest_path": obsidian_tools.get_shortest_path,
                "get_connected_notes": obsidian_tools.get_connected_notes,
                "analyze_graph": obsidian_tools.analyze_graph,
                "suggest_links": obsidian_tools.suggest_links,
                
                # Tag tools
                "list_all_tags": obsidian_tools.list_all_tags,
                "get_tag_statistics": obsidian_tools.get_tag_statistics,
                "rename_tag": obsidian_tools.rename_tag,
                "get_related_tags": obsidian_tools.get_related_tags,
                
                # Folder tools
                "list_folders": obsidian_tools.list_folders,
                "create_folder": obsidian_tools.create_folder,
                "move_note": obsidian_tools.move_note,
                "rename_note": obsidian_tools.rename_note,
                "get_folder_notes": obsidian_tools.get_folder_notes,
                "get_vault_statistics": obsidian_tools.get_vault_statistics,
                
                # Search tools
                "advanced_search": obsidian_tools.advanced_search,
                "search_by_date": obsidian_tools.search_by_date,
                "search_recent": obsidian_tools.search_recent,
                "find_duplicates": obsidian_tools.find_duplicates,
                "search_untagged": obsidian_tools.search_untagged,
                
                # Template tools
                "apply_template": obsidian_tools.apply_template,
                "create_from_template": obsidian_tools.create_from_template,
                "list_templates": obsidian_tools.list_templates,
                "batch_create_notes": obsidian_tools.batch_create_notes,
                
                # Canvas tools
                "list_canvases": obsidian_tools.list_canvases,
                "read_canvas": obsidian_tools.read_canvas,
                "create_canvas": obsidian_tools.create_canvas,
                
                # External tools
                "extract_urls": obsidian_tools.extract_urls,
                "get_external_links": obsidian_tools.get_external_links,
                "create_bibliography": obsidian_tools.create_bibliography,
            }
            
            if name not in tool_map:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
            
            # Execute tool
            result = await tool_map[name](**arguments)
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e))
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Tool execution failed: {str(e)}"})
            )]
    
    return server


async def main():
    """Run the MCP server."""
    server = create_server()
    
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
