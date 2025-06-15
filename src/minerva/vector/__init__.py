"""Vector search module for semantic search capabilities."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # static type-checkers still "see" the real classes
    from .embeddings import EmbeddingProvider, SentenceTransformerProvider
    from .indexer import VectorIndexer
    from .searcher import VectorSearcher

__all__ = [
    "EmbeddingProvider",
    "SentenceTransformerProvider",
    "VectorIndexer",
    "VectorSearcher",
]


def __getattr__(name: str):  # pragma: no cover
    """Lazy loading for vector search components to avoid eager imports."""
    if name == "EmbeddingProvider":
        from .embeddings import EmbeddingProvider

        return EmbeddingProvider
    if name == "SentenceTransformerProvider":
        from .embeddings import SentenceTransformerProvider

        return SentenceTransformerProvider
    if name == "VectorIndexer":
        from .indexer import VectorIndexer

        return VectorIndexer
    if name == "VectorSearcher":
        from .searcher import VectorSearcher

        return VectorSearcher
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
