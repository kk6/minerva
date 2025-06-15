"""
Tests for incremental indexing functionality in VectorIndexer.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

# Abort early when the heavy optional dependency is not installed
pytest.importorskip("duckdb", reason="duckdb not available")

from minerva.vector.indexer import VectorIndexer


class TestIncrementalIndexing:
    """Test cases for incremental indexing functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        # Create a temporary directory and a database filename within it
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir) / "test_vectors.db"

        yield temp_path

        # Cleanup
        try:
            if temp_path.exists():
                temp_path.unlink()
            temp_path.parent.rmdir()
        except Exception:
            pass

    @pytest.fixture
    def indexer(self, temp_db_path):
        """Create a VectorIndexer instance for testing."""
        indexer = VectorIndexer(temp_db_path)
        # Initialize with a test schema
        indexer.initialize_schema(384)
        yield indexer
        indexer.close()

    def test_needs_update_file_not_indexed(self, indexer):
        """Test needs_update returns True for files not yet indexed."""
        # Arrange
        test_file = "/test/file.md"

        with patch("os.stat") as mock_stat:
            mock_stat.return_value.st_mtime = datetime.now().timestamp()

            # Act
            result = indexer.needs_update(test_file)

            # Assert
            assert result is True

    def test_needs_update_file_modified(self, indexer):
        """Test needs_update returns True for files modified since indexing."""
        # Arrange
        test_file = "/test/file.md"
        content_hash = "test_hash"

        # First, add the file to tracking
        with patch("os.stat") as mock_stat:
            # Original modification time
            old_time = datetime.now() - timedelta(hours=1)
            mock_stat.return_value.st_mtime = old_time.timestamp()
            indexer.update_file_tracking(test_file, content_hash, 1)

            # Now simulate file being modified
            new_time = datetime.now()
            mock_stat.return_value.st_mtime = new_time.timestamp()

            # Act
            result = indexer.needs_update(test_file)

            # Assert
            assert result is True

    def test_needs_update_file_unchanged(self, indexer):
        """Test needs_update returns False for unchanged files."""
        # Arrange
        test_file = "/test/file.md"
        content = "test content"
        content_hash = "abc123"

        # Set up a specific time for consistency
        file_time = datetime(2023, 1, 1, 12, 0, 0)

        with (
            patch("os.stat") as mock_stat,
            patch("builtins.open", mock_open(read_data=content)),
            patch("hashlib.sha256") as mock_hash,
            patch.object(indexer, "_get_connection") as mock_get_connection,
        ):
            # Setup file modification time
            mock_stat.return_value.st_mtime = file_time.timestamp()

            # Setup hash calculation
            mock_hash_obj = Mock()
            mock_hash_obj.hexdigest.return_value = content_hash
            mock_hash.return_value = mock_hash_obj

            # Mock database connection and query result
            mock_conn = Mock()
            mock_get_connection.return_value = mock_conn

            # Mock the result to show file exists with same hash and time
            # The time should be returned as ISO format string (as stored in database)
            stored_time_str = file_time.isoformat()
            mock_result = Mock()
            mock_result.fetchone.return_value = (stored_time_str, content_hash)
            mock_conn.execute.return_value = mock_result

            # Act
            result = indexer.needs_update(test_file)

            # Assert
            assert result is False

    def test_needs_update_content_changed(self, indexer):
        """Test needs_update returns True when file content changed."""
        # Arrange
        test_file = "/test/file.md"
        new_content = "new content"
        old_hash = "old_hash"
        new_hash = "new_hash"

        with (
            patch("os.stat") as mock_stat,
            patch("builtins.open", mock_open(read_data=new_content)),
            patch("hashlib.sha256") as mock_hash,
        ):
            # Setup file modification time (same time)
            file_time = datetime.now()
            mock_stat.return_value.st_mtime = file_time.timestamp()

            # Setup hash calculation to return new hash
            mock_hash_obj = Mock()
            mock_hash_obj.hexdigest.return_value = new_hash
            mock_hash.return_value = mock_hash_obj

            # Add file to tracking with old hash
            indexer.update_file_tracking(test_file, old_hash, 1)

            # Act
            result = indexer.needs_update(test_file)

            # Assert
            assert result is True

    def test_update_file_tracking_success(self, indexer):
        """Test successful file tracking update."""
        # Arrange
        test_file = "/test/file.md"
        content_hash = "test_hash"
        embedding_count = 2

        with patch("os.stat") as mock_stat:
            file_time = datetime.now()
            mock_stat.return_value.st_mtime = file_time.timestamp()

            # Act
            indexer.update_file_tracking(test_file, content_hash, embedding_count)

            # Assert - verify the record was inserted/updated
            conn = indexer._get_connection()
            result = conn.execute(
                "SELECT content_hash, embedding_count FROM indexed_files WHERE file_path = ?",
                (test_file,),
            ).fetchone()

            assert result is not None
            assert result[0] == content_hash
            assert result[1] == embedding_count

    def test_get_outdated_files_mixed_status(self, indexer):
        """Test get_outdated_files with mix of outdated and current files."""
        # Arrange
        file1 = "/test/file1.md"
        file2 = "/test/file2.md"
        file3 = "/test/file3.md"
        files = [file1, file2, file3]

        with patch.object(indexer, "needs_update") as mock_needs_update:
            # file1: needs update, file2: current, file3: needs update
            mock_needs_update.side_effect = [True, False, True]

            # Act
            outdated_files = indexer.get_outdated_files(files)

            # Assert
            assert len(outdated_files) == 2
            assert file1 in outdated_files
            assert file3 in outdated_files
            assert file2 not in outdated_files

    def test_get_outdated_files_all_current(self, indexer):
        """Test get_outdated_files when all files are current."""
        # Arrange
        files = ["/test/file1.md", "/test/file2.md"]

        with patch.object(indexer, "needs_update", return_value=False):
            # Act
            outdated_files = indexer.get_outdated_files(files)

            # Assert
            assert len(outdated_files) == 0

    def test_get_outdated_files_all_outdated(self, indexer):
        """Test get_outdated_files when all files need updates."""
        # Arrange
        files = ["/test/file1.md", "/test/file2.md", "/test/file3.md"]

        with patch.object(indexer, "needs_update", return_value=True):
            # Act
            outdated_files = indexer.get_outdated_files(files)

            # Assert
            assert len(outdated_files) == 3
            assert set(outdated_files) == set(files)

    def test_store_embedding_updates_tracking(self, indexer):
        """Test that store_embedding automatically updates file tracking."""
        # Arrange
        test_file = "/test/file.md"
        content = "test content for embedding"
        embedding = Mock()
        embedding.ndim = 1
        embedding.reshape.return_value = Mock()
        embedding.tolist.return_value = [0.1] * 384

        with (
            patch("os.stat") as mock_stat,
            patch("hashlib.sha256") as mock_hash,
            patch.object(indexer, "add_vectors", return_value=1) as mock_add_vectors,
        ):
            # Setup file stats
            file_time = datetime.now()
            mock_stat.return_value.st_mtime = file_time.timestamp()

            # Setup hash calculation
            content_hash = "test_hash"
            mock_hash_obj = Mock()
            mock_hash_obj.hexdigest.return_value = content_hash
            mock_hash.return_value = mock_hash_obj

            # Act
            indexer.store_embedding(test_file, embedding, content)

            # Assert
            mock_add_vectors.assert_called_once()

            # Verify tracking was updated
            conn = indexer._get_connection()
            result = conn.execute(
                "SELECT content_hash FROM indexed_files WHERE file_path = ?",
                (test_file,),
            ).fetchone()

            assert result is not None
            assert result[0] == content_hash

    def test_needs_update_file_read_error(self, indexer):
        """Test needs_update handles file read errors gracefully."""
        # Arrange
        test_file = "/test/unreadable.md"
        content_hash = "test_hash"

        with (
            patch("os.stat") as mock_stat,
            patch("builtins.open", side_effect=IOError("Permission denied")),
        ):
            file_time = datetime.now()
            mock_stat.return_value.st_mtime = file_time.timestamp()

            # Add file to tracking first
            indexer.update_file_tracking(test_file, content_hash, 1)

            # Act - should return True when file can't be read
            result = indexer.needs_update(test_file)

            # Assert
            assert result is True

    def test_needs_update_invalid_timestamp(self, indexer):
        """Test needs_update handles invalid stored timestamps."""
        # Arrange
        test_file = "/test/file.md"
        content = "test content"

        with (
            patch("os.stat") as mock_stat,
            patch("builtins.open", mock_open(read_data=content)),
            patch("hashlib.sha256") as mock_hash,
        ):
            file_time = datetime.now()
            mock_stat.return_value.st_mtime = file_time.timestamp()

            # Setup hash calculation
            mock_hash_obj = Mock()
            mock_hash_obj.hexdigest.return_value = "test_hash"
            mock_hash.return_value = mock_hash_obj

            # First add a normal record
            indexer.update_file_tracking(test_file, "test_hash", 1)

            # Then corrupt the timestamp by setting it to NULL (which DuckDB allows)
            conn = indexer._get_connection()
            conn.execute(
                """
                UPDATE indexed_files
                SET file_modified_at = NULL
                WHERE file_path = ?
                """,
                (test_file,),
            )
            conn.close()

            # Act - should return True due to invalid timestamp (NULL)
            result = indexer.needs_update(test_file)

            # Assert
            assert result is True

    def test_needs_update_exception_handling(self, indexer):
        """Test needs_update handles exceptions gracefully."""
        # Arrange
        test_file = "/test/file.md"

        with patch("os.stat", side_effect=Exception("Unexpected error")):
            # Act
            result = indexer.needs_update(test_file)

            # Assert
            assert result is True  # When in doubt, update
            # Note: The actual logger warning is called, but we can't easily mock it
            # without affecting the entire module. The important part is that the
            # method returns True when an exception occurs.


