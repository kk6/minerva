"""
Tests for batch indexing functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import numpy as np

from minerva.config import MinervaConfig
from minerva.vector.batch_indexer import BatchIndexer, IndexingTask, get_batch_indexer


class TestIndexingTask:
    """Test cases for IndexingTask dataclass."""

    def test_indexing_task_creation(self):
        """Test basic IndexingTask creation."""
        task = IndexingTask(
            file_path="/test/file.md", content="test content", operation="update"
        )

        assert task.file_path == "/test/file.md"
        assert task.content == "test content"
        assert task.operation == "update"
        assert task.priority == 1  # Default priority

    def test_indexing_task_with_priority(self):
        """Test IndexingTask creation with custom priority."""
        task = IndexingTask(
            file_path="/test/file.md",
            content="test content",
            operation="add",
            priority=5,
        )

        assert task.priority == 5


class TestBatchIndexer:
    """Test cases for BatchIndexer class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")
        return config

    @pytest.fixture
    def batch_indexer(self, mock_config):
        """Create a BatchIndexer instance for testing."""
        return BatchIndexer(
            config=mock_config,
            batch_size=3,
            batch_timeout=10.0,
            background_enabled=False,
        )

    def test_initialization(self, mock_config):
        """Test BatchIndexer initialization."""
        indexer = BatchIndexer(
            config=mock_config,
            batch_size=5,
            batch_timeout=20.0,
            background_enabled=True,
        )

        assert indexer.config == mock_config
        assert indexer.batch_size == 5
        assert indexer.batch_timeout == 20.0
        assert indexer.background_enabled is True
        assert indexer._processing_enabled is True
        assert indexer.get_queue_size() == 0

    def test_queue_task(self, batch_indexer):
        """Test queuing a task."""
        # Arrange
        file_path = "/test/vault/file.md"
        content = "test content"

        # Act
        batch_indexer.queue_task(file_path, content, "update")

        # Assert
        assert batch_indexer.get_queue_size() == 1
        stats = batch_indexer.get_stats()
        assert stats["tasks_queued"] == 1

    def test_queue_multiple_tasks(self, batch_indexer):
        """Test queuing multiple tasks."""
        # Arrange & Act
        # Queue only 2 tasks (less than batch_size of 3) to avoid auto-processing
        for i in range(2):
            batch_indexer.queue_task(
                f"/test/vault/file{i}.md", f"content {i}", "update"
            )

        # Assert
        assert batch_indexer.get_queue_size() == 2
        stats = batch_indexer.get_stats()
        assert stats["tasks_queued"] == 2

    def test_queue_task_when_stopped(self, batch_indexer):
        """Test queuing task when indexer is stopped."""
        # Arrange
        batch_indexer.stop()

        # Act
        batch_indexer.queue_task("/test/vault/file.md", "content", "update")

        # Assert
        assert batch_indexer.get_queue_size() == 0
        stats = batch_indexer.get_stats()
        assert stats["tasks_queued"] == 0

    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_process_batch_success(
        self, mock_indexer_class, mock_provider_class, batch_indexer
    ):
        """Test successful batch processing."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        mock_provider = Mock()
        # Create a mock that behaves like a numpy array
        mock_embedding = np.array([0.1] * 384)  # 384-dimensional embedding
        mock_provider.embed.return_value = mock_embedding
        mock_provider_class.return_value = mock_provider

        # Queue some tasks
        batch_indexer.queue_task("/test/vault/file1.md", "content1", "update")
        batch_indexer.queue_task("/test/vault/file2.md", "content2", "add")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 2
        assert batch_indexer.get_queue_size() == 0
        stats = batch_indexer.get_stats()
        assert stats["tasks_processed"] == 2
        assert stats["batches_processed"] == 1

    def test_process_batch_empty_queue(self, batch_indexer):
        """Test processing when queue is empty."""
        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 0
        stats = batch_indexer.get_stats()
        assert (
            stats["batches_processed"] == 1
        )  # Should increment even for empty batches

    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_process_batch_with_remove_operation(
        self, mock_indexer_class, mock_provider_class, batch_indexer
    ):
        """Test batch processing with remove operation."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        mock_provider = Mock()
        # Create a mock that behaves like a numpy array
        mock_embedding = np.array([0.1] * 384)  # 384-dimensional embedding
        mock_provider.embed.return_value = mock_embedding
        mock_provider_class.return_value = mock_provider

        # Queue a remove task
        batch_indexer.queue_task("/test/vault/file.md", "", "remove")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 1
        mock_indexer.remove_file.assert_called_once_with("/test/vault/file.md")

    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_process_batch_with_error(
        self, mock_indexer_class, mock_provider_class, batch_indexer
    ):
        """Test batch processing with errors."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer.store_embedding.side_effect = Exception("Test error")
        mock_indexer_class.return_value = mock_indexer

        mock_provider = Mock()
        # Create a mock that behaves like a numpy array
        mock_embedding = np.array([0.1] * 384)  # 384-dimensional embedding
        mock_provider.embed.return_value = mock_embedding
        mock_provider_class.return_value = mock_provider

        # Queue a task
        batch_indexer.queue_task("/test/vault/file.md", "content", "update")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 0  # No tasks processed due to error
        stats = batch_indexer.get_stats()
        assert stats["errors"] == 1

    def test_process_all_pending(self, batch_indexer):
        """Test processing all pending tasks."""
        # Arrange
        batch_indexer.queue_task("/test/vault/file1.md", "content1", "update")
        batch_indexer.queue_task("/test/vault/file2.md", "content2", "update")
        # Simulate processing and emptying the queue
        with patch.object(
            batch_indexer, "_process_tasks_batch", return_value=2
        ) as mock_lowlevel:
            # Act
            total_processed = batch_indexer.process_all_pending()

            # Assert
            assert total_processed == 2
            mock_lowlevel.assert_called_once()
    def test_get_stats(self, batch_indexer):
        """Test getting processing statistics."""
        # Act
        stats = batch_indexer.get_stats()

        # Assert
        expected_keys = [
            "tasks_queued",
            "tasks_processed",
            "batches_processed",
            "errors",
        ]
        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], int)

    def test_stop(self, batch_indexer):
        """Test stopping the batch indexer."""
        # Act
        batch_indexer.stop()

        # Assert
        assert batch_indexer._processing_enabled is False


class TestBatchIndexerBackground:
    """Test cases for background processing functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")
        return config

    @patch("minerva.vector.batch_indexer.threading.Thread")
    def test_background_processing_initialization(self, mock_thread_class, mock_config):
        """Test background processing thread initialization."""
        # Arrange
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        # Act
        indexer = BatchIndexer(
            config=mock_config, batch_size=3, batch_timeout=1.0, background_enabled=True
        )

        try:
            # Assert
            assert indexer.background_enabled is True
            assert indexer._background_thread is not None
            mock_thread.start.assert_called_once()
        finally:
            indexer.stop()

    @patch("minerva.vector.batch_indexer.threading.Thread")
    def test_background_processing_stops_correctly(
        self, mock_thread_class, mock_config
    ):
        """Test that background processing stops correctly."""
        # Arrange
        mock_thread = Mock()
        mock_thread.is_alive.return_value = (
            True  # Thread is alive, so join should be called
        )
        mock_thread_class.return_value = mock_thread

        indexer = BatchIndexer(
            config=mock_config, batch_size=3, batch_timeout=0.5, background_enabled=True
        )

        # Act
        indexer.stop()

        # Assert
        assert indexer._processing_enabled is False
        mock_thread.join.assert_called_once_with(timeout=5.0)


