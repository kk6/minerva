"""
Integration tests for service-based tools API.

These tests verify that the tools module correctly integrates with the service layer
and provides the expected functionality through the new service-based architecture.
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from minerva.service import create_minerva_service, MinervaService
from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.tools import (
    create_note,
    edit_note,
    read_note,
    search_notes,
    add_tag,
    remove_tag,
    get_tags,
    get_note_delete_confirmation,
    perform_note_delete,
)


class TestToolsServiceIntegration:
    """Test tools integration with service layer."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()
            yield vault_dir

    @pytest.fixture
    def test_service(self, temp_vault):
        """Create a test service instance."""
        config = MinervaConfig(
            vault_path=temp_vault,
            default_note_dir="test_notes",
            default_author="Test Author",
        )
        frontmatter_manager = FrontmatterManager("Test Author")
        return MinervaService(config, frontmatter_manager)

    def test_create_and_read_note_integration(self, test_service):
        """Test creating and reading a note through the tools API."""
        # Arrange
        content = "This is a test note"
        filename = "test_note"

        # Act - Create note
        note_path = create_note(test_service, content, filename)

        # Assert - Note was created
        assert note_path.exists()
        assert note_path.name == "test_note.md"

        # Act - Read note
        read_content = read_note(test_service, str(note_path))

        # Assert - Content is correct (after frontmatter parsing)
        import frontmatter

        post = frontmatter.loads(read_content)
        assert post.content == content
        assert post.metadata["author"] == "Test Author"

    def test_edit_note_integration(self, test_service):
        """Test editing an existing note through the tools API."""
        # Arrange - Create initial note
        initial_content = "Initial content"
        filename = "edit_test"
        note_path = create_note(test_service, initial_content, filename)

        # Act - Edit note
        new_content = "Updated content"
        edited_path = edit_note(test_service, new_content, filename)

        # Assert - Note was edited
        assert edited_path == note_path
        read_content = read_note(test_service, str(note_path))

        import frontmatter

        post = frontmatter.loads(read_content)
        assert post.content == new_content

    def test_tag_operations_integration(self, test_service):
        """Test tag operations through the tools API."""
        # Arrange - Create note
        content = "Note with tags"
        filename = "tagged_note"
        create_note(test_service, content, filename)

        # Act & Assert - Add tag
        add_tag(test_service, "test-tag", filename=filename)
        tags = get_tags(test_service, filename=filename)
        assert "test-tag" in tags

        # Act & Assert - Add another tag
        add_tag(test_service, "another-tag", filename=filename)
        tags = get_tags(test_service, filename=filename)
        assert "test-tag" in tags
        assert "another-tag" in tags

        # Act & Assert - Remove tag
        remove_tag(test_service, "test-tag", filename=filename)
        tags = get_tags(test_service, filename=filename)
        assert "test-tag" not in tags
        assert "another-tag" in tags

    def test_delete_operations_integration(self, test_service):
        """Test delete operations through the tools API."""
        # Arrange - Create note
        content = "Note to delete"
        filename = "delete_test"
        note_path = create_note(test_service, content, filename)
        assert note_path.exists()

        # Act - Get delete confirmation
        confirmation = get_note_delete_confirmation(test_service, filename=filename)

        # Assert - Confirmation contains expected info
        assert "file_path" in confirmation
        assert "message" in confirmation
        assert str(note_path) == confirmation["file_path"]

        # Act - Perform deletion
        deleted_path = perform_note_delete(test_service, filename=filename)

        # Assert - Note was deleted
        assert deleted_path == note_path
        assert not note_path.exists()

    def test_search_notes_integration(self, test_service):
        """Test search functionality through the tools API."""
        # Arrange - Create test notes
        create_note(test_service, "This contains apple", "note1")
        create_note(test_service, "This contains banana", "note2")
        create_note(test_service, "This contains APPLE", "note3")

        # Act - Search for keyword
        results = search_notes(test_service, "apple", case_sensitive=False)

        # Assert - Found matching notes
        assert len(results) >= 2  # Should find both "apple" and "APPLE"

        # Check that results contain expected information
        for result in results:
            assert hasattr(result, "file_path")
            assert hasattr(result, "line_number")
            assert hasattr(result, "context")

    def test_error_handling_integration(self, test_service):
        """Test error handling through the tools API."""
        # Test reading non-existent file
        with pytest.raises(FileNotFoundError):
            read_note(test_service, "/non/existent/file.md")

        # Test editing non-existent file
        with pytest.raises(FileNotFoundError):
            edit_note(test_service, "content", "non_existent_file")

        # Test deleting non-existent file
        with pytest.raises(FileNotFoundError):
            get_note_delete_confirmation(test_service, filename="non_existent_file")


class TestToolsWithMockService:
    """Test tools with mocked service instances."""

    def test_create_note_with_mock_service(self):
        """Test create_note with a mock service."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/fake/path/test.md")
        mock_service.create_note.return_value = expected_path

        # Act
        result = create_note(mock_service, "test content", "test", "Test Author")

        # Assert
        mock_service.create_note.assert_called_once_with(
            "test content", "test", "Test Author", None
        )
        assert result == expected_path

    def test_read_note_with_mock_service(self):
        """Test read_note with a mock service."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_content = "mock content"
        mock_service.read_note.return_value = expected_content

        # Act
        result = read_note(mock_service, "/path/to/file.md")

        # Assert
        mock_service.read_note.assert_called_once_with("/path/to/file.md")
        assert result == expected_content

    def test_add_tag_with_mock_service(self):
        """Test add_tag with a mock service."""
        # Arrange
        mock_service = Mock(spec=MinervaService)
        expected_path = Path("/fake/path/test.md")
        mock_service.add_tag.return_value = expected_path

        # Act
        result = add_tag(mock_service, "test-tag", filename="test")

        # Assert
        mock_service.add_tag.assert_called_once_with("test-tag", "test", None, None)
        assert result == expected_path


class TestServiceCreationIntegration:
    """Test service creation and integration."""

    @patch.dict(
        os.environ,
        {
            "OBSIDIAN_VAULT_ROOT": "/test/vault",
            "DEFAULT_VAULT": "test_vault",
            "DEFAULT_NOTE_DIR": "notes",
            "DEFAULT_NOTE_AUTHOR": "Integration Test",
        },
    )
    def test_create_minerva_service_integration(self):
        """Test that create_minerva_service works correctly."""
        # Act
        service = create_minerva_service()

        # Assert
        assert isinstance(service, MinervaService)
        assert service.config.vault_path == Path("/test/vault/test_vault")
        assert service.config.default_note_dir == "notes"
        assert service.config.default_author == "Integration Test"

    def test_tools_work_with_factory_service(self):
        """Test that tools work with service created by factory function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                # Arrange
                service = create_minerva_service()

                # Act & Assert - Basic functionality works
                note_path = create_note(service, "Factory test", "factory_test")
                assert note_path.exists()

                content = read_note(service, str(note_path))
                import frontmatter

                post = frontmatter.loads(content)
                assert post.content == "Factory test"
