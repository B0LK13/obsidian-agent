"""Advanced search tools for Obsidian MCP."""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict

from obsidian_mcp.client import ObsidianClient


async def advanced_search(
    query: str,
    use_regex: bool = False,
    case_sensitive: bool = False,
    in_title: bool = False,
    in_content: bool = True,
    folder: str = None,
    tag: str = None,
) -> str:
    """Advanced search with multiple filters.
    
    Args:
        query: Search query
        use_regex: Whether to use regex matching
        case_sensitive: Case sensitive search
        in_title: Search in note titles only
        in_content: Search in note content
        folder: Limit to specific folder
        tag: Limit to notes with specific tag
        
    Returns:
        JSON string with search results
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files(folder)
        md_files = [f for f in files if f.endswith(".md")]
        
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for filepath in md_files:
            # Check tag filter
            if tag:
                content = await client.read_note(filepath)
                tag_pattern = f"#{tag}"
                if tag_pattern not in content:
                    continue
            else:
                content = await client.read_note(filepath)
            
            title = filepath.split("/")[-1].replace(".md", "")
            
            match = False
            
            if in_title:
                if use_regex:
                    if re.search(query, title, flags):
                        match = True
                else:
                    if query.lower() in title.lower() if not case_sensitive else query in title:
                        match = True
            
            if in_content:
                search_content = content if case_sensitive else content.lower()
                search_query = query if case_sensitive else query.lower()
                
                if use_regex:
                    if re.search(query, content, flags):
                        match = True
                else:
                    if search_query in search_content:
                        match = True
            
            if match:
                # Find context snippets
                snippets = []
                if in_content:
                    pattern = re.compile(query if use_regex else re.escape(query), flags)
                    for match_obj in pattern.finditer(content):
                        start = max(0, match_obj.start() - 50)
                        end = min(len(content), match_obj.end() + 50)
                        snippets.append(content[start:end])
                
                results.append({
                    "path": filepath,
                    "title": title,
                    "snippets": snippets[:3],  # Limit to 3 snippets
                })
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "query": query,
            "filters": {
                "use_regex": use_regex,
                "case_sensitive": case_sensitive,
                "in_title": in_title,
                "in_content": in_content,
                "folder": folder,
                "tag": tag,
            },
            "result_count": len(results),
            "results": results,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def search_by_date(
    start_date: str = None,
    end_date: str = None,
    date_format: str = "modified",
) -> str:
    """Search notes by date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        date_format: "created" or "modified"
        
    Returns:
        JSON string with matching notes
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.min
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.max
        
        # Note: Obsidian API doesn't expose file dates directly
        # This is a simplified implementation
        results = []
        for filepath in md_files:
            # Check if it's a daily note with date in path
            if "Daily Notes" in filepath or any(char.isdigit() for char in filepath):
                # Extract date from filename if possible
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filepath)
                if date_match:
                    note_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                    if start <= note_date <= end:
                        results.append({
                            "path": filepath,
                            "date": date_match.group(1),
                        })
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "date_range": {
                "start": start_date,
                "end": end_date,
            },
            "result_count": len(results),
            "results": results,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def search_recent(days: int = 7) -> str:
    """Get recently modified notes.
    
    Args:
        days: Number of days to look back
        
    Returns:
        JSON string with recent notes
    """
    client = ObsidianClient()
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Search daily notes in range
        result = await search_by_date(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
        
        await client.close()
        return result
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def find_duplicates(threshold: float = 0.8) -> str:
    """Find potentially duplicate notes based on content similarity.
    
    Args:
        threshold: Similarity threshold (0.0-1.0)
        
    Returns:
        JSON string with duplicate pairs
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        # Get content of all notes
        note_contents = {}
        for filepath in md_files:
            try:
                content = await client.read_note(filepath)
                # Normalize content for comparison
                normalized = re.sub(r'\s+', ' ', content.lower())
                note_contents[filepath] = normalized
            except:
                pass
        
        # Find duplicates
        duplicates = []
        checked = set()
        
        for path1, content1 in note_contents.items():
            for path2, content2 in note_contents.items():
                if path1 >= path2 or (path1, path2) in checked:
                    continue
                
                checked.add((path1, path2))
                
                # Simple similarity: common words ratio
                words1 = set(content1.split())
                words2 = set(content2.split())
                
                if words1 and words2:
                    intersection = words1 & words2
                    union = words1 | words2
                    similarity = len(intersection) / len(union)
                    
                    if similarity >= threshold:
                        duplicates.append({
                            "note1": path1,
                            "note2": path2,
                            "similarity": round(similarity, 2),
                        })
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "threshold": threshold,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def search_untagged() -> str:
    """Find notes without any tags.
    
    Returns:
        JSON string with untagged notes
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        untagged = []
        for filepath in md_files:
            content = await client.read_note(filepath)
            # Check for any tags
            if not re.search(r'#\w+', content):
                untagged.append(filepath)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "untagged_count": len(untagged),
            "total_notes": len(md_files),
            "untagged_notes": untagged,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
