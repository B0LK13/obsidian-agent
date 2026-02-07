"""Folder management tools for Obsidian MCP."""

import json
import os
from typing import List, Dict
from datetime import datetime

from obsidian_mcp.client import ObsidianClient


async def list_folders(path: str = "") -> str:
    """List all folders in the vault.
    
    Args:
        path: Optional parent folder path
        
    Returns:
        JSON string with folder list
    """
    client = ObsidianClient()
    
    try:
        all_files = await client.list_files(path)
        
        # Extract unique folders
        folders = set()
        for filepath in all_files:
            if "/" in filepath:
                folder = "/".join(filepath.split("/")[:-1])
                folders.add(folder)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "folder_count": len(folders),
            "folders": sorted(list(folders)),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def create_folder(folder_path: str) -> str:
    """Create a new folder (by creating a placeholder note).
    
    Args:
        folder_path: Folder path to create
        
    Returns:
        JSON string with creation result
    """
    client = ObsidianClient()
    
    try:
        # Create a placeholder note to establish folder
        placeholder = f"{folder_path}/.folder"
        await client.create_note(placeholder, "# Folder Placeholder\n\n")
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Created folder: {folder_path}",
            "folder_path": folder_path,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def move_note(from_path: str, to_folder: str) -> str:
    """Move a note to a different folder.
    
    Args:
        from_path: Current note path
        to_folder: Target folder path
        
    Returns:
        JSON string with move result
    """
    client = ObsidianClient()
    
    try:
        # Read original content
        content = await client.read_note(from_path)
        
        # Determine new path
        filename = from_path.split("/")[-1]
        new_path = f"{to_folder}/{filename}"
        
        # Create in new location
        await client.create_note(new_path, content)
        
        # Delete original
        await client.delete_note(from_path)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Moved note from {from_path} to {new_path}",
            "old_path": from_path,
            "new_path": new_path,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def rename_note(old_path: str, new_name: str) -> str:
    """Rename a note while keeping it in the same folder.
    
    Args:
        old_path: Current note path
        new_name: New note name (without .md extension)
        
    Returns:
        JSON string with rename result
    """
    client = ObsidianClient()
    
    try:
        # Read original content
        content = await client.read_note(old_path)
        
        # Determine new path
        if "/" in old_path:
            folder = "/".join(old_path.split("/")[:-1])
            new_path = f"{folder}/{new_name}.md"
        else:
            new_path = f"{new_name}.md"
        
        # Create with new name
        await client.create_note(new_path, content)
        
        # Delete original
        await client.delete_note(old_path)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Renamed note from {old_path} to {new_path}",
            "old_path": old_path,
            "new_path": new_new_path,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_folder_notes(folder_path: str) -> str:
    """Get all notes in a specific folder.
    
    Args:
        folder_path: Folder path
        
    Returns:
        JSON string with folder contents
    """
    client = ObsidianClient()
    
    try:
        all_files = await client.list_files(folder_path)
        
        # Filter notes in this folder (not subfolders)
        notes = []
        for f in all_files:
            if f.endswith(".md") and "/" not in f.replace(folder_path + "/", ""):
                notes.append(f)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "folder": folder_path,
            "note_count": len(notes),
            "notes": notes,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_vault_statistics() -> str:
    """Get comprehensive statistics about the vault.
    
    Returns:
        JSON string with vault statistics
    """
    client = ObsidianClient()
    
    try:
        all_files = await client.list_files()
        
        md_files = [f for f in all_files if f.endswith(".md")]
        canvas_files = [f for f in all_files if f.endswith(".canvas")]
        image_files = [f for f in all_files if f.endswith((".png", ".jpg", ".jpeg", ".gif"))]
        pdf_files = [f for f in all_files if f.endswith(".pdf")]
        
        # Calculate total content size
        total_chars = 0
        for filepath in md_files:
            try:
                content = await client.read_note(filepath)
                total_chars += len(content)
            except:
                pass
        
        # Get folder count
        folders = set()
        for filepath in all_files:
            if "/" in filepath:
                folder = "/".join(filepath.split("/")[:-1])
                folders.add(folder)
        
        # Get tag count
        tags = await client.get_all_tags()
        
        await client.close()
        
        stats = {
            "total_files": len(all_files),
            "markdown_notes": len(md_files),
            "canvas_files": len(canvas_files),
            "images": len(image_files),
            "pdfs": len(pdf_files),
            "folders": len(folders),
            "unique_tags": len(tags),
            "total_characters": total_chars,
            "average_note_length": round(total_chars / len(md_files), 2) if md_files else 0,
        }
        
        return json.dumps({
            "success": True,
            "statistics": stats,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
