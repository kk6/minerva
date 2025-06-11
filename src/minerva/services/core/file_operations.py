"""
File operations utilities for service modules.

This module provides common file operations including path building,
note assembly, and file validation utilities.
"""

import logging
from pathlib import Path
from typing import Any

import frontmatter

from minerva.config import MinervaConfig
from minerva.exceptions import ValidationError
from minerva.frontmatter_manager import FrontmatterManager

logger = logging.getLogger(__name__)


def validate_filename(*args: Any, **kwargs: Any) -> None:
    """Validate filename parameter is not empty."""
    # For create_note/edit_note: self, text, filename, author=None, default_path=None
    filename = None
    if len(args) >= 3:  # args[0] is self, args[1] is text, args[2] is filename
        filename = args[2]
    elif "filename" in kwargs:
        filename = kwargs["filename"]

    if filename is not None and not filename.strip():
        raise ValidationError("Filename cannot be empty or whitespace")


def validate_text_content(*args: Any, **kwargs: Any) -> None:
    """Validate text content parameter is not empty."""
    # For create_note/edit_note: self, text, filename, author=None, default_path=None
    text = None
    if len(args) >= 2:  # args[0] is self, args[1] is text
        text = args[1]
    elif "text" in kwargs:
        text = kwargs["text"]

    if text is not None and not text.strip():
        raise ValidationError("Text content cannot be empty or whitespace")


def build_file_path(
    config: MinervaConfig, filename: str, default_path: str | None = None
) -> tuple[Path, str]:
    """
    Resolve and build the complete file path from a filename.

    Args:
        config: Configuration instance containing paths and settings
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
    full_dir_path = config.vault_path

    # Add default_path first if it's not empty
    effective_default = default_path or config.default_note_dir
    if isinstance(effective_default, str) and effective_default.strip() != "":
        full_dir_path = full_dir_path / effective_default

    # Then add subdirectories if they exist
    if str(subdirs) != ".":
        full_dir_path = full_dir_path / subdirs

    return full_dir_path, base_filename


def assemble_complete_note(
    config: MinervaConfig,
    frontmatter_manager: FrontmatterManager,
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
    is_new_note: bool = True,
) -> tuple[Path, str, str]:
    """
    Assemble a complete note by combining file path resolution and content preparation.

    Args:
        config: Configuration instance containing paths and settings
        frontmatter_manager: Manager for frontmatter operations
        text: The content to write to the file
        filename: The name of the file to write
        author: The author name to add to the frontmatter
        default_path: The default directory to save the file
        is_new_note: Whether this is a new note (True) or an update to an existing note (False)

    Returns:
        tuple: (full_dir_path, base_filename, prepared_content)
    """
    # Build file path
    full_dir_path, base_filename = build_file_path(config, filename, default_path)

    # Check existing frontmatter
    file_path = full_dir_path / base_filename
    existing_frontmatter = frontmatter_manager.read_existing_metadata(file_path)

    # Generate metadata
    post = frontmatter_manager.generate_metadata(
        text=text,
        author=author or config.default_author,
        is_new_note=is_new_note,
        existing_frontmatter=existing_frontmatter,
    )

    content = frontmatter.dumps(post)

    return full_dir_path, base_filename, content


def resolve_note_file(
    config: MinervaConfig,
    filename: str | None,
    filepath: str | None,
    default_path: str | None,
) -> Path:
    """
    Resolve note file path from filename or filepath.

    Args:
        config: Configuration instance containing paths and settings
        filename: The name of the file
        filepath: The full path of the file
        default_path: The default directory path

    Returns:
        Path: Resolved file path

    Raises:
        ValueError: If neither filename nor filepath is provided
    """
    if filepath:
        return Path(filepath)
    elif filename:
        full_dir_path, base_filename = build_file_path(config, filename, default_path)
        return full_dir_path / base_filename
    else:
        raise ValueError("Either filename or filepath must be provided")


def load_note_with_frontmatter(file_path: Path) -> tuple["frontmatter.Post", dict]:
    """
    Load note and extract frontmatter metadata.

    Args:
        file_path: Path to the note file

    Returns:
        tuple: (frontmatter.Post object, metadata dict)

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    post = frontmatter.loads(content)
    return post, dict(post.metadata)
