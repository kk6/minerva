"""
Service layer for Minerva application.

This module provides the main service class that encapsulates all business logic
for note operations using dependency injection patterns. It serves as the central
coordination point between configuration, file handling, and frontmatter management.
"""

import logging
from pathlib import Path
from typing import ParamSpec, TypeVar

import frontmatter

from minerva.config import MinervaConfig
from minerva.error_handler import (
    MinervaErrorHandler,
    log_performance,
    safe_operation,
)
from minerva.exceptions import (
    NoteNotFoundError,
)
from minerva.file_handler import (
    FileWriteRequest,
    SearchConfig,
    SearchResult,
    search_keyword_in_files,
    write_file,
)
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.note_operations import NoteOperations
from minerva.services.tag_operations import TagOperations

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
        self.error_handler = MinervaErrorHandler(vault_path=config.vault_path)

        # Initialize specialized service modules
        self.note_operations = NoteOperations(config, frontmatter_manager)
        self.tag_operations = TagOperations(config, frontmatter_manager)

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

    @log_performance(threshold_ms=1000)
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
        if not query or not query.strip():
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

    def _validate_alias(self, alias: str) -> str:
        """
        Validate alias format and content.

        Args:
            alias: The alias string to validate

        Returns:
            str: Validated alias string

        Raises:
            ValueError: If alias is invalid
        """
        if not alias or not alias.strip():
            raise ValueError("Alias cannot be empty or only whitespace")

        # Remove leading/trailing whitespace
        alias = alias.strip()

        # Check for reasonable length (1-100 characters)
        if len(alias) > 100:
            raise ValueError("Alias cannot exceed 100 characters")

        # Obsidian doesn't allow aliases with certain characters
        forbidden_chars = ["|", "#", "^", "[", "]"]
        for char in forbidden_chars:
            if char in alias:
                raise ValueError(f"Alias cannot contain '{char}' character")

        return alias

    def _normalize_alias(self, alias: str) -> str:
        """
        Normalize alias for comparison (case-insensitive, whitespace-trimmed).

        Args:
            alias: The alias to normalize

        Returns:
            str: Normalized alias
        """
        return alias.strip().lower()

    def _get_aliases_from_file(self, file_path: Path) -> list[str]:
        """
        Get current aliases from a note's frontmatter.

        Args:
            file_path: Path to the note file

        Returns:
            list[str]: List of aliases (preserves original casing)
        """
        post, _ = self._load_note_with_tags(file_path)
        aliases_value = post.metadata.get("aliases", [])
        return list(aliases_value) if isinstance(aliases_value, list) else []

    def _save_note_with_updated_aliases(
        self, file_path: Path, post: "frontmatter.Post", aliases: list[str]
    ) -> Path:
        """
        Save note with updated aliases.

        Args:
            file_path: Path to the note file
            post: Frontmatter post object
            aliases: List of aliases to save

        Returns:
            Path: Path to the saved file
        """
        # Get current metadata
        current_metadata = dict(post.metadata)

        # Update aliases in metadata
        if aliases:
            current_metadata["aliases"] = aliases
        else:
            # Remove aliases field if no aliases remain
            current_metadata.pop("aliases", None)

        # Get author
        author_value = current_metadata.get("author")
        author_str = str(author_value) if author_value is not None else None

        # Generate updated metadata (preserving existing fields)
        updated_post = self.frontmatter_manager.generate_metadata(
            text=post.content,
            author=author_str,
            is_new_note=False,
            existing_frontmatter=current_metadata,
        )

        # Ensure aliases are preserved (generate_metadata might not handle custom fields)
        if aliases:
            updated_post.metadata["aliases"] = aliases
        else:
            updated_post.metadata.pop("aliases", None)

        content = frontmatter.dumps(updated_post)
        file_write_request = FileWriteRequest(
            directory=str(file_path.parent),
            filename=file_path.name,
            content=content,
            overwrite=True,
        )

        return write_file(file_write_request)

    def _check_alias_conflicts(
        self, alias: str, exclude_file: Path | None = None
    ) -> list[str]:
        """
        Check if alias conflicts with existing aliases or filenames.

        Args:
            alias: The alias to check
            exclude_file: File to exclude from conflict checking (for updating existing notes)

        Returns:
            list[str]: List of conflicting file paths
        """
        normalized_alias = self._normalize_alias(alias)
        conflicts = []

        # Check all markdown files in vault
        for file_path in self.config.vault_path.rglob("*.md"):
            # Skip the file being updated
            if exclude_file and file_path == exclude_file:
                continue

            # Check if alias conflicts with filename (without .md extension)
            filename_without_ext = file_path.stem
            if self._normalize_alias(filename_without_ext) == normalized_alias:
                conflicts.append(str(file_path))
                continue

            # Check if alias conflicts with existing aliases
            try:
                existing_aliases = self._get_aliases_from_file(file_path)
                for existing_alias in existing_aliases:
                    if self._normalize_alias(existing_alias) == normalized_alias:
                        conflicts.append(str(file_path))
                        break
            except Exception as e:
                # Log error but don't fail the entire operation
                logger.warning("Error checking aliases in %s: %s", file_path, e)
                continue

        return conflicts

    @log_performance(threshold_ms=300)
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
        # Validate alias
        alias = self._validate_alias(alias)

        file_path = self._resolve_note_file(filename, filepath, default_path)

        # Check for conflicts unless explicitly allowed
        if not allow_conflicts:
            conflicts = self._check_alias_conflicts(alias, exclude_file=file_path)
            if conflicts:
                raise ValueError(
                    f"Alias '{alias}' conflicts with existing aliases or filenames in: {', '.join(conflicts)}"
                )

        # Load current aliases
        current_aliases = self._get_aliases_from_file(file_path)
        normalized_current = [self._normalize_alias(a) for a in current_aliases]
        normalized_new = self._normalize_alias(alias)

        # Add alias if not already present
        if normalized_new not in normalized_current:
            current_aliases.append(alias)
            post, _ = self._load_note_with_tags(file_path)
            written_path = self._save_note_with_updated_aliases(
                file_path, post, current_aliases
            )
            logger.info("Added alias '%s' to %s", alias, written_path.name)
            return written_path
        else:
            logger.info("Alias '%s' already exists in %s", alias, file_path.name)
            return file_path

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
        normalized_alias = self._normalize_alias(alias)
        file_path = self._resolve_note_file(filename, filepath, default_path)

        # Load current aliases
        current_aliases = self._get_aliases_from_file(file_path)

        # Remove alias if present
        new_aliases = []
        alias_was_removed = False

        for existing_alias in current_aliases:
            if self._normalize_alias(existing_alias) == normalized_alias:
                alias_was_removed = True
            else:
                new_aliases.append(existing_alias)

        # Save updated aliases only if an alias was actually removed
        if alias_was_removed:
            post, _ = self._load_note_with_tags(file_path)
            written_path = self._save_note_with_updated_aliases(
                file_path, post, new_aliases
            )
            logger.info("Removed alias '%s' from %s", alias, written_path.name)
            return written_path
        else:
            logger.info("Alias '%s' not found in %s", alias, file_path.name)
            return file_path

    @log_performance(threshold_ms=200)
    @safe_operation(default_return=[], log_errors=True)
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
        file_path = self._resolve_note_file(filename, filepath, default_path)

        if not file_path.exists():
            raise NoteNotFoundError(f"File {file_path} not found")

        aliases = self._get_aliases_from_file(file_path)
        logger.info(
            "Get_aliases: Successfully retrieved aliases %s from %s", aliases, file_path
        )
        return aliases

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
        self._validate_alias(alias)

        effective_directory_str = (
            directory if directory else str(self.config.vault_path)
        )
        effective_directory_path = Path(effective_directory_str)

        if not effective_directory_path.is_dir():
            raise FileNotFoundError(
                f"Directory '{effective_directory_path}' not found or is not a directory."
            )

        normalized_target_alias = self._normalize_alias(alias)
        matching_files_paths: list[str] = []
        files_processed_count = 0

        for file_path in effective_directory_path.rglob("*.md"):
            files_processed_count += 1
            try:
                aliases_in_file = self._get_aliases_from_file(file_path)
                normalized_aliases_in_file = [
                    self._normalize_alias(a) for a in aliases_in_file
                ]

                if normalized_target_alias in normalized_aliases_in_file:
                    matching_files_paths.append(str(file_path))
            except Exception as e:
                logger.warning("Error checking aliases in %s: %s", file_path, e)
                continue

        logger.info(
            "Search_by_alias: Processed %d files in '%s'. Found %d notes with alias '%s'.",
            files_processed_count,
            effective_directory_path,
            len(matching_files_paths),
            alias,
        )
        return matching_files_paths


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
