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
    """Read a note from a file in the Obsidian vault."""
    return _read_note(service, filepath)


def search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]:
    """Search for a keyword in all files in the Obsidian vault."""
    return _search_notes(service, query, case_sensitive)


def create_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """Create a new note in the Obsidian vault."""
    return _create_note(service, text, filename, author, default_path)


def edit_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """Edit an existing note in the Obsidian vault."""
    return _edit_note(service, text, filename, author, default_path)


def get_note_delete_confirmation(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> dict[str, str]:
    """Get confirmation for deleting a note from the Obsidian vault."""
    return _get_note_delete_confirmation(service, filename, filepath, default_path)


def perform_note_delete(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """Perform the deletion of a note from the Obsidian vault."""
    return _perform_note_delete(service, filename, filepath, default_path)


def add_tag(
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """Add a specified tag to an existing note in the Obsidian vault."""
    return _add_tag(service, tag, filename, filepath, default_path)


def remove_tag(
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """Remove a specified tag from an existing note in the Obsidian vault."""
    return _remove_tag(service, tag, filename, filepath, default_path)


def rename_tag(
    old_tag: str,
    new_tag: str,
    directory: str | None = None,
) -> list[Path]:
    """Rename a tag in all notes within a specified directory (or the entire vault)."""
    return _rename_tag(service, old_tag, new_tag, directory)


def get_tags(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> list[str]:
    """Retrieve the list of tags from a specific note's frontmatter."""
    return _get_tags(service, filename, filepath, default_path)


def list_all_tags(directory: str | None = None) -> list[str]:
    """List all unique, normalized tags from all Markdown files within a specified directory."""
    return _list_all_tags(service, directory)


def find_notes_with_tag(tag: str, directory: str | None = None) -> list[str]:
    """Find all notes that contain a specific tag."""
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
