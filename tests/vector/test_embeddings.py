"""Tests for embedding providers."""

import pytest
import numpy as np
from unittest.mock import patch

# Abort early when the heavy optional dependency is not installed
pytest.importorskip(
    "sentence_transformers", reason="sentence-transformers not available"
)

from minerva.vector.embeddings import EmbeddingProvider, SentenceTransformerProvider


class TestEmbeddingProvider:
    """Test the abstract embedding provider base class."""

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented in subclasses."""
        # Arrange & Act & Assert
        with pytest.raises(TypeError):
            EmbeddingProvider()  # type: ignore[abstract]  # Intentionally testing abstract class instantiation


class TestSentenceTransformerProvider:
    """Test the sentence transformer embedding provider."""

    def test_initialization_with_default_model(self):
        """Test provider initialization with default model."""
        # Arrange & Act
        provider = SentenceTransformerProvider()

        # Assert
        assert provider.model_name == "all-MiniLM-L6-v2"
        assert provider._model is None
        assert provider._embedding_dim is None

    def test_initialization_with_custom_model(self):
        """Test provider initialization with custom model."""
        # Arrange
        custom_model = "custom-model"

        # Act
        provider = SentenceTransformerProvider(custom_model)

        # Assert
        assert provider.model_name == custom_model

    @pytest.mark.slow
    def test_embed_single_text_real(self):
        """Test embedding a single text string with real implementation."""
        # Arrange
        provider = SentenceTransformerProvider()

        # Act
        result = provider.embed("single text")

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.ndim == 2
        assert result.shape[0] == 1  # One text
        assert result.shape[1] > 0  # Has embedding dimensions

    @pytest.mark.slow
    def test_embed_multiple_texts_real(self):
        """Test embedding multiple text strings with real implementation."""
        # Arrange
        provider = SentenceTransformerProvider()
        texts = ["first text", "second text"]

        # Act
        result = provider.embed(texts)

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.ndim == 2
        assert result.shape[0] == 2  # Two texts
        assert result.shape[1] > 0  # Has embedding dimensions

    @pytest.mark.slow
    def test_embedding_dimension_property_real(self):
        """Test the embedding dimension property with real implementation."""
        # Arrange
        provider = SentenceTransformerProvider()

        # Act
        dimension = provider.embedding_dim

        # Assert
        assert isinstance(dimension, int)
        assert dimension > 0  # Should have positive dimensions

    @pytest.mark.slow
    def test_model_caching(self):
        """Test that model is loaded once and reused."""
        # Arrange
        provider = SentenceTransformerProvider()

        # Act - multiple calls should reuse the same model
        provider.embed("first call")
        model_after_first = provider._model

        provider.embed("second call")
        model_after_second = provider._model

        # Assert
        assert model_after_first is not None
        assert model_after_second is model_after_first  # Same object

    @pytest.mark.slow
    def test_model_lazy_loading_behavior(self):
        """Test that model is loaded lazily on first use."""
        # Arrange
        provider = SentenceTransformerProvider()

        # Assert model is not loaded initially
        assert provider._model is None

        # Act - first embedding call should load the model
        provider.embed("test text")

        # Assert model is now loaded
        assert provider._model is not None

    def test_import_error_handling_with_mock(self):
        """Test handling of missing sentence-transformers dependency."""
        # Arrange
        provider = SentenceTransformerProvider()

        # Mock the _ensure_model_loaded method to simulate ImportError
        with patch.object(provider, "_ensure_model_loaded") as mock_ensure:
            mock_ensure.side_effect = ImportError("sentence-transformers is required")

            # Act & Assert
            with pytest.raises(ImportError, match="sentence-transformers is required"):
                provider.embed("test")
