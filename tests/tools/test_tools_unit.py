"""
Unit tests for tools module functions.

These tests focus on verifying that tool functions correctly delegate to service methods
with the right parameters, using mocked service instances.
"""

from unittest.mock import Mock, MagicMock
from pathlib import Path

from minerva.service import MinervaService
from minerva.tools import (
    create_note,
    edit_note,
    read_note,
    search_notes,
    add_tag,
    remove_tag,
    rename_tag,
    get_tags,
    list_all_tags,
    find_notes_with_tag,
    get_note_delete_confirmation,
    perform_note_delete,
)


class TestCreateNote:
    """Unit tests for create_note function."""

    def test_create_note_delegates_to_service(self):
        """Test that create_note properly delegates to service.create_note."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/test/path.md")
        mock_service.create_note.return_value = expected_path

        # Act
        result = create_note(mock_service, "content", "filename", "author", "path")

        # Assert
        mock_service.create_note.assert_called_once_with(
            "content", "filename", "author", "path"
        )
        assert result == expected_path

    def test_create_note_with_defaults(self):
        """Test create_note with default parameters."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/test/path.md")
        mock_service.create_note.return_value = expected_path

        # Act
        result = create_note(mock_service, "content", "filename")

        # Assert
        mock_service.create_note.assert_called_once_with(
            "content", "filename", None, None
        )
        assert result == expected_path


class TestEditNote:
    """Unit tests for edit_note function."""

    def test_edit_note_delegates_to_service(self):
        """Test that edit_note properly delegates to service.edit_note."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/test/path.md")
        mock_service.edit_note.return_value = expected_path

        # Act
        result = edit_note(mock_service, "new content", "filename", "author", "path")

        # Assert
        mock_service.edit_note.assert_called_once_with(
            "new content", "filename", "author", "path"
        )
        assert result == expected_path


class TestReadNote:
    """Unit tests for read_note function."""

    def test_read_note_delegates_to_service(self):
        """Test that read_note properly delegates to service.read_note."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_content = "file content"
        mock_service.read_note.return_value = expected_content

        # Act
        result = read_note(mock_service, "/path/to/file.md")

        # Assert
        mock_service.read_note.assert_called_once_with("/path/to/file.md")
        assert result == expected_content


class TestSearchNotes:
    """Unit tests for search_notes function."""

    def test_search_notes_delegates_to_service(self):
        """Test that search_notes properly delegates to service.search_notes."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_results = [MagicMock(), MagicMock()]
        mock_service.search_notes.return_value = expected_results

        # Act
        result = search_notes(mock_service, "query", case_sensitive=False)

        # Assert
        mock_service.search_notes.assert_called_once_with("query", False)
        assert result == expected_results

    def test_search_notes_with_default_case_sensitive(self):
        """Test search_notes with default case_sensitive parameter."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_results = []
        mock_service.search_notes.return_value = expected_results

        # Act
        result = search_notes(mock_service, "query")

        # Assert
        mock_service.search_notes.assert_called_once_with("query", True)
        assert result == expected_results


