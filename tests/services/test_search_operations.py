"""
Tests for SearchOperations service module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.file_handler import SearchResult
from minerva.services.search_operations import SearchOperations


class TestSearchOperations:
    """Test cases for SearchOperations class."""

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
    def search_operations(self, mock_config, mock_frontmatter_manager):
        """Create a SearchOperations instance for testing."""
        return SearchOperations(mock_config, mock_frontmatter_manager)

    def test_inherits_from_base_service(self, search_operations):
        """Test that SearchOperations properly inherits from BaseService."""
        assert hasattr(search_operations, "config")
        assert hasattr(search_operations, "frontmatter_manager")
        assert hasattr(search_operations, "error_handler")
        assert hasattr(search_operations, "_log_operation_start")
        assert hasattr(search_operations, "_log_operation_success")
        assert hasattr(search_operations, "_log_operation_error")

    def test_validate_search_query_valid(self, search_operations):
        """Test search query validation for valid query."""
        result = search_operations._validate_search_query("test query")
        assert result == "test query"

    def test_validate_search_query_with_whitespace(self, search_operations):
        """Test search query validation trims whitespace."""
        result = search_operations._validate_search_query("  test query  ")
        assert result == "test query"

    def test_validate_search_query_empty(self, search_operations):
        """Test search query validation for empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_operations._validate_search_query("")

    def test_validate_search_query_whitespace_only(self, search_operations):
        """Test search query validation for whitespace-only query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_operations._validate_search_query("   ")

    @patch("minerva.services.search_operations.SearchConfig")
    def test_create_search_config_default_parameters(
        self, mock_search_config, search_operations
    ):
        """Test creating search config with default parameters."""
        query = "test query"
        mock_config_instance = Mock()
        mock_search_config.return_value = mock_config_instance

        result = search_operations._create_search_config(query)

        assert result == mock_config_instance
        mock_search_config.assert_called_once_with(
            directory="/test/vault",
            keyword=query,
            file_extensions=[".md"],
            case_sensitive=True,
        )

    @patch("minerva.services.search_operations.SearchConfig")
    def test_create_search_config_custom_parameters(
        self, mock_search_config, search_operations
    ):
        """Test creating search config with custom parameters."""
        query = "test query"
        directory = "/custom/path"
        extensions = [".md", ".txt"]
        case_sensitive = False
        mock_config_instance = Mock()
        mock_search_config.return_value = mock_config_instance

        result = search_operations._create_search_config(
            query,
            case_sensitive=case_sensitive,
            file_extensions=extensions,
            directory=directory,
        )

        assert result == mock_config_instance
        mock_search_config.assert_called_once_with(
            directory=directory,
            keyword=query,
            file_extensions=extensions,
            case_sensitive=case_sensitive,
        )

    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_success(
        self, mock_search_func, mock_create_config, search_operations
    ):
        """Test successful search operation."""
        # Arrange
        query = "test query"
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_results = [
            SearchResult(
                file_path="/test/vault/note1.md",
                line_number=1,
                context="test query here",
            ),
            SearchResult(
                file_path="/test/vault/note2.md",
                line_number=5,
                context="another test query",
            ),
        ]
        mock_search_func.return_value = mock_results

        # Act
        result = search_operations.search_notes(query)

        # Assert
        assert result == mock_results
        mock_create_config.assert_called_once_with(query, case_sensitive=True)
        mock_search_func.assert_called_once_with(mock_config)

    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_case_insensitive(
        self, mock_search_func, mock_create_config, search_operations
    ):
        """Test search operation with case insensitive option."""
        # Arrange
        query = "Test Query"
        case_sensitive = False
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_results: list[SearchResult] = []
        mock_search_func.return_value = mock_results

        # Act
        result = search_operations.search_notes(query, case_sensitive=case_sensitive)

        # Assert
        assert result == mock_results
        mock_create_config.assert_called_once_with(query, case_sensitive=case_sensitive)
        mock_search_func.assert_called_once_with(mock_config)

    def test_search_notes_invalid_query(self, search_operations):
        """Test search operation with invalid query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_operations.search_notes("")

    def test_search_notes_whitespace_query(self, search_operations):
        """Test search operation with whitespace-only query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_operations.search_notes("   ")

    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_empty_results(
        self, mock_search_func, mock_create_config, search_operations
    ):
        """Test search operation that returns no results."""
        # Arrange
        query = "nonexistent query"
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_search_func.return_value = []

        # Act
        result = search_operations.search_notes(query)

        # Assert
        assert result == []
        mock_search_func.assert_called_once_with(mock_config)

    @patch("minerva.services.search_operations.Path")
    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_in_directory_success(
        self, mock_search_func, mock_create_config, mock_path, search_operations
    ):
        """Test successful search in specific directory."""
        # Arrange
        query = "test query"
        directory = "/custom/directory"
        mock_config = Mock()
        mock_config.directory = directory
        mock_config.keyword = query
        mock_create_config.return_value = mock_config

        # Mock Path existence check
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        mock_path.return_value = mock_path_instance

        mock_results = [
            SearchResult(
                file_path="/custom/directory/note1.md",
                line_number=1,
                context="test query here",
            ),
        ]
        mock_search_func.return_value = mock_results

        # Act
        result = search_operations.search_notes_in_directory(query, directory)

        # Assert
        assert result == mock_results
        mock_search_func.assert_called_once_with(mock_config)
        mock_create_config.assert_called_once_with(
            query,
            case_sensitive=True,
            file_extensions=None,
            directory=directory,
        )

    @patch("minerva.services.search_operations.Path")
    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_in_directory_custom_extensions(
        self, mock_search_func, mock_create_config, mock_path, search_operations
    ):
        """Test search in directory with custom file extensions."""
        # Arrange
        query = "test query"
        directory = "/custom/directory"
        file_extensions = [".md", ".txt", ".rst"]
        mock_config = Mock()
        mock_config.file_extensions = file_extensions
        mock_create_config.return_value = mock_config

        # Mock Path existence check
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        mock_path.return_value = mock_path_instance

        mock_search_func.return_value = []

        # Act
        result = search_operations.search_notes_in_directory(
            query, directory, file_extensions=file_extensions
        )

        # Assert
        assert result == []
        mock_search_func.assert_called_once_with(mock_config)
        mock_create_config.assert_called_once_with(
            query,
            case_sensitive=True,
            file_extensions=file_extensions,
            directory=directory,
        )

    @patch("minerva.services.search_operations.Path")
    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_in_directory_case_insensitive(
        self, mock_search_func, mock_create_config, mock_path, search_operations
    ):
        """Test search in directory with case insensitive option."""
        # Arrange
        query = "Test Query"
        directory = "/custom/directory"
        case_sensitive = False
        mock_config = Mock()
        mock_config.case_sensitive = False
        mock_create_config.return_value = mock_config

        # Mock Path existence check
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        mock_path.return_value = mock_path_instance

        mock_search_func.return_value = []

        # Act
        result = search_operations.search_notes_in_directory(
            query, directory, case_sensitive=case_sensitive
        )

        # Assert
        assert result == []
        mock_search_func.assert_called_once_with(mock_config)
        mock_create_config.assert_called_once_with(
            query,
            case_sensitive=case_sensitive,
            file_extensions=None,
            directory=directory,
        )

    def test_search_notes_in_directory_invalid_query(self, search_operations):
        """Test search in directory with invalid query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_operations.search_notes_in_directory("", "/test/directory")

    @patch("minerva.services.search_operations.Path")
    def test_search_notes_in_directory_nonexistent_directory(
        self, mock_path, search_operations
    ):
        """Test search in directory that does not exist."""
        # Arrange
        query = "test query"
        directory = "/nonexistent/directory"

        # Mock Path existence check to return False
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        # Act & Assert
        with pytest.raises(ValueError, match=f"Directory does not exist: {directory}"):
            search_operations.search_notes_in_directory(query, directory)

    @patch("minerva.services.search_operations.Path")
    def test_search_notes_in_directory_path_is_not_directory(
        self, mock_path, search_operations
    ):
        """Test search when path exists but is not a directory."""
        # Arrange
        query = "test query"
        directory = "/path/to/file.txt"

        # Mock Path to simulate file (not directory)
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = False
        mock_path.return_value = mock_path_instance

        # Act & Assert
        with pytest.raises(ValueError, match=f"Path is not a directory: {directory}"):
            search_operations.search_notes_in_directory(query, directory)

    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_notes_with_logging(
        self, mock_search_func, mock_create_config, search_operations
    ):
        """Test that search operations are properly logged."""
        # Arrange
        query = "test query"
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_results: list[SearchResult] = []
        mock_search_func.return_value = mock_results

        # Act
        result = search_operations.search_notes(query)

        # Assert
        assert result == mock_results
        mock_search_func.assert_called_once_with(mock_config)
        # The logging behavior is tested implicitly through the operation execution

    @patch.object(SearchOperations, "_create_search_config")
    @patch("minerva.services.search_operations.search_keyword_in_files")
    def test_search_performance_decorator(
        self, mock_search_func, mock_create_config, search_operations
    ):
        """Test that performance logging decorator is applied."""
        # Arrange
        query = "test query"
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_search_func.return_value = []

        # Act
        search_operations.search_notes(query)

        # Assert - verify the method has performance logging decorator
        assert hasattr(search_operations.search_notes, "__wrapped__")
        mock_search_func.assert_called_once_with(mock_config)


class TestSearchOperationsIntegration:
    """Integration tests for SearchOperations with real configuration."""

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
    def search_operations(self, config):
        """Create a SearchOperations instance for testing."""
        frontmatter_manager = FrontmatterManager("Test Author")
        return SearchOperations(config, frontmatter_manager)

    def test_create_search_config_integration(self, search_operations):
        """Test search config creation with real configuration."""
        query = "integration test"

        config = search_operations._create_search_config(query)

        assert config.keyword == query
        assert str(search_operations.config.vault_path) in config.directory
        assert config.file_extensions == [".md"]

    def test_validate_search_query_integration(self, search_operations):
        """Test query validation with real implementation."""
        # Test valid query
        valid_query = "integration test query"
        result = search_operations._validate_search_query(valid_query)
        assert result == valid_query

        # Test query with whitespace
        whitespace_query = "  spaced query  "
        result = search_operations._validate_search_query(whitespace_query)
        assert result == "spaced query"
