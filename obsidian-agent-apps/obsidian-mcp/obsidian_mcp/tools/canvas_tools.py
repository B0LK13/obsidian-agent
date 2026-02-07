"""Canvas tools for Obsidian MCP."""

import json
from typing import List, Dict

from obsidian_mcp.client import ObsidianClient


async def list_canvases(folder: str = "") -> str:
    """List all canvas files in the vault.
    
    Args:
        folder: Optional folder to search in
        
    Returns:
        JSON string with canvas list
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files(folder)
        canvases = [f for f in files if f.endswith(".canvas")]
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "canvas_count": len(canvases),
            "folder": folder or "root",
            "canvases": canvases,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def read_canvas(canvas_path: str) -> str:
    """Read a canvas file.
    
    Args:
        canvas_path: Path to canvas file
        
    Returns:
        JSON string with canvas data
    """
    client = ObsidianClient()
    
    try:
        if not canvas_path.endswith(".canvas"):
            canvas_path += ".canvas"
        
        content = await client.read_note(canvas_path)
        
        # Try to parse as JSON (canvas files are JSON)
        try:
            canvas_data = json.loads(content)
            nodes = canvas_data.get("nodes", [])
            edges = canvas_data.get("edges", [])
            
            await client.close()
            
            return json.dumps({
                "success": True,
                "path": canvas_path,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "nodes": nodes,
                "edges": edges,
            }, indent=2)
        
        except json.JSONDecodeError:
            await client.close()
            return json.dumps({
                "success": True,
                "path": canvas_path,
                "raw_content": content,
            }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def create_canvas(canvas_path: str, title: str = "New Canvas") -> str:
    """Create a new canvas file.
    
    Args:
        canvas_path: Path for new canvas
        title: Canvas title
        
    Returns:
        JSON string with creation result
    """
    client = ObsidianClient()
    
    try:
        if not canvas_path.endswith(".canvas"):
            canvas_path += ".canvas"
        
        # Create empty canvas structure
        canvas_data = {
            "nodes": [],
            "edges": [],
        }
        
        await client.create_note(canvas_path, json.dumps(canvas_data, indent=2))
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Created canvas: {canvas_path}",
            "path": canvas_path,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
