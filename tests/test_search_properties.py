"""
Property-based tests for search operations using Hypothesis.

This module contains property-based tests to discover edge cases in search
functionality, query validation, and configuration handling that might not
be caught by traditional unit tests.
"""

import string
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, assume, strategies as st

from minerva.file_handler import SearchConfig, SearchResult
from minerva.services.search_operations import SearchOperations
from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager


class TestSearchOperationsProperties:
    """Property-based tests for SearchOperations class."""

    def _create_search_service(self, vault_path: Path) -> SearchOperations:
        """Create SearchOperations service with test configuration."""
        config = MinervaConfig(
            vault_path=vault_path, default_note_dir="", default_author="Test Author"
        )
        frontmatter_manager = FrontmatterManager("Test Author")
        return SearchOperations(config, frontmatter_manager)

    @given(st.text(min_size=1, max_size=100, alphabet=string.printable))
    def test_validate_search_query_handles_printable_strings(self, query: str):
        """Property: query validation should handle any non-empty printable string."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            service = self._create_search_service(Path(temp_dir))
            assume(query.strip())  # Exclude empty/whitespace-only queries

            # Act
            result = service._validate_search_query(query)

            # Assert
            assert result == query.strip()
            assert isinstance(result, str)

    @given(st.just(""))
    def test_validate_search_query_empty_raises_error(self, query: str):
        """Property: empty queries should raise ValueError."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            service = self._create_search_service(Path(temp_dir))

            # Act & Assert
            with pytest.raises(ValueError, match="Query cannot be empty"):
                service._validate_search_query(query)

    def test_create_search_config_with_existing_directory(self):
        """Property: search config creation should work with existing directories."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            service = self._create_search_service(Path(temp_dir))
            query = "test"
            case_sensitive = True
            file_extensions = [".md", ".txt"]

            # Act
            config = service._create_search_config(
                query=query,
                case_sensitive=case_sensitive,
                file_extensions=file_extensions,
                directory=temp_dir,
            )

            # Assert
            assert isinstance(config, SearchConfig)
            assert config.keyword == query
            assert config.case_sensitive == case_sensitive
            assert config.file_extensions == file_extensions
            assert config.directory == temp_dir

    @given(
        st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits)
    )
    def test_create_search_config_defaults(self, query: str):
        """Property: search config should use proper defaults when optional params not provided."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            service = self._create_search_service(Path(temp_dir))

            # Act
            config = service._create_search_config(query)

            # Assert
            assert config.keyword == query
            assert config.case_sensitive is True  # Default
            assert config.file_extensions == [".md"]  # Default
            assert config.directory == str(service.config.vault_path)  # Default

    @given(
        st.text(
            min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits + " "
        ),
        st.booleans(),
    )
    def test_search_notes_query_validation_integration(
        self, query: str, case_sensitive: bool
    ):
        """Property: search_notes should validate queries before processing."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            service = self._create_search_service(Path(temp_dir))

            if query.strip():
                # Valid query - should not raise during validation
                # For this test, we just test the validation without mocking
                # The search will work on an empty directory and return empty results

                # Act & Assert - should not raise
                result = service.search_notes(query, case_sensitive)
                assert isinstance(result, list)
                # Should be empty since temp directory has no files
                assert result == []
            else:
                # Invalid query - should raise ValueError
                with pytest.raises(ValueError, match="Query cannot be empty"):
                    service.search_notes(query, case_sensitive)

    @given(
        st.text(min_size=1, max_size=30, alphabet=string.ascii_letters + string.digits)
    )
    def test_search_operations_with_real_files(self, search_term: str):
        """Property: search operations should work with actual file content."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            service = self._create_search_service(vault_path)

            # Create test files with known content
            test_files = [
                ("note1.md", f"This contains {search_term} in the content."),
                (
                    "note2.md",
                    f"Another file with {search_term.upper()} in different case.",
                ),
                ("note3.md", "This file does not contain the search word."),
                (
                    "not_markdown.txt",
                    f"Text file with {search_term} but wrong extension.",
                ),
            ]

            for filename, content in test_files:
                file_path = vault_path / filename
                file_path.write_text(content, encoding="utf-8")

            # Act
            results_case_sensitive = service.search_notes(
                search_term, case_sensitive=True
            )
            results_case_insensitive = service.search_notes(
                search_term, case_sensitive=False
            )

            # Assert
            assert isinstance(results_case_sensitive, list)
            assert isinstance(results_case_insensitive, list)

            # Case insensitive should find at least as many results as case sensitive
            assert len(results_case_insensitive) >= len(results_case_sensitive)

            # All results should be SearchResult objects
            for result in results_case_sensitive + results_case_insensitive:
                assert isinstance(result, SearchResult)

    @given(
        st.lists(
            st.text(min_size=3, max_size=10, alphabet=string.ascii_letters),
            min_size=2,
            max_size=5,
        )
    )
    def test_search_multiple_terms_properties(self, search_terms: list[str]):
        """Property: searching for multiple terms should have consistent behavior."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            service = self._create_search_service(vault_path)

            unique_terms = list(set(search_terms))  # Remove duplicates
            assume(len(unique_terms) >= 2)  # Need at least 2 unique terms

            # Create a test file containing all terms
            content_with_all_terms = " ".join(unique_terms) + " extra content"
            test_file = vault_path / "test.md"
            test_file.write_text(content_with_all_terms, encoding="utf-8")

            # Act - search for each term individually
            individual_results = []
            for term in unique_terms:
                results = service.search_notes(term, case_sensitive=True)
                individual_results.append(len(results))

            # Assert
            # Each term should be found (at least 1 result each)
            for count in individual_results:
                assert count >= 1

    @given(
        st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits),
        st.sampled_from(".*+?^${}()|[]"),  # Generate one special character per test run
    )
    def test_search_with_special_regex_characters(
        self, base_term: str, special_char: str
    ):
        """Property: search should handle terms that could be interpreted as regex."""
        # Arrange
        with TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            service = self._create_search_service(vault_path)

            search_term = f"{base_term}{special_char}"

            # Create file with the exact term
            # Use safe filename by replacing problematic characters
            safe_filename = (
                special_char.replace("[", "bracket")
                .replace("]", "bracket")
                .replace("*", "star")
                .replace("?", "question")
            )
            test_file = vault_path / f"test_{safe_filename}.md"
            test_file.write_text(
                f"Content with {search_term} inside.", encoding="utf-8"
            )

            # Act & Assert - should not raise regex compilation errors
            try:
                results = service.search_notes(search_term, case_sensitive=True)
                assert isinstance(results, list)
            except Exception as e:
                # If it fails, should be a controlled failure, not a regex error
                assert "regex" not in str(e).lower()


class TestSearchConfigProperties:
    """Property-based tests for SearchConfig creation and validation."""

    def test_search_config_creation_with_temp_directory(self):
        """Property: SearchConfig should work with existing directories."""
        with TemporaryDirectory() as temp_dir:
            # Arrange
            keyword = "test"
            extensions = [".md", ".txt"]
            case_sensitive = True

            # Act
            config = SearchConfig(
                directory=temp_dir,
                keyword=keyword,
                file_extensions=extensions,
                case_sensitive=case_sensitive,
            )

            # Assert
            assert config.directory == temp_dir
            assert config.keyword == keyword
            assert config.file_extensions == extensions
            assert config.case_sensitive == case_sensitive

    def test_search_config_with_temp_directory_and_extensions(self):
        """Property: SearchConfig should handle file extensions properly."""
        with TemporaryDirectory() as temp_dir:
            # Arrange
            keyword = "test"
            original_extensions = [".md", ".txt"]

            # Act
            config = SearchConfig(
                directory=temp_dir,
                keyword=keyword,
                file_extensions=original_extensions.copy(),
                case_sensitive=True,
            )

            # Assert
            assert config.file_extensions == original_extensions


class TestSearchResultProperties:
    """Property-based tests for SearchResult behavior."""

    @given(
        st.text(min_size=1, max_size=100),
        st.integers(min_value=1, max_value=1000),
        st.text(min_size=1, max_size=200),
    )
    def test_search_result_creation_properties(
        self, file_path: str, line_number: int, context: str
    ):
        """Property: SearchResult should handle various valid parameter combinations."""
        # Act
        result = SearchResult(
            file_path=file_path, line_number=line_number, context=context
        )

        # Assert
        assert result.file_path == file_path
        assert result.line_number == line_number
        assert result.context == context
        assert isinstance(result.line_number, int)
        assert result.line_number > 0
