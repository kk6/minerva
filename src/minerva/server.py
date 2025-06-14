import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from minerva.__version__ import __version__
from minerva.services.service_manager import ServiceManager, create_minerva_service
from minerva.file_handler import SearchResult, SemanticSearchResult

# Set up logging
logger = logging.getLogger(__name__)

# Lazy initialization of service layer to support testing
service: ServiceManager | None = None


def get_service() -> ServiceManager:
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
def semantic_search(
    query: str,
    limit: int = 10,
    threshold: float | None = None,
    directory: str | None = None,
) -> list[SemanticSearchResult]:
    """
    Perform semantic search using AI embeddings to find conceptually similar notes.

    This uses vector similarity to find notes that are semantically related to your
    query, even if they don't contain the exact keywords. Great for discovering
    connections and related content.

    Example:
        semantic_search("machine learning concepts")
        semantic_search("project planning", limit=5, threshold=0.7)
        semantic_search("data analysis", directory="research")

    Args:
        query: Natural language description of what you're looking for
        limit: Maximum number of results to return (default: 10)
        threshold: Minimum similarity score 0.0-1.0 (optional, filters weak matches)
        directory: Specific folder to search in (optional, searches entire vault)

    Returns:
        List of semantic search results with similarity scores and content previews

    Note:
        Requires vector search to be enabled (VECTOR_SEARCH_ENABLED=true) and
        notes to be indexed first. Install dependencies: sentence-transformers, duckdb
    """
    return get_service().search_operations.semantic_search(
        query, limit, threshold, directory
    )


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


@mcp.tool()
def debug_vector_schema() -> dict:
    """
    Debug vector schema and embedding information.

    Returns detailed information about the current database state and embeddings.
    """

    service = get_service()
    if not service.config.vector_search_enabled:
        raise RuntimeError("Vector search is not enabled in configuration")

    if not service.config.vector_db_path:
        raise RuntimeError("Vector database path is not configured")

    try:
        from minerva.vector.embeddings import SentenceTransformerProvider
        from minerva.vector.indexer import VectorIndexer

        # Test embedding generation
        embedding_provider = SentenceTransformerProvider(service.config.embedding_model)
        test_text = "This is a test sentence for embedding."
        test_embedding = embedding_provider.embed(test_text)

        # Ensure we get the first embedding if it's a batch
        if test_embedding.ndim == 2:
            test_embedding = test_embedding[0]

        # Check database state
        indexer = VectorIndexer(service.config.vector_db_path)
        db_exists = service.config.vector_db_path.exists()

        result = {
            "embedding_model": service.config.embedding_model,
            "test_embedding_dimension": len(test_embedding),
            "test_embedding_type": str(type(test_embedding)),
            "database_path": str(service.config.vector_db_path),
            "database_exists": db_exists,
        }

        if db_exists:
            try:
                conn = indexer._get_connection()
                # Check if tables exist
                tables_result = conn.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name IN ('vectors', 'indexed_files')
                """).fetchall()
                result["existing_tables"] = [row[0] for row in tables_result]

                # If vectors table exists, check its schema
                if any(table[0] == "vectors" for table in tables_result):
                    schema_result = conn.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = 'vectors'
                    """).fetchall()
                    result["vectors_table_schema"] = {
                        row[0]: row[1] for row in schema_result
                    }

                indexer.close()
            except Exception as e:
                result["database_error"] = str(e)

        return result

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def reset_vector_database() -> dict[str, str]:
    """
    Completely reset the vector database by deleting the database file.

    This is useful when encountering dimension mismatch errors that cannot
    be resolved by force_rebuild alone.

    Returns:
        Dict with status message
    """
    import os

    service = get_service()
    if not service.config.vector_search_enabled:
        raise RuntimeError("Vector search is not enabled in configuration")

    if not service.config.vector_db_path:
        raise RuntimeError("Vector database path is not configured")

    try:
        db_path = service.config.vector_db_path
        if db_path.exists():
            os.remove(str(db_path))
            return {"status": f"Successfully deleted vector database at {db_path}"}
        else:
            return {"status": f"Vector database file does not exist at {db_path}"}
    except Exception as e:
        return {"status": f"Failed to delete vector database: {e}"}


def _initialize_batch_schema(
    indexer, embedding_provider, all_files, force_rebuild
) -> None:
    """Helper function to initialize schema for batch processing."""
    from minerva.vector.indexer import VectorIndexer

    if not all_files:
        return

    with open(all_files[0], "r", encoding="utf-8") as f:
        sample_content = f.read()[:500]
    sample_embedding = embedding_provider.embed(sample_content)

    if force_rebuild:
        try:
            conn = indexer._get_connection()
            conn.execute("DROP TABLE IF EXISTS vectors")
            conn.execute("DROP TABLE IF EXISTS indexed_files")
            conn.execute("DROP SEQUENCE IF EXISTS vectors_id_seq")
            # Also close and recreate the connection to ensure clean state
            indexer.close()
            indexer = VectorIndexer(indexer.db_path)
        except Exception:
            pass  # Ignore errors if tables don't exist

    # Get the actual embedding dimension (shape[1] for 2D array)
    embedding_dim = (
        sample_embedding.shape[1]
        if sample_embedding.ndim == 2
        else len(sample_embedding)
    )
    indexer.initialize_schema(embedding_dim)


