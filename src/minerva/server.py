import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from minerva.__version__ import __version__
from minerva.service import create_minerva_service
from minerva.file_handler import SearchResult

# Set up logging
logger = logging.getLogger(__name__)

# Lazy initialization of service layer to support testing
service = None


def get_service():
    """Get or create the service instance."""
    global service
    if service is None:
        try:
            service = create_minerva_service()
            logger.info("MCP server initialized with dependency injection")
        except Exception as e:
            logger.error("Failed to initialize service layer: %s", e)
            raise
    return service


# Create an MCP server
mcp = FastMCP("minerva", __version__)


@mcp.tool()
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
    return get_service().read_note(filepath)


@mcp.tool()
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
    return get_service().search_notes(query, case_sensitive)


@mcp.tool()
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
    return get_service().create_note(text, filename, author, default_path)


@mcp.tool()
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
    return get_service().edit_note(text, filename, author, default_path)


@mcp.tool()
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
    return get_service().get_note_delete_confirmation(filename, filepath, default_path)


@mcp.tool()
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
    return get_service().perform_note_delete(filename, filepath, default_path)


@mcp.tool()
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
    return get_service().add_tag(tag, filename, filepath, default_path)


@mcp.tool()
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
    return get_service().remove_tag(tag, filename, filepath, default_path)


@mcp.tool()
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
    return get_service().rename_tag(old_tag, new_tag, directory)


@mcp.tool()
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
    return get_service().get_tags(filename, filepath, default_path)


@mcp.tool()
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
    return get_service().list_all_tags(directory)


@mcp.tool()
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
    return get_service().find_notes_with_tag(tag, directory)


@mcp.tool()
def add_alias(
    alias: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
    allow_conflicts: bool = False,
) -> Path:
    """
    Add an alias to an existing note's frontmatter.

    Aliases provide alternative names for notes, making them easier to reference
    and discover. They're stored in the frontmatter 'aliases' field and are
    compatible with Obsidian's alias system.

    Example:
        add_alias("last week's meeting", filename="meeting_20250523.md")
        add_alias("May review", filepath="/full/path/to/note.md")

    Args:
        alias: The alias to add to the note
        filename: Name of the file to modify (provide this OR filepath)
        filepath: Full path to the file to modify (provide this OR filename)
        default_path: Subfolder to look for the file (optional)
        allow_conflicts: Whether to allow aliases that conflict with existing filenames or aliases

    Returns:
        Path to the modified note file

    Note:
        By default, prevents adding aliases that conflict with existing filenames
        or other aliases. Set allow_conflicts=True to override this protection.
    """
    return get_service().add_alias(
        alias, filename, filepath, default_path, allow_conflicts
    )


@mcp.tool()
def remove_alias(
    alias: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> Path:
    """
    Remove an alias from an existing note's frontmatter.

    This removes the specified alias from the note's aliases list.
    Alias matching is case-insensitive.

    Example:
        remove_alias("old name", filename="updated-note.md")
        remove_alias("temp alias", filepath="/full/path/to/note.md")

    Args:
        alias: The alias to remove from the note
        filename: Name of the file to modify (provide this OR filepath)
        filepath: Full path to the file to modify (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        Path to the modified note file

    Note:
        If the alias doesn't exist, the note's timestamp is still updated
    """
    return get_service().remove_alias(alias, filename, filepath, default_path)


@mcp.tool()
def get_aliases(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
) -> list[str]:
    """
    Get all aliases from a specific note's frontmatter.

    This returns the list of aliases currently assigned to a note.
    Aliases are read from the frontmatter 'aliases' field.

    Example:
        get_aliases(filename="project-notes.md")
        get_aliases(filepath="/full/path/to/note.md")

    Args:
        filename: Name of the file to check (provide this OR filepath)
        filepath: Full path to the file to check (provide this OR filename)
        default_path: Subfolder to look for the file (optional)

    Returns:
        List of alias strings assigned to the note

    Note:
        Returns empty list if the note has no aliases or no frontmatter
    """
    return get_service().get_aliases(filename, filepath, default_path)


@mcp.tool()
def search_by_alias(alias: str, directory: str | None = None) -> list[str]:
    """
    Find notes that have a specific alias.

    This searches through all notes and returns the file paths of those
    that contain the specified alias in their frontmatter.

    Example:
        search_by_alias("meeting notes")
        search_by_alias("project alpha", directory="projects")

    Args:
        alias: The alias to search for
        directory: Specific folder to search (if None, searches entire vault)

    Returns:
        List of file paths for notes containing the alias

    Note:
        Alias matching is case-insensitive. Useful for finding notes by
        their alternative names or natural language references.
    """
    return get_service().search_by_alias(alias, directory)
