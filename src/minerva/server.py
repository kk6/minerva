# NOTE:
# When running this file from the command line (e.g. `uv run mcp dev src/minerva/server.py:mcp`),
# the parent directory is automatically added to sys.path, so absolute imports like `from minerva.tools import ...` work fine.
# However, when launched from Claude Desktop (see `claude_desktop_config.json`), the sys.path may not include the parent directory.
# In that case, adding the following lines ensures the minerva package can always be imported:
#
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
# This guarantees the minerva package is importable regardless of the execution context.

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP

from minerva.__version__ import __version__
from minerva.service import create_minerva_service
from minerva.tools import (
    read_note as _read_note,
    search_notes as _search_notes,
    create_note as _create_note,
    edit_note as _edit_note,
    get_note_delete_confirmation as _get_note_delete_confirmation,
    perform_note_delete as _perform_note_delete,
    add_tag as _add_tag,
    remove_tag as _remove_tag,
    rename_tag as _rename_tag,
    get_tags as _get_tags,
    list_all_tags as _list_all_tags,
    find_notes_with_tag as _find_notes_with_tag,
)
from minerva.file_handler import SearchResult

# Set up logging
logger = logging.getLogger(__name__)

# Initialize service layer with dependency injection
try:
    service = create_minerva_service()
    logger.info("MCP server initialized with dependency injection")
except Exception as e:
    logger.error("Failed to initialize service layer: %s", e)
    raise

# Create an MCP server
mcp = FastMCP("minerva", __version__)

# Create wrapper functions that bind the service instance
# These wrappers maintain the original function signatures for MCP


def read_note(filepath: str) -> str:
    """
    Read the content of a markdown note from your Obsidian vault.

    Use this to view the contents of any note file. The file path should be
    relative to your vault root or an absolute path.

    Example:
        read_note("daily/2023-06-08.md")
        read_note("/full/path/to/note.md")

    Args:
        filepath: Path to the note file you want to read

    Returns:
        The complete content of the note including any frontmatter

    Note:
        If the file doesn't exist, you'll get a FileNotFoundError
    """
    return _read_note(service, filepath)


def search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]:
    """
    Search for text across all markdown files in your Obsidian vault.

    This searches through the content of all notes and returns matches with
    context lines around each result.

    Example:
        search_notes("machine learning")
        search_notes("TODO", case_sensitive=False)

    Args:
        query: The text you want to search for
        case_sensitive: Whether to match exact case (default: True)

    Returns:
        List of search results with file paths, line numbers, and matching content

    Note:
        Binary files are automatically skipped during search
    """
    return _search_notes(service, query, case_sensitive)


def create_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Create a new markdown note in your Obsidian vault.

    This creates a new note with frontmatter (metadata) automatically added.
    The frontmatter includes creation date, author, and tags fields.

    Example:
        create_note("# My New Note\n\nThis is the content", "my-note.md")
        create_note("Daily standup notes", "standup-2023-06-08.md", "John", "meetings")

    Args:
        text: The markdown content for your note
        filename: Name for the new file (should end with .md)
        author: Your name to add to frontmatter (optional)
        default_path: Subfolder within your vault to save the note (optional)

    Returns:
        Path to the newly created note file

    Note:
        If a file with the same name already exists, you'll get a FileExistsError
    """
    return _create_note(service, text, filename, author, default_path)


def edit_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Update the content of an existing note in your Obsidian vault.

    This replaces the entire content while preserving existing frontmatter.
    The modification date in frontmatter is automatically updated.

    Example:
        edit_note("# Updated Title\n\nNew content", "existing-note.md")
        edit_note("Updated meeting notes", "standup.md", "John", "meetings")

    Args:
        text: The new markdown content for your note
        filename: Name of the existing file to edit
        author: Your name to update in frontmatter (optional)
        default_path: Subfolder to look for the file (optional)

    Returns:
        Path to the updated note file

    Note:
        If the file doesn't exist, you'll get a FileNotFoundError
    """
    return _edit_note(service, text, filename, author, default_path)


