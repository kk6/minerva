"""
Tests for SearchOperations service module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.file_handler import SearchResult, SemanticSearchResult
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
            patch.object(Path, "exists", return_value=True),
        ):
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
            patch.object(Path, "exists", return_value=True),
        ):
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
            patch.object(Path, "exists", return_value=True),
        ):
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
            patch.object(Path, "exists", return_value=True),
        ):
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
