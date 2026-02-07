"""External integration tools for Obsidian MCP."""

import json
import re
from typing import List, Dict

from obsidian_mcp.client import ObsidianClient


async def extract_urls(domain_filter: str = None) -> str:
    """Extract all URLs from the vault.
    
    Args:
        domain_filter: Optional domain to filter URLs
        
    Returns:
        JSON string with found URLs
    """
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        md_files = [f for f in files if f.endswith(".md")]
        
        url_pattern = r'https?://[^\s<>"\')\]]+(?:[^\s<>"\')\]]+)'
        all_urls = {}
        
        for filepath in md_files:
            content = await client.read_note(filepath)
            urls = re.findall(url_pattern, content)
            
            # Filter if domain specified
            if domain_filter:
                urls = [u for u in urls if domain_filter in u]
            
            if urls:
                all_urls[filepath] = list(set(urls))  # Remove duplicates
        
        await client.close()
        
        # Flatten and count
        total_urls = sum(len(urls) for urls in all_urls.values())
        
        return json.dumps({
            "success": True,
            "total_urls": total_urls,
            "files_with_urls": len(all_urls),
            "urls_by_file": all_urls,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def get_external_links(note_path: str) -> str:
    """Get all external links from a specific note.
    
    Args:
        note_path: Path to the note
        
    Returns:
        JSON string with external links
    """
    client = ObsidianClient()
    
    try:
        content = await client.read_note(note_path)
        
        # Find external links (not wiki-links)
        url_pattern = r'https?://[^\s<>"\')\]]+(?:[^\s<>"\')\]]+)'
        urls = re.findall(url_pattern, content)
        
        # Also find markdown links [text](url)
        md_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "path": note_path,
            "raw_url_count": len(urls),
            "raw_urls": list(set(urls)),
            "markdown_link_count": len(md_links),
            "markdown_links": [
                {"text": text, "url": url}
                for text, url in md_links
            ],
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def create_bibliography(tag: str = "source") -> str:
    """Create a bibliography from notes tagged as sources.
    
    Args:
        tag: Tag to identify source notes
        
    Returns:
        JSON string with bibliography
    """
    client = ObsidianClient()
    
    try:
        # Find all notes with the source tag
        results = await client.search_by_tag(tag)
        
        sources = []
        for result in json.loads(results).get("results", []):
            path = result.get("path", "")
            try:
                content = await client.read_note(path)
                
                # Extract title (first # heading)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else path
                
                # Try to extract author and date
                author_match = re.search(r'author[:\s]+(.+)', content, re.IGNORECASE)
                author = author_match.group(1) if author_match else "Unknown"
                
                date_match = re.search(r'date[:\s]+(\d{4}-\d{2}-\d{2})', content, re.IGNORECASE)
                date = date_match.group(1) if date_match else "Unknown"
                
                # Find URL if exists
                url_match = re.search(r'url[:\s]+(https?://[^\s]+)', content, re.IGNORECASE)
                url = url_match.group(1) if url_match else None
                
                sources.append({
                    "title": title,
                    "author": author,
                    "date": date,
                    "url": url,
                    "path": path,
                })
            
            except Exception:
                pass
        
        await client.close()
        
        # Sort by date
        sources.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Generate bibliography text
        bib_entries = []
        for source in sources:
            entry = f"- {source['title']}"
            if source['author'] != "Unknown":
                entry += f" by {source['author']}"
            if source['date'] != "Unknown":
                entry += f" ({source['date']})"
            if source['url']:
                entry += f" - {source['url']}"
            bib_entries.append(entry)
        
        bibliography = "\n".join(bib_entries)
        
        return json.dumps({
            "success": True,
            "source_count": len(sources),
            "sources": sources,
            "bibliography_text": bibliography,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
