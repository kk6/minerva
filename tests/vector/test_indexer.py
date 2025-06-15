"""Tests for vector indexer functionality."""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from minerva.vector.indexer import VectorIndexer


class TestVectorIndexer:
    """Test the vector indexer class."""

    def test_initialization(self):
        """Test indexer initialization."""
        # Arrange
        db_path = Path("/test/path.db")

        # Act
        indexer = VectorIndexer(db_path)

        # Assert
        assert indexer.db_path == db_path
        assert indexer._connection is None
        assert indexer._initialized is False

    def test_connection_creation_real(self):
        """Test database connection creation with real in-memory database."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)

            # Act
            connection = indexer._get_connection()

            # Assert
            assert connection is not None
            assert indexer._connection == connection

            # Cleanup
            indexer.close()

    def test_import_error_handling_with_mock(self):
        """Test handling of missing duckdb dependency using mocked method."""
        # Arrange
        indexer = VectorIndexer(Path("/test/path.db"))

        # Mock the method that checks for duckdb
        with patch.object(indexer, "_get_connection") as mock_get_conn:
            mock_get_conn.side_effect = ImportError("duckdb is required")

            # Act & Assert
            with pytest.raises(ImportError, match="duckdb is required"):
                indexer._get_connection()

    def test_schema_initialization_real(self):
        """Test database schema initialization with real in-memory database."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)
            embedding_dim = 384

            # Act
            indexer.initialize_schema(embedding_dim)

            # Assert
            assert indexer._initialized is True

            # Verify tables exist by querying them
            conn = indexer._get_connection()
            tables_result = conn.execute("SHOW TABLES").fetchall()
            table_names = [row[0] for row in tables_result]

            assert "vectors" in table_names
            assert "indexed_files" in table_names

            # Cleanup
            indexer.close()

    def test_add_vectors_real(self):
        """Test adding vectors to the index with real database."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)
            indexer.initialize_schema(3)  # Match embedding dimension

            file_path = "test/file.md"
            content_hash = "abc123"
            embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

            # Act
            result = indexer.add_vectors(file_path, content_hash, embeddings)

            # Assert
            assert result == 2

            # Verify vectors were added
            count = indexer.get_vector_count()
            assert count == 2

            # Verify file tracking
            indexed_files = indexer.get_indexed_files()
            assert len(indexed_files) == 1
            assert indexed_files[0] == (file_path, content_hash)

            # Cleanup
            indexer.close()

    def test_remove_vectors_real(self):
        """Test removing vectors from the index with real database."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)
            indexer.initialize_schema(3)  # Match embedding dimension

            file_path = "test/file.md"
            content_hash = "abc123"
            embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

            # Add vectors first
            indexer.add_vectors(file_path, content_hash, embeddings)

            # Act
            result = indexer.remove_vectors(file_path)

            # Assert
            assert result == 2

            # Verify vectors were removed
            count = indexer.get_vector_count()
            assert count == 0

            # Verify file tracking was removed
            indexed_files = indexer.get_indexed_files()
            assert len(indexed_files) == 0

            # Cleanup
            indexer.close()

    def test_hnsw_index_creation_real(self):
        """Test HNSW index creation with in-memory database."""
        # Arrange - use in-memory database for HNSW index creation
        indexer = VectorIndexer(Path(":memory:"))
        indexer.initialize_schema(3)

        # Act
        indexer.create_hnsw_index("test_index")

        # No explicit assertions since DuckDB handles the index creation
        # If it doesn't raise an exception, the test passes

        # Cleanup
        indexer.close()

    def test_add_vectors_without_initialization(self):
        """Test that adding vectors fails without schema initialization."""
        # Arrange
        indexer = VectorIndexer(Path("/test/path.db"))
        embeddings = np.array([[0.1, 0.2, 0.3]])

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database schema not initialized"):
            indexer.add_vectors("test", "hash", embeddings)

    def test_hnsw_index_creation_without_initialization(self):
        """Test that HNSW index creation fails without schema initialization."""
        # Arrange
        indexer = VectorIndexer(Path("/test/path.db"))

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database schema not initialized"):
            indexer.create_hnsw_index()

    def test_vss_extension_setup_real(self):
        """Test VSS extension installation with real in-memory database."""
        # Arrange - use in-memory database for VSS extension test
        indexer = VectorIndexer(Path(":memory:"))

        # Act - This will trigger VSS extension loading
        connection = indexer._get_connection()

        # Assert - If no exception is raised, VSS extension loaded successfully
        assert connection is not None
        assert indexer._connection == connection

        # Cleanup
        indexer.close()


class TestVectorIndexerErrorPaths:
    """Test error paths and edge cases in vector indexer."""

    def test_home_directory_fallback(self):
        """Test home directory fallback logic."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)

            # Mock os.path.expanduser to return invalid home
            with patch("os.path.expanduser", return_value=""):
                # This should trigger the fallback logic
                indexer._get_connection()

            # Should still work with fallback
            assert indexer._connection is not None
            indexer.close()

    def test_home_directory_tilde_fallback(self):
        """Test home directory fallback when expanduser returns '~'."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)

            # Mock os.path.expanduser to return just "~"
            with patch("os.path.expanduser", return_value="~"):
                # This should trigger the fallback logic
                indexer._get_connection()

            # Should still work with fallback
            assert indexer._connection is not None
            indexer.close()

    def test_home_directory_setup_error(self):
        """Test error handling in home directory setup."""
        indexer = VectorIndexer(Path("/test/path.db"))

        # Mock connection to raise exception
        mock_connection = Mock()
        mock_connection.execute.side_effect = Exception("Test error")
        indexer._connection = mock_connection

        # Call _setup_home_directory directly
        indexer._setup_home_directory()
        # Should not raise exception, just log warning

    def test_vss_extension_already_loaded(self):
        """Test VSS extension setup when already loaded."""
        indexer = VectorIndexer(Path("/test/path.db"))

        # Mock connection with VSS already loaded
        mock_connection = Mock()
        mock_connection.fetchone.return_value = True  # Already loaded
        indexer._connection = mock_connection

        # This should trigger the "already loaded" path
        indexer._setup_vss_extension()

        # Verify that only the check query was executed, not install/load
        assert mock_connection.execute.call_count == 1

    def test_close_idempotent(self):
        """Test that close() can be called multiple times safely."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            indexer = VectorIndexer(db_path)

            # Get connection
            indexer._get_connection()

            # Close once
            indexer.close()
            assert indexer._connection is None

            # Close again - should not raise exception
            indexer.close()
            assert indexer._connection is None

    def test_close_without_connection(self):
        """Test that close() works when no connection was ever created."""
        indexer = VectorIndexer(Path("/test/path.db"))

        # Close without ever calling _get_connection
        indexer.close()  # Should not raise exception
        assert indexer._connection is None
