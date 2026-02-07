"""
Vector Database Layer for Semantic Search
Issue #96: Implement Vector Database Layer for Semantic Search

Provides efficient storage and retrieval of note embeddings using ChromaDB
with fallback options and comprehensive search capabilities.
"""

import hashlib
import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from a vector search."""
    note_id: str
    score: float
    content: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            'note_id': self.note_id,
            'score': self.score,
            'content': self.content,
            'metadata': self.metadata
        }


@dataclass
class EmbeddingRecord:
    """Record of an embedding in the vector store."""
    note_id: str
    embedding: np.ndarray
    content_hash: str
    created_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'note_id': self.note_id,
            'embedding': self.embedding.tolist(),
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


class VectorStoreBackend(ABC):
    """Abstract base class for vector store backends."""
    
    @abstractmethod
    def add(self, note_id: str, embedding: np.ndarray, metadata: Dict) -> bool:
        """Add or update an embedding."""
        pass
    
    @abstractmethod
    def add_batch(self, records: List[EmbeddingRecord]) -> bool:
        """Add multiple embeddings efficiently."""
        pass
    
    @abstractmethod
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """Search for similar embeddings."""
        pass
    
    @abstractmethod
    def delete(self, note_id: str) -> bool:
        """Delete an embedding."""
        pass
    
    @abstractmethod
    def get(self, note_id: str) -> Optional[EmbeddingRecord]:
        """Get a specific embedding."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of embeddings."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all embeddings."""
        pass


class ChromaBackend(VectorStoreBackend):
    """ChromaDB backend for vector storage."""
    
    def __init__(self, collection_name: str = "obsidian_notes", persist_dir: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.persist_dir)
            ))
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized at {persist_dir}")
            self.available = True
        except ImportError:
            logger.error("ChromaDB not installed. Run: pip install chromadb")
            self.available = False
            self.client = None
            self.collection = None
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            self.available = False
            self.client = None
            self.collection = None
    
    def add(self, note_id: str, embedding: np.ndarray, metadata: Dict) -> bool:
        if not self.available:
            return False
        
        try:
            self.collection.upsert(
                ids=[note_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add embedding for {note_id}: {e}")
            return False
    
    def add_batch(self, records: List[EmbeddingRecord]) -> bool:
        if not self.available or not records:
            return False
        
        try:
            self.collection.upsert(
                ids=[r.note_id for r in records],
                embeddings=[r.embedding.tolist() for r in records],
                metadatas=[r.metadata for r in records]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add batch: {e}")
            return False
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        if not self.available:
            return []
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filters
            )
            
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i, note_id in enumerate(results['ids'][0]):
                    score = 1.0 - results['distances'][0][i]  # Convert distance to similarity
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    search_results.append(SearchResult(
                        note_id=note_id,
                        score=score,
                        metadata=metadata
                    ))
            
            return search_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete(self, note_id: str) -> bool:
        if not self.available:
            return False
        
        try:
            self.collection.delete(ids=[note_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete {note_id}: {e}")
            return False
    
    def get(self, note_id: str) -> Optional[EmbeddingRecord]:
        if not self.available:
            return None
        
        try:
            result = self.collection.get(ids=[note_id], include=['embeddings', 'metadatas'])
            if result['ids']:
                return EmbeddingRecord(
                    note_id=note_id,
                    embedding=np.array(result['embeddings'][0]),
                    content_hash=result['metadatas'][0].get('content_hash', ''),
                    created_at=datetime.fromisoformat(result['metadatas'][0].get('created_at', datetime.utcnow().isoformat())),
                    metadata=result['metadatas'][0]
                )
        except Exception as e:
            logger.error(f"Failed to get {note_id}: {e}")
        return None
    
    def count(self) -> int:
        if not self.available:
            return 0
        return self.collection.count()
    
    def clear(self) -> bool:
        if not self.available:
            return False
        
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False


class SQLiteBackend(VectorStoreBackend):
    """SQLite-based fallback backend using simple dot product similarity."""
    
    def __init__(self, db_path: str = "vector_store.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    note_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_note_id ON embeddings(note_id);
            """)
    
    def add(self, note_id: str, embedding: np.ndarray, metadata: Dict) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings 
                    (note_id, embedding, content_hash, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    note_id,
                    embedding.tobytes(),
                    metadata.get('content_hash', ''),
                    metadata.get('created_at', datetime.utcnow().isoformat()),
                    json.dumps(metadata)
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to add embedding: {e}")
            return False
    
    def add_batch(self, records: List[EmbeddingRecord]) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany("""
                    INSERT OR REPLACE INTO embeddings 
                    (note_id, embedding, content_hash, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    (
                        r.note_id,
                        r.embedding.tobytes(),
                        r.content_hash,
                        r.created_at.isoformat(),
                        json.dumps(r.metadata)
                    )
                    for r in records
                ])
            return True
        except Exception as e:
            logger.error(f"Failed to add batch: {e}")
            return False
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute("SELECT note_id, embedding, metadata FROM embeddings").fetchall()
                
                results = []
                query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
                
                for note_id, emb_blob, metadata_json in rows:
                    embedding = np.frombuffer(emb_blob, dtype=np.float32)
                    if embedding.shape[0] != query_embedding.shape[0]:
                        continue
                    
                    emb_norm = embedding / (np.linalg.norm(embedding) + 1e-8)
                    similarity = float(np.dot(query_norm, emb_norm))
                    
                    results.append((note_id, similarity, metadata_json))
                
                # Sort by similarity and return top_k
                results.sort(key=lambda x: x[1], reverse=True)
                
                return [
                    SearchResult(
                        note_id=note_id,
                        score=score,
                        metadata=json.loads(metadata_json)
                    )
                    for note_id, score, metadata_json in results[:top_k]
                ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete(self, note_id: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM embeddings WHERE note_id = ?", (note_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False
    
    def get(self, note_id: str) -> Optional[EmbeddingRecord]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT * FROM embeddings WHERE note_id = ?",
                    (note_id,)
                ).fetchone()
                
                if row:
                    return EmbeddingRecord(
                        note_id=row[0],
                        embedding=np.frombuffer(row[1], dtype=np.float32),
                        content_hash=row[2],
                        created_at=datetime.fromisoformat(row[3]),
                        metadata=json.loads(row[4])
                    )
        except Exception as e:
            logger.error(f"Failed to get: {e}")
        return None
    
    def count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Failed to count: {e}")
            return 0
    
    def clear(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM embeddings")
            return True
        except Exception as e:
            logger.error(f"Failed to clear: {e}")
            return False


class VectorDatabase:
    """
    High-level vector database interface with automatic backend selection
    and embedding generation integration.
    """
    
    def __init__(
        self,
        backend: Optional[str] = None,
        persist_dir: str = "./vector_db",
        embedding_function: Optional[Callable[[str], np.ndarray]] = None
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_function = embedding_function
        
        # Initialize backend
        if backend == "chroma":
            self.backend = ChromaBackend(persist_dir=persist_dir)
            if not self.backend.available:
                logger.warning("ChromaDB not available, falling back to SQLite")
                self.backend = SQLiteBackend(str(self.persist_dir / "fallback.db"))
        elif backend == "sqlite":
            self.backend = SQLiteBackend(str(self.persist_dir / "vectors.db"))
        else:
            # Auto-select: try ChromaDB first, fall back to SQLite
            chroma = ChromaBackend(persist_dir=persist_dir)
            if chroma.available:
                self.backend = chroma
            else:
                logger.info("Using SQLite fallback for vector storage")
                self.backend = SQLiteBackend(str(self.persist_dir / "vectors.db"))
        
        logger.info(f"VectorDatabase initialized with {type(self.backend).__name__}")
    
    def add_note(
        self, 
        note_id: str, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a note to the vector database.
        Automatically generates embedding if embedding_function is set.
        """
        if self.embedding_function is None:
            logger.error("No embedding function configured")
            return False
        
        try:
            # Generate embedding
            embedding = self.embedding_function(content)
            if embedding is None:
                return False
            
            # Ensure numpy array
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding, dtype=np.float32)
            
            # Compute content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Prepare metadata
            full_metadata = metadata or {}
            full_metadata.update({
                'content_hash': content_hash,
                'created_at': datetime.utcnow().isoformat(),
                'note_id': note_id
            })
            
            return self.backend.add(note_id, embedding, full_metadata)
        except Exception as e:
            logger.error(f"Failed to add note {note_id}: {e}")
            return False
    
    def add_notes_batch(
        self, 
        notes: List[Tuple[str, str, Optional[Dict]]]
    ) -> Tuple[int, int]:
        """
        Add multiple notes efficiently.
        Returns: (success_count, failure_count)
        """
        if self.embedding_function is None:
            logger.error("No embedding function configured")
            return 0, len(notes)
        
        records = []
        for note_id, content, metadata in notes:
            try:
                embedding = self.embedding_function(content)
                if embedding is None:
                    continue
                
                if not isinstance(embedding, np.ndarray):
                    embedding = np.array(embedding, dtype=np.float32)
                
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                full_metadata = metadata or {}
                full_metadata.update({
                    'content_hash': content_hash,
                    'created_at': datetime.utcnow().isoformat(),
                    'note_id': note_id
                })
                
                records.append(EmbeddingRecord(
                    note_id=note_id,
                    embedding=embedding,
                    content_hash=content_hash,
                    created_at=datetime.utcnow(),
                    metadata=full_metadata
                ))
            except Exception as e:
                logger.warning(f"Failed to process {note_id}: {e}")
        
        if records:
            success = self.backend.add_batch(records)
            if success:
                return len(records), len(notes) - len(records)
        
        return 0, len(notes)
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search for notes similar to the query.
        """
        if self.embedding_function is None:
            logger.error("No embedding function configured")
            return []
        
        try:
            query_embedding = self.embedding_function(query)
            if query_embedding is None:
                return []
            
            if not isinstance(query_embedding, np.ndarray):
                query_embedding = np.array(query_embedding, dtype=np.float32)
            
            return self.backend.search(query_embedding, top_k, filters)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_embedding(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """Search using a pre-computed embedding."""
        return self.backend.search(embedding, top_k, filters)
    
    def delete_note(self, note_id: str) -> bool:
        """Remove a note from the vector database."""
        return self.backend.delete(note_id)
    
    def get_note(self, note_id: str) -> Optional[EmbeddingRecord]:
        """Get a note's embedding record."""
        return self.backend.get(note_id)
    
    def count(self) -> int:
        """Get total number of indexed notes."""
        return self.backend.count()
    
    def clear(self) -> bool:
        """Clear all notes from the database."""
        return self.backend.clear()
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            'backend': type(self.backend).__name__,
            'total_notes': self.count(),
            'has_embedding_function': self.embedding_function is not None,
            'persist_dir': str(self.persist_dir)
        }