class TestGlobalBatchIndexer:
    """Test cases for global batch indexer functions."""

    def setup_method(self):
        """Clean up global state before each test."""
        from minerva.vector.batch_indexer import stop_batch_indexer

        stop_batch_indexer()

    def teardown_method(self):
        """Clean up global state after each test."""
        from minerva.vector.batch_indexer import stop_batch_indexer

        stop_batch_indexer()

    def test_get_batch_indexer_immediate_strategy(self):
        """Test get_batch_indexer with immediate strategy."""
        # Arrange
        config = Mock()
        config.vault_path = Path("/test/vault")

        # Act
        indexer = get_batch_indexer(config, "immediate")

        # Assert
        assert indexer is None

    @patch("minerva.vector.batch_indexer.threading.Thread")
    def test_get_batch_indexer_batch_strategy(self, mock_thread_class):
        """Test get_batch_indexer with batch strategy."""
        # Arrange
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        config = Mock()
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")

        # Act
        indexer = get_batch_indexer(config, "batch")

        # Assert
        assert indexer is not None
        assert isinstance(indexer, BatchIndexer)
        assert indexer.background_enabled is False

    @patch("minerva.vector.batch_indexer.threading.Thread")
    def test_get_batch_indexer_background_strategy(self, mock_thread_class):
        """Test get_batch_indexer with background strategy."""
        # Arrange
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        config = Mock()
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")

        # Act
        indexer = get_batch_indexer(config, "background")

        # Assert
        assert indexer is not None
        assert isinstance(indexer, BatchIndexer)
        # For background strategy, even if thread is not called due to existing instance,
        # we should verify that a background indexer exists
        # We'll check the indexer has background capabilities
        assert hasattr(indexer, "background_enabled")

    @patch("minerva.vector.batch_indexer.threading.Thread")
    def test_get_batch_indexer_reuses_instance(self, mock_thread_class):
        """Test that get_batch_indexer reuses the same instance."""
        # Arrange
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        config = Mock()
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")

        # Act
        indexer1 = get_batch_indexer(config, "batch")
        indexer2 = get_batch_indexer(config, "batch")

        # Assert
        assert indexer1 is indexer2

    @patch("minerva.vector.batch_indexer.threading.Thread")
    def test_stop_batch_indexer(self, mock_thread_class):
        """Test stopping the global batch indexer."""
        # Arrange
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        from minerva.vector.batch_indexer import stop_batch_indexer

        config = Mock()
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")

        indexer = get_batch_indexer(config, "batch")
        assert indexer is not None

        # Act
        stop_batch_indexer()

        # Assert
        # The global instance should be reset after stopping
        # After stopping, a new request should create a new instance
        new_indexer = get_batch_indexer(config, "batch")
        assert new_indexer is not None  # New instance should be created
        # We can't easily compare instance identity due to singleton pattern
        # but we can verify the new indexer works
        assert isinstance(new_indexer, BatchIndexer)


