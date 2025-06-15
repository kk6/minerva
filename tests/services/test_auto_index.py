"""
Tests for automatic vector index updates in NoteOperations.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.note_operations import NoteOperations


class TestAutoIndexUpdates:
    """Test cases for automatic vector index updates."""

    @pytest.fixture
    def mock_config_auto_enabled(self):
        """Create mock config with auto-indexing enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        config.vector_search_enabled = True
        config.auto_index_enabled = True
        config.auto_index_strategy = "immediate"
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def mock_config_auto_disabled(self):
        """Create mock config with auto-indexing disabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        config.vector_search_enabled = True
        config.auto_index_enabled = False
        config.auto_index_strategy = "immediate"
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def mock_frontmatter_manager(self):
        """Create mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def note_ops_auto_enabled(self, mock_config_auto_enabled, mock_frontmatter_manager):
        """Create NoteOperations with auto-indexing enabled."""
        return NoteOperations(mock_config_auto_enabled, mock_frontmatter_manager)

    @pytest.fixture
    def note_ops_auto_disabled(
        self, mock_config_auto_disabled, mock_frontmatter_manager
    ):
        """Create NoteOperations with auto-indexing disabled."""
        return NoteOperations(mock_config_auto_disabled, mock_frontmatter_manager)

    def test_should_auto_update_index_enabled(self, note_ops_auto_enabled):
        """Test that auto-update check returns True when enabled."""
        assert note_ops_auto_enabled._should_auto_update_index() is True

    def test_should_auto_update_index_disabled(self, note_ops_auto_disabled):
        """Test that auto-update check returns False when disabled."""
        assert note_ops_auto_disabled._should_auto_update_index() is False

    def test_should_auto_update_index_vector_search_disabled(
        self, mock_config_auto_enabled, mock_frontmatter_manager
    ):
        """Test that auto-update check returns False when vector search is disabled."""
        mock_config_auto_enabled.vector_search_enabled = False
        note_ops = NoteOperations(mock_config_auto_enabled, mock_frontmatter_manager)
        assert note_ops._should_auto_update_index() is False

    def test_should_auto_update_index_no_db_path(
        self, mock_config_auto_enabled, mock_frontmatter_manager
    ):
        """Test that auto-update check returns False when no DB path is configured."""
        mock_config_auto_enabled.vector_db_path = None
        note_ops = NoteOperations(mock_config_auto_enabled, mock_frontmatter_manager)
        assert note_ops._should_auto_update_index() is False

    @pytest.mark.vector
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_update_vector_index_if_enabled_success(
        self, mock_indexer_class, mock_embedding_class, note_ops_auto_enabled
    ):
        """Test successful vector index update."""
        # Arrange
        import numpy as np

        mock_embedding_provider = Mock()
        # Create actual numpy arrays for proper testing
        actual_embedding = np.array([0.2] * 384)
        mock_embedding_provider.embed.return_value = actual_embedding
        mock_embedding_provider.embedding_dim = 384  # Mock the property
        mock_embedding_class.return_value = mock_embedding_provider

        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        file_path = Path("/test/vault/note.md")
        content = "Test note content"

        # Act
        note_ops_auto_enabled._update_vector_index_if_enabled(file_path, content)

        # Assert
        mock_embedding_class.assert_called_once_with("all-MiniLM-L6-v2")
        mock_indexer_class.assert_called_once_with(Path("/test/vectors.db"))
        assert mock_embedding_provider.embed.call_count == 1
        mock_indexer.initialize_schema.assert_called_once_with(384)
        mock_indexer.store_embedding.assert_called_once()
        mock_indexer.close.assert_called_once()

    def test_update_vector_index_if_enabled_disabled(self, note_ops_auto_disabled):
        """Test that vector index update is skipped when disabled."""
        file_path = Path("/test/vault/note.md")
        content = "Test note content"

        with patch(
            "minerva.vector.embeddings.SentenceTransformerProvider"
        ) as mock_embedding:
            note_ops_auto_disabled._update_vector_index_if_enabled(file_path, content)
            mock_embedding.assert_not_called()

    @patch("minerva.services.note_operations.logger")
    def test_update_vector_index_if_enabled_import_error(
        self, mock_logger, note_ops_auto_enabled
    ):
        """Test that ImportError is handled gracefully."""
        file_path = Path("/test/vault/note.md")
        content = "Test note content"

        with patch(
            "minerva.vector.embeddings.SentenceTransformerProvider",
            side_effect=ImportError("No module named 'sentence_transformers'"),
        ):
            note_ops_auto_enabled._update_vector_index_if_enabled(file_path, content)
            mock_logger.debug.assert_called_with(
                "Vector search dependencies not available, skipping auto-index update"
            )

    @patch("minerva.services.note_operations.logger")
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    def test_update_vector_index_if_enabled_other_error(
        self, mock_embedding_class, mock_logger, note_ops_auto_enabled
    ):
        """Test that other exceptions are handled gracefully."""
        mock_embedding_class.side_effect = Exception("Database error")

        file_path = Path("/test/vault/note.md")
        content = "Test note content"

        note_ops_auto_enabled._update_vector_index_if_enabled(file_path, content)

        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args[0]
        assert "Failed to update vector index" in args[0]

    @patch("minerva.vector.indexer.VectorIndexer")
    def test_remove_from_vector_index_if_enabled_success(
        self, mock_indexer_class, note_ops_auto_enabled
    ):
        """Test successful vector index removal."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer.is_file_indexed.return_value = True
        mock_indexer_class.return_value = mock_indexer

        file_path = Path("/test/vault/note.md")

        # Act
        note_ops_auto_enabled._remove_from_vector_index_if_enabled(file_path)

        # Assert
        mock_indexer_class.assert_called_once_with(Path("/test/vectors.db"))
        mock_indexer.is_file_indexed.assert_called_once_with(str(file_path))
        mock_indexer.remove_file.assert_called_once_with(str(file_path))
        mock_indexer.close.assert_called_once()

    @patch("minerva.vector.indexer.VectorIndexer")
    def test_remove_from_vector_index_if_enabled_not_indexed(
        self, mock_indexer_class, note_ops_auto_enabled
    ):
        """Test removal when file is not indexed."""
        # Arrange
        mock_indexer = Mock()
        mock_indexer.is_file_indexed.return_value = False
        mock_indexer_class.return_value = mock_indexer

        file_path = Path("/test/vault/note.md")

        # Act
        note_ops_auto_enabled._remove_from_vector_index_if_enabled(file_path)

        # Assert
        mock_indexer.is_file_indexed.assert_called_once_with(str(file_path))
        mock_indexer.remove_file.assert_not_called()
        mock_indexer.close.assert_called_once()

    def test_remove_from_vector_index_if_enabled_disabled(self, note_ops_auto_disabled):
        """Test that vector index removal is skipped when disabled."""
        file_path = Path("/test/vault/note.md")

        with patch("minerva.vector.indexer.VectorIndexer") as mock_indexer:
            note_ops_auto_disabled._remove_from_vector_index_if_enabled(file_path)
            mock_indexer.assert_not_called()

    @patch("minerva.services.note_operations.logger")
    def test_remove_from_vector_index_if_enabled_import_error(
        self, mock_logger, note_ops_auto_enabled
    ):
        """Test that ImportError is handled gracefully during removal."""
        file_path = Path("/test/vault/note.md")

        with patch(
            "minerva.vector.indexer.VectorIndexer",
            side_effect=ImportError("No module named 'duckdb'"),
        ):
            note_ops_auto_enabled._remove_from_vector_index_if_enabled(file_path)
            mock_logger.debug.assert_called_with(
                "Vector search dependencies not available, skipping auto-index removal"
            )


class TestAutoIndexIntegration:
    """Integration tests for automatic indexing with note operations."""

    @pytest.fixture
    def mock_config_with_auto_index(self):
        """Create mock config with auto-indexing enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        config.vector_search_enabled = True
        config.auto_index_enabled = True
        config.auto_index_strategy = "immediate"
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def note_operations(self, mock_config_with_auto_index):
        """Create NoteOperations instance for integration testing."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return NoteOperations(mock_config_with_auto_index, frontmatter_manager)

    @patch("minerva.services.note_operations.assemble_complete_note")
    @patch("minerva.services.note_operations.write_file")
    @patch.object(NoteOperations, "_update_vector_index_if_enabled")
    def test_create_note_calls_auto_index(
        self, mock_auto_index, mock_write_file, mock_assemble, note_operations
    ):
        """Test that create_note calls auto-index update."""
        # Arrange
        file_path = Path("/test/vault/note.md")
        content = "Test content with frontmatter"

        mock_assemble.return_value = (Path("/test/vault"), "note.md", content)
        mock_write_file.return_value = file_path

        # Act
        result = note_operations.create_note("Test content", "note.md")

        # Assert
        assert result == file_path
        mock_auto_index.assert_called_once_with(file_path, content)

    @patch("minerva.services.note_operations.assemble_complete_note")
    @patch("minerva.services.note_operations.write_file")
    @patch.object(NoteOperations, "_update_vector_index_if_enabled")
    def test_edit_note_calls_auto_index(
        self, mock_auto_index, mock_write_file, mock_assemble, note_operations
    ):
        """Test that edit_note calls auto-index update."""
        # Arrange
        file_path = Path("/test/vault/note.md")
        content = "Updated content with frontmatter"

        mock_assemble.return_value = (Path("/test/vault"), "note.md", content)
        mock_write_file.return_value = file_path

        # Mock file existence check
        with patch.object(Path, "exists", return_value=True):
            # Act
            result = note_operations.edit_note("Updated content", "note.md")

            # Assert
            assert result == file_path
            mock_auto_index.assert_called_once_with(file_path, content)

    @patch("minerva.services.note_operations.delete_file")
    @patch.object(NoteOperations, "_remove_from_vector_index_if_enabled")
    @patch.object(NoteOperations, "_validate_and_resolve_file")
    def test_perform_note_delete_calls_auto_index_removal(
        self, mock_validate, mock_auto_remove, mock_delete_file, note_operations
    ):
        """Test that perform_note_delete calls auto-index removal."""
        # Arrange
        file_path = Path("/test/vault/note.md")
        mock_validate.return_value = file_path
        mock_delete_file.return_value = file_path

        # Act
        result = note_operations.perform_note_delete(filename="note.md")

        # Assert
        assert result == file_path
        mock_auto_remove.assert_called_once_with(file_path)
