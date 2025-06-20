"""
Frontmatter operations service module.

This module provides generic frontmatter management operations for notes
in the Obsidian vault, serving as a foundation for tag and alias operations.
"""

import logging
from pathlib import Path
from typing import Any, Callable, TypeVar

import frontmatter

from minerva.error_handler import (
    log_performance,
    safe_operation,
)
from minerva.exceptions import NoteNotFoundError
from minerva.file_handler import (
    FileWriteRequest,
    write_file,
)
from minerva.services.core.base_service import BaseService
from minerva.services.core.file_operations import resolve_note_file

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FrontmatterOperations(BaseService):
    """
    Service class for generic frontmatter management operations.

    This class provides unified frontmatter operations that can handle
    any frontmatter field, reducing code duplication and improving
    maintainability across tag and alias operations.
    """

    def _load_note_with_frontmatter(
        self, file_path: Path
    ) -> tuple["frontmatter.Post", dict[str, Any]]:
        """
        Load note and extract current frontmatter.

        Args:
            file_path: Path to the note file

        Returns:
            tuple: (frontmatter.Post object, frontmatter dict)

        Raises:
            NoteNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise NoteNotFoundError(
                f"File {file_path} does not exist",
                context={"filepath": str(file_path)},
                operation="load_note_with_frontmatter",
            )

        # Import here to avoid circular imports
        from minerva.services.note_operations import NoteOperations

        # Create a temporary note operations instance to read the file
        note_ops = NoteOperations(self.config, self.frontmatter_manager)
        content = note_ops.read_note(str(file_path))

        post = frontmatter.loads(content)
        frontmatter_dict = dict(post.metadata)
        return post, frontmatter_dict

    def _save_note_with_updated_frontmatter(
        self,
        file_path: Path,
        post: "frontmatter.Post",
        updated_frontmatter: dict[str, Any],
    ) -> Path:
        """
        Save note with updated frontmatter.

        Args:
            file_path: Path to the note file
            post: Frontmatter post object
            updated_frontmatter: Updated frontmatter dictionary

        Returns:
            Path: Path to the saved file
        """
        # Get author from updated frontmatter
        author_value = updated_frontmatter.get("author")
        author_str = str(author_value) if author_value is not None else None

        # Generate updated metadata using the frontmatter manager
        updated_post = self.frontmatter_manager.generate_metadata(
            text=post.content,
            author=author_str,
            is_new_note=False,
            existing_frontmatter=updated_frontmatter,
        )

        content = frontmatter.dumps(updated_post)
        file_write_request = FileWriteRequest(
            directory=str(file_path.parent),
            filename=file_path.name,
            content=content,
            overwrite=True,
        )

        return write_file(file_write_request)

    def _resolve_file_path(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Resolve file path for frontmatter operations.

        Args:
            filename: The name of the file
            filepath: The full path of the file
            default_path: The default directory to look for the file

        Returns:
            Path: The resolved file path

        Raises:
            ValueError: If neither filename nor filepath is provided
            NoteNotFoundError: If the file doesn't exist
        """
        if not filename and not filepath:
            raise ValueError("Either filename or filepath must be provided")

        file_path = resolve_note_file(self.config, filename, filepath, default_path)

        if not file_path.exists():
            raise NoteNotFoundError(
                f"File {file_path} does not exist",
                context={"filepath": str(file_path), "filename": filename},
                operation="resolve_file_path",
            )

        return file_path

    @log_performance(threshold_ms=200)
    @safe_operation(default_return=None, log_errors=True)
    def get_field(
        self,
        field_name: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Any:
        """
        Get a specific field value from a note's frontmatter.

        Args:
            field_name: Name of the frontmatter field to retrieve
            filename: The name of the note file
            filepath: The full path of the note file
            default_path: The default directory path

        Returns:
            Any: The field value, or None if field doesn't exist

        Raises:
            ValueError: If neither filename nor filepath is provided
            NoteNotFoundError: If the specified note file does not exist
        """
        self._log_operation_start(
            "get_field", field_name=field_name, filename=filename, filepath=filepath
        )

        file_path = self._resolve_file_path(filename, filepath, default_path)
        _, frontmatter_dict = self._load_note_with_frontmatter(file_path)

        value = frontmatter_dict.get(field_name)
        logger.info(
            "Retrieved field '%s' with value '%s' from %s",
            field_name,
            value,
            file_path.name,
        )

        self._log_operation_success("get_field", value)
        return value

    @log_performance(threshold_ms=300)
    @safe_operation(default_return=None, log_errors=True)
    def set_field(
        self,
        field_name: str,
        value: Any,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Set a specific field value in a note's frontmatter.

        Args:
            field_name: Name of the frontmatter field to set
            value: Value to set for the field
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path

        Returns:
            Path: The path of the modified note file

        Raises:
            ValueError: If neither filename nor filepath is provided
            NoteNotFoundError: If the specified note file does not exist
        """
        self._log_operation_start(
            "set_field",
            field_name=field_name,
            value=value,
            filename=filename,
            filepath=filepath,
        )

        file_path = self._resolve_file_path(filename, filepath, default_path)
        post, frontmatter_dict = self._load_note_with_frontmatter(file_path)

        # Update the field
        frontmatter_dict[field_name] = value

        # Save the updated note
        written_path = self._save_note_with_updated_frontmatter(
            file_path, post, frontmatter_dict
        )

        logger.info(
            "Set field '%s' to '%s' in %s", field_name, value, written_path.name
        )

        self._log_operation_success("set_field", written_path)
        return written_path

    @log_performance(threshold_ms=300)
    @safe_operation(default_return=None, log_errors=True)
    def update_field(
        self,
        field_name: str,
        update_func: Callable[[Any], Any],
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Update a field using an update function.

        Args:
            field_name: Name of the frontmatter field to update
            update_func: Function that takes current value and returns new value
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path

        Returns:
            Path: The path of the modified note file

        Raises:
            ValueError: If neither filename nor filepath is provided
            NoteNotFoundError: If the specified note file does not exist
        """
        self._log_operation_start(
            "update_field",
            field_name=field_name,
            filename=filename,
            filepath=filepath,
        )

        file_path = self._resolve_file_path(filename, filepath, default_path)
        post, frontmatter_dict = self._load_note_with_frontmatter(file_path)

        # Get current value and apply update function
        current_value = frontmatter_dict.get(field_name)
        new_value = update_func(current_value)

        # Update the field
        frontmatter_dict[field_name] = new_value

        # Save the updated note
        written_path = self._save_note_with_updated_frontmatter(
            file_path, post, frontmatter_dict
        )

        logger.info(
            "Updated field '%s' from '%s' to '%s' in %s",
            field_name,
            current_value,
            new_value,
            written_path.name,
        )

        self._log_operation_success("update_field", written_path)
        return written_path

    @log_performance(threshold_ms=300)
    @safe_operation(default_return=None, log_errors=True)
    def remove_field(
        self,
        field_name: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Remove a specific field from a note's frontmatter.

        Args:
            field_name: Name of the frontmatter field to remove
            filename: The name of the file to modify
            filepath: The full path of the file to modify
            default_path: The default directory path

        Returns:
            Path: The path of the modified note file

        Raises:
            ValueError: If neither filename nor filepath is provided
            NoteNotFoundError: If the specified note file does not exist
        """
        self._log_operation_start(
            "remove_field",
            field_name=field_name,
            filename=filename,
            filepath=filepath,
        )

        file_path = self._resolve_file_path(filename, filepath, default_path)
        post, frontmatter_dict = self._load_note_with_frontmatter(file_path)

        # Remove the field if it exists
        removed_value = frontmatter_dict.pop(field_name, None)

        # Save the updated note
        written_path = self._save_note_with_updated_frontmatter(
            file_path, post, frontmatter_dict
        )

        if removed_value is not None:
            logger.info(
                "Removed field '%s' (was '%s') from %s",
                field_name,
                removed_value,
                written_path.name,
            )
        else:
            logger.info("Field '%s' not found in %s", field_name, file_path.name)

        self._log_operation_success("remove_field", written_path)
        return written_path

    @log_performance(threshold_ms=200)
    @safe_operation(default_return={}, log_errors=True)
    def get_all_fields(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all frontmatter fields from a note.

        Args:
            filename: The name of the note file
            filepath: The full path of the note file
            default_path: The default directory path

        Returns:
            dict[str, Any]: Dictionary containing all frontmatter fields

        Raises:
            ValueError: If neither filename nor filepath is provided
            NoteNotFoundError: If the specified note file does not exist
        """
        self._log_operation_start(
            "get_all_fields", filename=filename, filepath=filepath
        )

        file_path = self._resolve_file_path(filename, filepath, default_path)
        _, frontmatter_dict = self._load_note_with_frontmatter(file_path)

        logger.info(
            "Retrieved all frontmatter fields from %s: %s",
            file_path.name,
            list(frontmatter_dict.keys()),
        )

        self._log_operation_success("get_all_fields", frontmatter_dict)
        return frontmatter_dict
