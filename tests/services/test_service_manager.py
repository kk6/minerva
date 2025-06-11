"""
Tests for ServiceManager facade module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.service_manager import ServiceManager, create_minerva_service
from minerva.services.alias_operations import AliasOperations
from minerva.services.note_operations import NoteOperations
from minerva.services.search_operations import SearchOperations
from minerva.services.tag_operations import TagOperations


class TestServiceManager:
    """Test cases for ServiceManager class."""

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
    def service_manager(self, mock_config, mock_frontmatter_manager):
        """Create a ServiceManager instance for testing."""
        return ServiceManager(mock_config, mock_frontmatter_manager)

    def test_initialization(
        self, service_manager, mock_config, mock_frontmatter_manager
    ):
        """Test ServiceManager initialization."""
        assert service_manager.config == mock_config
        assert service_manager.frontmatter_manager == mock_frontmatter_manager
        assert hasattr(service_manager, "error_handler")

    def test_service_properties(self, service_manager):
        """Test property-based access to specialized services."""
        assert isinstance(service_manager.note_operations, NoteOperations)
        assert isinstance(service_manager.tag_operations, TagOperations)
        assert isinstance(service_manager.alias_operations, AliasOperations)
        assert isinstance(service_manager.search_operations, SearchOperations)

    def test_build_file_path_simple(self, service_manager):
        """Test building file path with simple filename."""
        result_dir, result_name = service_manager._build_file_path("test")

        expected_dir = Path("/test/vault/notes")
        expected_name = "test.md"

        assert result_dir == expected_dir
        assert result_name == expected_name

    def test_build_file_path_with_md_extension(self, service_manager):
        """Test building file path when filename already has .md extension."""
        result_dir, result_name = service_manager._build_file_path("test.md")

        expected_dir = Path("/test/vault/notes")
        expected_name = "test.md"

        assert result_dir == expected_dir
        assert result_name == expected_name

    def test_build_file_path_with_subdirs(self, service_manager):
        """Test building file path with subdirectories."""
        result_dir, result_name = service_manager._build_file_path("subdir/test")

        expected_dir = Path("/test/vault/notes/subdir")
        expected_name = "test.md"

        assert result_dir == expected_dir
        assert result_name == expected_name

    def test_build_file_path_with_custom_default(self, service_manager):
        """Test building file path with custom default path."""
        result_dir, result_name = service_manager._build_file_path("test", "custom")

        expected_dir = Path("/test/vault/custom")
        expected_name = "test.md"

        assert result_dir == expected_dir
        assert result_name == expected_name

    def test_build_file_path_empty_filename(self, service_manager):
        """Test building file path with empty filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            service_manager._build_file_path("")

    @patch("minerva.services.core.file_operations.frontmatter.dumps")
    def test_assemble_complete_note(self, mock_dumps, service_manager):
        """Test assembling complete note."""
        # Arrange
        text = "Test content"
        filename = "test_note"
        author = "Test Author"

        service_manager.frontmatter_manager.read_existing_metadata.return_value = {}
        mock_post = Mock()
        service_manager.frontmatter_manager.generate_metadata.return_value = mock_post
        mock_dumps.return_value = "---\nauthor: Test Author\n---\nTest content"

        # Act
        result_dir, result_name, result_content = (
            service_manager._assemble_complete_note(text, filename, author)
        )

        # Assert
        expected_dir = Path("/test/vault/notes")
        expected_name = "test_note.md"
        expected_content = "---\nauthor: Test Author\n---\nTest content"
        expected_file_path = expected_dir / expected_name

        assert result_dir == expected_dir
        assert result_name == expected_name
        assert result_content == expected_content

        # Assert FrontmatterManager collaboration
        service_manager.frontmatter_manager.read_existing_metadata.assert_called_once_with(
            expected_file_path
        )
        service_manager.frontmatter_manager.generate_metadata.assert_called_once_with(
            text=text, author=author, is_new_note=True, existing_frontmatter={}
        )

    # Note operations delegation tests
    def test_create_note_delegation(self, service_manager):
        """Test create_note delegation to note_operations."""
        with patch.object(
            service_manager.note_operations, "create_note"
        ) as mock_create:
            mock_create.return_value = Path("/test/path")

            result = service_manager.create_note(
                "content", "filename", "author", "path"
            )

            mock_create.assert_called_once_with("content", "filename", "author", "path")
            assert result == Path("/test/path")

    def test_edit_note_delegation(self, service_manager):
        """Test edit_note delegation to note_operations."""
        with patch.object(service_manager.note_operations, "edit_note") as mock_edit:
            mock_edit.return_value = Path("/test/path")

            result = service_manager.edit_note("content", "filename", "author", "path")

            mock_edit.assert_called_once_with("content", "filename", "author", "path")
            assert result == Path("/test/path")

    def test_read_note_delegation(self, service_manager):
        """Test read_note delegation to note_operations."""
        with patch.object(service_manager.note_operations, "read_note") as mock_read:
            mock_read.return_value = "file content"

            result = service_manager.read_note("/test/path")

            mock_read.assert_called_once_with("/test/path")
            assert result == "file content"

    def test_get_note_delete_confirmation_delegation(self, service_manager):
        """Test get_note_delete_confirmation delegation to note_operations."""
        with patch.object(
            service_manager.note_operations, "get_note_delete_confirmation"
        ) as mock_confirm:
            mock_confirm.return_value = {
                "path": "/test/path",
                "message": "Confirm delete",
            }

            result = service_manager.get_note_delete_confirmation(
                "filename", "filepath", "default"
            )

            mock_confirm.assert_called_once_with("filename", "filepath", "default")
            assert result == {"path": "/test/path", "message": "Confirm delete"}

    def test_perform_note_delete_delegation(self, service_manager):
        """Test perform_note_delete delegation to note_operations."""
        with patch.object(
            service_manager.note_operations, "perform_note_delete"
        ) as mock_delete:
            mock_delete.return_value = Path("/test/path")

            result = service_manager.perform_note_delete(
                "filename", "filepath", "default"
            )

            mock_delete.assert_called_once_with("filename", "filepath", "default")
            assert result == Path("/test/path")

    # Search operations delegation tests
    def test_search_notes_delegation(self, service_manager):
        """Test search_notes delegation to search_operations."""
        with patch.object(
            service_manager.search_operations, "search_notes"
        ) as mock_search:
            mock_results = [Mock(), Mock()]
            mock_search.return_value = mock_results

            result = service_manager.search_notes("query", True)

            mock_search.assert_called_once_with("query", True)
            assert result == mock_results

    # Tag operations delegation tests
    def test_add_tag_delegation(self, service_manager):
        """Test add_tag delegation to tag_operations."""
        with patch.object(service_manager.tag_operations, "add_tag") as mock_add:
            mock_add.return_value = Path("/test/path")

            result = service_manager.add_tag("tag", "filename", "filepath", "default")

            mock_add.assert_called_once_with("tag", "filename", "filepath", "default")
            assert result == Path("/test/path")

    def test_remove_tag_delegation(self, service_manager):
        """Test remove_tag delegation to tag_operations."""
        with patch.object(service_manager.tag_operations, "remove_tag") as mock_remove:
            mock_remove.return_value = Path("/test/path")

            result = service_manager.remove_tag(
                "tag", "filename", "filepath", "default"
            )

            mock_remove.assert_called_once_with(
                "tag", "filename", "filepath", "default"
            )
            assert result == Path("/test/path")

    def test_get_tags_delegation(self, service_manager):
        """Test get_tags delegation to tag_operations."""
        with patch.object(service_manager.tag_operations, "get_tags") as mock_get:
            mock_get.return_value = ["tag1", "tag2"]

            result = service_manager.get_tags("filename", "filepath", "default")

            mock_get.assert_called_once_with("filename", "filepath", "default")
            assert result == ["tag1", "tag2"]

    def test_rename_tag_delegation(self, service_manager):
        """Test rename_tag delegation to tag_operations."""
        with patch.object(service_manager.tag_operations, "rename_tag") as mock_rename:
            mock_rename.return_value = [Path("/test/path1"), Path("/test/path2")]

            result = service_manager.rename_tag("old_tag", "new_tag", "directory")

            mock_rename.assert_called_once_with("old_tag", "new_tag", "directory")
            assert result == [Path("/test/path1"), Path("/test/path2")]

    def test_list_all_tags_delegation(self, service_manager):
        """Test list_all_tags delegation to tag_operations."""
        with patch.object(service_manager.tag_operations, "list_all_tags") as mock_list:
            mock_list.return_value = ["tag1", "tag2", "tag3"]

            result = service_manager.list_all_tags("directory")

            mock_list.assert_called_once_with("directory")
            assert result == ["tag1", "tag2", "tag3"]

    def test_find_notes_with_tag_delegation(self, service_manager):
        """Test find_notes_with_tag delegation to tag_operations."""
        with patch.object(
            service_manager.tag_operations, "find_notes_with_tag"
        ) as mock_find:
            mock_find.return_value = ["/path1", "/path2"]

            result = service_manager.find_notes_with_tag("tag", "directory")

            mock_find.assert_called_once_with("tag", "directory")
            assert result == ["/path1", "/path2"]

    # Alias operations delegation tests
    def test_add_alias_delegation(self, service_manager):
        """Test add_alias delegation to alias_operations."""
        with patch.object(service_manager.alias_operations, "add_alias") as mock_add:
            mock_add.return_value = Path("/test/path")

            result = service_manager.add_alias(
                "alias", "filename", "filepath", "default", True
            )

            mock_add.assert_called_once_with(
                "alias", "filename", "filepath", "default", True
            )
            assert result == Path("/test/path")

    def test_remove_alias_delegation(self, service_manager):
        """Test remove_alias delegation to alias_operations."""
        with patch.object(
            service_manager.alias_operations, "remove_alias"
        ) as mock_remove:
            mock_remove.return_value = Path("/test/path")

            result = service_manager.remove_alias(
                "alias", "filename", "filepath", "default"
            )

            mock_remove.assert_called_once_with(
                "alias", "filename", "filepath", "default"
            )
            assert result == Path("/test/path")

    def test_get_aliases_delegation(self, service_manager):
        """Test get_aliases delegation to alias_operations."""
        with patch.object(service_manager.alias_operations, "get_aliases") as mock_get:
            mock_get.return_value = ["alias1", "alias2"]

            result = service_manager.get_aliases("filename", "filepath", "default")

            mock_get.assert_called_once_with("filename", "filepath", "default")
            assert result == ["alias1", "alias2"]

    def test_search_by_alias_delegation(self, service_manager):
        """Test search_by_alias delegation to alias_operations."""
        with patch.object(
            service_manager.alias_operations, "search_by_alias"
        ) as mock_search:
            mock_search.return_value = ["/path1", "/path2"]

            result = service_manager.search_by_alias("alias", "directory")

            mock_search.assert_called_once_with("alias", "directory")
            assert result == ["/path1", "/path2"]

    # Helper method delegation tests
    # Note: Internal helper methods are no longer exposed through the facade


