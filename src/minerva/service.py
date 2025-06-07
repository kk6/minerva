"""
Service layer for Minerva application.

This module provides the main service class that encapsulates all business logic
for note operations using dependency injection patterns. It serves as the central
coordination point between configuration, file handling, and frontmatter management.
"""

import logging
from pathlib import Path
from typing import ParamSpec, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    import frontmatter

from minerva.config import MinervaConfig
from minerva.file_handler import (
    FileWriteRequest,
    FileReadRequest,
    FileDeleteRequest,
    SearchConfig,
    SearchResult,
    search_keyword_in_files,
)
from minerva.frontmatter_manager import FrontmatterManager
from minerva.validators import TagValidator

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for decorator compatibility
P = ParamSpec("P")
R = TypeVar("R")


class MinervaService:
    """
    Main service class for Minerva note operations.

    This class encapsulates all business logic for note operations including
    creation, editing, reading, deletion, searching, and tag management.
    It uses dependency injection to receive its dependencies, making it
    easily testable and configurable.
    """

    def __init__(
        self,
        config: MinervaConfig,
        frontmatter_manager: FrontmatterManager,
    ):
        """
        Initialize MinervaService with dependencies.

        Args:
            config: Configuration instance containing paths and settings
            frontmatter_manager: Manager for frontmatter operations
        """
        self.config = config
        self.frontmatter_manager = frontmatter_manager

    def _build_file_path(
        self, filename: str, default_path: str | None = None
    ) -> tuple[Path, str]:
        """
        Resolve and build the complete file path from a filename.

        Args:
            filename: The filename (may include subdirectories)
            default_path: The default path to use if no subdirectory is specified

        Returns:
            tuple: (directory_path, base_filename)

        Raises:
            ValueError: If the resulting filename is empty
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Add .md extension if missing
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        # Parse path components
        path_parts = Path(filename)
        subdirs = path_parts.parent
        base_filename = path_parts.name

        if not base_filename:
            raise ValueError("Filename cannot be empty")

        # Create final directory path
        full_dir_path = self.config.vault_path

        # Add default_path first if it's not empty
        effective_default = default_path or self.config.default_note_dir
        if isinstance(effective_default, str) and effective_default.strip() != "":
            full_dir_path = full_dir_path / effective_default

        # Then add subdirectories if they exist
        if str(subdirs) != ".":
            full_dir_path = full_dir_path / subdirs

        return full_dir_path, base_filename

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

        Args:
            text: The content to write to the file
            filename: The name of the file to write
            author: The author name to add to the frontmatter
            default_path: The default directory to save the file
            is_new_note: Whether this is a new note (True) or an update to an existing note (False)

        Returns:
            tuple: (full_dir_path, base_filename, prepared_content)
        """
        # Build file path
        full_dir_path, base_filename = self._build_file_path(filename, default_path)

        # Check existing frontmatter
        file_path = full_dir_path / base_filename
        existing_frontmatter = self.frontmatter_manager.read_existing_metadata(
            file_path
        )

        # Generate metadata
        post = self.frontmatter_manager.generate_metadata(
            text=text,
            author=author or self.config.default_author,
            is_new_note=is_new_note,
            existing_frontmatter=existing_frontmatter,
        )

        # Convert Post object to string with frontmatter
        import frontmatter

        content = frontmatter.dumps(post)

        return full_dir_path, base_filename, content

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
        from minerva.file_handler import write_file

        # Prepare note for writing
        full_dir_path, base_filename, content = self._assemble_complete_note(
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
        return file_path

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
        from minerva.file_handler import write_file

        # Prepare note for writing
        full_dir_path, base_filename, content = self._assemble_complete_note(
            text=text,
            filename=filename,
            author=author,
            default_path=default_path,
            is_new_note=False,
        )
        file_path_for_logging = full_dir_path / base_filename

        # Check if the file exists before attempting to edit it
        if not file_path_for_logging.exists():
            raise FileNotFoundError(
                f"Cannot edit note. File {file_path_for_logging} does not exist"
            )

        # Create the FileWriteRequest with overwrite=True
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=True,
        )

        file_path = write_file(file_write_request)
        logger.info("Note edited at %s", file_path)
        return file_path

    def read_note(self, filepath: str) -> str:
        """
        Read a note from a file in the Obsidian vault.

        Args:
            filepath: The full path of the file to read

        Returns:
            str: The content of the file
        """
        from minerva.file_handler import read_file
        import os

        directory, filename = os.path.split(filepath)
        file_read_request = FileReadRequest(
            directory=directory,
            filename=filename,
        )
        content = read_file(file_read_request)
        logger.info("File read from %s", filepath)
        return content

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
        if not query:
            raise ValueError("Query cannot be empty")

        search_config = SearchConfig(
            directory=str(self.config.vault_path),
            keyword=query,
            file_extensions=[".md"],
            case_sensitive=case_sensitive,
        )
        matching_files = search_keyword_in_files(search_config)
        logger.info("Found %s files matching the query: %s", len(matching_files), query)
        return matching_files

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
        if not filename and not filepath:
            raise ValueError("Either filename or filepath must be provided")

        if filepath:
            file_path = Path(filepath)
        else:
            if not filename:
                raise ValueError(
                    "Filename must be provided if filepath is not specified."
                )
            full_dir_path, base_filename = self._build_file_path(filename, default_path)
            file_path = full_dir_path / base_filename

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        message = f"File found at {file_path}. To delete, call 'perform_note_delete' with the same identification parameters."
        return {"file_path": str(file_path), "message": message}

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
        from minerva.file_handler import delete_file

        if not filename and not filepath:
            raise ValueError("Either filename or filepath must be provided")

        if filepath:
            file_path = Path(filepath)
        else:
            if not filename:
                raise ValueError(
                    "Filename must be provided if filepath is not specified."
                )
            full_dir_path, base_filename = self._build_file_path(filename, default_path)
            file_path = full_dir_path / base_filename

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        file_delete_request = FileDeleteRequest(
            directory=str(file_path.parent),
            filename=file_path.name,
        )

        deleted_path = delete_file(file_delete_request)
        logger.info("Note deleted successfully at %s", deleted_path)
        return deleted_path

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

    def _resolve_note_file(
        self, filename: str | None, filepath: str | None, default_path: str | None
    ) -> Path:
        """Resolve note file path from filename or filepath."""
        if filepath:
            return Path(filepath)
        elif filename:
            full_dir_path, base_filename = self._build_file_path(filename, default_path)
            return full_dir_path / base_filename
        else:
            raise ValueError("Either filename or filepath must be provided")

    def _load_note_with_tags(
        self, file_path: Path
    ) -> tuple["frontmatter.Post", list[str]]:
        """Load note and extract current tags."""
        import frontmatter

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        content = self.read_note(str(file_path))
        post = frontmatter.loads(content)
        tags_value = post.metadata.get("tags", [])
        tags = list(tags_value) if isinstance(tags_value, list) else []
        return post, tags

    def _save_note_with_updated_tags(
        self, file_path: Path, post: "frontmatter.Post", tags: list[str]
    ) -> Path:
        """Save note with updated tags."""
        import frontmatter
        from minerva.file_handler import write_file

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
        normalized_tag = self._normalize_tag(tag)
        if not self._validate_tag(tag):
            raise ValueError(f"Invalid tag: {tag}")

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

        return written_path

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
        try:
            file_path = self._resolve_note_file(filename, filepath, default_path)

            if not file_path.exists():
                logger.warning(
                    "Get_tags: File %s not found. Returning empty list.", file_path
                )
                return []

            _, tags = self._load_note_with_tags(file_path)
            logger.info(
                "Get_tags: Successfully retrieved tags %s from %s", tags, file_path
            )
            return tags

        except Exception as e:
            logger.error(
                "Get_tags: Error processing file: %s. Returning empty list.", e
            )
            return []


def create_minerva_service() -> MinervaService:
    """
    Create a MinervaService instance with default configuration.

    This factory function provides a convenient way to create a fully
    configured MinervaService instance using environment variables.

    Returns:
        MinervaService: Configured service instance

    Raises:
        ValueError: If required environment variables are not set
    """
    config = MinervaConfig.from_env()
    frontmatter_manager = FrontmatterManager(config.default_author)

    return MinervaService(config, frontmatter_manager)
