"""Tag management tools for Obsidian MCP."""

import json
import re
from collections import defaultdict
from typing import Dict, List

from obsidian_mcp.client import ObsidianClient


async def list_all_tags() -> str:
    """List all tags used in the vault.
    
    Returns:
        JSON string with all tags and their counts
    """
    client = ObsidianClient()
    
    try:
        tags = await client.get_all_tags()
        await client.close()
        
        # Sort by count
        sorted_tags = dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))
        
        return json.dumps({
            "success": True,
            "total_unique_tags": len(tags),
            "tags": sorted_tags,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_tag_statistics() -> str:
    """Get statistics about tag usage in the vault.
    
    Returns:
        JSON string with tag statistics
    """
    client = ObsidianClient()
    
    try:
        tags = await client.get_all_tags()
        await client.close()
        
        if not tags:
            return json.dumps({
                "success": True,
                "message": "No tags found in vault",
                "statistics": {},
            }, indent=2)
        
        counts = list(tags.values())
        stats = {
            "total_unique_tags": len(tags),
            "total_tag_instances": sum(counts),
            "most_used_tag": max(tags.items(), key=lambda x: x[1]),
            "least_used_tag": min(tags.items(), key=lambda x: x[1]),
            "average_uses_per_tag": round(sum(counts) / len(counts), 2),
            "median_uses": sorted(counts)[len(counts) // 2],
        }
        
        # Top 10 tags
        top_tags = dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10])
        stats["top_10_tags"] = top_tags
        
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


async def rename_tag(old_tag: str, new_tag: str) -> str:
    """Rename a tag across all notes.
    
    Args:
        old_tag: Current tag name (without #)
        new_tag: New tag name (without #)
        
    Returns:
        JSON string with rename result
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        old_pattern = f"#{old_tag}"
        new_pattern = f"#{new_tag}"
        
        updated_files = []
        for filepath in md_files:
            content = await client.read_note(filepath)
            if old_pattern in content:
                new_content = content.replace(old_pattern, new_pattern)
                await client.update_note(filepath, new_content)
                updated_files.append(filepath)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "old_tag": old_tag,
            "new_tag": new_tag,
            "updated_notes_count": len(updated_files),
            "updated_notes": updated_files,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_related_tags(tag: str) -> str:
    """Find tags that frequently appear together with a given tag.
    
    Args:
        tag: Tag to analyze (without #)
        
    Returns:
        JSON string with related tags
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        tag_to_find = f"#{tag}"
        co_occurrence = defaultdict(int)
        notes_with_tag = 0
        
        for filepath in md_files:
            content = await client.read_note(filepath)
            
            if tag_to_find in content:
                notes_with_tag += 1
                # Find all tags in this note
                all_tags = re.findall(r'#(\w+)', content)
                for t in all_tags:
                    if t != tag:
                        co_occurrence[t] += 1
        
        # Sort by co-occurrence
        related = dict(sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True))
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "tag": tag,
            "notes_with_tag": notes_with_tag,
            "related_tags_count": len(related),
            "related_tags": dict(list(related.items())[:20]),
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
