"""Link and graph analysis tools for Obsidian MCP."""

import json
import re
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict

import networkx as nx

from obsidian_mcp.client import ObsidianClient


async def get_backlinks(path: str) -> str:
    """Get all notes that link to this note.
    
    Args:
        path: Path to the note
        
    Returns:
        JSON string with backlink information
    """
    client = ObsidianClient()
    
    try:
        backlinks = await client.get_backlinks(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "backlink_count": len(backlinks),
            "backlinks": backlinks,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_forward_links(path: str) -> str:
    """Get all notes that this note links to.
    
    Args:
        path: Path to the note
        
    Returns:
        JSON string with forward link information
    """
    client = ObsidianClient()
    
    try:
        links = await client.get_outgoing_links(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "link_count": len(links),
            "links": links,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_orphan_notes() -> str:
    """Find all notes with no connections (no links in or out).
    
    Returns:
        JSON string with orphan notes
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        orphans = []
        for filepath in md_files:
            outgoing = await client.get_outgoing_links(filepath)
            backlinks = await client.get_backlinks(filepath)
            
            if not outgoing and not backlinks:
                orphans.append(filepath)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "orphan_count": len(orphans),
            "total_notes": len(md_files),
            "orphans": orphans,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_hub_notes(limit: int = 10) -> str:
    """Find the most connected notes (hubs).
    
    Args:
        limit: Number of top hubs to return
        
    Returns:
        JSON string with hub notes
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        connections = []
        for filepath in md_files:
            outgoing = await client.get_outgoing_links(filepath)
            backlinks = await client.get_backlinks(filepath)
            total = len(outgoing) + len(backlinks)
            connections.append({
                "path": filepath,
                "title": filepath.split("/")[-1].replace(".md", ""),
                "outgoing": len(outgoing),
                "backlinks": len(backlinks),
                "total": total,
            })
        
        # Sort by total connections
        connections.sort(key=lambda x: x["total"], reverse=True)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "hub_count": min(limit, len(connections)),
            "hubs": connections[:limit],
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_shortest_path(from_path: str, to_path: str) -> str:
    """Find the shortest path between two notes through links.
    
    Args:
        from_path: Starting note path
        to_path: Target note path
        
    Returns:
        JSON string with path information
    """
    client = ObsidianClient()
    
    try:
        # Build graph
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        G = nx.Graph()
        
        for filepath in md_files:
            G.add_node(filepath)
            links = await client.get_outgoing_links(filepath)
            for link in links:
                # Try to find matching file
                for other_file in md_files:
                    if other_file.endswith(f"{link}.md"):
                        G.add_edge(filepath, other_file)
                        break
        
        # Find shortest path
        try:
            path = nx.shortest_path(G, from_path, to_path)
            path_length = len(path) - 1
        except nx.NetworkXNoPath:
            path = []
            path_length = -1
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "from": from_path,
            "to": to_path,
            "path_exists": len(path) > 0,
            "path_length": path_length,
            "path": path,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_connected_notes(path: str, depth: int = 1) -> str:
    """Get all notes connected to a given note within a certain depth.
    
    Args:
        path: Starting note path
        depth: How many levels of connections to traverse (1-3)
        
    Returns:
        JSON string with connected notes
    """
    client = ObsidianClient()
    
    try:
        connected = {path}
        current_level = {path}
        
        for _ in range(depth):
            next_level = set()
            for note_path in current_level:
                outgoing = await client.get_outgoing_links(note_path)
                backlinks = await client.get_backlinks(note_path)
                
                # Convert link titles to paths
                files = await client.list_files()
                for link in outgoing:
                    for f in files:
                        if f.endswith(f"{link}.md"):
                            next_level.add(f)
                            break
                
                next_level.update(backlinks)
            
            connected.update(next_level)
            current_level = next_level
        
        connected.remove(path)
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "depth": depth,
            "connected_count": len(connected),
            "connected_notes": list(connected),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def analyze_graph() -> str:
    """Analyze the entire vault graph structure.
    
    Returns:
        JSON string with graph statistics
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        G = nx.Graph()
        total_links = 0
        
        for filepath in md_files:
            G.add_node(filepath)
            links = await client.get_outgoing_links(filepath)
            total_links += len(links)
            
            for link in links:
                for other_file in md_files:
                    if other_file.endswith(f"{link}.md"):
                        G.add_edge(filepath, other_file)
                        break
        
        # Calculate metrics
        stats = {
            "total_notes": len(md_files),
            "total_links": total_links,
            "unique_connections": G.number_of_edges(),
            "connected_components": nx.number_connected_components(G),
            "average_clustering": nx.average_clustering(G) if G.number_of_edges() > 0 else 0,
        }
        
        # Find most connected notes
        if G.number_of_nodes() > 0:
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 0
            most_connected = [n for n, d in degrees.items() if d == max_degree][:5]
            stats["most_connected_notes"] = most_connected
            stats["max_connections"] = max_degree
        
        await client.close()
        
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


async def suggest_links(path: str) -> str:
    """Suggest potential links for a note based on content analysis.
    
    Args:
        path: Path to the note
        
    Returns:
        JSON string with link suggestions
    """
    client = ObsidianClient()
    
    try:
        content = await client.read_note(path)
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        # Get all note titles
        note_titles = {}
        for f in md_files:
            title = f.split("/")[-1].replace(".md", "")
            note_titles[title.lower()] = f
        
        # Find potential links (words matching note titles)
        suggestions = []
        words = re.findall(r'\b[A-Za-z][A-Za-z\s]*[A-Za-z]\b', content)
        
        for word in words:
            word_lower = word.lower()
            if word_lower in note_titles and word_lower != path.split("/")[-1].replace(".md", "").lower():
                if f"[[{word}" not in content:  # Not already linked
                    suggestions.append({
                        "text": word,
                        "target_note": note_titles[word_lower],
                        "context": content[max(0, content.find(word) - 50):content.find(word) + len(word) + 50],
                    })
        
        # Remove duplicates
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s["text"] not in seen:
                seen.add(s["text"])
                unique_suggestions.append(s)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": path,
            "suggestion_count": len(unique_suggestions),
            "suggestions": unique_suggestions[:20],  # Limit to top 20
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
