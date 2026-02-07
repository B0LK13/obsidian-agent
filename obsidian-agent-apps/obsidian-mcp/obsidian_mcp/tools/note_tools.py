"""Note management tools for Obsidian MCP."""

import json
from typing import Any, Dict, List
from datetime import datetime

from obsidian_mcp.client import ObsidianClient


async def create_note(path: str, content: str, folder: str = "") -> str:
    """Create a new note in the vault.
    
    Args:
        path: Note path (e.g., "Projects/Idea" or "Projects/Idea.md")
        content: Note content in Markdown
        folder: Optional folder path (prepended to path)
        
    Returns:
        JSON string with creation result
    """
    client = ObsidianClient()
    
    try:
        if folder:
            path = f"{folder}/{path}"
        
        result = await client.create_note(path, content)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Created note: {path}",
            "path": path,
            "content_length": len(content),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def read_note(path: str) -> str:
    """Read a note's content.
    
    Args:
        path: Path to the note
        
    Returns:
        Note content or error message
    """
    client = ObsidianClient()
    
    try:
        content = await client.read_note(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "content": content,
            "length": len(content),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def update_note(path: str, content: str) -> str:
    """Update an existing note.
    
    Args:
        path: Path to the note
        content: New content
        
    Returns:
        JSON string with update result
    """
    client = ObsidianClient()
    
    try:
        result = await client.update_note(path, content)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Updated note: {path}",
            "path": path,
            "content_length": len(content),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def delete_note(path: str) -> str:
    """Delete a note.
    
    Args:
        path: Path to the note
        
    Returns:
        JSON string with deletion result
    """
    client = ObsidianClient()
    
    try:
        result = await client.delete_note(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Deleted note: {path}",
            "path": path,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def list_notes(folder: str = "", extension: str = ".md") -> str:
    """List all notes in the vault or a specific folder.
    
    Args:
        folder: Optional folder to list (empty for root)
        extension: File extension filter (default: .md)
        
    Returns:
        JSON string with list of notes
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files(folder)
        await client.close()
        
        # Filter by extension
        if extension:
            files = [f for f in files if f.endswith(extension)]
        
        return json.dumps({
            "success": True,
            "count": len(files),
            "folder": folder or "root",
            "notes": files,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def search_notes(query: str) -> str:
    """Search for notes containing specific text.
    
    Args:
        query: Search query text
        
    Returns:
        JSON string with search results
    """
    client = ObsidianClient()
    
    try:
        results = await client.search(query)
        await client.close()
        
        return json.dumps({
            "success": True,
            "query": query,
            "count": len(results),
            "results": results,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def search_by_tag(tag: str) -> str:
    """Search for notes with a specific tag.
    
    Args:
        tag: Tag to search for (with or without #)
        
    Returns:
        JSON string with matching notes
    """
    client = ObsidianClient()
    
    try:
        results = await client.search_by_tag(tag)
        await client.close()
        
        return json.dumps({
            "success": True,
            "tag": tag,
            "count": len(results),
            "results": results,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_note_metadata(path: str) -> str:
    """Get metadata about a note.
    
    Args:
        path: Path to the note
        
    Returns:
        JSON string with metadata
    """
    client = ObsidianClient()
    
    try:
        metadata = await client.get_file_metadata(path)
        tags = await client.get_tags_in_note(path)
        links = await client.get_outgoing_links(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "metadata": metadata,
            "tags": tags,
            "outgoing_links": links,
            "link_count": len(links),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def append_to_note(path: str, content: str, prepend_newline: bool = True) -> str:
    """Append content to an existing note.
    
    Args:
        path: Path to the note
        content: Content to append
        prepend_newline: Whether to add newline before content
        
    Returns:
        JSON string with append result
    """
    client = ObsidianClient()
    
    try:
        if prepend_newline:
            content = "\n\n" + content
        
        result = await client.append_to_note(path, content)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Appended to note: {path}",
            "path": path,
            "appended_length": len(content),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def create_daily_note(date: str = None, content: str = "") -> str:
    """Create a daily note for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
        content: Optional content (uses template if empty)
        
    Returns:
        JSON string with created note info
    """
    client = ObsidianClient()
    
    try:
        result = await client.create_daily_note(date, content)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Created daily note: {result['path']}",
            **result,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_daily_note(date: str = None) -> str:
    """Get a daily note for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
        
    Returns:
        JSON string with note content
    """
    client = ObsidianClient()
    
    try:
        result = await client.get_daily_note(date)
        await client.close()
        
        return json.dumps({
            "success": True,
            **result,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_note_links(path: str) -> str:
    """Get all links in a note (both outgoing and incoming).
    
    Args:
        path: Path to the note
        
    Returns:
        JSON string with links analysis
    """
    client = ObsidianClient()
    
    try:
        outgoing = await client.get_outgoing_links(path)
        backlinks = await client.get_backlinks(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "outgoing_links": outgoing,
            "outgoing_count": len(outgoing),
            "backlinks": backlinks,
            "backlink_count": len(backlinks),
            "total_connections": len(outgoing) + len(backlinks),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
