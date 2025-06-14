"""Tests for vector searcher functionality."""

import numpy as np
from pathlib import Path

from minerva.vector.searcher import VectorSearcher


class TestVectorSearcher:
    """Test the vector searcher class."""

    def test_initialization(self):
        """Test searcher initialization."""
        # Arrange
        db_path = Path("/test/path.db")

        # Act
        searcher = VectorSearcher(db_path)

        # Assert
        assert searcher.db_path == db_path
        assert searcher._connection is None

    def test_search_similar_stub(self):
        """Test that search_similar returns empty results (stub implementation)."""
        # Arrange
        searcher = VectorSearcher(Path("/test/path.db"))
        query_embedding = np.array([0.1, 0.2, 0.3])

        # Act
        result = searcher.search_similar(query_embedding, k=5)

        # Assert
        assert result == []

    def test_find_similar_to_file_stub(self):
        """Test that find_similar_to_file returns empty results (stub implementation)."""
        # Arrange
        searcher = VectorSearcher(Path("/test/path.db"))

        # Act
        result = searcher.find_similar_to_file("test/file.md", k=5)

        # Assert
        assert result == []

    def test_close_without_connection(self):
        """Test closing without an active connection."""
        # Arrange
        searcher = VectorSearcher(Path("/test/path.db"))

        # Act & Assert (should not raise)
        searcher.close()

        assert searcher._connection is None

    def test_close_with_connection(self):
        """Test closing with an active connection."""
        # Arrange
        from unittest.mock import Mock

        searcher = VectorSearcher(Path("/test/path.db"))
        mock_connection = Mock()
        searcher._connection = mock_connection  # type: ignore[assignment]

        # Act
        searcher.close()

        # Assert
        mock_connection.close.assert_called_once()
        assert searcher._connection is None
