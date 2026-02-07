# pyright: reportMissingImports=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportMissingTypeArgument=false
"""Vector store for semantic search using ChromaDB."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pkm_agent.data.models import Chunk, SearchResult
from pkm_agent.rag.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector store for semantic search."""

    COLLECTION_NAME = "pkm_embeddings"

    def __init__(
        self,
        persist_dir: Path,
        embedding_engine: EmbeddingEngine,
    ):
        self.persist_dir = persist_dir
        self.embedding_engine = embedding_engine
        self._client = None
        self._collection = None
        self.audit_logger: Callable[[str, str, dict[str, Any] | None], None] | None = None

    def _ensure_client(self) -> None:
        """Ensure ChromaDB client is initialized."""
        if self._client is not None:
            return

        try:
            import chromadb
            from chromadb.config import Settings

            self.persist_dir.mkdir(parents=True, exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

            logger.info(f"ChromaDB initialized at {self.persist_dir}")
            logger.info(f"Collection '{self.COLLECTION_NAME}' has {self._collection.count()} items")

        except ImportError as exc:
            logger.error("chromadb not installed. Install with: pip install chromadb")
            raise exc

    @property
    def collection(self):
        """Get the ChromaDB collection."""
        self._ensure_client()
        return self._collection

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to the vector store."""
        if not chunks:
            return 0

        self._ensure_client()

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_engine.embed(texts)

        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in chunks]
        documents = texts
        metadatas = []

        for chunk in chunks:
            meta = {
                "note_id": chunk.note_id,
                "chunk_index": chunk.index,
                "title": chunk.metadata.get("title", ""),
                "path": chunk.metadata.get("path", ""),
            }
            # Add tags as comma-separated string
            tags = chunk.metadata.get("tags", [])
            if tags:
                meta["tags"] = ",".join(tags)
            if chunk.metadata.get("area"):
                meta["area"] = chunk.metadata["area"]

            metadatas.append(meta)

        # Upsert to collection
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        if self.audit_logger:
            self.audit_logger(
                "vectorstore",
                "add_chunks",
                {"count": len(chunks), "ids": ids[:5], "truncated": len(ids) > 5},
            )

        logger.debug(f"Added {len(chunks)} chunks to vector store")
        return len(chunks)

    def search(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks."""
        self._ensure_client()

        # Generate query embedding
        query_embedding = self.embedding_engine.embed_query(query)

        # Build where clause for filters
        where = None
        if filters:
            conditions = []
            if filters.get("note_id"):
                conditions.append({"note_id": filters["note_id"]})
            if filters.get("area"):
                conditions.append({"area": filters["area"]})
            if filters.get("tags"):
                # ChromaDB doesn't support array contains, so we use string matching
                conditions.append({"tags": {"$contains": filters["tags"]}})

            if len(conditions) == 1:
                where = conditions[0]
            elif len(conditions) > 1:
                where = {"$and": conditions}

        # Query the collection
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        if self.audit_logger:
            self.audit_logger(
                "vectorstore",
                "search",
                {"query": query, "k": k, "filters": filters or {}},
            )

        # Convert to SearchResult objects
        search_results = []

        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                document = results["documents"][0][i] if results["documents"] else ""
                distance = results["distances"][0][i] if results["distances"] else 1.0

                # Convert distance to similarity score (cosine distance -> similarity)
                score = 1 - distance

                search_results.append(SearchResult(
                    note_id=metadata.get("note_id", ""),
                    path=metadata.get("path", ""),
                    title=metadata.get("title", ""),
                    score=score,
                    snippet=document[:200] + "..." if len(document) > 200 else document,
                    highlights=[query],
                ))

        return search_results

    def delete_note(self, note_id: str) -> int:
        """Delete all chunks for a note."""
        self._ensure_client()

        # Get all chunk IDs for this note
        results = self._collection.get(
            where={"note_id": note_id},
            include=[],
        )

        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            deleted = len(results["ids"])
            if self.audit_logger:
                self.audit_logger(
                    "vectorstore",
                    "delete_note",
                    {"note_id": note_id, "deleted_chunks": deleted},
                )
            logger.debug(f"Deleted {deleted} chunks for note {note_id}")
            return deleted

        return 0

    def clear(self) -> None:
        """Clear all data from the collection."""
        self._ensure_client()

        # Delete and recreate collection
        self._client.delete_collection(self.COLLECTION_NAME)
        self._collection = self._client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store cleared")

    def count(self) -> int:
        """Get number of items in the collection."""
        self._ensure_client()
        return self._collection.count()

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        self._ensure_client()

        return {
            "total_chunks": self._collection.count(),
            "collection_name": self.COLLECTION_NAME,
            "persist_dir": str(self.persist_dir),
        }
