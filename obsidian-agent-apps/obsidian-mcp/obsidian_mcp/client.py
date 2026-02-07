"""Obsidian API Client."""

import json
from typing import Any, List, Dict, Optional
from datetime import datetime

import httpx
import structlog

from obsidian_mcp.config import get_settings
from obsidian_mcp.exceptions import APIError, NoteNotFoundError, FolderNotFoundError

logger = structlog.get_logger()


class ObsidianClient:
    """Client for interacting with Obsidian Local REST API."""
    
    def __init__(self, api_token: str = None, base_url: str = None):
        """Initialize Obsidian client.
        
        Args:
            api_token: Obsidian API token. If None, loads from settings.
            base_url: Obsidian API base URL. If None, loads from settings.
        """
        settings = get_settings()
        self.api_token = api_token or settings.obsidian_api_token
        self.base_url = base_url or settings.obsidian_api_url
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        self._client: httpx.AsyncClient = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=30.0,
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to Obsidian API.
        
        Args:
            method: HTTP method
            path: API path
            **kwargs: Additional request arguments
            
        Returns:
            Response data as dictionary
        """
        try:
            response = await self.client.request(method, path, **kwargs)
            response.raise_for_status()
            
            if response.status_code == 204:
                return {}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NoteNotFoundError(f"Resource not found: {path}")
            raise APIError(
                f"API request failed: {e}",
                status_code=e.response.status_code,
                response=e.response.text,
            )
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {e}")
    
    # ==================== Vault Operations ====================
    
    async def list_files(self, directory: str = "") -> List[str]:
        """List all files in vault or directory.
        
        Args:
            directory: Optional subdirectory to list
            
        Returns:
            List of file paths
        """
        path = f"/vault/{directory}" if directory else "/vault/"
        result = await self._request("GET", path)
        return result.get("files", [])
    
    async def get_file(self, filepath: str) -> str:
        """Get file content.
        
        Args:
            filepath: Path to file
            
        Returns:
            File content as string
        """
        result = await self._request("GET", f"/vault/{filepath}")
        return result.get("content", "")
    
    async def create_or_update_file(self, filepath: str, content: str) -> Dict[str, Any]:
        """Create or update a file.
        
        Args:
            filepath: Path to file
            content: File content
            
        Returns:
            Response data
        """
        return await self._request(
            "PUT",
            f"/vault/{filepath}",
            json={"content": content}
        )
    
    async def delete_file(self, filepath: str) -> Dict[str, Any]:
        """Delete a file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Response data
        """
        return await self._request("DELETE", f"/vault/{filepath}")
    
    async def get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """Get file metadata.
        
        Args:
            filepath: Path to file
            
        Returns:
            File metadata
        """
        result = await self._request("GET", f"/vault/{filepath}")
        return {
            "path": filepath,
            "size": len(result.get("content", "")),
            "extension": filepath.split(".")[-1] if "." in filepath else "",
        }
    
    # ==================== Search Operations ====================
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search vault for content.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        result = await self._request(
            "POST",
            "/search/",
            json={"query": query}
        )
        return result.get("results", [])
    
    async def search_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Search for notes with specific tag.
        
        Args:
            tag: Tag to search for (with or without #)
            
        Returns:
            List of matching notes
        """
        if not tag.startswith("#"):
            tag = f"#{tag}"
        return await self.search(tag)
    
    async def search_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Search for notes by title.
        
        Args:
            title: Title to search for
            
        Returns:
            List of matching notes
        """
        all_files = await self.list_files()
        matches = []
        
        for filepath in all_files:
            if filepath.endswith(".md"):
                file_title = filepath.split("/")[-1].replace(".md", "")
                if title.lower() in file_title.lower():
                    matches.append({
                        "path": filepath,
                        "title": file_title,
                    })
        
        return matches
    
    # ==================== Note Operations ====================
    
    async def read_note(self, path: str) -> str:
        """Read note content.
        
        Args:
            path: Note path
            
        Returns:
            Note content
        """
        return await self.get_file(path)
    
    async def create_note(self, path: str, content: str) -> Dict[str, Any]:
        """Create a new note.
        
        Args:
            path: Note path
            content: Note content
            
        Returns:
            Response data
        """
        if not path.endswith(".md"):
            path += ".md"
        return await self.create_or_update_file(path, content)
    
    async def update_note(self, path: str, content: str) -> Dict[str, Any]:
        """Update existing note.
        
        Args:
            path: Note path
            content: New content
            
        Returns:
            Response data
        """
        return await self.create_or_update_file(path, content)
    
    async def append_to_note(self, path: str, content: str) -> Dict[str, Any]:
        """Append content to note.
        
        Args:
            path: Note path
            content: Content to append
            
        Returns:
            Response data
        """
        try:
            existing = await self.read_note(path)
            new_content = existing + "\n\n" + content
        except NoteNotFoundError:
            new_content = content
        
        return await self.update_note(path, new_content)
    
    async def delete_note(self, path: str) -> Dict[str, Any]:
        """Delete a note.
        
        Args:
            path: Note path
            
        Returns:
            Response data
        """
        return await self.delete_file(path)
    
    # ==================== Link Operations ====================
    
    async def get_backlinks(self, path: str) -> List[str]:
        """Get all backlinks to a note.
        
        Args:
            path: Note path
            
        Returns:
            List of paths linking to this note
        """
        note_title = path.split("/")[-1].replace(".md", "")
        all_files = await self.list_files()
        backlinks = []
        
        for filepath in all_files:
            if filepath.endswith(".md") and filepath != path:
                content = await self.read_note(filepath)
                # Check for wiki-links [[note_title]] or [[note_title|alias]]
                if f"[[{note_title}" in content:
                    backlinks.append(filepath)
        
        return backlinks
    
    async def get_outgoing_links(self, path: str) -> List[str]:
        """Get all links from a note.
        
        Args:
            path: Note path
            
        Returns:
            List of linked note titles
        """
        content = await self.read_note(path)
        import re
        
        # Find all wiki-links [[note_name]] or [[note_name|alias]]
        links = re.findall(r'\[\[([^\]|]+)', content)
        return list(set(links))  # Remove duplicates
    
    # ==================== Tag Operations ====================
    
    async def get_all_tags(self) -> Dict[str, int]:
        """Get all tags and their usage counts.
        
        Returns:
            Dictionary of tag -> count
        """
        all_files = await self.list_files()
        tags = {}
        
        for filepath in all_files:
            if filepath.endswith(".md"):
                content = await self.read_note(filepath)
                import re
                # Find all tags #tag
                file_tags = re.findall(r'#(\w+)', content)
                for tag in file_tags:
                    tags[tag] = tags.get(tag, 0) + 1
        
        return tags
    
    async def get_tags_in_note(self, path: str) -> List[str]:
        """Get all tags in a specific note.
        
        Args:
            path: Note path
            
        Returns:
            List of tags
        """
        content = await self.read_note(path)
        import re
        tags = re.findall(r'#(\w+)', content)
        return list(set(tags))
    
    # ==================== Daily Notes ====================
    
    async def get_daily_note(self, date: str = None) -> Dict[str, Any]:
        """Get daily note for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format. If None, uses today.
            
        Returns:
            Daily note data
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_note_path = f"Daily Notes/{date}.md"
        
        try:
            content = await self.read_note(daily_note_path)
            return {
                "path": daily_note_path,
                "date": date,
                "content": content,
                "exists": True,
            }
        except NoteNotFoundError:
            return {
                "path": daily_note_path,
                "date": date,
                "content": "",
                "exists": False,
            }
    
    async def create_daily_note(self, date: str = None, content: str = "") -> Dict[str, Any]:
        """Create daily note for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format. If None, uses today.
            content: Note content
            
        Returns:
            Created note data
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_note_path = f"Daily Notes/{date}.md"
        
        # Add default template if empty
        if not content:
            content = f"# {date}\n\n## Tasks\n\n- [ ] \n\n## Notes\n\n"
        
        await self.create_note(daily_note_path, content)
        
        return {
            "path": daily_note_path,
            "date": date,
            "content": content,
        }
