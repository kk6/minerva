"""Embedding providers for text vectorization."""

from abc import ABC, abstractmethod
from typing import List, Union, Any

# Import numpy conditionally
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

# Import at module level for proper testing/mocking
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment,misc]


def _check_numpy_available() -> None:
    """Check if numpy is available and raise error if not."""
    if np is None:
        raise ImportError(
            "numpy is required for vector operations. "
            "Install it with: pip install 'minerva[vector]'"
        )


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, text: Union[str, List[str]]) -> Any:
        """
        Generate embeddings for input text.

        Args:
            text: Single text string or list of text strings

        Returns:
            numpy array of embeddings with shape (n_texts, embedding_dim)
        """
        pass

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Return the dimensionality of embeddings produced by this provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name/identifier of the model being used."""
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider using sentence-transformers library."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize the provider with a specific model.

        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self._model_name = model_name
        self._model: Any = None
        self._embedding_dim: int | None = None

    def _ensure_model_loaded(self) -> None:
        """Lazy load the model when first needed."""
        if self._model is None:
            if SentenceTransformer is None:
                raise ImportError(
                    "sentence-transformers is required for SentenceTransformerProvider. "
                    "Install it with: pip install sentence-transformers"
                )
            self._model = SentenceTransformer(self._model_name)
            # Get embedding dimension directly from model metadata
            try:
                self._embedding_dim = self._model.get_sentence_embedding_dimension()
            except AttributeError:
                # Fallback to dummy encoding if method doesn't exist
                dummy_embedding = self._model.encode("test")
                self._embedding_dim = len(dummy_embedding)

    def embed(self, text: Union[str, List[str]]) -> Any:
        """
        Generate embeddings using sentence-transformers.

        Args:
            text: Single text string or list of text strings

        Returns:
            numpy array of embeddings with shape (n_texts, embedding_dim)
        """
        _check_numpy_available()
        self._ensure_model_loaded()

        # Ensure input is a list for consistent processing
        if isinstance(text, str):
            text = [text]

        embeddings = self._model.encode(text, convert_to_numpy=True)

        # Ensure we always return 2D array
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        return embeddings

    @property
    def embedding_dim(self) -> int:
        """Return the dimensionality of embeddings produced by this provider."""
        if self._embedding_dim is None:
            self._ensure_model_loaded()
        assert self._embedding_dim is not None
        return self._embedding_dim

    @property
    def model_name(self) -> str:
        """Return the name of the sentence-transformer model being used."""
        return self._model_name
