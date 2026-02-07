"""Embedding engine for RAG pipeline."""

import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Generate embeddings using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Path | None = None,
    ):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = None

    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                
                kwargs = {}
                if self.cache_dir:
                    kwargs["cache_folder"] = str(self.cache_dir)
                
                self._model = SentenceTransformer(self.model_name, **kwargs)
                logger.info(f"Loaded embedding model: {self.model_name}")
                
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()
