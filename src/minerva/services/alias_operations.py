"""
Alias operations service module.

This module provides alias management operations including adding, removing,
retrieving, and searching aliases for notes in the Obsidian vault.
"""

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

import frontmatter

from minerva.error_handler import (
    log_performance,
    safe_operation,
)
from minerva.exceptions import NoteNotFoundError
from minerva.services.core.base_service import BaseService
from minerva.services.core.file_operations import resolve_note_file

if TYPE_CHECKING:
    from minerva.config import MinervaConfig
    from minerva.frontmatter_manager import FrontmatterManager

logger = logging.getLogger(__name__)


class AliasOperations(BaseService):
    """
    Service class for alias management operations.

    This class handles adding, removing, retrieving, and searching aliases
    in notes within the Obsidian vault, using the core infrastructure utilities.
    """

    def __init__(
        self, config: "MinervaConfig", frontmatter_manager: "FrontmatterManager"
    ) -> None:
        """
        Initialize AliasOperations with FrontmatterOperations dependency.

        Args:
            config: Configuration instance
            frontmatter_manager: Frontmatter manager instance
        """
        super().__init__(config, frontmatter_manager)

        # Initialize frontmatter operations for unified frontmatter handling
        from minerva.services.frontmatter_operations import FrontmatterOperations

        self._frontmatter_ops = FrontmatterOperations(config, frontmatter_manager)

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

    def _load_note_with_frontmatter(
        self, file_path: Path
    ) -> tuple["frontmatter.Post", dict[str, Any]]:
        """Load note and extract current frontmatter using FrontmatterOperations."""
        # Use the unified frontmatter operations
        return self._frontmatter_ops._load_note_with_frontmatter(file_path)

    def _get_aliases_from_file(self, file_path: Path) -> list[str]:
        """
        Get current aliases from a note's frontmatter.

        Args:
            file_path: Path to the note file

        Returns:
            list[str]: List of aliases (preserves original casing)
        """
        _, frontmatter_dict = self._load_note_with_frontmatter(file_path)
        aliases_value = frontmatter_dict.get("aliases", [])
        return list(aliases_value) if isinstance(aliases_value, list) else []

    def _save_note_with_updated_aliases(
        self, file_path: Path, post: "frontmatter.Post", aliases: list[str]
    ) -> Path:
        """
        Save note with updated aliases using FrontmatterOperations.

        Args:
            file_path: Path to the note file
            post: Frontmatter post object
            aliases: List of aliases to save

        Returns:
            Path: Path to the saved file
        """
        # Update frontmatter with new aliases
        frontmatter_dict = dict(post.metadata)
        if aliases:
            frontmatter_dict["aliases"] = aliases
        else:
            # Remove aliases field if no aliases remain
            frontmatter_dict.pop("aliases", None)

        # Use the unified frontmatter operations
        return self._frontmatter_ops._save_note_with_updated_frontmatter(
            file_path, post, frontmatter_dict
        )

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
        self._log_operation_start(
            "add_alias",
            alias=alias,
            filename=filename,
            filepath=filepath,
            allow_conflicts=allow_conflicts,
        )

        # Validate alias
        alias = self._validate_alias(alias)

        file_path = resolve_note_file(self.config, filename, filepath, default_path)

        # Check for conflicts unless explicitly allowed
        if not allow_conflicts:
            conflicts = self._check_alias_conflicts(alias, exclude_file=file_path)
            if conflicts:
                error = ValueError(
                    f"Alias '{alias}' conflicts with existing aliases or filenames in: {', '.join(conflicts)}"
                )
                self._log_operation_error("add_alias", error)
                raise error

        # Load current aliases
        current_aliases = self._get_aliases_from_file(file_path)
        normalized_current = [self._normalize_alias(a) for a in current_aliases]
        normalized_new = self._normalize_alias(alias)

        # Add alias if not already present
        if normalized_new not in normalized_current:
            current_aliases.append(alias)
            post, _ = self._load_note_with_frontmatter(file_path)
            written_path = self._save_note_with_updated_aliases(
                file_path, post, current_aliases
            )
            logger.info("Added alias '%s' to %s", alias, written_path.name)
            self._log_operation_success("add_alias", written_path)
            return written_path
        else:
            logger.info("Alias '%s' already exists in %s", alias, file_path.name)
            self._log_operation_success("add_alias", file_path)
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
        self._log_operation_start(
            "remove_alias", alias=alias, filename=filename, filepath=filepath
        )

        normalized_alias = self._normalize_alias(alias)
        file_path = resolve_note_file(self.config, filename, filepath, default_path)

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
            post, _ = self._load_note_with_frontmatter(file_path)
            written_path = self._save_note_with_updated_aliases(
                file_path, post, new_aliases
            )
            logger.info("Removed alias '%s' from %s", alias, written_path.name)
            self._log_operation_success("remove_alias", written_path)
            return written_path
        else:
            logger.info("Alias '%s' not found in %s", alias, file_path.name)
            self._log_operation_success("remove_alias", file_path)
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
        self._log_operation_start("get_aliases", filename=filename, filepath=filepath)

        file_path = resolve_note_file(self.config, filename, filepath, default_path)

        if not file_path.exists():
            error = NoteNotFoundError(f"File {file_path} not found")
            self._log_operation_error("get_aliases", error)
            raise error

        aliases = self._get_aliases_from_file(file_path)
        logger.info(
            "Get_aliases: Successfully retrieved aliases %s from %s", aliases, file_path
        )

        self._log_operation_success("get_aliases", aliases)
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
        self._log_operation_start("search_by_alias", alias=alias, directory=directory)

        self._validate_alias(alias)

        effective_directory_str = (
            directory if directory else str(self.config.vault_path)
        )
        effective_directory_path = Path(effective_directory_str)

        if not effective_directory_path.is_dir():
            error = FileNotFoundError(
                f"Directory '{effective_directory_path}' not found or is not a directory."
            )
            self._log_operation_error("search_by_alias", error)
            raise error

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

        self._log_operation_success("search_by_alias", matching_files_paths)
        return matching_files_paths