class TestIncrementalIndexingIntegration:
    """Integration tests for incremental indexing with ServiceManager."""

    def test_build_vector_index_incremental_mode(self):
        """Test that build_vector_index uses incremental indexing by default."""
        from minerva.services.service_manager import ServiceManager
        from minerva.config import MinervaConfig
        from minerva.frontmatter_manager import FrontmatterManager

        # Arrange
        config = Mock(spec=MinervaConfig)
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")

        frontmatter_manager = Mock(spec=FrontmatterManager)
        service_manager = ServiceManager(config, frontmatter_manager)

        with (
            patch("glob.glob", return_value=["/test/file1.md", "/test/file2.md"]),
            patch("minerva.vector.embeddings.SentenceTransformerProvider"),
            patch("minerva.vector.indexer.VectorIndexer") as mock_indexer_class,
            patch.object(service_manager, "_prepare_vector_indexing"),
        ):
            # Setup mocks
            mock_indexer = Mock()
            mock_indexer.get_outdated_files.return_value = [
                "/test/file1.md"
            ]  # Only one file outdated
            mock_indexer_class.return_value = mock_indexer

            # Mock file reading
            with patch("builtins.open", mock_open(read_data="test content")):
                # Act
                result = service_manager.build_vector_index(force_rebuild=False)

                # Assert
                mock_indexer.get_outdated_files.assert_called_once()
                assert result["processed"] == 1
                assert result["skipped"] == 1  # One file was skipped as up-to-date

    def test_build_vector_index_force_rebuild_skips_incremental(self):
        """Test that force_rebuild=True skips incremental filtering."""
        from minerva.services.service_manager import ServiceManager
        from minerva.config import MinervaConfig
        from minerva.frontmatter_manager import FrontmatterManager

        # Arrange
        config = Mock(spec=MinervaConfig)
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")

        frontmatter_manager = Mock(spec=FrontmatterManager)
        service_manager = ServiceManager(config, frontmatter_manager)

        with (
            patch("glob.glob", return_value=["/test/file1.md", "/test/file2.md"]),
            patch("minerva.vector.embeddings.SentenceTransformerProvider"),
            patch("minerva.vector.indexer.VectorIndexer") as mock_indexer_class,
            patch.object(service_manager, "_prepare_vector_indexing"),
        ):
            # Setup mocks
            mock_indexer = Mock()
            mock_indexer_class.return_value = mock_indexer

            # Mock file reading
            with patch("builtins.open", mock_open(read_data="test content")):
                # Act
                result = service_manager.build_vector_index(force_rebuild=True)

                # Assert
                mock_indexer.get_outdated_files.assert_not_called()  # Should skip incremental check
                assert result["processed"] == 2  # Both files processed
                assert result["skipped"] == 0
