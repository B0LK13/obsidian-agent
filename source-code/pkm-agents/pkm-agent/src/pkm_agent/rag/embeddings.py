"""Embedding generation for PKM Agent."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Generates embeddings using sentence-transformers or OpenAI."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        use_openai: bool = False,
        openai_api_key: str | None = None,
        cache_dir: Path | None = None,
    ):
        self.model_name = model_name
        self.use_openai = use_openai
        self.openai_api_key = openai_api_key
        self.cache_dir = cache_dir
        self._model = None
        self._dimension = None

    def _load_model(self) -> None:
        """Lazy load the embedding model."""
        if self._model is not None:
            return

        if self.use_openai:
            self._load_openai()
        else:
            self._load_sentence_transformers()

    def _load_sentence_transformers(self) -> None:
        """Load sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=str(self.cache_dir) if self.cache_dir else None,
            )
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Dimension: {self._dimension}")
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise

    def _load_openai(self) -> None:
        """Set up OpenAI embeddings."""
        try:
            import openai

            if self.openai_api_key:
                openai.api_key = self.openai_api_key

            self._model = "openai"
            self._dimension = 1536 if "ada" in self.model_name else 3072
            logger.info(f"Using OpenAI embeddings: {self.model_name}")
        except ImportError:
            logger.error("openai not installed")
            raise

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        self._load_model()
        return self._dimension or 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        self._load_model()

        if not texts:
            return []

        if self.use_openai:
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts)

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using local model."""
        embeddings = self._model.encode(
            texts,
            show_progress_bar=len(texts) > 10,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API."""
        import openai

        client = openai.OpenAI(api_key=self.openai_api_key)

        # OpenAI has a limit on batch size
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=self.model_name,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        embeddings = self.embed([query])
        return embeddings[0] if embeddings else []


# Singleton-like factory for reuse
_embedding_engine: EmbeddingEngine | None = None


def get_embedding_engine(
    model_name: str = "all-MiniLM-L6-v2",
    **kwargs
) -> EmbeddingEngine:
    """Get or create embedding engine."""
    global _embedding_engine

    if _embedding_engine is None or _embedding_engine.model_name != model_name:
        _embedding_engine = EmbeddingEngine(model_name=model_name, **kwargs)

    return _embedding_engine
