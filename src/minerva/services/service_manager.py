"""
Service manager facade for Minerva application.

This module provides a unified interface for all service operations, serving as
a facade that coordinates between different specialized service modules while
maintaining backward compatibility with the existing API.
"""

import logging
from pathlib import Path
from typing import ParamSpec, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from minerva.vector.indexer import VectorIndexer
    from minerva.vector.embeddings import SentenceTransformerProvider

from minerva.config import MinervaConfig
from minerva.error_handler import MinervaErrorHandler
from minerva.file_handler import SearchResult
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.alias_operations import AliasOperations
from minerva.services.core.file_operations import (
    build_file_path,
    assemble_complete_note,
)
from minerva.services.note_operations import NoteOperations
from minerva.services.search_operations import SearchOperations
from minerva.services.tag_operations import TagOperations

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for decorator compatibility
P = ParamSpec("P")
R = TypeVar("R")


class ServiceManager:
    """
    Service manager facade for Minerva note operations.

    This class provides a unified interface for all service operations,
    coordinating between specialized service modules while maintaining
    backward compatibility. It replaces the monolithic MinervaService
    with a cleaner, more modular approach.
    """

    def __init__(
        self,
        config: MinervaConfig,
        frontmatter_manager: FrontmatterManager,
    ):
        """
        Initialize ServiceManager with dependencies.

        Args:
            config: Configuration instance containing paths and settings
            frontmatter_manager: Manager for frontmatter operations
        """
        self.config = config
        self.frontmatter_manager = frontmatter_manager
        self.error_handler = MinervaErrorHandler(vault_path=config.vault_path)

        # Initialize specialized service modules
        self._note_operations = NoteOperations(config, frontmatter_manager)
        self._tag_operations = TagOperations(config, frontmatter_manager)
        self._alias_operations = AliasOperations(config, frontmatter_manager)
        self._search_operations = SearchOperations(config, frontmatter_manager)

    # Property-based access to specialized services
    @property
    def note_operations(self) -> NoteOperations:
        """Access to note operations service."""
        return self._note_operations

    @property
    def tag_operations(self) -> TagOperations:
        """Access to tag operations service."""
        return self._tag_operations

    @property
    def alias_operations(self) -> AliasOperations:
        """Access to alias operations service."""
        return self._alias_operations

    @property
    def search_operations(self) -> SearchOperations:
        """Access to search operations service."""
        return self._search_operations

    # Utility methods that wrap imported functions for compatibility
    def _build_file_path(
        self, filename: str, default_path: str | None = None
    ) -> tuple[Path, str]:
        """
        Build file path for note operations.

        This is a wrapper around the build_file_path function from file_operations
        to maintain compatibility with existing code and tests.

        Args:
            filename: The name of the file to build path for
            default_path: The default directory to save the file

        Returns:
            tuple: (full_dir_path, base_filename)
        """
        return build_file_path(self.config, filename, default_path)

    def _assemble_complete_note(
        self,
        text: str,
        filename: str,
        author: str | None = None,
        default_path: str | None = None,
        is_new_note: bool = True,
    ) -> tuple[Path, str, str]:
        """
        Assemble a complete note by combining file path resolution and content preparation.

        This is a wrapper around the assemble_complete_note function from file_operations
        to maintain compatibility with existing code and tests.

        Args:
            text: The content to write to the file
            filename: The name of the file to write
            author: The author name to add to the frontmatter
            default_path: The default directory to save the file
            is_new_note: Whether this is a new note (True) or an update to an existing note (False)

        Returns:
            tuple: (full_dir_path, base_filename, prepared_content)
        """
        return assemble_complete_note(
            self.config,
            self.frontmatter_manager,
            text,
            filename,
            author,
            default_path,
            is_new_note,
        )

    # Note operations delegation methods
    def create_note(
        self,
        text: str,
        filename: str,
        author: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Create a new note in the Obsidian vault.

        Args:
            text: The content to write to the file
            filename: The name of the file to write
            author: The author name to add to the frontmatter
            default_path: The default directory to save the file

        Returns:
            Path: The path to the created file

        Raises:
            FileExistsError: If the file already exists
        """
        return self.note_operations.create_note(text, filename, author, default_path)

    def edit_note(
        self,
        text: str,
        filename: str,
        author: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Edit an existing note in the Obsidian vault.

        Args:
            text: The new content to write to the file
            filename: The name of the file to edit
            author: The author name to add to the frontmatter
            default_path: The default directory to save the file

        Returns:
            Path: The path to the edited file

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        return self.note_operations.edit_note(text, filename, author, default_path)

    def read_note(self, filepath: str) -> str:
        """
        Read a note from a file in the Obsidian vault.

        Args:
            filepath: The full path of the file to read

        Returns:
            str: The content of the file
        """
        return self.note_operations.read_note(filepath)

    def get_note_delete_confirmation(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> dict[str, str]:
        """
        Get confirmation for deleting a note from the Obsidian vault.

        Args:
            filename: The name of the file to delete
            filepath: The full path of the file to delete
            default_path: The default directory to look for the file

        Returns:
            dict: Object with file path and confirmation message

        Raises:
            ValueError: If neither filename nor filepath is provided
            FileNotFoundError: If the file doesn't exist
        """
        return self.note_operations.get_note_delete_confirmation(
            filename, filepath, default_path
        )

    def perform_note_delete(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Perform the deletion of a note from the Obsidian vault.

        Args:
            filename: The name of the file to delete
            filepath: The full path of the file to delete
            default_path: The default directory to look for the file

        Returns:
            Path: The path to the deleted file

        Raises:
            ValueError: If neither filename nor filepath is provided
            FileNotFoundError: If the file doesn't exist
        """
        return self.note_operations.perform_note_delete(
            filename, filepath, default_path
        )

    # Search operations delegation methods
    def search_notes(
        self, query: str, case_sensitive: bool = True
    ) -> list[SearchResult]:
        """
        Search for a keyword in all files in the Obsidian vault.

        Args:
            query: The keyword to search for
            case_sensitive: Whether the search should be case sensitive

        Returns:
            list[SearchResult]: A list of search results
        """
        return self.search_operations.search_notes(query, case_sensitive)

    # Tag operations delegation methods
    def add_tag(
        self,
        tag: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Add a specified tag to an existing note in the Obsidian vault.

        Args:
            tag: The tag to add to the note
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path

        Returns:
            Path: The path of the modified note file

        Raises:
            ValueError: If the provided tag is invalid
            FileNotFoundError: If the specified note file does not exist
        """
        return self.tag_operations.add_tag(tag, filename, filepath, default_path)

    def remove_tag(
        self,
        tag: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Remove a specified tag from an existing note in the Obsidian vault.

        Args:
            tag: The tag to remove from the note
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path

        Returns:
            Path: The path of the modified note file

        Raises:
            FileNotFoundError: If the specified note file does not exist
        """
        return self.tag_operations.remove_tag(tag, filename, filepath, default_path)

    def get_tags(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> list[str]:
        """
        Retrieve the list of tags from a specific note's frontmatter.

        Args:
            filename: The name of the note file
            filepath: The full, absolute path to the note file
            default_path: The default directory path

        Returns:
            list[str]: A list of tag strings
        """
        return self.tag_operations.get_tags(filename, filepath, default_path)

    def rename_tag(
        self,
        old_tag: str,
        new_tag: str,
        directory: str | None = None,
    ) -> list[Path]:
        """
        Rename a tag in all notes within a specified directory (or the entire vault).

        Args:
            old_tag: The current tag string to be replaced
            new_tag: The new tag string to replace the old tag
            directory: Optional path to a directory within the vault

        Returns:
            list[Path]: A list of Path objects for each note file that was modified

        Raises:
            ValueError: If new_tag is invalid
            FileNotFoundError: If the specified directory does not exist
        """
        return self.tag_operations.rename_tag(old_tag, new_tag, directory)

    def list_all_tags(self, directory: str | None = None) -> list[str]:
        """
        List all unique, normalized tags from all Markdown files within a specified directory.

        Args:
            directory: Optional path to a directory within the vault

        Returns:
            list[str]: A sorted list of unique, normalized tag strings

        Raises:
            FileNotFoundError: If the specified directory does not exist
        """
        return self.tag_operations.list_all_tags(directory)

    def find_notes_with_tag(self, tag: str, directory: str | None = None) -> list[str]:
        """
        Find all notes that contain a specific tag.

        Args:
            tag: The tag to search for
            directory: Optional path to a directory within the vault

        Returns:
            list[str]: A list of string paths for each note file containing the specified tag

        Raises:
            FileNotFoundError: If the specified directory does not exist
        """
        return self.tag_operations.find_notes_with_tag(tag, directory)

    # Alias operations delegation methods
    def add_alias(
        self,
        alias: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
        allow_conflicts: bool = False,
    ) -> Path:
        """
        Add an alias to an existing note in the Obsidian vault.

        Args:
            alias: The alias to add to the note
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path
            allow_conflicts: Whether to allow conflicting aliases

        Returns:
            Path: The path of the modified note file

        Raises:
            ValueError: If the alias is invalid or conflicts exist
            FileNotFoundError: If the specified note file does not exist
        """
        return self.alias_operations.add_alias(
            alias, filename, filepath, default_path, allow_conflicts
        )

    def remove_alias(
        self,
        alias: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Remove an alias from an existing note in the Obsidian vault.

        Args:
            alias: The alias to remove from the note
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path

        Returns:
            Path: The path of the modified note file

        Raises:
            FileNotFoundError: If the specified note file does not exist
        """
        return self.alias_operations.remove_alias(
            alias, filename, filepath, default_path
        )

    def get_aliases(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> list[str]:
        """
        Retrieve the list of aliases from a specific note's frontmatter.

        Args:
            filename: The name of the note file
            filepath: The full, absolute path to the note file
            default_path: The default directory path

        Returns:
            list[str]: A list of alias strings
        """
        return self.alias_operations.get_aliases(filename, filepath, default_path)

    def search_by_alias(self, alias: str, directory: str | None = None) -> list[str]:
        """
        Find notes that have a specific alias.

        Args:
            alias: The alias to search for
            directory: Optional path to a directory within the vault

        Returns:
            list[str]: A list of file paths that contain the specified alias

        Raises:
            FileNotFoundError: If the specified directory does not exist
        """
        return self.alias_operations.search_by_alias(alias, directory)

    # Vector search operations
    def _prepare_vector_indexing(
        self,
        indexer: "VectorIndexer",
        embedding_provider: "SentenceTransformerProvider",
        files_to_process: list[str],
        force_rebuild: bool,
    ) -> None:
        """Prepare vector indexing by initializing schema."""
        if not files_to_process:
            return

        # Get dimension from first embedding
        with open(files_to_process[0], "r", encoding="utf-8") as f:
            sample_content = f.read()[:500]  # Sample content for dimension detection
        sample_embedding = embedding_provider.embed(sample_content)

        # If force_rebuild is True, clear existing data first
        if force_rebuild:
            try:
                conn = indexer._get_connection()
                conn.execute("DROP TABLE IF EXISTS vectors")
                conn.execute("DROP TABLE IF EXISTS indexed_files")
                conn.execute("DROP SEQUENCE IF EXISTS vectors_id_seq")
                logger.info("Cleared existing vector database for rebuild")
            except Exception as e:
                logger.warning("Could not clear existing database: %s", e)

        # Get the actual embedding dimension (shape[1] for 2D array)
        embedding_dim = (
            sample_embedding.shape[1]
            if sample_embedding.ndim == 2
            else len(sample_embedding)
        )
        indexer.initialize_schema(embedding_dim)

    def build_vector_index(
        self,
        directory: str | None = None,
        file_pattern: str = "*.md",
        force_rebuild: bool = False,
    ) -> dict[str, int | list[str]]:
        """
        Build or update the vector search index for semantic search.

        Args:
            directory: Specific folder to index (if None, indexes entire vault)
            file_pattern: File pattern to match (default: "*.md")
            force_rebuild: Whether to rebuild existing embeddings (default: False)

        Returns:
            Dict with 'processed' (count), 'skipped' (count), and 'errors' (list) keys

        Raises:
            RuntimeError: If vector search is not enabled
            ImportError: If vector search dependencies are not available

        Note:
            If you encounter dimension mismatch errors, try force_rebuild=True
            to recreate the database with the correct embedding dimensions.
        """
        if not self.config.vector_search_enabled:
            raise RuntimeError("Vector search is not enabled in configuration")

        if not self.config.vector_db_path:
            raise RuntimeError("Vector database path is not configured")

        try:
            import glob
            import os
            from minerva.vector.embeddings import SentenceTransformerProvider
            from minerva.vector.indexer import VectorIndexer

            # Initialize components
            embedding_provider = SentenceTransformerProvider(
                self.config.embedding_model
            )
            indexer = VectorIndexer(self.config.vector_db_path)

            # Determine directory to process
            target_dir = directory or str(self.config.vault_path)

            # Find files to process
            search_pattern = os.path.join(target_dir, "**", file_pattern)
            files_to_process = glob.glob(search_pattern, recursive=True)

            # Initialize tracking
            processed = 0
            skipped = 0
            errors = []

            # Initialize schema (embedding dimension will be determined dynamically)
            try:
                self._prepare_vector_indexing(
                    indexer, embedding_provider, files_to_process, force_rebuild
                )
            except Exception as e:
                logger.error("Failed to initialize schema: %s", e)
                raise

            # Filter files that need updating (incremental indexing)
            if not force_rebuild:
                files_to_update = indexer.get_outdated_files(files_to_process)
                logger.info(
                    "Incremental indexing: %d out of %d files need updates",
                    len(files_to_update),
                    len(files_to_process),
                )
                skipped = len(files_to_process) - len(files_to_update)
                files_to_process = files_to_update
            else:
                logger.info(
                    "Force rebuild: processing all %d files", len(files_to_process)
                )

            # Process each file that needs updating
            for file_path in files_to_process:
                try:
                    # Read file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Generate embedding
                    embedding = embedding_provider.embed(content)

                    # Store in index
                    indexer.store_embedding(file_path, embedding, content)
                    processed += 1

                    if processed % 5 == 0:  # Log progress every 5 files
                        logger.info("Processed %d files for vector indexing", processed)

                    # Yield control periodically to prevent timeout
                    if processed % 3 == 0:
                        import time

                        time.sleep(0.1)  # Small pause to yield control

                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            # Close connections
            indexer.close()

            logger.info(
                "Vector indexing complete: %d processed, %d skipped, %d errors",
                processed,
                skipped,
                len(errors),
            )

            return {
                "processed": processed,
                "skipped": skipped,
                "errors": errors,
            }

        except ImportError as e:
            logger.error("Vector search dependencies not available: %s", e)
            raise ImportError(
                "Vector search requires additional dependencies. "
                "Install with: pip install sentence-transformers duckdb"
            ) from e

    def get_vector_index_status(self) -> dict[str, int | bool | str]:
        """
        Get information about the current vector search index status.

        Returns:
            Dict with index statistics and availability status

        Raises:
            RuntimeError: If vector search is not enabled
        """
        try:
            if not self.config.vector_search_enabled:
                return {
                    "vector_search_enabled": False,
                    "indexed_files_count": 0,
                    "database_exists": False,
                }

            if not self.config.vector_db_path:
                return {
                    "vector_search_enabled": True,
                    "indexed_files_count": 0,
                    "database_exists": False,
                }

            from minerva.vector.searcher import VectorSearcher

            # Check if database exists
            db_exists = self.config.vector_db_path.exists()

            if not db_exists:
                return {
                    "vector_search_enabled": True,
                    "indexed_files_count": 0,
                    "database_exists": False,
                }

            # Get indexed files count
            searcher = VectorSearcher(self.config.vector_db_path)
            indexed_files = searcher.get_indexed_files()
            searcher.close()

            return {
                "vector_search_enabled": True,
                "indexed_files_count": len(indexed_files),
                "database_exists": True,
            }

        except ImportError:
            return {
                "vector_search_enabled": False,
                "indexed_files_count": 0,
                "database_exists": False,
                "error": "Vector search dependencies not available",
            }


def create_minerva_service() -> ServiceManager:
    """
    Create a ServiceManager instance with default configuration.

    This factory function provides a convenient way to create a fully
    configured ServiceManager instance using environment variables.

    Returns:
        ServiceManager: Configured service manager instance

    Raises:
        ValueError: If required environment variables are not set
    """
    config = MinervaConfig.from_env()
    frontmatter_manager = FrontmatterManager(config.default_author)

    return ServiceManager(config, frontmatter_manager)
