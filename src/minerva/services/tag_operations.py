"""
Tag operations service module.

This module provides tag management operations including adding, removing,
retrieving, and searching tags for notes in the Obsidian vault.
"""

import logging
from pathlib import Path

import frontmatter

from minerva.error_handler import (
    log_performance,
    safe_operation,
)
from minerva.file_handler import (
    FileWriteRequest,
    write_file,
)
from minerva.services.core.base_service import BaseService
from minerva.services.core.file_operations import resolve_note_file
from minerva.validators import TagValidator

logger = logging.getLogger(__name__)


class TagOperations(BaseService):
    """
    Service class for tag management operations.

    This class handles adding, removing, retrieving, and searching tags
    in notes within the Obsidian vault, using the core infrastructure utilities.
    """

    def _validate_and_resolve_file(
        self,
        operation_name: str,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Validate input parameters and resolve file path for tag operations.

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

    # テストとの互換性のために_resolve_note_fileメソッドも追加
    def _resolve_note_file(
        self,
        filename: str | None = None,
        filepath: str | None = None,
        default_path: str | None = None,
    ) -> Path:
        """
        Resolve file path for tag operations (legacy method for test compatibility).

        Args:
            filename: The name of the file
            filepath: The full path of the file
            default_path: The default directory to look for the file

        Returns:
            Path: The resolved file path

        Raises:
            ValueError: If neither filename nor filepath is provided or if filename is empty
        """
        if filename is not None and filename == "":
            raise ValueError("Filename cannot be empty")

        if not filename and not filepath:
            raise ValueError("Either filename or filepath must be provided")

        return resolve_note_file(self.config, filename, filepath, default_path)

    def _normalize_tag(self, tag: str) -> str:
        """Convert a tag to its normalized form."""
        return TagValidator.normalize_tag(tag)

    def _validate_tag(self, tag: str) -> bool:
        """Check if a tag is valid."""
        try:
            TagValidator.validate_tag(tag)
            return True
        except ValueError:
            return False

    def _load_note_with_tags(
        self, file_path: Path
    ) -> tuple["frontmatter.Post", list[str]]:
        """Load note and extract current tags."""
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        # Import here to avoid circular imports
        from minerva.services.note_operations import NoteOperations

        # Create a temporary note operations instance to read the file
        note_ops = NoteOperations(self.config, self.frontmatter_manager)
        content = note_ops.read_note(str(file_path))

        post = frontmatter.loads(content)
        tags_value = post.metadata.get("tags", [])
        tags = list(tags_value) if isinstance(tags_value, list) else []
        return post, tags

    def _save_note_with_updated_tags(
        self, file_path: Path, post: "frontmatter.Post", tags: list[str]
    ) -> Path:
        """Save note with updated tags."""
        author_value = post.metadata.get("author")
        author_str = str(author_value) if author_value is not None else None

        # Generate updated metadata
        updated_post = self.frontmatter_manager.generate_metadata(
            text=post.content,
            author=author_str,
            is_new_note=False,
            existing_frontmatter=dict(post.metadata),
            tags=tags,
        )

        content = frontmatter.dumps(updated_post)
        file_write_request = FileWriteRequest(
            directory=str(file_path.parent),
            filename=file_path.name,
            content=content,
            overwrite=True,
        )

        return write_file(file_write_request)

    @log_performance(threshold_ms=300)
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
        self._log_operation_start(
            "add_tag", tag=tag, filename=filename, filepath=filepath
        )

        normalized_tag = self._normalize_tag(tag)
        if not self._validate_tag(tag):
            error = ValueError(f"Invalid tag: {tag}")
            self._log_operation_error("add_tag", error)
            raise error

        file_path = self._resolve_note_file(filename, filepath, default_path)
        post, current_tags = self._load_note_with_tags(file_path)
        current_normalized = [self._normalize_tag(str(t)) for t in current_tags]

        if normalized_tag not in current_normalized:
            current_tags.append(normalized_tag)
            written_path = self._save_note_with_updated_tags(
                file_path, post, current_tags
            )
            logger.info("Added tag '%s' to %s", normalized_tag, written_path.name)
        else:
            # Rewrite the file to update the 'updated' field even if the tag already exists
            written_path = self._save_note_with_updated_tags(
                file_path, post, current_tags
            )
            logger.info("Tag '%s' already exists in %s", normalized_tag, file_path.name)

        self._log_operation_success("add_tag", written_path)
        return written_path

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
        self._log_operation_start(
            "remove_tag", tag=tag, filename=filename, filepath=filepath
        )

        tag_to_remove = self._normalize_tag(tag)

        file_path = self._resolve_note_file(filename, filepath, default_path)
        post, current_tags = self._load_note_with_tags(file_path)

        # Remove tag if present
        new_tags = []
        tag_was_removed = False

        for existing_tag in current_tags:
            if self._normalize_tag(str(existing_tag)) == tag_to_remove:
                tag_was_removed = True
            else:
                new_tags.append(str(existing_tag))

        written_path = self._save_note_with_updated_tags(file_path, post, new_tags)

        if tag_was_removed:
            logger.info("Removed tag '%s' from %s", tag, written_path.name)
        else:
            logger.info("Tag '%s' not found in %s", tag, file_path.name)

        self._log_operation_success("remove_tag", written_path)
        return written_path

    @log_performance(threshold_ms=200)
    @safe_operation(default_return=[], log_errors=True)
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
        self._log_operation_start("get_tags", filename=filename, filepath=filepath)

        file_path = self._resolve_note_file(filename, filepath, default_path)

        if not file_path.exists():
            from minerva.exceptions import NoteNotFoundError

            error = NoteNotFoundError(f"File {file_path} not found")
            self._log_operation_error("get_tags", error)
            raise error

        _, tags = self._load_note_with_tags(file_path)
        logger.info("Get_tags: Successfully retrieved tags %s from %s", tags, file_path)

        self._log_operation_success("get_tags", tags)
        return tags

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
        self._log_operation_start(
            "rename_tag", old_tag=old_tag, new_tag=new_tag, directory=directory
        )

        normalized_new_tag = self._normalize_tag(new_tag)
        if not self._validate_tag(new_tag):
            new_tag_error = ValueError(f"Invalid new_tag: {new_tag}")
            self._log_operation_error("rename_tag", new_tag_error)
            raise new_tag_error
        if not self._validate_tag(old_tag):
            old_tag_error = ValueError(f"Invalid old_tag: {old_tag}")
            self._log_operation_error("rename_tag", old_tag_error)
            raise old_tag_error

        normalized_old_tag = self._normalize_tag(old_tag)

        if normalized_old_tag == normalized_new_tag:
            logger.info("Old and new tags are the same after normalization")
            return []

        effective_directory = Path(directory or str(self.config.vault_path))
        if not effective_directory.is_dir():
            dir_error: FileNotFoundError = FileNotFoundError(
                f"Directory '{effective_directory}' not found"
            )
            self._log_operation_error("rename_tag", dir_error)
            raise dir_error

        # Process all markdown files
        modified_files: list[Path] = []
        md_files = list(effective_directory.rglob("*.md"))

        for file_path in md_files:
            if self._rename_tag_in_file(
                file_path, normalized_old_tag, normalized_new_tag
            ):
                modified_files.append(file_path)
                logger.info(
                    "Renamed tag '%s' to '%s' in %s", old_tag, new_tag, file_path.name
                )

        logger.info("Renamed tag in %d file(s)", len(modified_files))

        self._log_operation_success("rename_tag", modified_files)
        return modified_files

    def _rename_tag_in_file(
        self, file_path: Path, old_tag_normalized: str, new_tag: str
    ) -> bool:
        """
        Rename a tag in a single file.

        Args:
            file_path: Path to the note file
            old_tag_normalized: Normalized old tag to replace
            new_tag: New tag to add

        Returns:
            bool: True if file was modified, False otherwise
        """
        try:
            post, current_tags = self._load_note_with_tags(file_path)

            if not current_tags:
                return False

            new_tags = []
            old_tag_found = False
            new_tag_normalized = self._normalize_tag(new_tag)

            # Remove old tag and check if new tag already exists
            for tag in current_tags:
                tag_normalized = self._normalize_tag(str(tag))
                if tag_normalized == old_tag_normalized:
                    old_tag_found = True
                else:
                    new_tags.append(str(tag))

            if old_tag_found:
                # Add new tag if not already present
                if new_tag_normalized not in [self._normalize_tag(t) for t in new_tags]:
                    new_tags.append(new_tag)

                # Check if tags actually changed
                old_normalized = {self._normalize_tag(str(t)) for t in current_tags}
                new_normalized = {self._normalize_tag(t) for t in new_tags}

                if old_normalized != new_normalized:
                    self._save_note_with_updated_tags(file_path, post, new_tags)
                    return True

        except Exception as e:
            logger.error("Error processing file %s: %s", file_path, e)

        return False

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
        self._log_operation_start("list_all_tags", directory=directory)

        effective_directory_str = (
            directory if directory else str(self.config.vault_path)
        )
        effective_directory_path = Path(effective_directory_str)

        if not effective_directory_path.is_dir():
            logger.error(
                "List_all_tags: Directory '%s' does not exist or is not a directory.",
                effective_directory_path,
            )
            error = FileNotFoundError(
                f"Directory '{effective_directory_path}' not found or is not a directory."
            )
            self._log_operation_error("list_all_tags", error)
            raise error

        all_tags_set: set[str] = set()
        files_processed_count = 0
        tags_found_count = 0

        for file_path in effective_directory_path.rglob("*.md"):
            files_processed_count += 1
            tags_in_file = self.get_tags(filename=None, filepath=str(file_path))
            for tag in tags_in_file:
                normalized_tag = self._normalize_tag(tag)
                if normalized_tag:
                    all_tags_set.add(normalized_tag)
                    tags_found_count += 1

        sorted_tags_list = sorted(list(all_tags_set))

        logger.info(
            "List_all_tags: Processed %d files in '%s'. Found %d unique normalized tags (from %d total tag instances). Tags: %s",
            files_processed_count,
            effective_directory_path,
            len(sorted_tags_list),
            tags_found_count,
            sorted_tags_list
            if len(sorted_tags_list) < 20
            else str(sorted_tags_list[:20]) + "...",  # Avoid overly long log
        )

        self._log_operation_success("list_all_tags", sorted_tags_list)
        return sorted_tags_list

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
        self._log_operation_start("find_notes_with_tag", tag=tag, directory=directory)

        effective_directory_str = (
            directory if directory else str(self.config.vault_path)
        )
        effective_directory_path = Path(effective_directory_str)

        if not effective_directory_path.is_dir():
            logger.error(
                "Find_notes_with_tag: Directory '%s' does not exist or is not a directory.",
                effective_directory_path,
            )
            error = FileNotFoundError(
                f"Directory '{effective_directory_path}' not found or is not a directory."
            )
            self._log_operation_error("find_notes_with_tag", error)
            raise error

        normalized_target_tag = self._normalize_tag(tag)

        if not normalized_target_tag:
            logger.warning(
                "Find_notes_with_tag: The provided tag '%s' is empty after normalization. "
                "Cannot search for an empty tag. Returning empty list.",
                tag,
            )
            return []

        matching_files_paths: list[str] = []
        files_processed_count = 0

        for file_path in effective_directory_path.rglob("*.md"):
            files_processed_count += 1
            tags_in_file = self.get_tags(filename=None, filepath=str(file_path))

            normalized_tags_in_file = [self._normalize_tag(t) for t in tags_in_file]

            if normalized_target_tag in normalized_tags_in_file:
                matching_files_paths.append(str(file_path))

        logger.info(
            "Find_notes_with_tag: Processed %d files in '%s'. Found %d notes with tag '%s'.",
            files_processed_count,
            effective_directory_path,
            len(matching_files_paths),
            tag,  # Log original tag for clarity
        )

        self._log_operation_success("find_notes_with_tag", matching_files_paths)
        return matching_files_paths
