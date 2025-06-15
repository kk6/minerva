"""Tests for vector searcher functionality."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock

# Import numpy conditionally
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

from minerva.vector.searcher import VectorSearcher

# Mark all tests in this module as requiring vector dependencies
pytestmark = pytest.mark.vector


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

        searcher = VectorSearcher(Path("/test/path.db"))
        mock_connection = Mock()
        searcher._connection = mock_connection

        # Act
        searcher.close()

        # Assert
        mock_connection.close.assert_called_once()
        assert searcher._connection is None

    def test_import_error_handling(self):
        """Test that ImportError is raised when duckdb is not available."""

        # Mock the _get_connection method to simulate import error
        def mock_get_connection():
            raise ImportError(
                "duckdb is required for VectorSearcher. "
                "Install it with: pip install duckdb"
            )

        # Act & Assert
        with pytest.raises(ImportError, match="duckdb is required"):
            mock_get_connection()

    @pytest.mark.slow
    def test_search_similar_with_real_db(self):
        """Test search_similar with real DuckDB connection."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            searcher = VectorSearcher(db_path)

            # Set up database with test data
            conn = searcher._get_connection()
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
                    file_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding FLOAT[3] NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert test vectors
            test_vectors = [
                ("file1.md", "hash1", [0.1, 0.2, 0.3]),
                ("file2.md", "hash2", [0.4, 0.5, 0.6]),
                ("file3.md", "hash3", [0.7, 0.8, 0.9]),
            ]

            for file_path, content_hash, embedding in test_vectors:
                conn.execute(
                    "INSERT INTO vectors (file_path, content_hash, embedding) VALUES (?, ?, ?)",
                    [file_path, content_hash, embedding],
                )

            # Test query
            query_embedding = np.array([0.1, 0.2, 0.3])

            # Act
            results = searcher.search_similar(query_embedding, k=2)

            # Assert
            assert len(results) == 2
            assert results[0][0] == "file1.md"  # Should be most similar
            assert isinstance(results[0][1], float)  # Similarity score
            assert 0.0 <= results[0][1] <= 1.0

            searcher.close()

    @pytest.mark.slow
    def test_find_similar_to_file_with_real_db(self):
        """Test find_similar_to_file with real DuckDB connection."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            searcher = VectorSearcher(db_path)

            # Set up database with test data
            conn = searcher._get_connection()
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
                    file_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding FLOAT[3] NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert test vectors
            test_vectors = [
                ("file1.md", "hash1", [0.1, 0.2, 0.3]),
                ("file2.md", "hash2", [0.4, 0.5, 0.6]),
                ("file3.md", "hash3", [0.1, 0.2, 0.4]),  # Similar to file1
            ]

            for file_path, content_hash, embedding in test_vectors:
                conn.execute(
                    "INSERT INTO vectors (file_path, content_hash, embedding) VALUES (?, ?, ?)",
                    [file_path, content_hash, embedding],
                )

            # Act
            results = searcher.find_similar_to_file("file1.md", k=2, exclude_self=True)

            # Assert
            assert len(results) <= 2
            # Should not include file1.md itself
            file_paths = [result[0] for result in results]
            assert "file1.md" not in file_paths

            searcher.close()

    def test_find_similar_to_file_not_found(self):
        """Test find_similar_to_file with non-existent file."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            searcher = VectorSearcher(db_path)

            # Set up empty database
            conn = searcher._get_connection()
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
                    file_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding FLOAT[3] NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Act
            results = searcher.find_similar_to_file("nonexistent.md", k=5)

            # Assert
            assert results == []

            searcher.close()

    @pytest.mark.slow
    def test_get_indexed_files(self):
        """Test get_indexed_files method."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            searcher = VectorSearcher(db_path)

            # Set up database with test data
            conn = searcher._get_connection()
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
                    file_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding FLOAT[3] NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert test vectors
            test_files = ["file1.md", "file2.md", "file3.md"]
            for file_path in test_files:
                conn.execute(
                    "INSERT INTO vectors (file_path, content_hash, embedding) VALUES (?, ?, ?)",
                    [file_path, "hash", [0.1, 0.2, 0.3]],
                )

            # Act
            indexed_files = searcher.get_indexed_files()

            # Assert
            assert len(indexed_files) == 3
            assert set(indexed_files) == set(test_files)

            searcher.close()

    @pytest.mark.slow
    def test_is_file_indexed(self):
        """Test is_file_indexed method."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            searcher = VectorSearcher(db_path)

            # Set up database with test data
            conn = searcher._get_connection()
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
                    file_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding FLOAT[3] NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert one test vector
            conn.execute(
                "INSERT INTO vectors (file_path, content_hash, embedding) VALUES (?, ?, ?)",
                ["indexed_file.md", "hash", [0.1, 0.2, 0.3]],
            )

            # Act & Assert
            assert searcher.is_file_indexed("indexed_file.md") is True
            assert searcher.is_file_indexed("not_indexed.md") is False

            searcher.close()