class TestCreateMinervaService:
    """Test cases for create_minerva_service factory function."""

    @patch("minerva.services.service_manager.FrontmatterManager")
    @patch("minerva.services.service_manager.MinervaConfig")
    def test_create_minerva_service_success(self, mock_config_class, mock_fm_class):
        """Test successful creation of ServiceManager instance."""
        # Arrange
        mock_config = Mock()
        mock_config.default_author = "Test Author"
        mock_config_class.from_env.return_value = mock_config

        mock_fm = Mock()
        mock_fm_class.return_value = mock_fm

        # Act
        result = create_minerva_service()

        # Assert
        assert isinstance(result, ServiceManager)
        mock_config_class.from_env.assert_called_once()
        mock_fm_class.assert_called_once_with("Test Author")

    @patch("minerva.services.service_manager.MinervaConfig")
    def test_create_minerva_service_config_error(self, mock_config_class):
        """Test create_minerva_service with configuration error."""
        # Arrange
        mock_config_class.from_env.side_effect = ValueError("Invalid environment")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid environment"):
            create_minerva_service()


class TestServiceManagerIntegration:
    """Integration tests for ServiceManager with real configuration."""

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault for testing."""
        vault_path = tmp_path / "test_vault"
        vault_path.mkdir(parents=True)
        return vault_path

    @pytest.fixture
    def config(self, temp_vault):
        """Create a test configuration."""
        return MinervaConfig(
            vault_path=temp_vault,
            default_note_dir="notes",
            default_author="Test Author",
        )

    @pytest.fixture
    def service_manager(self, config):
        """Create a ServiceManager instance for testing."""
        frontmatter_manager = FrontmatterManager("Test Author")
        return ServiceManager(config, frontmatter_manager)

    def test_service_manager_initialization_integration(self, service_manager):
        """Test ServiceManager initialization with real dependencies."""
        # Test that all services are properly initialized
        assert isinstance(service_manager.note_operations, NoteOperations)
        assert isinstance(service_manager.tag_operations, TagOperations)
        assert isinstance(service_manager.alias_operations, AliasOperations)
        assert isinstance(service_manager.search_operations, SearchOperations)

        # Test that configuration is shared
        assert service_manager.note_operations.config == service_manager.config
        assert service_manager.tag_operations.config == service_manager.config
        assert service_manager.alias_operations.config == service_manager.config
        assert service_manager.search_operations.config == service_manager.config

    def test_build_file_path_integration(self, service_manager):
        """Test file path building with real configuration."""
        # Test simple filename
        result_dir, result_name = service_manager._build_file_path("test")
        expected_dir = service_manager.config.vault_path / "notes"
        assert result_dir == expected_dir
        assert result_name == "test.md"

        # Test with subdirectories
        result_dir, result_name = service_manager._build_file_path("sub/dir/test")
        expected_dir = service_manager.config.vault_path / "notes" / "sub" / "dir"
        assert result_dir == expected_dir
        assert result_name == "test.md"

    def test_assemble_complete_note_integration(self, service_manager):
        """Test note assembly with real configuration."""
        text = "Integration test content"
        filename = "integration_test"

        result_dir, result_name, result_content = (
            service_manager._assemble_complete_note(text, filename)
        )

        # Verify structure
        assert result_dir == service_manager.config.vault_path / "notes"
        assert result_name == "integration_test.md"
        assert "Integration test content" in result_content
        assert "---" in result_content  # Should have frontmatter
