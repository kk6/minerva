"""
Tests for batch indexing functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

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
        file_path = "/test/file.md"
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
            batch_indexer.queue_task(f"/test/file{i}.md", f"content {i}", "update")

        # Assert
        assert batch_indexer.get_queue_size() == 2
        stats = batch_indexer.get_stats()
        assert stats["tasks_queued"] == 2

    def test_queue_task_when_stopped(self, batch_indexer):
        """Test queuing task when indexer is stopped."""
        # Arrange
        batch_indexer.stop()

        # Act
        batch_indexer.queue_task("/test/file.md", "content", "update")

        # Assert
        assert batch_indexer.get_queue_size() == 0
        stats = batch_indexer.get_stats()
        assert stats["tasks_queued"] == 0

    @patch("minerva.vector.batch_indexer.SentenceTransformerProvider")
    @patch("minerva.vector.batch_indexer.VectorIndexer")
    def test_process_batch_success(
        self, mock_indexer_class, mock_provider_class, batch_indexer
    ):
        """Test successful batch processing."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        mock_provider = Mock()
        mock_embedding = Mock()
        mock_embedding.ndim = 1
        mock_provider.embed.return_value = mock_embedding
        mock_provider_class.return_value = mock_provider

        # Queue some tasks
        batch_indexer.queue_task("/test/file1.md", "content1", "update")
        batch_indexer.queue_task("/test/file2.md", "content2", "add")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 2
        assert batch_indexer.get_queue_size() == 0
        stats = batch_indexer.get_stats()
        assert stats["tasks_processed"] == 2
        assert stats["batches_processed"] == 1

    def test_process_batch_with_vector_search_disabled(self, batch_indexer):
        """Test batch processing when vector search is disabled."""
        # Arrange
        batch_indexer.config.vector_search_enabled = False
        batch_indexer.queue_task("/test/file.md", "content", "update")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 0
        assert batch_indexer.get_queue_size() == 1  # Task remains in queue

    def test_process_batch_empty_queue(self, batch_indexer):
        """Test processing when queue is empty."""
        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 0
        stats = batch_indexer.get_stats()
        assert stats["batches_processed"] == 1

    @patch("minerva.vector.batch_indexer.SentenceTransformerProvider")
    @patch("minerva.vector.batch_indexer.VectorIndexer")
    def test_process_batch_with_remove_operation(
        self, mock_indexer_class, mock_provider_class, batch_indexer
    ):
        """Test batch processing with remove operation."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        mock_provider = Mock()
        mock_embedding = Mock()
        mock_embedding.ndim = 1
        mock_provider.embed.return_value = mock_embedding
        mock_provider_class.return_value = mock_provider

        # Queue a remove task
        batch_indexer.queue_task("/test/file.md", "", "remove")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 1
        mock_indexer.remove_file.assert_called_once_with("/test/file.md")

    @patch("minerva.vector.batch_indexer.SentenceTransformerProvider")
    @patch("minerva.vector.batch_indexer.VectorIndexer")
    def test_process_batch_with_error(
        self, mock_indexer_class, mock_provider_class, batch_indexer
    ):
        """Test batch processing with errors."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer.store_embedding.side_effect = Exception("Test error")
        mock_indexer_class.return_value = mock_indexer

        mock_provider = Mock()
        mock_embedding = Mock()
        mock_embedding.ndim = 1
        mock_provider.embed.return_value = mock_embedding
        mock_provider_class.return_value = mock_provider

        # Queue a task
        batch_indexer.queue_task("/test/file.md", "content", "update")

        # Act
        processed = batch_indexer.process_batch()

        # Assert
        assert processed == 0  # No tasks processed due to error
        stats = batch_indexer.get_stats()
        assert stats["errors"] == 1

    def test_process_all_pending(self, batch_indexer):
        """Test processing all pending tasks."""
        # Arrange
        with patch.object(
            batch_indexer, "process_batch", return_value=2
        ) as mock_process:
            batch_indexer.queue_task("/test/file1.md", "content1", "update")
            batch_indexer.queue_task("/test/file2.md", "content2", "update")

            # Act
            total_processed = batch_indexer.process_all_pending()

            # Assert
            assert total_processed == 2
            mock_process.assert_called()

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
        mock_thread.is_alive.return_value = False
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

        # Act
        indexer = get_batch_indexer(config, "background")

        # Assert
        assert indexer is not None
        assert isinstance(indexer, BatchIndexer)
        assert indexer.background_enabled is True

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

        indexer = get_batch_indexer(config, "batch")
        assert indexer is not None

        # Act
        stop_batch_indexer()

        # Assert
        # The global instance should be None after stopping
        new_indexer = get_batch_indexer(config, "batch")
        assert new_indexer != indexer  # Should be a new instance
