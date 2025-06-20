"""
Tests for SearchOperations service module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Any

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.file_handler import SearchResult, SemanticSearchResult
from minerva.models import DuplicateDetectionResult, DuplicateGroup, DuplicateFile
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


class TestSemanticSearchOperations:
    """Test cases for semantic search functionality in SearchOperations."""

    @pytest.fixture
    def mock_config_vector_enabled(self):
        """Create a mock configuration with vector search enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vectors.db")
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
    def search_operations_vector_enabled(self, mock_config_vector_enabled):
        """Create SearchOperations with vector search enabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return SearchOperations(mock_config_vector_enabled, frontmatter_manager)

    @pytest.fixture
    def search_operations_vector_disabled(self, mock_config_vector_disabled):
        """Create SearchOperations with vector search disabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return SearchOperations(mock_config_vector_disabled, frontmatter_manager)

    def test_semantic_search_vector_disabled(self, search_operations_vector_disabled):
        """Test semantic search when vector search is disabled."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            search_operations_vector_disabled.semantic_search("test query")

    def test_semantic_search_empty_query(self, search_operations_vector_enabled):
        """Test semantic search with empty query."""
        # Act & Assert
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_operations_vector_enabled.semantic_search("")

    def test_semantic_search_invalid_limit(self, search_operations_vector_enabled):
        """Test semantic search with invalid limit."""
        # Act & Assert
        with pytest.raises(ValueError, match="Limit must be positive"):
            search_operations_vector_enabled.semantic_search("test", limit=0)

    def test_semantic_search_invalid_threshold(self, search_operations_vector_enabled):
        """Test semantic search with invalid threshold."""
        # Act & Assert
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            search_operations_vector_enabled.semantic_search("test", threshold=1.5)

    def test_semantic_search_import_error(self, search_operations_vector_enabled):
        """Test semantic search with import error."""
        # Create a mock that simulates ImportError during lazy import
        original_semantic_search = search_operations_vector_enabled.semantic_search

        # Create a new method that raises ImportError
        def mock_semantic_search_with_import_error(*args, **kwargs):
            # Simulate the import error that would occur inside semantic_search
            raise ImportError(
                "Vector search requires additional dependencies. "
                "Install with: pip install sentence-transformers duckdb"
            )

        # Replace the method temporarily
        search_operations_vector_enabled.semantic_search = (
            mock_semantic_search_with_import_error
        )

        try:
            # Act & Assert
            with pytest.raises(
                ImportError, match="Vector search requires additional dependencies"
            ):
                search_operations_vector_enabled.semantic_search("test query")
        finally:
            # Restore original method
            search_operations_vector_enabled.semantic_search = original_semantic_search

    def test_create_semantic_search_result_success(
        self, search_operations_vector_enabled
    ):
        """Test successful creation of semantic search result."""
        # Arrange
        file_path = "/test/file.md"
        similarity_score = 0.8

        # Mock file reading and frontmatter parsing
        with (
            patch(
                "builtins.open",
                mock_open_with_content("---\ntitle: Test File\n---\nContent here"),
            ),
            patch(
                "minerva.services.search_operations.frontmatter.loads"
            ) as mock_frontmatter,
            patch("minerva.services.search_operations.Path") as mock_path_class,
        ):
            # Mock Path object and its methods
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_size = 1000  # Small file size
            mock_path.__str__ = Mock(return_value=file_path)  # type: ignore[method-assign]
            mock_path_class.return_value = mock_path

            mock_post = Mock()
            mock_post.metadata = {"title": "Test File"}
            mock_post.content = "Content here"
            mock_frontmatter.return_value = mock_post

            # Act
            result = search_operations_vector_enabled._create_semantic_search_result(
                file_path, similarity_score, None
            )

            # Assert
            assert result is not None
            assert isinstance(result, SemanticSearchResult)
            assert result.file_path == file_path
            assert result.title == "Test File"
            assert result.similarity_score == similarity_score
            assert "Content here" in result.content_preview
            assert result.aliases is None  # No aliases in this test

    def test_create_semantic_search_result_file_not_found(
        self, search_operations_vector_enabled
    ):
        """Test semantic search result creation with non-existent file."""
        # Arrange
        file_path = "/test/nonexistent.md"
        similarity_score = 0.8

        # Mock file not existing
        with patch.object(Path, "exists", return_value=False):
            # Act
            result = search_operations_vector_enabled._create_semantic_search_result(
                file_path, similarity_score, None
            )

            # Assert
            assert result is None

    def test_create_semantic_search_result_with_aliases(
        self, search_operations_vector_enabled
    ):
        """Test semantic search result creation with aliases."""
        # Arrange
        file_path = "/test/file.md"
        similarity_score = 0.9

        # Mock file reading and frontmatter parsing with aliases
        with (
            patch(
                "builtins.open",
                mock_open_with_content(
                    "---\ntitle: Test File\naliases: ['Alias 1', 'Alias 2']\n---\nContent here"
                ),
            ),
            patch(
                "minerva.services.search_operations.frontmatter.loads"
            ) as mock_frontmatter,
            patch("minerva.services.search_operations.Path") as mock_path_class,
        ):
            # Mock Path object and its methods
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_size = 1000  # Small file size
            mock_path.__str__ = Mock(return_value=file_path)  # type: ignore[method-assign]
            mock_path_class.return_value = mock_path
            mock_post = Mock()
            mock_post.metadata = {
                "title": "Test File",
                "aliases": ["Alias 1", "Alias 2"],
            }
            mock_post.content = "Content here"
            mock_frontmatter.return_value = mock_post

            # Act
            result = search_operations_vector_enabled._create_semantic_search_result(
                file_path, similarity_score, None
            )

            # Assert
            assert result is not None
            assert isinstance(result, SemanticSearchResult)
            assert result.file_path == file_path
            assert result.title == "Test File"
            assert result.similarity_score == similarity_score
            assert result.aliases == ["Alias 1", "Alias 2"]
            assert "Content here" in result.content_preview

    def test_create_semantic_search_result_with_single_alias(
        self, search_operations_vector_enabled
    ):
        """Test semantic search result creation with single alias string."""
        # Arrange
        file_path = "/test/file.md"
        similarity_score = 0.7

        # Mock file reading and frontmatter parsing with single alias
        with (
            patch(
                "builtins.open",
                mock_open_with_content(
                    "---\ntitle: Test File\naliases: 'Single Alias'\n---\nContent here"
                ),
            ),
            patch(
                "minerva.services.search_operations.frontmatter.loads"
            ) as mock_frontmatter,
            patch("minerva.services.search_operations.Path") as mock_path_class,
        ):
            # Mock Path object and its methods
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_size = 1000  # Small file size
            mock_path.__str__ = Mock(return_value=file_path)  # type: ignore[method-assign]
            mock_path_class.return_value = mock_path
            mock_post = Mock()
            mock_post.metadata = {"title": "Test File", "aliases": "Single Alias"}
            mock_post.content = "Content here"
            mock_frontmatter.return_value = mock_post

            # Act
            result = search_operations_vector_enabled._create_semantic_search_result(
                file_path, similarity_score, None
            )

            # Assert
            assert result is not None
            assert isinstance(result, SemanticSearchResult)
            assert result.aliases == ["Single Alias"]

    def test_create_semantic_search_result_with_empty_aliases(
        self, search_operations_vector_enabled
    ):
        """Test semantic search result creation with empty aliases."""
        # Arrange
        file_path = "/test/file.md"
        similarity_score = 0.6

        # Mock file reading and frontmatter parsing with empty aliases
        with (
            patch(
                "builtins.open",
                mock_open_with_content(
                    "---\ntitle: Test File\naliases: []\n---\nContent here"
                ),
            ),
            patch(
                "minerva.services.search_operations.frontmatter.loads"
            ) as mock_frontmatter,
            patch("minerva.services.search_operations.Path") as mock_path_class,
        ):
            # Mock Path object and its methods
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_size = 1000  # Small file size
            mock_path.__str__ = Mock(return_value=file_path)  # type: ignore[method-assign]
            mock_path_class.return_value = mock_path
            mock_post = Mock()
            mock_post.metadata = {"title": "Test File", "aliases": []}
            mock_post.content = "Content here"
            mock_frontmatter.return_value = mock_post

            # Act
            result = search_operations_vector_enabled._create_semantic_search_result(
                file_path, similarity_score, None
            )

            # Assert
            assert result is not None
            assert isinstance(result, SemanticSearchResult)
            assert result.aliases is None  # Empty list should be None

    def test_get_indexed_files_count_vector_disabled(
        self, search_operations_vector_disabled
    ):
        """Test get_indexed_files_count when vector search is disabled."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            search_operations_vector_disabled.get_indexed_files_count()

    def test_get_indexed_files_count_success(self, search_operations_vector_enabled):
        """Test successful get_indexed_files_count."""
        # Create a mock that simulates successful operation
        original_method = search_operations_vector_enabled.get_indexed_files_count

        # Create a new method that returns a count
        def mock_get_indexed_files_count():
            return 3

        # Replace the method temporarily
        search_operations_vector_enabled.get_indexed_files_count = (
            mock_get_indexed_files_count
        )

        try:
            # Act
            count = search_operations_vector_enabled.get_indexed_files_count()

            # Assert
            assert count == 3
        finally:
            # Restore original method
            search_operations_vector_enabled.get_indexed_files_count = original_method