# Simple embedding function factory
def create_embedding_function(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Create an embedding function using sentence-transformers.
    Falls back to a simple hash-based approach if the model is not available.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        
        def embed(text: str) -> np.ndarray:
            return model.encode(text, convert_to_numpy=True)
        
        logger.info(f"Using sentence-transformers model: {model_name}")
        return embed
    except ImportError:
        logger.warning("sentence-transformers not available, using fallback")
        
        # Fallback: simple hashing (not for production!)
        def fallback_embed(text: str, dim: int = 384) -> np.ndarray:
            """Simple hash-based embedding for testing."""
            hash_val = hashlib.sha256(text.encode()).hexdigest()
            np.random.seed(int(hash_val[:8], 16))
            return np.random.randn(dim).astype(np.float32)
        
        return fallback_embed


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create a simple test embedding function
    def test_embed(text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(384).astype(np.float32)
    
    # Initialize database
    db = VectorDatabase(
        persist_dir="./test_vector_db",
        embedding_function=test_embed
    )
    
    # Add some notes
    db.add_note("note1", "This is about machine learning and AI.", {"tag": "ai"})
    db.add_note("note2", "Python programming best practices.", {"tag": "programming"})
    db.add_note("note3", "Deep learning neural networks.", {"tag": "ai"})
    
    # Search
    results = db.search("artificial intelligence", top_k=3)
    print("\nSearch results for 'artificial intelligence':")
    for r in results:
        print(f"  {r.note_id}: {r.score:.3f}")
    
    # Stats
    print(f"\nDatabase stats: {db.get_stats()}")
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_vector_db", ignore_errors=True)
    
    print("\nVector Database test completed successfully!")
