"""
Search module for Obsidian Agent
"""

from pathlib import Path
from typing import List, Dict, Optional
from whoosh.index import open_dir, exists_in
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.query import And, Or, Term


class VaultSearcher:
    """Search indexed vault documents"""
    
    def __init__(self, vault_path: str, index_dir: Optional[str] = None):
        self.vault_path = Path(vault_path).resolve()
        
        if index_dir is None:
            index_dir = self.vault_path / ".obsidian" / "agent-index"
        else:
            index_dir = Path(index_dir)
        
        self.index_dir = index_dir
        
        if not exists_in(str(self.index_dir)):
            raise ValueError(
                f"No index found at {index_dir}. Please run 'obsidian-agent index' first."
            )
        
        self.index = open_dir(str(self.index_dir))
    
    def search(self, query_str: str, limit: int = 10, fields: Optional[List[str]] = None) -> List[Dict]:
        """
        Search the vault for documents matching the query
        
        Args:
            query_str: Search query string
            limit: Maximum number of results to return
            fields: Fields to search in (default: title, content, tags)
        
        Returns:
            List of matching documents with scores
        """
        if fields is None:
            fields = ['title', 'content', 'tags']
        
        results = []
        
        with self.index.searcher() as searcher:
            # Create a multifield parser
            parser = MultifieldParser(fields, schema=self.index.schema)
            query = parser.parse(query_str)
            
            # Execute search
            search_results = searcher.search(query, limit=limit)
            
            for hit in search_results:
                results.append({
                    'path': hit['path'],
                    'title': hit['title'],
                    'score': hit.score,
                    'excerpt': self._get_excerpt(hit, query_str),
                    'modified': hit.get('modified')
                })
        
        return results
    
    def _get_excerpt(self, hit, query_str: str, context: int = 100) -> str:
        """Get a relevant excerpt from the document content"""
        content = hit.get('content', '')
        if not content:
            return ""
        
        # Simple excerpt: first N characters or around first occurrence of query term
        query_lower = query_str.lower()
        content_lower = content.lower()
        
        # Find first occurrence of any word from the query
        words = query_lower.split()
        best_pos = -1
        
        for word in words:
            pos = content_lower.find(word)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
        
        if best_pos != -1:
            # Extract context around the match
            start = max(0, best_pos - context)
            end = min(len(content), best_pos + len(query_str) + context)
            excerpt = content[start:end]
            
            # Add ellipsis if truncated
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(content):
                excerpt = excerpt + "..."
            
            return excerpt.strip()
        else:
            # No match found, return beginning of content
            return content[:context * 2].strip() + "..."
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict]:
        """Search documents by tags"""
        tag_query = ' OR '.join(tags)
        return self.search(tag_query, limit=limit, fields=['tags'])