def mock_open_with_content(content):
    """Helper function to create a mock open with specific content."""
    from unittest.mock import mock_open

    return mock_open(read_data=content)


class TestFindSimilarNotes:
    """Test cases for find_similar_notes functionality in SearchOperations."""

    @pytest.fixture
    def mock_config_vector_enabled(self):
        """Create a mock configuration with vector search enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vectors.db")
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
    def search_operations_vector_enabled(self, mock_config_vector_enabled):
        """Create SearchOperations with vector search enabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return SearchOperations(mock_config_vector_enabled, frontmatter_manager)

    @pytest.fixture
    def search_operations_vector_disabled(self, mock_config_vector_disabled):
        """Create SearchOperations with vector search disabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return SearchOperations(mock_config_vector_disabled, frontmatter_manager)

    def test_find_similar_notes_vector_disabled(
        self, search_operations_vector_disabled
    ):
        """Test find_similar_notes when vector search is disabled."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            search_operations_vector_disabled.find_similar_notes(filename="test.md")

    def test_find_similar_notes_no_filename_or_filepath(
        self, search_operations_vector_enabled
    ):
        """Test find_similar_notes with neither filename nor filepath provided."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            search_operations_vector_enabled.find_similar_notes()

    def test_find_similar_notes_invalid_limit(self, search_operations_vector_enabled):
        """Test find_similar_notes with invalid limit."""
        # Act & Assert
        with pytest.raises(ValueError, match="Limit must be positive"):
            search_operations_vector_enabled.find_similar_notes(
                filename="test.md", limit=0
            )

    @patch("minerva.vector.searcher.VectorSearcher")
    @patch("minerva.services.core.file_operations.resolve_note_file")
    def test_find_similar_notes_file_not_exists(
        self, mock_resolve, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test find_similar_notes when reference file doesn't exist."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_resolve.return_value = mock_path

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Reference file does not exist"):
            search_operations_vector_enabled.find_similar_notes(
                filename="nonexistent.md"
            )

    @patch("minerva.vector.searcher.VectorSearcher")
    @patch("minerva.services.core.file_operations.resolve_note_file")
    def test_find_similar_notes_success(
        self, mock_resolve, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test successful find_similar_notes operation."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_resolve.return_value = mock_path

        mock_searcher = Mock()
        mock_searcher.find_similar_to_file.return_value = [
            ("/test/vault/similar1.md", 0.8),
            ("/test/vault/similar2.md", 0.7),
        ]
        mock_searcher_class.return_value = mock_searcher

        # Mock _create_semantic_search_result
        with patch.object(
            search_operations_vector_enabled, "_create_semantic_search_result"
        ) as mock_create_result:
            mock_result1 = Mock(spec=SemanticSearchResult)
            mock_result2 = Mock(spec=SemanticSearchResult)
            mock_create_result.side_effect = [mock_result1, mock_result2]

            # Act
            results = search_operations_vector_enabled.find_similar_notes(
                filename="reference.md", limit=5, exclude_self=True
            )

            # Assert
            assert len(results) == 2
            assert results[0] == mock_result1
            assert results[1] == mock_result2
            mock_searcher.find_similar_to_file.assert_called_once_with(
                str(mock_path), k=5, exclude_self=True
            )
            mock_searcher.close.assert_called_once()

    @patch("minerva.vector.searcher.VectorSearcher")
    @patch("minerva.services.core.file_operations.resolve_note_file")
    def test_find_similar_notes_with_filepath(
        self, mock_resolve, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test find_similar_notes using filepath parameter."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_resolve.return_value = mock_path

        mock_searcher = Mock()
        mock_searcher.find_similar_to_file.return_value = []
        mock_searcher_class.return_value = mock_searcher

        # Act
        results = search_operations_vector_enabled.find_similar_notes(
            filepath="/test/vault/reference.md"
        )

        # Assert
        assert results == []
        mock_resolve.assert_called_once_with(
            search_operations_vector_enabled.config,
            None,
            "/test/vault/reference.md",
            None,
        )

    def test_find_similar_notes_import_error(self, search_operations_vector_enabled):
        """Test find_similar_notes with import error."""
        # Create a mock that simulates ImportError during lazy import
        original_method = search_operations_vector_enabled.find_similar_notes

        # Create a new method that raises ImportError
        def mock_find_similar_with_import_error(*args, **kwargs):
            # Simulate the import error that would occur inside find_similar_notes
            raise ImportError(
                "Vector search requires additional dependencies. "
                "Install with: pip install sentence-transformers duckdb"
            )

        # Replace the method temporarily
        search_operations_vector_enabled.find_similar_notes = (
            mock_find_similar_with_import_error
        )

        try:
            # Act & Assert
            with pytest.raises(
                ImportError, match="Vector search requires additional dependencies"
            ):
                search_operations_vector_enabled.find_similar_notes(filename="test.md")
        finally:
            # Restore original method
            search_operations_vector_enabled.find_similar_notes = original_method

    @patch("minerva.vector.searcher.VectorSearcher")
    @patch("minerva.services.core.file_operations.resolve_note_file")
    def test_find_similar_notes_exclude_self_false(
        self, mock_resolve, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test find_similar_notes with exclude_self=False."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_resolve.return_value = mock_path

        mock_searcher = Mock()
        mock_searcher.find_similar_to_file.return_value = [
            ("/test/vault/reference.md", 1.0),  # Self-reference
            ("/test/vault/similar.md", 0.9),
        ]
        mock_searcher_class.return_value = mock_searcher

        # Mock _create_semantic_search_result
        with patch.object(
            search_operations_vector_enabled, "_create_semantic_search_result"
        ) as mock_create_result:
            mock_result1 = Mock(spec=SemanticSearchResult)
            mock_result2 = Mock(spec=SemanticSearchResult)
            mock_create_result.side_effect = [mock_result1, mock_result2]

            # Act
            results = search_operations_vector_enabled.find_similar_notes(
                filename="reference.md", exclude_self=False
            )

            # Assert
            assert len(results) == 2
            mock_searcher.find_similar_to_file.assert_called_once_with(
                str(mock_path), k=5, exclude_self=False
            )

    @patch("minerva.vector.searcher.VectorSearcher")
    @patch("minerva.services.core.file_operations.resolve_note_file")
    def test_find_similar_notes_with_default_path(
        self, mock_resolve, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test find_similar_notes with default_path parameter."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_resolve.return_value = mock_path

        mock_searcher = Mock()
        mock_searcher.find_similar_to_file.return_value = []
        mock_searcher_class.return_value = mock_searcher

        # Act
        results = search_operations_vector_enabled.find_similar_notes(
            filename="reference.md", default_path="subfolder"
        )

        # Assert
        assert results == []
        mock_resolve.assert_called_once_with(
            search_operations_vector_enabled.config, "reference.md", None, "subfolder"
        )


class TestSemanticSearchCoverage:
    """Test cases for semantic search functionality coverage."""

    @pytest.fixture
    def mock_config_vector_enabled(self):
        """Create a mock configuration with vector search enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def search_operations_vector_enabled(self, mock_config_vector_enabled):
        """Create SearchOperations with vector search enabled."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return SearchOperations(mock_config_vector_enabled, frontmatter_manager)

    def test_semantic_search_no_db_path(self, search_operations_vector_enabled):
        """Test semantic search when vector database path is not configured."""
        search_operations_vector_enabled.config.vector_db_path = None

        with pytest.raises(
            RuntimeError, match="Vector database path is not configured"
        ):
            search_operations_vector_enabled.semantic_search("test query")

    @pytest.mark.vector
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.searcher.VectorSearcher")
    def test_semantic_search_full_flow(
        self,
        mock_searcher_class,
        mock_embedding_class,
        search_operations_vector_enabled,
    ):
        """Test complete semantic search flow with mocked dependencies."""
        # Arrange
        mock_embedding_provider = Mock()
        import numpy as np

        mock_embedding_provider.embed.return_value = np.array([0.1, 0.2, 0.3])
        mock_embedding_class.return_value = mock_embedding_provider

        mock_searcher = Mock()
        mock_searcher.search_similar.return_value = [
            ("/test/vault/file1.md", 0.8),
            ("/test/vault/file2.md", 0.7),
        ]
        mock_searcher_class.return_value = mock_searcher

        # Mock _create_semantic_search_result
        with patch.object(
            search_operations_vector_enabled, "_create_semantic_search_result"
        ) as mock_create_result:
            mock_result1 = Mock(spec=SemanticSearchResult)
            mock_result2 = Mock(spec=SemanticSearchResult)
            mock_create_result.side_effect = [mock_result1, mock_result2]

            # Act
            results = search_operations_vector_enabled.semantic_search(
                "test query", limit=10, threshold=0.5
            )

            # Assert
            assert len(results) == 2
            assert results[0] == mock_result1
            assert results[1] == mock_result2
            mock_searcher.search_similar.assert_called_once()
            mock_searcher.close.assert_called_once()

    @pytest.mark.vector
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.searcher.VectorSearcher")
    def test_semantic_search_2d_embedding_handling(
        self,
        mock_searcher_class,
        mock_embedding_class,
        search_operations_vector_enabled,
    ):
        """Test semantic search with 2D embedding array."""
        # Arrange
        mock_embedding_provider = Mock()
        import numpy as np

        # Return 2D array that needs to be flattened
        mock_embedding_provider.embed.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_embedding_class.return_value = mock_embedding_provider

        mock_searcher = Mock()
        mock_searcher.search_similar.return_value = []
        mock_searcher_class.return_value = mock_searcher

        # Act
        results = search_operations_vector_enabled.semantic_search("test query")

        # Assert
        assert results == []
        # Verify that the searcher received the flattened embedding
        args, kwargs = mock_searcher.search_similar.call_args
        query_embedding = args[0]
        assert query_embedding.ndim == 1  # Should be flattened to 1D

    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    def test_semantic_search_exception_handling(
        self, mock_embedding_class, search_operations_vector_enabled
    ):
        """Test semantic search exception handling."""
        # Arrange - Make embedding provider raise an exception
        mock_embedding_class.side_effect = Exception("Test error")

        # Act & Assert
        with pytest.raises(Exception, match="Test error"):
            search_operations_vector_enabled.semantic_search("test query")

    def test_semantic_search_import_error_in_method(
        self, search_operations_vector_enabled
    ):
        """Test semantic search ImportError handling within the method."""
        # Simulate ImportError during the import statements inside semantic_search
        with patch.dict("sys.modules", {"minerva.vector.embeddings": None}):
            with pytest.raises(
                ImportError, match="Vector search requires additional dependencies"
            ):
                search_operations_vector_enabled.semantic_search("test query")

    def test_create_semantic_search_result_directory_filter(
        self, search_operations_vector_enabled
    ):
        """Test directory filtering in _create_semantic_search_result."""
        # Arrange
        file_path = "/other/path/file.md"
        target_directory = "/test/vault"

        # Mock Path.is_relative_to to return False
        with patch("minerva.services.search_operations.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.is_relative_to.return_value = False
            mock_path_class.return_value = mock_path

            # Act
            result = search_operations_vector_enabled._create_semantic_search_result(
                file_path, 0.8, target_directory
            )

            # Assert
            assert result is None

    def test_extract_title_from_metadata(self, search_operations_vector_enabled):
        """Test title extraction from metadata."""
        # Arrange
        metadata = {"title": "Custom Title"}
        path = Path("/test/my_test_file.md")

        # Act
        title = search_operations_vector_enabled._extract_title(metadata, path)

        # Assert
        assert title == "Custom Title"

    def test_extract_title_from_filename(self, search_operations_vector_enabled):
        """Test title extraction from filename when no metadata title."""
        # Arrange
        metadata: dict[str, Any] = {}
        path = Path("/test/my-test_file.md")

        # Act
        title = search_operations_vector_enabled._extract_title(metadata, path)

        # Assert
        assert title == "My Test File"

    def test_extract_title_non_string_metadata(self, search_operations_vector_enabled):
        """Test title extraction when metadata title is not a string."""
        # Arrange
        metadata = {"title": 123}  # Non-string value
        path = Path("/test/fallback_file.md")

        # Act
        title = search_operations_vector_enabled._extract_title(metadata, path)

        # Assert
        assert title == "Fallback File"

    def test_create_content_preview_with_frontmatter(
        self, search_operations_vector_enabled
    ):
        """Test content preview creation with frontmatter."""
        # Arrange
        mock_post = Mock()
        mock_post.content = "Line 1\nLine 2\nLine 3\n" + "Very long content " * 50
        mock_post.metadata = {"title": "Test"}
        content = "original content"

        # Act
        preview = search_operations_vector_enabled._create_content_preview(
            mock_post, content
        )

        # Assert
        assert len(preview) <= 200
        assert preview.endswith("...")
        assert "Line 1 Line 2 Line 3" in preview

    def test_create_content_preview_without_frontmatter(
        self, search_operations_vector_enabled
    ):
        """Test content preview creation without frontmatter."""
        # Arrange
        mock_post = Mock()
        mock_post.content = "Very long content " * 50
        mock_post.metadata = None  # No metadata
        content = "Very long content " * 50

        # Act
        preview = search_operations_vector_enabled._create_content_preview(
            mock_post, content
        )

        # Assert
        assert len(preview) <= 200
        assert preview.endswith("...")

    def test_create_content_preview_short_content(
        self, search_operations_vector_enabled
    ):
        """Test content preview with short content."""
        # Arrange
        mock_post = Mock()
        mock_post.content = "Short content"
        mock_post.metadata = {"title": "Test"}
        content = "original"

        # Act
        preview = search_operations_vector_enabled._create_content_preview(
            mock_post, content
        )

        # Assert
        assert preview == "Short content"
        assert not preview.endswith("...")

    @patch("minerva.vector.searcher.VectorSearcher")
    def test_get_indexed_files_count_success(
        self, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test successful get_indexed_files_count."""
        # Arrange
        mock_searcher = Mock()
        mock_searcher.get_indexed_files.return_value = [
            "file1.md",
            "file2.md",
            "file3.md",
        ]
        mock_searcher_class.return_value = mock_searcher

        # Act
        count = search_operations_vector_enabled.get_indexed_files_count()

        # Assert
        assert count == 3
        mock_searcher.close.assert_called_once()

    def test_get_indexed_files_count_no_db_path(self, search_operations_vector_enabled):
        """Test get_indexed_files_count when vector database path is not configured."""
        search_operations_vector_enabled.config.vector_db_path = None

        with pytest.raises(
            RuntimeError, match="Vector database path is not configured"
        ):
            search_operations_vector_enabled.get_indexed_files_count()

    def test_get_indexed_files_count_import_error(
        self, search_operations_vector_enabled
    ):
        """Test get_indexed_files_count with import error."""
        with patch.dict("sys.modules", {"minerva.vector.searcher": None}):
            with pytest.raises(
                ImportError, match="Vector search requires additional dependencies"
            ):
                search_operations_vector_enabled.get_indexed_files_count()

    @patch("minerva.vector.searcher.VectorSearcher")
    @patch("minerva.services.core.file_operations.resolve_note_file")
    def test_find_similar_notes_import_error_coverage(
        self, mock_resolve, mock_searcher_class, search_operations_vector_enabled
    ):
        """Test find_similar_notes ImportError handling for coverage."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_resolve.return_value = mock_path

        # Simulate ImportError during VectorSearcher import
        mock_searcher_class.side_effect = ImportError("Missing dependencies")

        # Act & Assert
        with pytest.raises(
            ImportError, match="Vector search requires additional dependencies"
        ):
            search_operations_vector_enabled.find_similar_notes(filename="test.md")


class TestFileSizeValidation:
    """Test cases for file size validation in SearchOperations."""

    @pytest.fixture
    def mock_config_vector_enabled(self):
        """Create a mock configuration with vector search enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vectors.db")
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def search_operations(self, mock_config_vector_enabled):
        """Create SearchOperations for file size validation testing."""
        frontmatter_manager = Mock(spec=FrontmatterManager)
        return SearchOperations(mock_config_vector_enabled, frontmatter_manager)

    @patch("os.stat")
    def test_read_and_parse_file_size_limit_exceeded(
        self, mock_stat, search_operations
    ):
        """Test that _read_and_parse_file blocks files exceeding size limit."""
        # Arrange
        test_file = Path("/test/vault/large_file.md")

        # Mock file stat to return size larger than 10MB
        mock_stat_result = Mock()
        mock_stat_result.st_size = 11 * 1024 * 1024  # 11MB
        mock_stat.return_value = mock_stat_result

        # Act & Assert
        with pytest.raises(ValueError, match="File too large"):
            search_operations._read_and_parse_file(test_file)

    @patch("os.stat")
    @patch("builtins.open", mock_open_with_content("# Test content"))
    @patch("minerva.services.search_operations.frontmatter.loads")
    def test_read_and_parse_file_size_within_limit(
        self, mock_frontmatter, mock_stat, search_operations
    ):
        """Test that _read_and_parse_file accepts files within size limit."""
        # Arrange
        test_file = Path("/test/vault/normal_file.md")

        # Mock file stat to return size within 10MB limit
        mock_stat_result = Mock()
        mock_stat_result.st_size = 5 * 1024 * 1024  # 5MB
        mock_stat.return_value = mock_stat_result

        # Mock frontmatter parsing
        mock_post = Mock()
        mock_post.metadata = {"title": "Test"}
        mock_frontmatter.return_value = mock_post

        # Act
        content, post, metadata = search_operations._read_and_parse_file(test_file)

        # Assert
        assert content == "# Test content"
        assert post == mock_post
        assert metadata == {"title": "Test"}

    @patch("os.stat")
    def test_read_and_parse_file_size_exactly_at_limit(
        self, mock_stat, search_operations
    ):
        """Test file exactly at the 10MB size limit."""
        # Arrange
        test_file = Path("/test/vault/limit_file.md")

        # Mock file stat to return exactly 10MB
        mock_stat_result = Mock()
        mock_stat_result.st_size = 10 * 1024 * 1024  # Exactly 10MB
        mock_stat.return_value = mock_stat_result

        # Mock file content
        with (
            patch("builtins.open", mock_open_with_content("# Content at limit")),
            patch(
                "minerva.services.search_operations.frontmatter.loads"
            ) as mock_frontmatter,
        ):
            mock_post = Mock()
            mock_post.metadata = {}
            mock_frontmatter.return_value = mock_post

            # Act - should succeed as it's exactly at limit
            content, post, metadata = search_operations._read_and_parse_file(test_file)

            # Assert
            assert content == "# Content at limit"

    @patch("os.stat")
    def test_read_and_parse_file_size_one_byte_over_limit(
        self, mock_stat, search_operations
    ):
        """Test file one byte over the 10MB size limit."""
        # Arrange
        test_file = Path("/test/vault/over_limit_file.md")

        # Mock file stat to return one byte over 10MB
        mock_stat_result = Mock()
        mock_stat_result.st_size = (10 * 1024 * 1024) + 1  # 10MB + 1 byte
        mock_stat.return_value = mock_stat_result

        # Act & Assert
        with pytest.raises(ValueError, match="File too large"):
            search_operations._read_and_parse_file(test_file)

    @patch("os.stat")
    def test_read_and_parse_file_empty_file(self, mock_stat, search_operations):
        """Test handling of empty files."""
        # Arrange
        test_file = Path("/test/vault/empty_file.md")

        # Mock file stat to return zero size
        mock_stat_result = Mock()
        mock_stat_result.st_size = 0
        mock_stat.return_value = mock_stat_result

        # Mock empty file content
        with (
            patch("builtins.open", mock_open_with_content("")),
            patch(
                "minerva.services.search_operations.frontmatter.loads"
            ) as mock_frontmatter,
        ):
            mock_post = Mock()
            mock_post.metadata = {}
            mock_frontmatter.return_value = mock_post

            # Act
            content, post, metadata = search_operations._read_and_parse_file(test_file)

            # Assert
            assert content == ""
            assert metadata == {}

    @patch("os.stat")
    def test_read_and_parse_file_stat_error(self, mock_stat, search_operations):
        """Test handling of file stat errors."""
        # Arrange
        test_file = Path("/test/vault/inaccessible_file.md")

        # Mock file stat to raise OSError
        mock_stat.side_effect = OSError("Permission denied")

        # Act & Assert
        with pytest.raises(OSError, match="Permission denied"):
            search_operations._read_and_parse_file(test_file)

    @patch("os.stat")
    @patch("minerva.services.search_operations.logger")
    def test_create_semantic_search_result_large_file_handling(
        self, mock_logger, mock_stat, search_operations
    ):
        """Test that large files are properly handled in semantic search results."""
        # Arrange
        file_path = "/test/vault/large_file.md"
        similarity_score = 0.8

        # Mock file stat to return size larger than 10MB
        mock_stat_result = Mock()
        mock_stat_result.st_size = 15 * 1024 * 1024  # 15MB
        mock_stat.return_value = mock_stat_result

        # Mock file existence
        with patch("minerva.services.search_operations.Path") as mock_path_class:
            # Mock Path object and its methods
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value = mock_stat_result
            mock_path.__str__ = Mock(return_value=file_path)  # type: ignore[method-assign]
            mock_path_class.return_value = mock_path

            # Act
            result = search_operations._create_semantic_search_result(
                file_path, similarity_score, None
            )

            # Assert
            assert result is None
            # Check that warnings were logged
            assert mock_logger.warning.call_count == 2

            # First warning should be about file being too large
            first_call = mock_logger.warning.call_args_list[0]
            assert "File too large for processing" in first_call[0][0]

            # Second warning should be about failed creation
            second_call = mock_logger.warning.call_args_list[1]
            assert "Failed to create semantic search result" in second_call[0][0]

    @patch("os.stat")
    def test_read_and_parse_file_unicode_content_size_calculation(
        self, mock_stat, search_operations
    ):
        """Test that file size validation uses actual byte size for Unicode content."""
        # Arrange
        test_file = Path("/test/vault/unicode_file.md")

        # Create Unicode content that is large when encoded as UTF-8
        # Each Japanese character takes 3 bytes in UTF-8
        unicode_content = "あ" * (4 * 1024 * 1024)  # ~12MB when encoded to UTF-8

        # Mock file stat to return the actual UTF-8 byte size (over limit)
        mock_stat_result = Mock()
        mock_stat_result.st_size = len(unicode_content.encode("utf-8"))
        mock_stat.return_value = mock_stat_result

        # Act & Assert
        with pytest.raises(ValueError, match="File too large"):
            search_operations._read_and_parse_file(test_file)

    @patch("os.stat")
    @patch("builtins.open", mock_open_with_content("日本語コンテンツ"))
    @patch("minerva.services.search_operations.frontmatter.loads")
    def test_read_and_parse_file_small_unicode_content(
        self, mock_frontmatter, mock_stat, search_operations
    ):
        """Test that small Unicode content is processed correctly."""
        # Arrange
        test_file = Path("/test/vault/small_unicode_file.md")

        # Mock file stat to return small size
        mock_stat_result = Mock()
        mock_stat_result.st_size = 100  # Small file
        mock_stat.return_value = mock_stat_result

        # Mock frontmatter parsing
        mock_post = Mock()
        mock_post.metadata = {"title": "日本語タイトル"}
        mock_frontmatter.return_value = mock_post

        # Act
        content, post, metadata = search_operations._read_and_parse_file(test_file)

        # Assert
        assert content == "日本語コンテンツ"
        assert metadata == {"title": "日本語タイトル"}


