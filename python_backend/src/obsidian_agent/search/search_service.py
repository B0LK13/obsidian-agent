"""Search service for querying indexed notes"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from ..config import SearchConfig
from ..database import DatabaseConnection, Note
from ..vector_store import ChromaDBStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result"""
    id: str
    path: str
    title: str
    content: str
    score: float
    snippet: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchService:
    """Service for searching indexed notes"""
    
    def __init__(
        self,
        config: SearchConfig,
        db: DatabaseConnection,
        vector_store: Optional[ChromaDBStore] = None,
    ):
        self.config = config
        self.db = db
        self.vector_store = vector_store
    
    def search(
        self,
        query: str,
        limit: int = None,
        semantic: bool = True,
        threshold: float = None,
    ) -> List[SearchResult]:
        """Search notes using semantic or keyword search"""
        limit = limit or self.config.default_limit
        threshold = threshold or self.config.semantic_threshold
        
        if semantic and self.vector_store:
            return self._semantic_search(query, limit, threshold)
        else:
            return self._keyword_search(query, limit)
    
    def _semantic_search(
        self,
        query: str,
        limit: int,
        threshold: float,
    ) -> List[SearchResult]:
        """Perform semantic search using vector store"""
        results = self.vector_store.search(
            query=query,
            n_results=limit,
            threshold=threshold,
        )
        
        search_results = []
        for result in results:
            note_id = result["id"]
            
            with self.db.get_session() as session:
                note = session.query(Note).filter(Note.id == note_id).first()
                if note:
                    snippet = self._generate_snippet(note.content, query)
                    search_results.append(SearchResult(
                        id=note.id,
                        path=note.path,
                        title=note.title,
                        content=note.content[:500],
                        score=result["similarity"],
                        snippet=snippet,
                        metadata=note.metadata,
                    ))
        
        return search_results
    
    def _keyword_search(
        self,
        query: str,
        limit: int,
    ) -> List[SearchResult]:
        """Perform keyword search using FTS5"""
        search_results = []
        
        with self.db.get_session() as session:
            sql = text("""
                SELECT notes.id, notes.path, notes.title, notes.content, notes.metadata,
                       bm25(notes_fts) as score
                FROM notes_fts
                JOIN notes ON notes.rowid = notes_fts.rowid
                WHERE notes_fts MATCH :query
                ORDER BY score
                LIMIT :limit
            """)
            
            results = session.execute(sql, {"query": query, "limit": limit})
            
            for row in results:
                snippet = self._generate_snippet(row.content, query)
                search_results.append(SearchResult(
                    id=row.id,
                    path=row.path,
                    title=row.title,
                    content=row.content[:500],
                    score=-row.score,
                    snippet=snippet,
                    metadata=row.metadata,
                ))
        
        return search_results
    
    def _generate_snippet(
        self,
        content: str,
        query: str,
        context_chars: int = 150,
    ) -> str:
        """Generate a snippet around the query match"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        pos = content_lower.find(query_lower)
        if pos == -1:
            words = query_lower.split()
            for word in words:
                pos = content_lower.find(word)
                if pos != -1:
                    break
        
        if pos == -1:
            return content[:context_chars * 2] + "..."
        
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search/indexing statistics"""
        with self.db.get_session() as session:
            total_notes = session.query(Note).count()
        
        vector_count = 0
        if self.vector_store:
            vector_count = self.vector_store.count()
        
        return {
            "total_notes": total_notes,
            "vector_indexed": vector_count,
        }
