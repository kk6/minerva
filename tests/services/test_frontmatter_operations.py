"""
Test module for FrontmatterOperations service.

This module contains comprehensive tests for the generic frontmatter
operations service that forms the foundation for tag and alias operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from minerva.services.frontmatter_operations import FrontmatterOperations
from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.exceptions import NoteNotFoundError


@pytest.fixture
def config():
    """Create a test configuration."""
    return MinervaConfig(
        vault_path=Path("/test/vault"),
        default_note_dir="notes",
        default_author="Test Author",
    )


@pytest.fixture
def frontmatter_manager():
    """Create a test frontmatter manager."""
    return FrontmatterManager("Test Author")


@pytest.fixture
def frontmatter_operations(config, frontmatter_manager):
    """Create a FrontmatterOperations instance for testing."""
    return FrontmatterOperations(config, frontmatter_manager)


class TestFrontmatterOperations:
    """Test class for FrontmatterOperations service."""

    def test_get_field_success(self, frontmatter_operations):
        """Test successfully getting a field value."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter = {"status": "in-progress", "priority": "high"}

        with (
            patch.object(
                frontmatter_operations,
                "_load_note_with_frontmatter",
                return_value=(mock_post, mock_frontmatter),
            ),
            patch.object(
                frontmatter_operations, "_resolve_file_path", return_value=file_path
            ),
        ):
            # Act
            result = frontmatter_operations.get_field("status", filename="test.md")

        # Assert
        assert result == "in-progress"

    def test_get_field_not_found(self, frontmatter_operations):
        """Test getting a field that doesn't exist."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter = {"other_field": "value"}

        with (
            patch.object(
                frontmatter_operations,
                "_load_note_with_frontmatter",
                return_value=(mock_post, mock_frontmatter),
            ),
            patch.object(
                frontmatter_operations, "_resolve_file_path", return_value=file_path
            ),
        ):
            # Act
            result = frontmatter_operations.get_field("status", filename="test.md")

        # Assert
        assert result is None

    def test_set_field_success(self, frontmatter_operations):
        """Test successfully setting a field value."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter = {"existing_field": "value"}

        with (
            patch.object(
                frontmatter_operations,
                "_load_note_with_frontmatter",
                return_value=(mock_post, mock_frontmatter),
            ),
            patch.object(
                frontmatter_operations, "_resolve_file_path", return_value=file_path
            ),
            patch.object(
                frontmatter_operations,
                "_save_note_with_updated_frontmatter",
                return_value=file_path,
            ) as mock_save,
        ):
            # Act
            result = frontmatter_operations.set_field(
                "status", "completed", filename="test.md"
            )

        # Assert
        assert result == file_path
        # Verify save was called with updated frontmatter
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        updated_frontmatter = call_args[2]  # Third argument is frontmatter dict
        assert updated_frontmatter["status"] == "completed"
        assert updated_frontmatter["existing_field"] == "value"

    def test_remove_field_success(self, frontmatter_operations):
        """Test successfully removing a field."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter = {"status": "in-progress", "priority": "high"}

        with (
            patch.object(
                frontmatter_operations,
                "_load_note_with_frontmatter",
                return_value=(mock_post, mock_frontmatter),
            ),
            patch.object(
                frontmatter_operations, "_resolve_file_path", return_value=file_path
            ),
            patch.object(
                frontmatter_operations,
                "_save_note_with_updated_frontmatter",
                return_value=file_path,
            ) as mock_save,
        ):
            # Act
            result = frontmatter_operations.remove_field("status", filename="test.md")

        # Assert
        assert result == file_path
        # Verify save was called with field removed
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        updated_frontmatter = call_args[2]  # Third argument is frontmatter dict
        assert "status" not in updated_frontmatter
        assert updated_frontmatter["priority"] == "high"

    def test_get_all_fields_success(self, frontmatter_operations):
        """Test successfully getting all frontmatter fields."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter = {
            "status": "in-progress",
            "priority": "high",
            "tags": ["project", "urgent"],
            "author": "Test Author",
        }

        with (
            patch.object(
                frontmatter_operations,
                "_load_note_with_frontmatter",
                return_value=(mock_post, mock_frontmatter),
            ),
            patch.object(
                frontmatter_operations, "_resolve_file_path", return_value=file_path
            ),
        ):
            # Act
            result = frontmatter_operations.get_all_fields(filename="test.md")

        # Assert
        assert result == mock_frontmatter

    def test_update_field_with_function(self, frontmatter_operations):
        """Test updating a field using an update function."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter = {"counter": 5}

        def increment(value):
            return (value or 0) + 1

        with (
            patch.object(
                frontmatter_operations,
                "_load_note_with_frontmatter",
                return_value=(mock_post, mock_frontmatter),
            ),
            patch.object(
                frontmatter_operations, "_resolve_file_path", return_value=file_path
            ),
            patch.object(
                frontmatter_operations,
                "_save_note_with_updated_frontmatter",
                return_value=file_path,
            ) as mock_save,
        ):
            # Act
            result = frontmatter_operations.update_field(
                "counter", increment, filename="test.md"
            )

        # Assert
        assert result == file_path
        # Verify save was called with updated value
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        updated_frontmatter = call_args[2]  # Third argument is frontmatter dict
        assert updated_frontmatter["counter"] == 6

    def test_resolve_file_path_with_filename(self, frontmatter_operations):
        """Test resolving file path with filename."""
        with (
            patch(
                "minerva.services.frontmatter_operations.resolve_note_file"
            ) as mock_resolve,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_path = Path("/test/vault/notes/test.md")
            mock_resolve.return_value = mock_path

            # Act
            result = frontmatter_operations._resolve_file_path(filename="test.md")

            # Assert
            assert result == mock_path
            mock_resolve.assert_called_once_with(
                frontmatter_operations.config, "test.md", None, None
            )

    def test_resolve_file_path_file_not_found(self, frontmatter_operations):
        """Test resolving file path when file doesn't exist."""
        with (
            patch(
                "minerva.services.frontmatter_operations.resolve_note_file"
            ) as mock_resolve,
            patch("pathlib.Path.exists", return_value=False),
        ):
            mock_path = Path("/test/vault/notes/nonexistent.md")
            mock_resolve.return_value = mock_path

            # Act & Assert
            with pytest.raises(NoteNotFoundError):
                frontmatter_operations._resolve_file_path(filename="nonexistent.md")

    def test_resolve_file_path_no_filename_or_filepath(self, frontmatter_operations):
        """Test resolving file path when neither filename nor filepath provided."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            frontmatter_operations._resolve_file_path()
