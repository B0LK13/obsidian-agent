"""Vector store for RAG pipeline using FAISS."""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Callable

import numpy as np

from pkm_agent.rag.chunker import Chunk

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS vector store for semantic search."""

    def __init__(
        self,
        persist_path: Path,
        embedding_engine,
        collection_name: str = "pkm_chunks",
    ):
        self.persist_path = Path(persist_path)
        self.embedding_engine = embedding_engine
        self.collection_name = collection_name
        self._index = None
        self._documents: list[dict] = []  # Store docs with metadata
        self._id_to_idx: dict[str, int] = {}  # Map chunk ID to index
        self.audit_logger: Callable | None = None
        
        # Ensure persist path exists
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.persist_path / f"{collection_name}.faiss"
        self._docs_path = self.persist_path / f"{collection_name}_docs.pkl"
        
        # Load existing index if available
        self._load()

    def _load(self):
        """Load existing index and documents."""
        try:
            import faiss
            
            if self._index_path.exists() and self._docs_path.exists():
                self._index = faiss.read_index(str(self._index_path))
                with open(self._docs_path, "rb") as f:
                    data = pickle.load(f)
                    self._documents = data.get("documents", [])
                    self._id_to_idx = data.get("id_to_idx", {})
                logger.info(f"Loaded FAISS index ({type(self._index).__name__}) with {len(self._documents)} documents")
            else:
                # Create new index - will be initialized on first add
                self._index = None
                self._documents = []
                self._id_to_idx = {}
                logger.info("Created new FAISS index")
        except ImportError:
            raise ImportError("faiss-cpu not installed. Install with: pip install faiss-cpu")

    def _save(self):
        """Persist index and documents to disk."""
        import faiss
        
        if self._index is not None:
            faiss.write_index(self._index, str(self._index_path))
            with open(self._docs_path, "wb") as f:
                pickle.dump({
                    "documents": self._documents,
                    "id_to_idx": self._id_to_idx,
                }, f)

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to the vector store."""
        import faiss
        
        if not chunks:
            return 0

        documents = [c.content for c in chunks]
        
        # Generate embeddings
        embeddings = self.embedding_engine.embed(documents)
        embeddings = np.array(embeddings).astype("float32")
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Initialize index if needed
        if self._index is None:
            dim = embeddings.shape[1]
            # Use HNSW for better performance on large datasets
            # M=32: number of connections per layer (higher = better recall, more memory)
            # efConstruction=40: controls index build time (higher = better quality, slower build)
            if len(self._documents) > 1000:
                # For larger datasets, use HNSW
                self._index = faiss.IndexHNSWFlat(dim, 32)
                self._index.hnsw.efConstruction = 40
                logger.info("Using HNSW index for improved performance")
            else:
                # For smaller datasets, flat index is sufficient
                self._index = faiss.IndexFlatIP(dim)
                logger.info("Using flat index")
        
        # Add to index
        start_idx = len(self._documents)
        self._index.add(embeddings)
        
        # Store documents and build ID map
        for i, chunk in enumerate(chunks):
            idx = start_idx + i
            self._id_to_idx[chunk.id] = idx
            self._documents.append({
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
            })
        
        self._save()
        
        if self.audit_logger:
            self.audit_logger("vectorstore", "add_chunks", {"count": len(chunks)})
        
        logger.debug(f"Added {len(chunks)} chunks to vector store")
        return len(chunks)

    def search(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks."""
        import faiss
        
        if self._index is None or self._index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_engine.embed_single(query)
        query_embedding = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query_embedding)
        
        # Search - get more results if filtering
        search_k = k * 3 if filters else k
        scores, indices = self._index.search(query_embedding, min(search_k, self._index.ntotal))
        
        # Format results
        formatted = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
                
            doc = self._documents[idx]
            
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    if doc.get("metadata", {}).get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            formatted.append({
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc.get("metadata", {}),
                "distance": 1 - scores[0][i],  # Convert similarity to distance
                "score": float(scores[0][i]),
            })
            
            if len(formatted) >= k:
                break
        
        return formatted

    def delete_note_chunks(self, note_id: str):
        """Delete all chunks for a note.
        
        Note: FAISS doesn't support deletion well, so we rebuild the index.
        """
        # Find indices to delete
        to_delete = []
        for i, doc in enumerate(self._documents):
            if doc.get("metadata", {}).get("note_id") == note_id:
                to_delete.append(i)
        
        if not to_delete:
            return
        
        # Rebuild without deleted documents
        new_docs = [d for i, d in enumerate(self._documents) if i not in to_delete]
        
        if new_docs:
            # Re-embed and rebuild index
            embeddings = self.embedding_engine.embed([d["content"] for d in new_docs])
            embeddings = np.array(embeddings).astype("float32")
            
            import faiss
            faiss.normalize_L2(embeddings)
            
            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatIP(dim)
            self._index.add(embeddings)
            
            self._documents = new_docs
            self._id_to_idx = {d["id"]: i for i, d in enumerate(new_docs)}
        else:
            self._index = None
            self._documents = []
            self._id_to_idx = {}
        
        self._save()
        logger.debug(f"Deleted {len(to_delete)} chunks for note {note_id}")

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        return {
            "collection_name": self.collection_name,
            "total_chunks": len(self._documents),
        }
