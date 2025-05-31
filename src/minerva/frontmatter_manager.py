"""
Frontmatter management module for Minerva.

This module provides centralized frontmatter processing functionality for Obsidian notes,
including metadata generation, reading, and tag management operations.
"""

import logging
from datetime import datetime
from pathlib import Path

import frontmatter

from minerva.config import DEFAULT_NOTE_AUTHOR
from minerva.validators import TagValidator

# Set up logging
logger = logging.getLogger(__name__)


class FrontmatterManager:
    """
    YAML frontmatter metadata management for Obsidian notes.

    This class centralizes all frontmatter-related operations including
    generation, reading, updating, and tag management. It provides a clean
    interface for metadata operations while maintaining consistency and
    preserving existing data.
    """

    def __init__(self, default_author: str | None = None):
        """
        Initialize FrontmatterManager with optional default author.

        Args:
            default_author: Default author name for new notes. If None,
                          uses the system default from config.
        """
        self.default_author = default_author or DEFAULT_NOTE_AUTHOR

    def _load_post(self, text: str) -> frontmatter.Post:
        """
        Load frontmatter from text.

        Args:
            text: Text content to load frontmatter from.

        Returns:
            frontmatter.Post: Post object with frontmatter.
        """
        has_frontmatter = text.startswith("---\n")
        if has_frontmatter:
            return frontmatter.loads(text)
        else:
            return frontmatter.Post(text)

    def _merge_existing_metadata(
        self, post: frontmatter.Post, existing_frontmatter: dict | None
    ) -> None:
        """
        Merge existing frontmatter into post metadata.

        Args:
            post: Post object to update
            existing_frontmatter: Existing frontmatter data
        """
        if not existing_frontmatter:
            return

        # Copy all existing metadata except special fields we handle manually
        # This preserves custom fields that might be present in the existing frontmatter
        for key, value in existing_frontmatter.items():
            # Skip fields we'll handle separately: author, created, updated, tags
            if key not in ["author", "created", "updated", "tags"]:
                post.metadata[key] = value

    def _set_author(self, post: frontmatter.Post, author: str | None) -> None:
        """
        Set author metadata in post.

        Args:
            post: Post object to update
            author: Author to set
        """
        final_author = author or self.default_author
        if final_author:
            post.metadata["author"] = final_author

    def _set_timestamp_fields(
        self,
        post: frontmatter.Post,
        is_new_note: bool,
        existing_frontmatter: dict | None,
    ) -> None:
        """
        Set created and updated timestamp fields.

        Args:
            post: Post object to update
            is_new_note: Whether this is a new note
            existing_frontmatter: Existing frontmatter data
        """
        now = datetime.now().isoformat()

        # Handle created field
        if existing_frontmatter and "created" in existing_frontmatter:
            # Preserve existing created field
            post.metadata["created"] = existing_frontmatter["created"]
        elif is_new_note:
            # Add created field for new notes only if it doesn't exist
            if "created" not in post.metadata:
                post.metadata["created"] = now

        # Handle updated field
        if not is_new_note:
            # Always update the 'updated' field for existing notes
            post.metadata["updated"] = now

    def _process_tags(
        self,
        post: frontmatter.Post,
        tags: list[str] | None,
        existing_frontmatter: dict | None,
    ) -> None:
        """
        Process and set tags metadata.

        Args:
            post: Post object to update
            tags: Tags to process
            existing_frontmatter: Existing frontmatter data
        """
        if tags is not None:
            # Tags were explicitly provided (even if empty list)
            if tags:
                # Validate and normalize tags
                normalized_tags = []
                for tag in tags:
                    try:
                        TagValidator.validate_tag(tag)
                        normalized_tag = TagValidator.normalize_tag(tag)
                        if normalized_tag not in normalized_tags:
                            normalized_tags.append(normalized_tag)
                    except ValueError as e:
                        logger.warning("Invalid tag '%s' dropped: %s", tag, e)

                if normalized_tags:
                    post.metadata["tags"] = normalized_tags
                else:
                    # All tags were invalid, remove tags field if it exists
                    post.metadata.pop("tags", None)
            else:
                # Empty list provided - remove tags
                post.metadata.pop("tags", None)
        else:
            # No tags parameter provided - preserve existing tags
            if existing_frontmatter and "tags" in existing_frontmatter:
                post.metadata["tags"] = existing_frontmatter["tags"]

    def generate_metadata(
        self,
        text: str,
        author: str | None = None,
        is_new_note: bool = True,
        existing_frontmatter: dict | None = None,
        tags: list[str] | None = None,
    ) -> frontmatter.Post:
        """
        Generate or update YAML frontmatter metadata for a note.

        This method processes only the metadata portion of a note (frontmatter),
        handling both creation of new metadata and updating of existing metadata.
        It does not perform any file operations or path manipulations.

        Args:
            text: The text content of the note (with or without existing frontmatter).
            author: The author name to include in the metadata.
            is_new_note: Whether this is a new note (True) or an update to an existing note (False).
            existing_frontmatter: Existing frontmatter data from the file (if any).
            tags: An optional list of tags. If provided (even as an empty list),
                  it will replace any existing tags after normalization and validation.
                  Invalid tags are logged and dropped. Duplicates are removed.
                  If an empty list is provided, existing tags will be removed.
                  If `None` (default), existing tags are preserved.

        Returns:
            frontmatter.Post: Post object with properly processed frontmatter.

        Note:
            This method only handles the metadata portion of a note.
            It does not perform any file path resolution or file I/O operations.
        """
        # Load the post from text
        post = self._load_post(text)

        # Update metadata fields
        self._merge_existing_metadata(post, existing_frontmatter)
        self._set_author(post, author)
        self._set_timestamp_fields(post, is_new_note, existing_frontmatter)
        self._process_tags(post, tags, existing_frontmatter)

        return post

    def read_existing_metadata(self, file_path: Path) -> dict | None:
        """
        Read and extract frontmatter metadata from an existing file.

        This method focuses only on retrieving the YAML frontmatter metadata
        from an existing file, without modifying the file or its content.

        Args:
            file_path: Path to the file to read

        Returns:
            dict | None: Existing frontmatter metadata as a dictionary, or:
                - Empty dict ({}) if the file exists but has no frontmatter
                - None if the file doesn't exist or can't be read as text

        Raises:
            PermissionError: When the file exists but cannot be accessed due to permission issues
        """
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.startswith("---\n"):  # If frontmatter exists
                    post = frontmatter.loads(content)
                    metadata = dict(post.metadata)
                    # Ensure date values are consistently processed as strings
                    for key, value in metadata.items():
                        if isinstance(value, datetime):
                            metadata[key] = value.isoformat()
                    return metadata
                # No frontmatter found in file
                return {}
        except PermissionError as e:
            logger.error("Permission denied when reading file %s: %s", file_path, e)
            raise
        except UnicodeDecodeError as e:
            logger.warning(
                "File %s cannot be decoded as text (possibly binary): %s", file_path, e
            )
            return None
        except (IOError, OSError) as e:
            logger.warning(
                "I/O or OS error reading existing file %s for metadata: %s",
                file_path,
                e,
            )
            return None
        except Exception as e:
            logger.warning(
                "Unexpected error processing file %s for metadata: %s", file_path, e
            )
            return None

    def update_tags(self, file_path: Path, tags: list[str]) -> None:
        """
        Update tags in an existing note's frontmatter.

        This method replaces all existing tags with the provided list.

        Args:
            file_path: Path to the note file
            tags: List of tags to set (replaces existing tags)

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be accessed
            ValueError: If any tags are invalid
        """
        # Read existing content
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.error("Error reading file %s: %s", file_path, e)
            raise

        # Read existing metadata
        existing_metadata = self.read_existing_metadata(file_path)

        # Generate updated metadata with new tags
        post = self.generate_metadata(
            text=content,
            is_new_note=False,
            existing_frontmatter=existing_metadata,
            tags=tags,
        )

        # Write back to file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
        except (IOError, OSError) as e:
            logger.error("Error writing file %s: %s", file_path, e)
            raise

    def add_tag(self, file_path: Path, tag: str) -> None:
        """
        Add a single tag to an existing note's frontmatter.

        If the tag already exists (after normalization), it won't be added again.

        Args:
            file_path: Path to the note file
            tag: Tag to add

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be accessed
            ValueError: If the tag is invalid
        """
        # Validate tag first
        TagValidator.validate_tag(tag)
        normalized_tag = TagValidator.normalize_tag(tag)

        # Get current tags
        current_tags = self.get_tags(file_path)

        # Add tag if not already present (after normalization)
        normalized_current = [TagValidator.normalize_tag(t) for t in current_tags]
        if normalized_tag not in normalized_current:
            current_tags.append(tag)  # Add original tag, not normalized
            self.update_tags(file_path, current_tags)

    def remove_tag(self, file_path: Path, tag: str) -> None:
        """
        Remove a single tag from an existing note's frontmatter.

        Tag matching is case-insensitive and uses normalized forms.

        Args:
            file_path: Path to the note file
            tag: Tag to remove

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be accessed
        """
        normalized_target = TagValidator.normalize_tag(tag)

        # Get current tags
        current_tags = self.get_tags(file_path)

        # Remove matching tags (case-insensitive)
        updated_tags = []
        for current_tag in current_tags:
            if TagValidator.normalize_tag(current_tag) != normalized_target:
                updated_tags.append(current_tag)

        # Update tags (this will handle the case where no tags remain)
        self.update_tags(file_path, updated_tags)

    def get_tags(self, file_path: Path) -> list[str]:
        """
        Get current tags from a note's frontmatter.

        Args:
            file_path: Path to the note file

        Returns:
            list[str]: List of tags (preserves original casing)
        """
        existing_metadata = self.read_existing_metadata(file_path)
        if existing_metadata is None:
            return []

        tags = existing_metadata.get("tags", [])
        if not isinstance(tags, list):
            return []

        return tags
