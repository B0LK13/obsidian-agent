"""ChromaDB vector store implementation"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from ..config import VectorStoreConfig
from ..errors import VectorStoreError, ErrorCode, ErrorSeverity

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB vector store for semantic search"""
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self._client = None
        self._collection = None
        self._embedding_model = None
    
    def initialize(self):
        """Initialize ChromaDB client and embedding model"""
        try:
            persist_dir = Path(self.config.persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Loading embedding model: {self.config.embedding_model}")
            self._embedding_model = SentenceTransformer(self.config.embedding_model)
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to initialize ChromaDB: {e}",
                code=ErrorCode.VECTOR_STORE_CONNECTION_FAILED,
                severity=ErrorSeverity.CRITICAL,
                recoverable=False,
            )
    
    def _get_embeddings(self, texts):
        """Generate embeddings for texts"""
        if self._embedding_model is None:
            raise VectorStoreError(
                message="Embedding model not initialized",
                code=ErrorCode.EMBEDDING_GENERATION_FAILED
            )
        return self._embedding_model.encode(texts).tolist()
    
    def add_documents(self, ids, texts, metadatas=None):
        """Add documents to the vector store"""
        if not ids or not texts:
            return
        try:
            embeddings = self._get_embeddings(texts)
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas or [{}] * len(ids)
            )
            logger.info(f"Added {len(ids)} documents to vector store")
        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to add documents: {e}",
                code=ErrorCode.VECTOR_STORE_INDEX_FAILED,
                recoverable=True
            )
    
    def search(self, query, n_results=10, threshold=None):
        """Search for similar documents"""
        try:
            query_embedding = self._get_embeddings([query])[0]
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            documents = []
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                similarity = 1 - distance
                if threshold and similarity < threshold:
                    continue
                documents.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": similarity
                })
            return documents
        except Exception as e:
            raise VectorStoreError(
                message=f"Search failed: {e}",
                code=ErrorCode.VECTOR_STORE_SEARCH_FAILED,
                recoverable=True
            )
    
    def delete_documents(self, ids):
        """Delete documents from the vector store"""
        if not ids:
            return
        self._collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from vector store")
    
    def count(self):
        """Get the number of documents in the store"""
        return self._collection.count() if self._collection else 0
    
    def close(self):
        """Close the vector store connection"""
        self._client = None
        self._collection = None
        self._embedding_model = None
