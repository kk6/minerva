"""
Note operations service module.

This module provides note CRUD operations including creation, editing, reading,
and deletion functionality for the Minerva application.
"""

import logging
import os
from pathlib import Path

from minerva.error_handler import (
    handle_file_operations,
    validate_inputs,
    log_performance,
)
from minerva.file_handler import (
    FileWriteRequest,
    FileReadRequest,
    FileDeleteRequest,
    write_file,
    read_file,
    delete_file,
)
from minerva.services.core.base_service import BaseService
from minerva.services.core.file_operations import (
    validate_filename,
    validate_text_content,
    assemble_complete_note,
    resolve_note_file,
)

logger = logging.getLogger(__name__)


class NoteOperations(BaseService):
    """
    Service class for note CRUD operations.

    This class handles creation, editing, reading, and deletion of notes
    in the Obsidian vault, using the core infrastructure utilities.
    """

    def _validate_and_resolve_file(
        self,
        operation_name: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Validate input parameters and resolve file path for note operations.

        Args:
            operation_name: Name of the operation for logging purposes
            filename: The name of the file
            filepath: The full path of the file
            default_path: The default directory to look for the file

        Returns:
            Path: The resolved file path

        Raises:
            ValueError: If neither filename nor filepath is provided or if file resolution fails
            FileNotFoundError: If the file doesn't exist
        """
        if not filename and not filepath:
            value_error: ValueError = ValueError(
                "Either filename or filepath must be provided"
            )
            self._log_operation_error(operation_name, value_error)
            raise value_error

        try:
            file_path = resolve_note_file(self.config, filename, filepath, default_path)
        except ValueError as e:
            self._log_operation_error(operation_name, e)
            raise

        if not file_path.exists():
            file_error: FileNotFoundError = FileNotFoundError(
                f"File {file_path} does not exist"
            )
            self._log_operation_error(operation_name, file_error)
            raise file_error

        return file_path

    @log_performance(threshold_ms=500)
    @validate_inputs(validate_text_content, validate_filename)
    @handle_file_operations()
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
        self._log_operation_start("create_note", filename=filename, author=author)

        # Prepare note for writing
        full_dir_path, base_filename, content = assemble_complete_note(
            config=self.config,
            frontmatter_manager=self.frontmatter_manager,
            text=text,
            filename=filename,
            author=author,
            default_path=default_path,
            is_new_note=True,
        )

        # Create the FileWriteRequest with overwrite=False
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=False,
        )

        file_path = write_file(file_write_request)
        logger.info("New note created at %s", file_path)

        self._log_operation_success("create_note", file_path)
        # Auto-update vector index if enabled
        self._update_vector_index_if_enabled(file_path, content)

        return file_path

    @log_performance(threshold_ms=500)
    @validate_inputs(validate_text_content, validate_filename)
    @handle_file_operations()
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
        self._log_operation_start("edit_note", filename=filename, author=author)

        # Prepare note for writing
        full_dir_path, base_filename, content = assemble_complete_note(
            config=self.config,
            frontmatter_manager=self.frontmatter_manager,
            text=text,
            filename=filename,
            author=author,
            default_path=default_path,
            is_new_note=False,
        )
        file_path_for_logging = full_dir_path / base_filename

        # Check if the file exists before attempting to edit it
        if not file_path_for_logging.exists():
            error = FileNotFoundError(
                f"Cannot edit note. File {file_path_for_logging} does not exist"
            )
            self._log_operation_error("edit_note", error)
            raise error

        # Create the FileWriteRequest with overwrite=True
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=True,
        )

        file_path = write_file(file_write_request)
        logger.info("Note edited at %s", file_path)

        self._log_operation_success("edit_note", file_path)
        # Auto-update vector index if enabled
        self._update_vector_index_if_enabled(file_path, content)

        return file_path

    @log_performance(threshold_ms=200)
    @handle_file_operations()
    def read_note(self, filepath: str) -> str:
        """
        Read a note from a file in the Obsidian vault.

        Args:
            filepath: The full path of the file to read

        Returns:
            str: The content of the file
        """
        self._log_operation_start("read_note", filepath=filepath)

        directory, filename = os.path.split(filepath)
        file_read_request = FileReadRequest(
            directory=directory,
            filename=filename,
        )
        content = read_file(file_read_request)
        logger.info("File read from %s", filepath)

        self._log_operation_success("read_note", filepath)
        return content

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
        self._log_operation_start(
            "get_note_delete_confirmation", filename=filename, filepath=filepath
        )

        file_path = self._validate_and_resolve_file(
            "get_note_delete_confirmation", filename, filepath, default_path
        )

        message = f"File found at {file_path}. To delete, call 'perform_note_delete' with the same identification parameters."
        result = {"file_path": str(file_path), "message": message}

        self._log_operation_success("get_note_delete_confirmation", result)
        return result

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
        self._log_operation_start(
            "perform_note_delete", filename=filename, filepath=filepath
        )

        file_path = self._validate_and_resolve_file(
            "perform_note_delete", filename, filepath, default_path
        )

        file_delete_request = FileDeleteRequest(
            directory=str(file_path.parent),
            filename=file_path.name,
        )

        deleted_path = delete_file(file_delete_request)
        logger.info("Note deleted successfully at %s", deleted_path)

        self._log_operation_success("perform_note_delete", deleted_path)
        # Remove from vector index if enabled
        self._remove_from_vector_index_if_enabled(deleted_path)

        return deleted_path

    def _update_vector_index_if_enabled(self, file_path: Path, content: str) -> None:
        """
        Update vector index for the file if auto-indexing is enabled.

        Args:
            file_path: Path to the file that was created/updated
            content: Content of the file for embedding generation
        """
        if not self._should_auto_update_index():
            return

        strategy = self.config.auto_index_strategy.lower()

        if strategy == "immediate":
            self._update_vector_index_immediate(file_path, content)
        elif strategy in ["batch", "background"]:
            self._update_vector_index_batched(file_path, content, strategy)
        else:
            logger.warning(
                "Unknown auto-index strategy: %s, falling back to immediate", strategy
            )
            self._update_vector_index_immediate(file_path, content)

    def _update_vector_index_immediate(self, file_path: Path, content: str) -> None:
        """
        Update vector index immediately.

        Args:
            file_path: Path to the file that was created/updated
            content: Content of the file for embedding generation
        """
        try:
            from minerva.vector.embeddings import SentenceTransformerProvider
            from minerva.vector.indexer import VectorIndexer

            # Initialize components
            embedding_provider = SentenceTransformerProvider(
                self.config.embedding_model
            )
            if not self.config.vector_db_path:
                raise RuntimeError("Vector database path is not configured")
            indexer = VectorIndexer(self.config.vector_db_path)

            # Ensure schema is initialized - get dimension directly from provider
            embedding_dim = embedding_provider.embedding_dim
            try:
                indexer.initialize_schema(embedding_dim)

                # Generate and store embedding
                embedding = embedding_provider.embed(content)
                indexer.store_embedding(str(file_path), embedding, content)
            finally:
                # Ensure connections are closed
                indexer.close()
            logger.debug("Vector index updated immediately for file: %s", file_path)

        except ImportError:
            logger.debug(
                "Vector search dependencies not available, skipping auto-index update"
            )
        except Exception as e:
            logger.warning("Failed to update vector index for %s: %s", file_path, e)

    def _update_vector_index_batched(
        self, file_path: Path, content: str, strategy: str
    ) -> None:
        """
        Queue file for batch/background vector index update.

        Args:
            file_path: Path to the file that was created/updated
            content: Content of the file for embedding generation
            strategy: Update strategy ('batch' or 'background')
        """
        try:
            from minerva.vector.batch_indexer import get_batch_indexer

            batch_indexer = get_batch_indexer(self.config, strategy)
            if batch_indexer:
                batch_indexer.queue_task(str(file_path), content, "update")
                logger.debug("Queued vector index update for file: %s", file_path)
            else:
                logger.warning(
                    "Failed to get batch indexer, falling back to immediate update"
                )
                self._update_vector_index_immediate(file_path, content)

        except ImportError:
            logger.debug(
                "Vector search dependencies not available, skipping auto-index update"
            )
        except Exception as e:
            logger.warning(
                "Failed to queue vector index update for %s: %s", file_path, e
            )

    def _remove_from_vector_index_if_enabled(self, file_path: Path) -> None:
        """
        Remove file from vector index if auto-indexing is enabled.

        Args:
            file_path: Path to the file that was deleted
        """
        if not self._should_auto_update_index():
            return

        strategy = self.config.auto_index_strategy.lower()

        if strategy == "immediate":
            self._remove_from_vector_index_immediate(file_path)
        elif strategy in ["batch", "background"]:
            self._remove_from_vector_index_batched(file_path, strategy)
        else:
            logger.warning(
                "Unknown auto-index strategy: %s, falling back to immediate", strategy
            )
            self._remove_from_vector_index_immediate(file_path)

    def _remove_from_vector_index_immediate(self, file_path: Path) -> None:
        """
        Remove file from vector index immediately.

        Args:
            file_path: Path to the file that was deleted
        """
        try:
            from minerva.vector.indexer import VectorIndexer

            if not self.config.vector_db_path:
                raise RuntimeError("Vector database path is not configured")
            indexer = VectorIndexer(self.config.vector_db_path)

            # Remove from index if it exists
            if indexer.is_file_indexed(str(file_path)):
                indexer.remove_file(str(file_path))
                logger.debug(
                    "Removed file from vector index immediately: %s", file_path
                )

            indexer.close()

        except ImportError:
            logger.debug(
                "Vector search dependencies not available, skipping auto-index removal"
            )
        except Exception as e:
            logger.warning(
                "Failed to remove from vector index for %s: %s", file_path, e
            )

    def _remove_from_vector_index_batched(self, file_path: Path, strategy: str) -> None:
        """
        Queue file for batch/background vector index removal.

        Args:
            file_path: Path to the file that was deleted
            strategy: Update strategy ('batch' or 'background')
        """
        try:
            from minerva.vector.batch_indexer import get_batch_indexer

            batch_indexer = get_batch_indexer(self.config, strategy)
            if batch_indexer:
                batch_indexer.queue_task(str(file_path), "", "remove")
                logger.debug("Queued vector index removal for file: %s", file_path)
            else:
                logger.warning(
                    "Failed to get batch indexer, falling back to immediate removal"
                )
                self._remove_from_vector_index_immediate(file_path)

        except ImportError:
            logger.debug(
                "Vector search dependencies not available, skipping auto-index removal"
            )
        except Exception as e:
            logger.warning(
                "Failed to queue vector index removal for %s: %s", file_path, e
            )

    def _should_auto_update_index(self) -> bool:
        """
        Check if automatic vector index updates should be performed.

        Returns:
            bool: True if auto-updates should be performed
        """
        return (
            self.config.vector_search_enabled
            and self.config.auto_index_enabled
            and self.config.vector_db_path is not None
        )