class TestTagOperations:
    """Unit tests for tag operation functions."""

    def test_add_tag_delegates_to_service(self):
        """Test that add_tag properly delegates to service.add_tag."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/test/path.md")
        mock_service.add_tag.return_value = expected_path

        # Act
        result = add_tag(mock_service, "test-tag", "filename", "/path", "default")

        # Assert
        mock_service.add_tag.assert_called_once_with(
            "test-tag", "filename", "/path", "default"
        )
        assert result == expected_path

    def test_remove_tag_delegates_to_service(self):
        """Test that remove_tag properly delegates to service.remove_tag."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/test/path.md")
        mock_service.remove_tag.return_value = expected_path

        # Act
        result = remove_tag(mock_service, "test-tag", filename="filename")

        # Assert
        mock_service.remove_tag.assert_called_once_with(
            "test-tag", "filename", None, None
        )
        assert result == expected_path

    def test_rename_tag_delegates_to_service(self):
        """Test that rename_tag properly delegates to service.rename_tag."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_paths = [Path("/test/path1.md"), Path("/test/path2.md")]
        mock_service.rename_tag.return_value = expected_paths

        # Act
        result = rename_tag(mock_service, "old-tag", "new-tag", "/directory")

        # Assert
        mock_service.rename_tag.assert_called_once_with(
            "old-tag", "new-tag", "/directory"
        )
        assert result == expected_paths

    def test_get_tags_delegates_to_service(self):
        """Test that get_tags properly delegates to service.get_tags."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_tags = ["tag1", "tag2", "tag3"]
        mock_service.get_tags.return_value = expected_tags

        # Act
        result = get_tags(mock_service, filename="filename")

        # Assert
        mock_service.get_tags.assert_called_once_with("filename", None, None)
        assert result == expected_tags

    def test_list_all_tags_delegates_to_service(self):
        """Test that list_all_tags properly delegates to service.list_all_tags."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_tags = ["tag1", "tag2", "tag3"]
        mock_service.list_all_tags.return_value = expected_tags

        # Act
        result = list_all_tags(mock_service, "/directory")

        # Assert
        mock_service.list_all_tags.assert_called_once_with("/directory")
        assert result == expected_tags

    def test_find_notes_with_tag_delegates_to_service(self):
        """Test that find_notes_with_tag properly delegates to service.find_notes_with_tag."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_paths = ["/path1.md", "/path2.md"]
        mock_service.find_notes_with_tag.return_value = expected_paths

        # Act
        result = find_notes_with_tag(mock_service, "test-tag", "/directory")

        # Assert
        mock_service.find_notes_with_tag.assert_called_once_with(
            "test-tag", "/directory"
        )
        assert result == expected_paths


class TestDeleteOperations:
    """Unit tests for delete operation functions."""

    def test_get_note_delete_confirmation_delegates_to_service(self):
        """Test that get_note_delete_confirmation properly delegates to service."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_result = {"file_path": "/path.md", "message": "Confirm delete"}
        mock_service.get_note_delete_confirmation.return_value = expected_result

        # Act
        result = get_note_delete_confirmation(
            mock_service, "filename", "/path.md", "default"
        )

        # Assert
        mock_service.get_note_delete_confirmation.assert_called_once_with(
            "filename", "/path.md", "default"
        )
        assert result == expected_result

    def test_perform_note_delete_delegates_to_service(self):
        """Test that perform_note_delete properly delegates to service."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/deleted/path.md")
        mock_service.perform_note_delete.return_value = expected_path

        # Act
        result = perform_note_delete(mock_service, filepath="/path.md")

        # Assert
        mock_service.perform_note_delete.assert_called_once_with(None, "/path.md", None)
        assert result == expected_path


class TestParameterHandling:
    """Test proper parameter handling in tool functions."""

    def test_functions_handle_none_parameters_correctly(self):
        """Test that functions handle None parameters correctly."""
        mock_service = Mock(spec=MinervaService)

        # Test various functions with None parameters
        create_note(mock_service, "content", "file")
        mock_service.create_note.assert_called_with("content", "file", None, None)

        edit_note(mock_service, "content", "file")
        mock_service.edit_note.assert_called_with("content", "file", None, None)

        add_tag(mock_service, "tag")
        mock_service.add_tag.assert_called_with("tag", None, None, None)

        get_tags(mock_service)
        mock_service.get_tags.assert_called_with(None, None, None)

    def test_functions_preserve_parameter_order(self):
        """Test that functions preserve correct parameter order."""
        mock_service = Mock(spec=MinervaService)

        # Test parameter order is preserved
        create_note(mock_service, "text", "filename", "author", "default_path")
        mock_service.create_note.assert_called_with(
            "text", "filename", "author", "default_path"
        )

        add_tag(mock_service, "tag", "filename", "filepath", "default_path")
        mock_service.add_tag.assert_called_with(
            "tag", "filename", "filepath", "default_path"
        )
