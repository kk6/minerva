"""
Search operations service module.

This module provides search functionality for finding content within notes
in the Obsidian vault using various search criteria and configurations,
including semantic search using vector embeddings.
"""

import logging
from pathlib import Path
from typing import List, Optional
import frontmatter

from minerva.error_handler import log_performance
from minerva.file_handler import (
    SearchConfig,
    SearchResult,
    SemanticSearchResult,
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

    @log_performance(threshold_ms=2000)
    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None,
        directory: Optional[str] = None,
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search using vector embeddings.

        Args:
            query: Natural language query to search for
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            directory: Directory to search in (defaults to vault root)

        Returns:
            List[SemanticSearchResult]: List of semantic search results

        Raises:
            ValueError: If query is empty or parameters are invalid
            ImportError: If vector search dependencies are not available
            RuntimeError: If vector search is not enabled in configuration
        """
        self._log_operation_start(
            "semantic_search",
            query=query,
            limit=limit,
            threshold=threshold,
            directory=directory,
        )

        # Check if vector search is enabled
        if not self.config.vector_search_enabled:
            raise RuntimeError(
                "Vector search is not enabled. Set VECTOR_SEARCH_ENABLED=true in configuration."
            )

        # Check if vector database path is configured
        if not self.config.vector_db_path:
            raise RuntimeError("Vector database path is not configured.")

        # Validate query
        validated_query = self._validate_search_query(query)

        # Validate parameters
        if limit <= 0:
            raise ValueError("Limit must be positive")
        if threshold is not None and not (0.0 <= threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")

        try:
            # Import vector search components (lazy loading)
            from minerva.vector.embeddings import SentenceTransformerProvider
            from minerva.vector.searcher import VectorSearcher

            # Initialize embedding provider and searcher
            embedding_provider = SentenceTransformerProvider(
                self.config.embedding_model
            )
            searcher = VectorSearcher(self.config.vector_db_path)

            # Generate query embedding
            query_embedding = embedding_provider.embed(validated_query)

            # Ensure query_embedding is 1D (take first row if 2D)
            if query_embedding.ndim == 2:
                query_embedding = query_embedding[0]

            # Perform vector search
            search_results = searcher.search_similar(
                query_embedding, k=limit, threshold=threshold
            )

            # Convert to semantic search results with content preview
            semantic_results = []
            for file_path, similarity_score in search_results:
                semantic_result = self._create_semantic_search_result(
                    file_path, similarity_score, directory
                )
                if semantic_result:
                    semantic_results.append(semantic_result)

            # Close connections
            searcher.close()

            logger.info(
                "Semantic search found %d results for query: %s",
                len(semantic_results),
                validated_query,
            )

            self._log_operation_success("semantic_search", semantic_results)
            return semantic_results

        except ImportError as e:
            logger.error("Vector search dependencies not available: %s", e)
            raise ImportError(
                "Vector search requires additional dependencies. "
                "Install with: pip install sentence-transformers duckdb"
            ) from e
        except Exception as e:
            logger.error("Semantic search failed: %s", e)
            raise

    def _create_semantic_search_result(
        self, file_path: str, similarity_score: float, target_directory: Optional[str]
    ) -> Optional[SemanticSearchResult]:
        """
        Create a SemanticSearchResult from a file path and similarity score.

        Args:
            file_path: Path to the file
            similarity_score: Similarity score from vector search
            target_directory: Target directory filter (if any)

        Returns:
            SemanticSearchResult or None if file cannot be processed
        """
        try:
            path = Path(file_path)

            # Apply directory filter if specified
            if target_directory and not path.is_relative_to(Path(target_directory)):
                return None

            # Check if file exists
            if not path.exists():
                logger.warning("File not found: %s", file_path)
                return None

            # Read and parse file content
            content, post, metadata = self._read_and_parse_file(path)

            # Extract title and aliases
            title = self._extract_title(metadata, path)
            aliases = self._extract_aliases(metadata)

            # Create content preview
            content_preview = self._create_content_preview(post, content)

            return SemanticSearchResult(
                file_path=str(path),
                title=title,
                content_preview=content_preview,
                similarity_score=similarity_score,
                metadata=metadata,
                aliases=aliases if aliases else None,
            )

        except Exception as e:
            logger.warning(
                "Failed to create semantic search result for %s: %s", file_path, e
            )
            return None

    def _read_and_parse_file(self, path: Path) -> tuple[str, object, dict]:
        """Read file content and parse frontmatter."""
        # Check file size to prevent memory exhaustion
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            logger.warning(
                "File too large for processing: %s (%d bytes)", path, file_size
            )
            raise ValueError(f"File too large: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        post = frontmatter.loads(content)
        metadata = dict(post.metadata) if post.metadata else {}

        return content, post, metadata

    def _extract_title(self, metadata: dict, path: Path) -> str:
        """Extract title from metadata or generate from filename."""
        title_value = metadata.get("title")
        title = title_value if isinstance(title_value, str) else None
        if not title:
            title = path.stem.replace("_", " ").replace("-", " ").title()
        return title

    def _extract_aliases(self, metadata: dict) -> list[str]:
        """Extract aliases from metadata."""
        aliases = []
        if "aliases" in metadata:
            alias_value = metadata["aliases"]
            if isinstance(alias_value, list):
                aliases = [str(alias) for alias in alias_value if alias]
            elif isinstance(alias_value, str):
                aliases = [alias_value] if alias_value else []
        return aliases

    def _create_content_preview(self, post: object, content: str) -> str:
        """Create content preview from post or raw content."""
        main_content = post.content if hasattr(post, "content") else content
        if hasattr(post, "metadata") and post.metadata:
            # Remove frontmatter from content preview
            lines = main_content.split("\n")
            content_preview = " ".join(lines).strip()[:200]
        else:
            content_preview = main_content.strip()[:200]

        if len(content_preview) > 197:  # Account for "..."
            content_preview = content_preview[:197] + "..."

        return content_preview

    def get_indexed_files_count(self) -> int:
        """
        Get the number of files that have been indexed for vector search.

        Returns:
            int: Number of indexed files

        Raises:
            RuntimeError: If vector search is not enabled
            ImportError: If vector search dependencies are not available
        """
        if not self.config.vector_search_enabled:
            raise RuntimeError("Vector search is not enabled in configuration")

        if not self.config.vector_db_path:
            raise RuntimeError("Vector database path is not configured")

        try:
            from minerva.vector.searcher import VectorSearcher

            searcher = VectorSearcher(self.config.vector_db_path)
            indexed_files = searcher.get_indexed_files()
            searcher.close()

            return len(indexed_files)

        except ImportError as e:
            logger.error("Vector search dependencies not available: %s", e)
            raise ImportError(
                "Vector search requires additional dependencies. "
                "Install with: pip install sentence-transformers duckdb"
            ) from e

    @log_performance(threshold_ms=1000)
    def find_similar_notes(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
        limit: int = 5,
        exclude_self: bool = True,
    ) -> List[SemanticSearchResult]:
        """
        Find notes that are similar to a given note using vector similarity.

        Args:
            filename: Name of the reference file (provide this OR filepath)
            filepath: Full path to the reference file (provide this OR filename)
            default_path: Subfolder to look for the file (optional)
            limit: Maximum number of similar notes to return
            exclude_self: Whether to exclude the reference file from results

        Returns:
            List of semantic search results ordered by similarity

        Raises:
            RuntimeError: If vector search is not enabled
            ValueError: If neither filename nor filepath is provided or if file doesn't exist
            ImportError: If vector search dependencies are not available
        """
        self._log_operation_start(
            "find_similar_notes", filename=filename, filepath=filepath, limit=limit
        )

        if not self.config.vector_search_enabled:
            error = RuntimeError("Vector search is not enabled in configuration")
            self._log_operation_error("find_similar_notes", error)
            raise error

        # Validate input parameters
        if not filename and not filepath:
            param_error = ValueError("Either filename or filepath must be provided")
            self._log_operation_error("find_similar_notes", param_error)
            raise param_error

        # Validate limit parameter
        if limit <= 0:
            limit_error = ValueError("Limit must be positive")
            self._log_operation_error("find_similar_notes", limit_error)
            raise limit_error

        try:
            from minerva.vector.searcher import VectorSearcher
            from minerva.services.core.file_operations import resolve_note_file

            # Resolve the reference file path
            reference_file_path = resolve_note_file(
                self.config, filename, filepath, default_path
            )

            if not reference_file_path.exists():
                file_error = FileNotFoundError(
                    f"Reference file does not exist: {reference_file_path}"
                )
                self._log_operation_error("find_similar_notes", file_error)
                raise file_error

            # Initialize vector searcher
            if not self.config.vector_db_path:
                raise RuntimeError("Vector database path is not configured")
            searcher = VectorSearcher(self.config.vector_db_path)

            # Find similar files using vector similarity
            similar_files = searcher.find_similar_to_file(
                str(reference_file_path), k=limit, exclude_self=exclude_self
            )

            # Convert to semantic search results
            semantic_results = []
            for file_path, similarity_score in similar_files:
                semantic_result = self._create_semantic_search_result(
                    file_path, similarity_score, None
                )
                if semantic_result:
                    semantic_results.append(semantic_result)

            # Close connections
            searcher.close()

            logger.info(
                "Found %d similar notes to %s",
                len(semantic_results),
                reference_file_path,
            )

            self._log_operation_success("find_similar_notes", semantic_results)
            return semantic_results

        except ImportError as e:
            logger.error("Vector search dependencies not available: %s", e)
            import_error = ImportError(
                "Vector search requires additional dependencies. "
                "Install with: pip install sentence-transformers duckdb"
            )
            self._log_operation_error("find_similar_notes", import_error)
            raise import_error from e

        except Exception as e:
            logger.error("Find similar notes failed: %s", e)
            self._log_operation_error("find_similar_notes", e)
            raise
