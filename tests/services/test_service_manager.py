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


class TestServiceManagerVectorOperations:
    """Test cases for vector search operations in ServiceManager."""

    @pytest.fixture
    def mock_config_vector_enabled(self):
        """Create a mock configuration with vector search enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.vector_search_enabled = True
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/test/vectors.db")  # type: ignore[method-assign]
        config.vector_db_path = mock_path
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def mock_config_vector_disabled(self):
        """Create a mock configuration with vector search disabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.vector_search_enabled = False
        return config

    @pytest.fixture
    def service_manager_vector_enabled(self, mock_config_vector_enabled):
        """Create ServiceManager with vector search enabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return ServiceManager(mock_config_vector_enabled, frontmatter_manager)

    @pytest.fixture
    def service_manager_vector_disabled(self, mock_config_vector_disabled):
        """Create ServiceManager with vector search disabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return ServiceManager(mock_config_vector_disabled, frontmatter_manager)

    def test_build_vector_index_disabled(self, service_manager_vector_disabled):
        """Test build_vector_index when vector search is disabled."""
        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            service_manager_vector_disabled.build_vector_index()

    def test_build_vector_index_no_db_path(self, service_manager_vector_enabled):
        """Test build_vector_index when vector database path is not configured."""
        service_manager_vector_enabled.config.vector_db_path = None

        with pytest.raises(
            RuntimeError, match="Vector database path is not configured"
        ):
            service_manager_vector_enabled.build_vector_index()

    @patch("glob.glob")
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_prepare_vector_indexing_empty_files(
        self,
        mock_indexer_class,
        mock_embedding_class,
        mock_glob,
        service_manager_vector_enabled,
    ):
        """Test _prepare_vector_indexing with empty file list."""
        mock_glob.return_value = []

        mock_indexer = Mock()
        mock_indexer.get_outdated_files.return_value = []
        mock_indexer_class.return_value = mock_indexer

        # Should return early when no files to process
        result = service_manager_vector_enabled.build_vector_index()

        # Should have processed 0 files
        assert result["processed"] == 0
        assert result["skipped"] == 0
        mock_indexer.close.assert_called_once()

    @pytest.mark.vector
    @patch("glob.glob")
    @patch("builtins.open")
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_prepare_vector_indexing_force_rebuild(
        self,
        mock_indexer_class,
        mock_embedding_class,
        mock_open,
        mock_glob,
        service_manager_vector_enabled,
    ):
        """Test _prepare_vector_indexing with force_rebuild=True."""
        mock_glob.return_value = ["/test/file1.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "Sample content"
        )

        mock_embedding_provider = Mock()
        import numpy as np

        mock_embedding_provider.embed.return_value = np.array([0.1, 0.2, 0.3])
        mock_embedding_class.return_value = mock_embedding_provider

        mock_indexer = Mock()
        mock_connection = Mock()
        mock_indexer._get_connection.return_value = mock_connection
        mock_indexer.get_outdated_files.return_value = ["/test/file1.md"]
        mock_indexer_class.return_value = mock_indexer

        result = service_manager_vector_enabled.build_vector_index(force_rebuild=True)

        # Verify force rebuild clears tables
        expected_calls = [
            ("DROP TABLE IF EXISTS vectors",),
            ("DROP TABLE IF EXISTS indexed_files",),
            ("DROP SEQUENCE IF EXISTS vectors_id_seq",),
        ]
        actual_calls = [call[0] for call in mock_connection.execute.call_args_list]
        for expected_call in expected_calls:
            assert expected_call in actual_calls

        assert result["processed"] >= 0

    @patch("glob.glob")
    @patch("builtins.open")
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_prepare_vector_indexing_initialization_error(
        self,
        mock_indexer_class,
        mock_embedding_class,
        mock_open,
        mock_glob,
        service_manager_vector_enabled,
    ):
        """Test _prepare_vector_indexing when schema initialization fails."""
        mock_glob.return_value = ["/test/file1.md"]
        mock_open.return_value.__enter__.return_value.read.side_effect = Exception(
            "File read error"
        )

        mock_embedding_provider = Mock()
        mock_embedding_class.return_value = mock_embedding_provider

        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        with pytest.raises(Exception):
            service_manager_vector_enabled.build_vector_index()

    def test_get_vector_index_status_disabled(self, service_manager_vector_disabled):
        """Test get_vector_index_status when vector search is disabled."""
        result = service_manager_vector_disabled.get_vector_index_status()

        expected = {
            "vector_search_enabled": False,
            "indexed_files_count": 0,
            "database_exists": False,
        }
        assert result == expected

    def test_get_vector_index_status_no_db_path(self, service_manager_vector_enabled):
        """Test get_vector_index_status when database path is not configured."""
        service_manager_vector_enabled.config.vector_db_path = None

        result = service_manager_vector_enabled.get_vector_index_status()

        expected = {
            "vector_search_enabled": True,
            "indexed_files_count": 0,
            "database_exists": False,
        }
        assert result == expected

    def test_get_vector_index_status_db_not_exists(
        self, service_manager_vector_enabled
    ):
        """Test get_vector_index_status when database file doesn't exist."""
        service_manager_vector_enabled.config.vector_db_path.exists.return_value = False

        result = service_manager_vector_enabled.get_vector_index_status()

        expected = {
            "vector_search_enabled": True,
            "indexed_files_count": 0,
            "database_exists": False,
        }
        assert result == expected

    @patch("minerva.vector.searcher.VectorSearcher")
    def test_get_vector_index_status_success(
        self, mock_searcher_class, service_manager_vector_enabled
    ):
        """Test successful get_vector_index_status."""
        service_manager_vector_enabled.config.vector_db_path.exists.return_value = True

        mock_searcher = Mock()
        mock_searcher.get_indexed_files.return_value = ["file1.md", "file2.md"]
        mock_searcher_class.return_value = mock_searcher

        result = service_manager_vector_enabled.get_vector_index_status()

        expected = {
            "vector_search_enabled": True,
            "indexed_files_count": 2,
            "database_exists": True,
        }
        assert result == expected
        mock_searcher.close.assert_called_once()

    def test_get_vector_index_status_import_error(self, service_manager_vector_enabled):
        """Test get_vector_index_status with import error."""
        service_manager_vector_enabled.config.vector_db_path.exists.return_value = True

        with patch.dict("sys.modules", {"minerva.vector.searcher": None}):
            result = service_manager_vector_enabled.get_vector_index_status()

            expected = {
                "vector_search_enabled": False,
                "indexed_files_count": 0,
                "database_exists": False,
                "error": "Vector search dependencies not available",
            }
            assert result == expected
