"""
Tools module providing service-based API for Minerva note operations.

This module serves as a bridge between the MCP server and the service layer,
providing clean tool functions that work with the service architecture.
"""

import logging
from pathlib import Path

from minerva.service import MinervaService, SearchResult

# Set up logging
logger = logging.getLogger(__name__)


def read_note(service: MinervaService, filepath: str) -> str:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        service: MinervaService instance
        filepath: The full path of the file to read

    Returns:
        str: The content of the file
    """
    return service.read_note(filepath)


def search_notes(
    service: MinervaService, query: str, case_sensitive: bool = True
) -> list[SearchResult]:
    """
    Search for a keyword in all files in the Obsidian vault.

    Args:
        service: MinervaService instance
        query: The keyword to search for
        case_sensitive: Whether the search should be case sensitive

    Returns:
        list[SearchResult]: A list of search results
    """
    return service.search_notes(query, case_sensitive)


def create_note(
    service: MinervaService,
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Create a new note in the Obsidian vault.

    Args:
        service: MinervaService instance
        text: The content to write to the file
        filename: The name of the file to write
        author: The author name to add to the frontmatter
        default_path: The default directory to save the file

    Returns:
        Path: The path to the created file

    Raises:
        FileExistsError: If the file already exists
    """
    return service.create_note(text, filename, author, default_path)


def edit_note(
    service: MinervaService,
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Edit an existing note in the Obsidian vault.

    Args:
        service: MinervaService instance
        text: The new content to write to the file
        filename: The name of the file to edit
        author: The author name to add to the frontmatter
        default_path: The default directory to save the file

    Returns:
        Path: The path to the edited file

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    return service.edit_note(text, filename, author, default_path)


def get_note_delete_confirmation(
    service: MinervaService,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> dict[str, str]:
    """
    Get confirmation for deleting a note from the Obsidian vault.

    Args:
        service: MinervaService instance
        filename: The name of the file to delete
        filepath: The full path of the file to delete
        default_path: The default directory to look for the file

    Returns:
        dict: Object with file path and confirmation message

    Raises:
        ValueError: If neither filename nor filepath is provided
        FileNotFoundError: If the file doesn't exist
    """
    return service.get_note_delete_confirmation(filename, filepath, default_path)


def perform_note_delete(
    service: MinervaService,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Perform the deletion of a note from the Obsidian vault.

    Args:
        service: MinervaService instance
        filename: The name of the file to delete
        filepath: The full path of the file to delete
        default_path: The default directory to look for the file

    Returns:
        Path: The path to the deleted file

    Raises:
        ValueError: If neither filename nor filepath is provided
        FileNotFoundError: If the file doesn't exist
    """
    return service.perform_note_delete(filename, filepath, default_path)


def add_tag(
    service: MinervaService,
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Add a specified tag to an existing note in the Obsidian vault.

    Args:
        service: MinervaService instance
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
    return service.add_tag(tag, filename, filepath, default_path)


def remove_tag(
    service: MinervaService,
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Remove a specified tag from an existing note in the Obsidian vault.

    Args:
        service: MinervaService instance
        tag: The tag to remove from the note
        filename: The name of the file to modify
        filepath: The full path of the file to modify
        default_path: The default directory path

    Returns:
        Path: The path of the modified note file

    Raises:
        FileNotFoundError: If the specified note file does not exist
    """
    return service.remove_tag(tag, filename, filepath, default_path)


def get_tags(
    service: MinervaService,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> list[str]:
    """
    Retrieve the list of tags from a specific note's frontmatter.

    Args:
        service: MinervaService instance
        filename: The name of the note file
        filepath: The full, absolute path to the note file
        default_path: The default directory path

    Returns:
        list[str]: A list of tag strings
    """
    return service.get_tags(filename, filepath, default_path)


def rename_tag(
    service: MinervaService,
    old_tag: str,
    new_tag: str,
    directory: str | None = None,
) -> list[Path]:
    """
    Rename a tag in all notes within a specified directory (or the entire vault).

    Args:
        service: MinervaService instance
        old_tag: The current tag string to be replaced
        new_tag: The new tag string to replace the old tag
        directory: Optional path to a directory within the vault

    Returns:
        list[Path]: A list of Path objects for each note file that was modified

    Raises:
        ValueError: If new_tag is invalid
        FileNotFoundError: If the specified directory does not exist
    """
    return service.rename_tag(old_tag, new_tag, directory)


def list_all_tags(
    service: MinervaService,
    directory: str | None = None,
) -> list[str]:
    """
    List all unique, normalized tags from all Markdown files within a specified directory.

    Args:
        service: MinervaService instance
        directory: Optional path to a directory within the vault

    Returns:
        list[str]: A sorted list of unique, normalized tag strings

    Raises:
        FileNotFoundError: If the specified directory does not exist
    """
    return service.list_all_tags(directory)


def find_notes_with_tag(
    service: MinervaService,
    tag: str,
    directory: str | None = None,
) -> list[str]:
    """
    Find all notes that contain a specific tag.

    Args:
        service: MinervaService instance
        tag: The tag to search for
        directory: Optional path to a directory within the vault

    Returns:
        list[str]: A list of string paths for each note file containing the specified tag

    Raises:
        FileNotFoundError: If the specified directory does not exist
    """
    return service.find_notes_with_tag(tag, directory)