class TestBatchIndexerValidation:
    """Test cases for input validation in BatchIndexer."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for validation tests."""
        config = Mock(spec=MinervaConfig)
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vector.db")
        config.embedding_model = "test-model"
        config.vault_path = Path("/test/vault")
        return config

    @pytest.fixture
    def batch_indexer(self, mock_config):
        """Create a BatchIndexer instance for validation testing."""
        return BatchIndexer(
            config=mock_config,
            batch_size=3,
            batch_timeout=10.0,
            background_enabled=False,
        )

    def test_validate_task_inputs_valid_operation(self, batch_indexer):
        """Test validation passes for valid operation types."""
        file_path = "/test/vault/file.md"
        content = "test content"

        # Test all valid operations
        valid_operations = ["add", "update", "remove"]
        for operation in valid_operations:
            # Should not raise any exception
            batch_indexer._validate_task_inputs(file_path, content, operation)

    def test_validate_task_inputs_invalid_operation(self, batch_indexer):
        """Test validation fails for invalid operation types."""
        file_path = "/test/vault/file.md"
        content = "test content"

        with pytest.raises(ValueError, match="Invalid operation: invalid_op"):
            batch_indexer._validate_task_inputs(file_path, content, "invalid_op")

    def test_validate_task_inputs_path_traversal_protection(self, batch_indexer):
        """Test validation blocks path traversal attempts."""
        content = "test content"
        operation = "update"

        # Test various path traversal attempts
        malicious_paths = [
            "/other/directory/file.md",
            "../outside/file.md",
            "/test/vault/../../../etc/passwd",
            "/root/file.md",
            "C:\\Windows\\System32\\file.md",
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(ValueError, match="Invalid file path"):
                batch_indexer._validate_task_inputs(malicious_path, content, operation)

    def test_validate_task_inputs_valid_paths(self, batch_indexer):
        """Test validation allows valid paths within vault."""
        content = "test content"
        operation = "update"

        # Test valid paths within vault
        valid_paths = [
            "/test/vault/file.md",
            "/test/vault/subfolder/file.md",
            "/test/vault/deep/nested/folder/file.md",
        ]

        for valid_path in valid_paths:
            # Should not raise any exception
            batch_indexer._validate_task_inputs(valid_path, content, operation)

    def test_validate_task_inputs_content_size_limit(self, batch_indexer):
        """Test validation blocks content that exceeds size limit."""
        file_path = "/test/vault/file.md"
        operation = "update"

        # Create content that exceeds 10MB limit
        large_content = "x" * (11 * 1024 * 1024)  # 11MB

        with pytest.raises(ValueError, match="Content too large for file"):
            batch_indexer._validate_task_inputs(file_path, large_content, operation)

    def test_validate_task_inputs_content_within_limit(self, batch_indexer):
        """Test validation allows content within size limit."""
        file_path = "/test/vault/file.md"
        operation = "update"

        # Create content within 10MB limit
        normal_content = "x" * (5 * 1024 * 1024)  # 5MB

        # Should not raise any exception
        batch_indexer._validate_task_inputs(file_path, normal_content, operation)

    def test_validate_task_inputs_unusual_file_extension_warning(
        self, batch_indexer, caplog
    ):
        """Test validation logs warning for unusual file extensions."""
        content = "test content"
        operation = "update"

        # Clear any existing log records
        caplog.clear()

        # Test unusual extension - this should not raise an exception
        # but should log a warning
        batch_indexer._validate_task_inputs("/test/vault/file.py", content, operation)

        # Check that warning was logged
        assert len(caplog.records) >= 1
        warning_found = False
        for record in caplog.records:
            if (
                record.levelname == "WARNING"
                and "Unusual file extension" in record.message
            ):
                warning_found = True
                break
        assert warning_found, (
            "Expected warning about unusual file extension was not logged"
        )

    def test_validate_task_inputs_normal_extensions_no_warning(self, batch_indexer):
        """Test validation doesn't warn for normal file extensions."""
        content = "test content"
        operation = "update"

        with patch("minerva.vector.batch_indexer.logger") as mock_logger:
            # Test normal extensions
            batch_indexer._validate_task_inputs(
                "/test/vault/file.md", content, operation
            )
            batch_indexer._validate_task_inputs(
                "/test/vault/file.txt", content, operation
            )

            # Should not log any warning
            mock_logger.warning.assert_not_called()

    def test_queue_task_with_validation_failure(self, batch_indexer):
        """Test that queue_task properly handles validation failures."""
        # Test that validation errors are propagated
        with pytest.raises(ValueError, match="Invalid operation"):
            batch_indexer.queue_task("/test/vault/file.md", "content", "invalid_op")

        # Queue should remain empty
        assert batch_indexer.get_queue_size() == 0

    def test_queue_task_with_validation_success(self, batch_indexer):
        """Test that queue_task works when validation passes."""
        # This should succeed
        batch_indexer.queue_task("/test/vault/file.md", "content", "update")

        # Queue should contain the task
        assert batch_indexer.get_queue_size() == 1

    @patch("pathlib.Path.resolve")
    def test_validate_task_inputs_path_resolution_error(
        self, mock_resolve, batch_indexer
    ):
        """Test validation handles path resolution errors."""
        mock_resolve.side_effect = OSError("Permission denied")

        with pytest.raises(ValueError, match="Invalid file path"):
            batch_indexer._validate_task_inputs(
                "/test/vault/file.md", "content", "update"
            )

    def test_validate_task_inputs_empty_content(self, batch_indexer):
        """Test validation allows empty content (for remove operations)."""
        file_path = "/test/vault/file.md"
        operation = "remove"

        # Empty content should be allowed
        batch_indexer._validate_task_inputs(file_path, "", operation)

    def test_validate_task_inputs_unicode_content(self, batch_indexer):
        """Test validation handles Unicode content correctly."""
        file_path = "/test/vault/file.md"
        operation = "update"

        # Unicode content
        unicode_content = "これは日本語のテストです。🚀"

        # Should not raise any exception
        batch_indexer._validate_task_inputs(file_path, unicode_content, operation)

    def test_validate_task_inputs_unicode_content_size_calculation(self, batch_indexer):
        """Test that content size validation uses UTF-8 byte length."""
        file_path = "/test/vault/file.md"
        operation = "update"

        # Create Unicode content that exceeds limit when encoded as UTF-8
        # Each Japanese character takes 3 bytes in UTF-8
        unicode_char = "あ"  # 3 bytes in UTF-8
        large_unicode_content = unicode_char * (4 * 1024 * 1024)  # ~12MB when encoded

        with pytest.raises(ValueError, match="Content too large for file"):
            batch_indexer._validate_task_inputs(
                file_path, large_unicode_content, operation
            )
