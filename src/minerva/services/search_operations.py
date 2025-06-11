"""
Search operations service module.

This module provides search functionality for finding content within notes
in the Obsidian vault using various search criteria and configurations.
"""

import logging
from pathlib import Path
from typing import List

from minerva.error_handler import log_performance
from minerva.file_handler import (
    SearchConfig,
    SearchResult,
    search_keyword_in_files,
)
from minerva.services.core.base_service import BaseService

logger = logging.getLogger(__name__)


class SearchOperations(BaseService):
    """
    Service class for search operations.

    This class handles searching for content within notes in the Obsidian vault,
    providing flexible search configurations and result handling using the core
    infrastructure utilities.
    """

    def _validate_search_query(self, query: str) -> str:
        """
        Validate and normalize search query.

        Args:
            query: The search query to validate

        Returns:
            str: Validated and normalized query

        Raises:
            ValueError: If query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        return query.strip()

    def _create_search_config(
        self,
        query: str,
        case_sensitive: bool = True,
        file_extensions: List[str] | None = None,
        directory: str | None = None,
    ) -> SearchConfig:
        """
        Create search configuration based on parameters.

        Args:
            query: The keyword to search for
            case_sensitive: Whether the search should be case sensitive
            file_extensions: List of file extensions to search (defaults to [".md"])
            directory: Directory to search in (defaults to vault root)

        Returns:
            SearchConfig: Configured search parameters
        """
        effective_directory = directory or str(self.config.vault_path)
        effective_extensions = file_extensions or [".md"]

        return SearchConfig(
            directory=effective_directory,
            keyword=query,
            file_extensions=effective_extensions,
            case_sensitive=case_sensitive,
        )

    @log_performance(threshold_ms=1000)
    def search_notes(
        self, query: str, case_sensitive: bool = True
    ) -> List[SearchResult]:
        """
        Search for a keyword in all files in the Obsidian vault.

        Args:
            query: The keyword to search for
            case_sensitive: Whether the search should be case sensitive

        Returns:
            List[SearchResult]: A list of search results

        Raises:
            ValueError: If query is empty or invalid
        """
        self._log_operation_start(
            "search_notes", query=query, case_sensitive=case_sensitive
        )

        # Validate query
        validated_query = self._validate_search_query(query)

        # Create search configuration
        search_config = self._create_search_config(
            validated_query, case_sensitive=case_sensitive
        )

        # Perform search
        matching_files = search_keyword_in_files(search_config)

        logger.info(
            "Found %s files matching the query: %s",
            len(matching_files),
            validated_query,
        )

        self._log_operation_success("search_notes", matching_files)
        return matching_files

    def search_notes_in_directory(
        self,
        query: str,
        directory: str,
        case_sensitive: bool = True,
        file_extensions: List[str] | None = None,
    ) -> List[SearchResult]:
        """
        Search for a keyword in files within a specific directory.

        Args:
            query: The keyword to search for
            directory: The directory to search in
            case_sensitive: Whether the search should be case sensitive
            file_extensions: List of file extensions to search

        Returns:
            List[SearchResult]: A list of search results

        Raises:
            ValueError: If query is empty or directory is invalid
        """
        self._log_operation_start(
            "search_notes_in_directory",
            query=query,
            directory=directory,
            case_sensitive=case_sensitive,
            file_extensions=file_extensions,
        )

        # Validate query
        validated_query = self._validate_search_query(query)

        # Validate directory existence
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Create search configuration
        search_config = self._create_search_config(
            validated_query,
            case_sensitive=case_sensitive,
            file_extensions=file_extensions,
            directory=directory,
        )

        # Perform search
        matching_files = search_keyword_in_files(search_config)

        logger.info(
            "Found %s files matching the query '%s' in directory '%s'",
            len(matching_files),
            validated_query,
            directory,
        )

        self._log_operation_success("search_notes_in_directory", matching_files)
        return matching_files