def get_note_delete_confirmation(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> dict[str, str]:
    """
    Get confirmation details before deleting a note (safety step).

    This is the first step of a two-phase deletion process. It shows you
    what will be deleted without actually deleting anything yet.

    Example:
        get_note_delete_confirmation(filename="old-note.md")
        get_note_delete_confirmation(filepath="/full/path/to/note.md")

    Args:
        filename: Name of the file to delete (provide this OR filepath)
        filepath: Full path to the file to delete (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        Dict with file path and confirmation message about what will be deleted

    Note:
        You must provide either filename or filepath. Use perform_note_delete() after this.
    """
    return _get_note_delete_confirmation(service, filename, filepath, default_path)


def perform_note_delete(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Actually delete a note from your Obsidian vault (final step).

    This is the second step of a two-phase deletion process. Use
    get_note_delete_confirmation() first to see what will be deleted.

    Example:
        perform_note_delete(filename="old-note.md")
        perform_note_delete(filepath="/full/path/to/note.md")

    Args:
        filename: Name of the file to delete (provide this OR filepath)
        filepath: Full path to the file to delete (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        Path to the file that was deleted

    Warning:
        This permanently deletes the file! Use get_note_delete_confirmation() first.
    """
    return _perform_note_delete(service, filename, filepath, default_path)


def add_tag(
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Add a tag to an existing note's frontmatter.

    Tags help organize and categorize your notes in Obsidian. The tag is
    added to the frontmatter 'tags' list if it doesn't already exist.

    Example:
        add_tag("project-alpha", filename="meeting-notes.md")
        add_tag("urgent", filepath="/full/path/to/note.md")

    Args:
        tag: The tag to add (without # symbol)
        filename: Name of the file to modify (provide this OR filepath)
        filepath: Full path to the file to modify (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        Path to the modified note file

    Note:
        If the tag already exists, the tag list remains unchanged but the note's
        timestamp is still updated
    """
    return _add_tag(service, tag, filename, filepath, default_path)


def remove_tag(
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Remove a tag from an existing note's frontmatter.

    This removes the specified tag from the note's frontmatter 'tags' list.
    The note content itself remains unchanged.

    Example:
        remove_tag("draft", filename="published-post.md")
        remove_tag("outdated", filepath="/full/path/to/note.md")

    Args:
        tag: The tag to remove (without # symbol)
        filename: Name of the file to modify (provide this OR filepath)
        filepath: Full path to the file to modify (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        Path to the modified note file

    Note:
        If the tag doesn't exist, the tag list remains unchanged but the note's
        timestamp is still updated
    """
    return _remove_tag(service, tag, filename, filepath, default_path)


def rename_tag(
    old_tag: str,
    new_tag: str,
    directory: str | None = None,
) -> list[Path]:
    """
    Rename a tag across multiple notes in your vault or a specific folder.

    This finds all notes with the old tag and replaces it with the new tag.
    Useful for reorganizing your tagging system.

    Example:
        rename_tag("old-project", "archived-project")
        rename_tag("temp", "draft", directory="blog-posts")

    Args:
        old_tag: The current tag name to replace
        new_tag: The new tag name to use instead
        directory: Specific folder to process (if None, processes entire vault)

    Returns:
        List of paths to all notes that were modified

    Note:
        This operation can modify many files at once - use carefully!
    """
    return _rename_tag(service, old_tag, new_tag, directory)


def get_tags(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> list[str]:
    """
    Get all tags from a specific note's frontmatter.

    This returns the list of tags currently assigned to a note.
    Tags are read from the frontmatter 'tags' field.

    Example:
        get_tags(filename="project-notes.md")
        get_tags(filepath="/full/path/to/note.md")

    Args:
        filename: Name of the file to check (provide this OR filepath)
        filepath: Full path to the file to check (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        List of tag strings assigned to the note

    Note:
        Returns empty list if the note has no tags or no frontmatter
    """
    return _get_tags(service, filename, filepath, default_path)


def list_all_tags(directory: str | None = None) -> list[str]:
    """
    Get a complete list of all unique tags used across your vault.

    This scans all markdown files and collects every unique tag from
    their frontmatter, returning them in alphabetical order.

    Example:
        list_all_tags()
        list_all_tags(directory="projects")

    Args:
        directory: Specific folder to scan (if None, scans entire vault)

    Returns:
        Sorted list of all unique tags found

    Note:
        Useful for getting an overview of your tagging system
    """
    return _list_all_tags(service, directory)


def find_notes_with_tag(tag: str, directory: str | None = None) -> list[str]:
    """
    Find all notes that have a specific tag assigned.

    This searches through all notes and returns the file paths of those
    that contain the specified tag in their frontmatter.

    Example:
        find_notes_with_tag("project-alpha")
        find_notes_with_tag("urgent", directory="inbox")

    Args:
        tag: The tag to search for (without # symbol)
        directory: Specific folder to search (if None, searches entire vault)

    Returns:
        List of file paths for notes containing the tag

    Note:
        Great for finding all notes related to a specific topic or project
    """
    return _find_notes_with_tag(service, tag, directory)


# Register tools with MCP server
mcp.add_tool(read_note)
mcp.add_tool(search_notes)
mcp.add_tool(create_note)
mcp.add_tool(edit_note)
mcp.add_tool(get_note_delete_confirmation)
mcp.add_tool(perform_note_delete)
mcp.add_tool(add_tag)
mcp.add_tool(remove_tag)
mcp.add_tool(rename_tag)
mcp.add_tool(get_tags)
mcp.add_tool(list_all_tags)
mcp.add_tool(find_notes_with_tag)
