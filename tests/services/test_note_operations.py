"""
Tests for NoteOperations service module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.exceptions import NoteNotFoundError
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.note_operations import NoteOperations


class TestNoteOperations:
    """Test cases for NoteOperations class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        return config

    @pytest.fixture
    def mock_frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def note_operations(self, mock_config, mock_frontmatter_manager):
        """Create a NoteOperations instance for testing."""
        return NoteOperations(mock_config, mock_frontmatter_manager)

    @patch("minerva.services.note_operations.write_file")
    @patch("minerva.services.note_operations.assemble_complete_note")
    def test_create_note_success(
        self, mock_assemble, mock_write, note_operations, mock_config
    ):
        """Test successful note creation."""
        # Arrange
        text = "Test content"
        filename = "test_note"
        author = "Custom Author"
        expected_path = Path("/test/vault/notes/test_note.md")

        mock_assemble.return_value = (
            Path("/test/vault/notes"),
            "test_note.md",
            "---\nauthor: Custom Author\n---\nTest content",
        )
        mock_write.return_value = expected_path

        # Act
        result = note_operations.create_note(text, filename, author)

        # Assert
        assert result == expected_path
        mock_assemble.assert_called_once_with(
            config=mock_config,
            frontmatter_manager=note_operations.frontmatter_manager,
            text=text,
            filename=filename,
            author=author,
            default_path=None,
            is_new_note=True,
        )
        mock_write.assert_called_once()

    @patch("minerva.services.note_operations.write_file")
    @patch("minerva.services.note_operations.assemble_complete_note")
    @patch("pathlib.Path.exists")
    def test_edit_note_success(
        self, mock_exists, mock_assemble, mock_write, note_operations, mock_config
    ):
        """Test successful note editing."""
        # Arrange
        text = "Updated content"
        filename = "existing_note"
        expected_path = Path("/test/vault/notes/existing_note.md")

        mock_exists.return_value = True
        mock_assemble.return_value = (
            Path("/test/vault/notes"),
            "existing_note.md",
            "---\nauthor: Test Author\n---\nUpdated content",
        )
        mock_write.return_value = expected_path

        # Act
        result = note_operations.edit_note(text, filename)

        # Assert
        assert result == expected_path
        mock_assemble.assert_called_once_with(
            config=mock_config,
            frontmatter_manager=note_operations.frontmatter_manager,
            text=text,
            filename=filename,
            author=None,
            default_path=None,
            is_new_note=False,
        )
        mock_write.assert_called_once()

    @patch("minerva.services.note_operations.assemble_complete_note")
    @patch("pathlib.Path.exists")
    def test_edit_note_file_not_found(
        self, mock_exists, mock_assemble, note_operations
    ):
        """Test editing note when file doesn't exist."""
        # Arrange
        text = "Updated content"
        filename = "nonexistent_note"

        mock_exists.return_value = False
        mock_assemble.return_value = (
            Path("/test/vault/notes"),
            "nonexistent_note.md",
            "content",
        )

        # Act & Assert
        with pytest.raises(
            NoteNotFoundError,
            match="File not found: Cannot edit note. File .* does not exist",
        ):
            note_operations.edit_note(text, filename)

    @patch("minerva.services.note_operations.read_file")
    def test_read_note_success(self, mock_read, note_operations):
        """Test successful note reading."""
        # Arrange
        filepath = "/test/vault/notes/test_note.md"
        expected_content = "Test file content"
        mock_read.return_value = expected_content

        # Act
        result = note_operations.read_note(filepath)

        # Assert
        assert result == expected_content
        mock_read.assert_called_once()

    @patch("minerva.services.note_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_note_delete_confirmation_success(
        self, mock_exists, mock_resolve, note_operations
    ):
        """Test successful delete confirmation."""
        # Arrange
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = True

        # Act
        result = note_operations.get_note_delete_confirmation(filename=filename)

        # Assert
        assert result["file_path"] == str(file_path)
        assert "To delete, call 'perform_note_delete'" in result["message"]

    @patch("minerva.services.note_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_note_delete_confirmation_file_not_found(
        self, mock_exists, mock_resolve, note_operations
    ):
        """Test delete confirmation when file doesn't exist."""
        # Arrange
        filename = "nonexistent_note"
        file_path = Path("/test/vault/notes/nonexistent_note.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = False

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File .* does not exist"):
            note_operations.get_note_delete_confirmation(filename=filename)

    def test_get_note_delete_confirmation_no_params(self, note_operations):
        """Test delete confirmation with no filename or filepath."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            note_operations.get_note_delete_confirmation()

    @patch("minerva.services.note_operations.delete_file")
    @patch("minerva.services.note_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_perform_note_delete_success(
        self, mock_exists, mock_resolve, mock_delete, note_operations
    ):
        """Test successful note deletion."""
        # Arrange
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = True
        mock_delete.return_value = file_path

        # Act
        result = note_operations.perform_note_delete(filename=filename)

        # Assert
        assert result == file_path
        mock_delete.assert_called_once()

    @patch("minerva.services.note_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_perform_note_delete_file_not_found(
        self, mock_exists, mock_resolve, note_operations
    ):
        """Test note deletion when file doesn't exist."""
        # Arrange
        filename = "nonexistent_note"
        file_path = Path("/test/vault/notes/nonexistent_note.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = False

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File .* does not exist"):
            note_operations.perform_note_delete(filename=filename)

    def test_perform_note_delete_no_params(self, note_operations):
        """Test note deletion with no filename or filepath."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            note_operations.perform_note_delete()

    @patch("minerva.services.note_operations.resolve_note_file")
    def test_get_note_delete_confirmation_resolve_error(
        self, mock_resolve, note_operations
    ):
        """Test delete confirmation when resolve_note_file raises ValueError."""
        # Arrange
        mock_resolve.side_effect = ValueError("Invalid parameters")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid parameters"):
            note_operations.get_note_delete_confirmation(filename="test")

    @patch("minerva.services.note_operations.resolve_note_file")
    def test_perform_note_delete_resolve_error(self, mock_resolve, note_operations):
        """Test note deletion when resolve_note_file raises ValueError."""
        # Arrange
        mock_resolve.side_effect = ValueError("Invalid parameters")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid parameters"):
            note_operations.perform_note_delete(filename="test")

    def test_note_operations_inherits_from_base_service(self, note_operations):
        """Test that NoteOperations properly inherits from BaseService."""
        # Assert
        assert hasattr(note_operations, "config")
        assert hasattr(note_operations, "frontmatter_manager")
        assert hasattr(note_operations, "error_handler")
        assert hasattr(note_operations, "_log_operation_start")
        assert hasattr(note_operations, "_log_operation_success")
        assert hasattr(note_operations, "_log_operation_error")

    @patch("minerva.services.note_operations.write_file")
    @patch("minerva.services.note_operations.assemble_complete_note")
    def test_create_note_with_default_path(
        self, mock_assemble, mock_write, note_operations, mock_config
    ):
        """Test note creation with custom default path."""
        # Arrange
        text = "Test content"
        filename = "test_note"
        default_path = "custom/path"
        expected_path = Path("/test/vault/custom/path/test_note.md")

        mock_assemble.return_value = (
            Path("/test/vault/custom/path"),
            "test_note.md",
            "content",
        )
        mock_write.return_value = expected_path

        # Act
        result = note_operations.create_note(text, filename, default_path=default_path)

        # Assert
        assert result == expected_path
        mock_assemble.assert_called_once_with(
            config=mock_config,
            frontmatter_manager=note_operations.frontmatter_manager,
            text=text,
            filename=filename,
            author=None,
            default_path=default_path,
            is_new_note=True,
        )

    @patch("minerva.services.note_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_note_delete_confirmation_with_filepath(
        self, mock_exists, mock_resolve, note_operations
    ):
        """Test delete confirmation using filepath parameter."""
        # Arrange
        filepath = "/test/vault/notes/test_note.md"
        file_path = Path(filepath)

        mock_resolve.return_value = file_path
        mock_exists.return_value = True

        # Act
        result = note_operations.get_note_delete_confirmation(filepath=filepath)

        # Assert
        assert result["file_path"] == filepath
        mock_resolve.assert_called_once_with(
            note_operations.config, None, filepath, None
        )