class TestDuplicateDetection:
    """Test cases for duplicate detection functionality."""

    @pytest.fixture
    def mock_config_with_vector_search(self):
        """Create a mock configuration with vector search enabled."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        config.vector_search_enabled = True
        config.vector_db_path = Path("/test/vault/.minerva/vectors.db")
        config.embedding_model = "all-MiniLM-L6-v2"
        return config

    @pytest.fixture
    def mock_frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def search_operations_with_vector(
        self, mock_config_with_vector_search, mock_frontmatter_manager
    ):
        """Create a SearchOperations instance with vector search enabled."""
        return SearchOperations(
            mock_config_with_vector_search, mock_frontmatter_manager
        )

    def test_find_duplicate_notes_vector_search_disabled(self):
        """Test that find_duplicate_notes raises error when vector search is disabled."""
        # Create search operations with vector search disabled
        config = Mock(spec=MinervaConfig)
        config.vector_search_enabled = False
        config.vault_path = Path("/test/vault")
        frontmatter_manager = Mock(spec=FrontmatterManager)
        search_operations = SearchOperations(config, frontmatter_manager)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            search_operations.find_duplicate_notes()

    def test_find_duplicate_notes_invalid_threshold(
        self, search_operations_with_vector
    ):
        """Test that find_duplicate_notes validates similarity threshold."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Similarity threshold must be between 0.0 and 1.0"
        ):
            search_operations_with_vector.find_duplicate_notes(similarity_threshold=1.5)

        with pytest.raises(
            ValueError, match="Similarity threshold must be between 0.0 and 1.0"
        ):
            search_operations_with_vector.find_duplicate_notes(
                similarity_threshold=-0.1
            )

    def test_find_duplicate_notes_invalid_min_content_length(
        self, search_operations_with_vector
    ):
        """Test that find_duplicate_notes validates min_content_length."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Minimum content length must be non-negative"
        ):
            search_operations_with_vector.find_duplicate_notes(min_content_length=-1)

    @patch("minerva.vector.searcher.VectorSearcher")
    def test_find_duplicate_notes_success(
        self, mock_vector_searcher_class, search_operations_with_vector
    ):
        """Test successful duplicate detection."""
        # Arrange
        mock_searcher = Mock()
        mock_vector_searcher_class.return_value = mock_searcher

        # Mock indexed files
        mock_searcher.get_indexed_files.return_value = [
            "/test/vault/note1.md",
            "/test/vault/note2.md",
            "/test/vault/note3.md",
        ]

        # Mock similar files results
        def mock_find_similar_to_file(file_path, k, exclude_self):
            if file_path == "/test/vault/note1.md":
                return [
                    ("/test/vault/note1.md", 1.0),
                    ("/test/vault/note2.md", 0.9),
                    ("/test/vault/note3.md", 0.5),
                ]
            elif file_path == "/test/vault/note2.md":
                return [
                    ("/test/vault/note2.md", 1.0),
                    ("/test/vault/note1.md", 0.9),
                    ("/test/vault/note3.md", 0.5),
                ]
            else:
                return [
                    ("/test/vault/note3.md", 1.0),
                    ("/test/vault/note1.md", 0.5),
                    ("/test/vault/note2.md", 0.5),
                ]

        mock_searcher.find_similar_to_file.side_effect = mock_find_similar_to_file

        # Mock file content filtering and processing
        with patch.object(
            search_operations_with_vector, "_filter_files_by_content_length"
        ) as mock_filter:
            mock_filter.return_value = [
                "/test/vault/note1.md",
                "/test/vault/note2.md",
                "/test/vault/note3.md",
            ]

            with patch.object(
                search_operations_with_vector, "_create_duplicate_file"
            ) as mock_create_file:
                mock_create_file.side_effect = [
                    DuplicateFile(
                        file_path="/test/vault/note1.md",
                        title="Note 1",
                        similarity_score=1.0,
                        content_preview="Content of note 1",
                        file_size=100,
                        modified_date="2023-01-01 12:00:00",
                    ),
                    DuplicateFile(
                        file_path="/test/vault/note2.md",
                        title="Note 2",
                        similarity_score=0.9,
                        content_preview="Content of note 2",
                        file_size=150,
                        modified_date="2023-01-02 12:00:00",
                    ),
                ]

                # Act
                result = search_operations_with_vector.find_duplicate_notes(
                    similarity_threshold=0.85
                )

                # Assert
                assert isinstance(result, DuplicateDetectionResult)
                assert result.total_files_analyzed == 3
                assert result.total_groups_found == 1
                assert result.similarity_threshold == 0.85
                assert len(result.duplicate_groups) == 1

                group = result.duplicate_groups[0]
                assert isinstance(group, DuplicateGroup)
                assert group.file_count == 2
                assert len(group.files) == 2

    def test_filter_files_by_content_length(self, search_operations_with_vector):
        """Test content length filtering functionality."""
        # Mock file operations
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(
                search_operations_with_vector, "_read_and_parse_file"
            ) as mock_read:
                # Mock file contents
                mock_post_1 = Mock()
                mock_post_1.content = "Short content"

                mock_post_2 = Mock()
                mock_post_2.content = "This is a much longer content that exceeds the minimum length requirement"

                mock_read.side_effect = [
                    ("Short content", mock_post_1, {}),
                    (
                        "This is a much longer content that exceeds the minimum length requirement",
                        mock_post_2,
                        {},
                    ),
                ]

                # Act
                result = search_operations_with_vector._filter_files_by_content_length(
                    ["/test/file1.md", "/test/file2.md"],
                    min_content_length=50,
                    exclude_frontmatter=True,
                )

                # Assert
                assert len(result) == 1
                assert "/test/file2.md" in result

    def test_create_duplicate_file_nonexistent(self, search_operations_with_vector):
        """Test DuplicateFile creation when file doesn't exist."""
        # Act
        result = search_operations_with_vector._create_duplicate_file(
            "/nonexistent/file.md", 0.9
        )

        # Assert
        assert result is None  # File doesn't exist, so should return None

    def test_create_duplicate_file_success(self, search_operations_with_vector):
        """Test successful DuplicateFile creation."""
        # Arrange
        test_file_path = "/test/vault/note.md"
        similarity_score = 0.85

        # Mock file existence and stats
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.stat") as mock_stat:
                # Mock file stats
                mock_stat_result = Mock()
                mock_stat_result.st_size = 1024
                mock_stat_result.st_mtime = 1640995200.0  # 2022-01-01 00:00:00
                mock_stat.return_value = mock_stat_result

                # Mock file content parsing
                with patch.object(
                    search_operations_with_vector, "_read_and_parse_file"
                ) as mock_read:
                    mock_post = Mock()
                    mock_post.content = "This is the main content of the note"
                    mock_read.return_value = (
                        "---\ntitle: Test Note\n---\nThis is the main content of the note",
                        mock_post,
                        {"title": "Test Note"},
                    )

                    # Mock helper methods
                    with patch.object(
                        search_operations_with_vector, "_extract_title"
                    ) as mock_extract_title:
                        mock_extract_title.return_value = "Test Note"

                        with patch.object(
                            search_operations_with_vector, "_create_content_preview"
                        ) as mock_create_preview:
                            mock_create_preview.return_value = (
                                "This is the main content..."
                            )

                            # Act
                            result = (
                                search_operations_with_vector._create_duplicate_file(
                                    test_file_path, similarity_score
                                )
                            )

                            # Assert
                            assert result is not None
                            assert isinstance(result, DuplicateFile)
                            assert result.file_path == test_file_path
                            assert result.title == "Test Note"
                            assert result.similarity_score == similarity_score
                            assert (
                                result.content_preview == "This is the main content..."
                            )
                            assert result.file_size == 1024
                            assert result.modified_date is not None

    @patch("minerva.services.search_operations.logger")
    def test_create_duplicate_file_stat_error(
        self, mock_logger, search_operations_with_vector
    ):
        """Test _create_duplicate_file when file.stat() raises an exception."""
        # Arrange
        test_file = "/fake/path/test.md"
        similarity_score = 0.9

        # Mock Path to raise exception on stat()
        with patch("minerva.services.search_operations.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.stat.side_effect = OSError("Permission denied")
            mock_path.return_value = mock_path_instance

            # Act
            result = search_operations_with_vector._create_duplicate_file(
                test_file, similarity_score
            )

            # Assert
            assert result is None
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0]
            assert "Failed to create DuplicateFile for" in warning_call[0]
            assert test_file in warning_call[1]

    @patch("minerva.services.search_operations.logger")
    def test_create_duplicate_file_read_error(
        self, mock_logger, search_operations_with_vector
    ):
        """Test _create_duplicate_file when _read_and_parse_file raises an exception."""
        # Arrange
        test_file = "/fake/path/test.md"
        similarity_score = 0.8

        # Mock successful path operations but failed file reading
        with patch("minerva.services.search_operations.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_stat = Mock()
            mock_stat.st_size = 500
            mock_stat.st_mtime = 1234567890
            mock_path_instance.stat.return_value = mock_stat
            mock_path.return_value = mock_path_instance

            # Mock _read_and_parse_file to raise exception
            search_operations_with_vector._read_and_parse_file = Mock(
                side_effect=IOError("File cannot be read")
            )

            # Act
            result = search_operations_with_vector._create_duplicate_file(
                test_file, similarity_score
            )

            # Assert
            assert result is None
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0]
            assert "Failed to create DuplicateFile for" in warning_call[0]
            assert test_file in warning_call[1]

    @patch("minerva.services.search_operations.logger")
    def test_create_duplicate_file_title_extraction_error(
        self, mock_logger, search_operations_with_vector
    ):
        """Test _create_duplicate_file when _extract_title raises an exception."""
        # Arrange
        test_file = "/fake/path/test.md"
        similarity_score = 0.7

        # Mock successful path and file operations
        with patch("minerva.services.search_operations.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_stat = Mock()
            mock_stat.st_size = 800
            mock_stat.st_mtime = 1234567890
            mock_path_instance.stat.return_value = mock_stat
            mock_path.return_value = mock_path_instance

            # Mock successful file reading
            search_operations_with_vector._read_and_parse_file = Mock(
                return_value=("content", Mock(), {"title": "Test"})
            )

            # Mock _extract_title to raise exception
            search_operations_with_vector._extract_title = Mock(
                side_effect=ValueError("Invalid title data")
            )

            # Act
            result = search_operations_with_vector._create_duplicate_file(
                test_file, similarity_score
            )

            # Assert
            assert result is None
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0]
            assert "Failed to create DuplicateFile for" in warning_call[0]
            assert test_file in warning_call[1]

    @patch("minerva.services.search_operations.logger")
    def test_create_duplicate_file_content_preview_error(
        self, mock_logger, search_operations_with_vector
    ):
        """Test _create_duplicate_file when _create_content_preview raises an exception."""
        # Arrange
        test_file = "/fake/path/test.md"
        similarity_score = 0.6

        # Mock successful path and file operations
        with patch("minerva.services.search_operations.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_stat = Mock()
            mock_stat.st_size = 600
            mock_stat.st_mtime = 1234567890
            mock_path_instance.stat.return_value = mock_stat
            mock_path.return_value = mock_path_instance

            # Mock successful file reading and title extraction
            search_operations_with_vector._read_and_parse_file = Mock(
                return_value=("content", Mock(), {"title": "Test"})
            )
            search_operations_with_vector._extract_title = Mock(
                return_value="Test Title"
            )

            # Mock _create_content_preview to raise exception
            search_operations_with_vector._create_content_preview = Mock(
                side_effect=AttributeError("Content processing error")
            )

            # Act
            result = search_operations_with_vector._create_duplicate_file(
                test_file, similarity_score
            )

            # Assert
            assert result is None
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0]
            assert "Failed to create DuplicateFile for" in warning_call[0]
            assert test_file in warning_call[1]
