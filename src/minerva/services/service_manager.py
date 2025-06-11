"""
Service manager facade for Minerva application.

This module provides a unified interface for all service operations, serving as
a facade that coordinates between different specialized service modules while
maintaining backward compatibility with the existing API.
"""

import logging
from pathlib import Path
from typing import ParamSpec, TypeVar

import frontmatter

from minerva.config import MinervaConfig
from minerva.error_handler import MinervaErrorHandler
from minerva.file_handler import SearchResult
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.alias_operations import AliasOperations
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

    # Utility methods that remain at the service manager level
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

        content = frontmatter.dumps(post)

        return full_dir_path, base_filename, content

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
    def _normalize_tag(self, tag: str) -> str:
        """Convert a tag to its normalized form."""
        return self.tag_operations._normalize_tag(tag)

    def _validate_tag(self, tag: str) -> bool:
        """Check if a tag is valid."""
        return self.tag_operations._validate_tag(tag)

    def _resolve_note_file(
        self, filename: str | None, filepath: str | None, default_path: str | None
    ) -> Path:
        """Resolve note file path from filename or filepath."""
        return self.tag_operations._resolve_note_file(filename, filepath, default_path)

    def _load_note_with_tags(
        self, file_path: Path
    ) -> tuple["frontmatter.Post", list[str]]:
        """Load note and extract current tags."""
        return self.tag_operations._load_note_with_tags(file_path)

    def _rename_tag_in_file(
        self, file_path: Path, old_tag_normalized: str, new_tag: str
    ) -> bool:
        """Rename a tag in a single file."""
        return self.tag_operations._rename_tag_in_file(
            file_path, old_tag_normalized, new_tag
        )

    def _save_note_with_updated_tags(
        self, file_path: Path, post: "frontmatter.Post", tags: list[str]
    ) -> Path:
        """Save note with updated tags."""
        return self.tag_operations._save_note_with_updated_tags(file_path, post, tags)

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
    def _validate_alias(self, alias: str) -> str:
        """Validate alias format and content."""
        return self.alias_operations._validate_alias(alias)

    def _normalize_alias(self, alias: str) -> str:
        """Normalize alias for comparison (case-insensitive, whitespace-trimmed)."""
        return self.alias_operations._normalize_alias(alias)

    def _get_aliases_from_file(self, file_path: Path) -> list[str]:
        """Get current aliases from a note's frontmatter."""
        return self.alias_operations._get_aliases_from_file(file_path)

    def _save_note_with_updated_aliases(
        self, file_path: Path, post: "frontmatter.Post", aliases: list[str]
    ) -> Path:
        """Save note with updated aliases."""
        return self.alias_operations._save_note_with_updated_aliases(
            file_path, post, aliases
        )

    def _check_alias_conflicts(
        self, alias: str, exclude_file: Path | None = None
    ) -> list[str]:
        """Check if alias conflicts with existing aliases or filenames."""
        return self.alias_operations._check_alias_conflicts(alias, exclude_file)

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