def _process_batch_files(indexer, embedding_provider, all_files, force_rebuild):
    """Helper function to process files in batch."""
    processed = 0
    skipped = 0
    errors = []

    for file_path in all_files:
        try:
            # Skip if already indexed and not forcing rebuild
            if not force_rebuild and indexer.is_file_indexed(file_path):
                skipped += 1
                continue

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate embedding
            embedding = embedding_provider.embed(content)

            # Store in index
            indexer.store_embedding(file_path, embedding, content)
            processed += 1

        except Exception as e:
            error_msg = f"Failed to process {file_path}: {e}"
            errors.append(error_msg)

    return processed, skipped, errors


@mcp.tool()
def build_vector_index_batch(
    directory: str | None = None,
    file_pattern: str = "*.md",
    max_files: int = 5,
    force_rebuild: bool = False,
) -> dict[str, int | list[str]]:
    """
    Build vector index for a small batch of files to avoid timeouts.

    This processes only a limited number of files at once for MCP Inspector testing.

    Args:
        directory: Specific folder to index (if None, indexes entire vault)
        file_pattern: File pattern to match (default: "*.md")
        max_files: Maximum number of files to process in this batch (default: 5)
        force_rebuild: Whether to rebuild existing embeddings (default: False)

    Returns:
        Dict with 'processed' (count), 'skipped' (count), and 'errors' (list) keys
    """
    import glob
    import os

    service = get_service()
    if not service.config.vector_search_enabled:
        raise RuntimeError("Vector search is not enabled in configuration")

    if not service.config.vector_db_path:
        raise RuntimeError("Vector database path is not configured")

    try:
        from minerva.vector.embeddings import SentenceTransformerProvider
        from minerva.vector.indexer import VectorIndexer

        # Initialize components
        embedding_provider = SentenceTransformerProvider(service.config.embedding_model)
        indexer = VectorIndexer(service.config.vector_db_path)

        # Determine directory to process
        target_dir = directory or str(service.config.vault_path)

        # Find files to process (limit to max_files)
        search_pattern = os.path.join(target_dir, "**", file_pattern)
        all_files = glob.glob(search_pattern, recursive=True)[:max_files]

        # Initialize schema if needed
        try:
            _initialize_batch_schema(
                indexer, embedding_provider, all_files, force_rebuild
            )
        except Exception as e:
            return {
                "processed": 0,
                "skipped": 0,
                "errors": [f"Schema initialization failed: {e}"],
            }

        # Process files
        processed, skipped, errors = _process_batch_files(
            indexer, embedding_provider, all_files, force_rebuild
        )

        # Close connections
        indexer.close()

        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total_files_found": len(all_files),
        }

    except ImportError as e:
        raise ImportError(
            "Vector search requires additional dependencies. "
            "Install with: pip install sentence-transformers duckdb"
        ) from e


@mcp.tool()
def build_vector_index(
    directory: str | None = None,
    file_pattern: str = "*.md",
    force_rebuild: bool = False,
) -> dict[str, int | list[str]]:
    """
    Build or update the vector search index for semantic search.

    This processes markdown files and creates vector embeddings for semantic search.
    Existing embeddings are preserved unless force_rebuild is True.

    Example:
        build_vector_index()
        build_vector_index(directory="research", force_rebuild=True)
        build_vector_index(file_pattern="*.txt")

    Args:
        directory: Specific folder to index (if None, indexes entire vault)
        file_pattern: File pattern to match (default: "*.md")
        force_rebuild: Whether to rebuild existing embeddings (default: False)

    Returns:
        Dict with 'processed' (count), 'skipped' (count), and 'errors' (list) keys

    Note:
        Requires vector search to be enabled (VECTOR_SEARCH_ENABLED=true).
        This can take time for large vaults. Progress is logged.
    """
    return get_service().build_vector_index(directory, file_pattern, force_rebuild)


@mcp.tool()
def get_vector_index_status() -> dict[str, int | bool | str]:
    """
    Get information about the current vector search index status.

    This shows how many files are indexed and whether vector search is available.
    Useful for checking if semantic search is ready to use.

    Example:
        get_vector_index_status()

    Returns:
        Dict with index statistics and availability status

    Note:
        Returns meaningful data only if vector search is enabled
    """
    return get_service().get_vector_index_status()
