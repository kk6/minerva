import functools
import logging
import os
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar

from minerva.service import MinervaService

import frontmatter
from pydantic import BaseModel, Field, field_validator, model_validator

from minerva.file_handler import (
    FileWriteRequest,
    write_file,
    FileReadRequest,
    read_file,
    FileDeleteRequest,
    delete_file,
    SearchConfig,
    SearchResult,
    search_keyword_in_files,
)
from minerva.validators import FilenameValidator, TagValidator
from minerva.frontmatter_manager import FrontmatterManager

from minerva.config import VAULT_PATH, DEFAULT_NOTE_DIR

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for decorator
P = ParamSpec("P")
R = TypeVar("R")


def handle_file_operations(
    operation_name: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for unified error handling in file operations.

    This decorator provides consistent error handling and logging for file operations
    across the application. It handles common exceptions that occur during file I/O
    operations and provides standardized error logging.

    Args:
        operation_name: A descriptive name of the operation being performed,
                       used in error messages and logging.

    Returns:
        A decorator function that wraps the target function with error handling.

    The decorator handles these exception types:
    - PermissionError: Access denied to files or directories
    - IOError/OSError: File system related errors
    - Exception: Unexpected errors (re-raised as RuntimeError with context)

    Note:
        - FileExistsError, FileNotFoundError, and ValueError are passed through unchanged
          as they represent expected business logic conditions that calling code should handle
        - The decorator preserves the original function's signature and return value
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except PermissionError as e:
                logger.error("Permission denied during %s: %s", operation_name, e)
                raise
            except (IOError, OSError) as e:
                logger.error("File system error during %s: %s", operation_name, e)
                raise
            except Exception as e:
                # Let FileExistsError, FileNotFoundError, and ValueError pass through
                if isinstance(e, (FileExistsError, FileNotFoundError, ValueError)):
                    raise
                logger.error("Unexpected error during %s: %s", operation_name, e)
                raise RuntimeError(
                    f"Unexpected error during {operation_name}: {e}"
                ) from e

        return wrapper

    return decorator


class ReadNoteRequest(BaseModel):
    """
    Request model for reading a note from a file.

    This model contains the filepath of the file to read.

    Attributes:
        filepath (str): The full path of the file to read.
    """

    filepath: str = Field(..., description="The full path of the file to read.")


class DeleteConfirmationResult(BaseModel):
    """
    Result model for delete note confirmation.

    This model contains the file path that would be deleted and a confirmation message.

    Attributes:
        file_path (str): The path to the file that would be deleted.
        message (str): Confirmation message.
    """

    file_path: str = Field(
        ..., description="The path to the file that would be deleted."
    )
    message: str = Field(..., description="Confirmation message.")


class DeleteNoteRequest(BaseModel):
    """
    Request model for deleting a note.

    This model contains either the filename or the full filepath of the note to delete.

    Attributes:
        filename (str, optional): The name of the file to delete. If it doesn't have a .md extension, it will be added.
        filepath (str, optional): The full path of the file to delete. If provided, filename is ignored.
        default_path (str): The default directory to look for the file. Default is the value of DEFAULT_NOTE_DIR.
        confirm (bool): Whether to confirm the deletion. If False, only returns what would be deleted without actually deleting.
    """

    filename: str | None = Field(None, description="The name of the file to delete.")
    filepath: str | None = Field(
        None, description="The full path of the file to delete."
    )
    default_path: str = Field(
        DEFAULT_NOTE_DIR, description="The default path to look for the file."
    )

    @field_validator("filename")
    def format_filename(cls, v: str | None) -> str | None:
        """
        Format the filename to ensure it has a .md extension if not None.
        """
        if v is not None:
            FilenameValidator.validate_filename_with_subdirs(v)
            if ".md" not in v:
                v = f"{v}.md"
        return v

    @model_validator(mode="after")
    def validate_input(self) -> "DeleteNoteRequest":
        """
        Validate that at least one of filename or filepath is provided.
        """
        if self.filename is None and self.filepath is None:
            raise ValueError("Either filename or filepath must be provided")
        return self


class SearchNoteRequest(BaseModel):
    """
    Request model for searching for a keyword in all files.

    This model contains the query string and a case sensitivity flag.

    Attributes:
        query (str): The keyword to search for.
        case_sensitive (bool): Whether the search should be case sensitive.
    """

    query: str = Field(..., description="The keyword to search for.")
    case_sensitive: bool = Field(
        True,
        description="Whether the search should be case sensitive.",
    )


def _normalize_tag(tag: str) -> str:
    """
    Converts a tag to its normalized form: lowercase and stripped of leading/trailing whitespace.
    """
    return tag.lower().strip()


def _validate_tag(tag: str) -> bool:
    """
    Checks if a tag contains any forbidden characters or is empty after normalization.

    Forbidden characters are: `,` `<` `>` `/` `?` `'` `"`

    Args:
        tag: The tag string to validate. (Assumed to be already normalized for emptiness check)

    Returns:
        True if the tag is valid, False otherwise.
    """
    return TagValidator.validate_normalized_tag(tag)


def _build_file_path(
    filename: str, default_path: str = DEFAULT_NOTE_DIR
) -> tuple[Path, str]:
    """
    Resolve and build the complete file path from a filename.

    This function focuses on path handling operations:
    1. Ensuring the proper .md extension
    2. Separating subdirectory components from the filename
    3. Building the full directory path including vault root

    Args:
        filename: The filename (may include subdirectories)
        default_path: The default path to use if no subdirectory is specified

    Returns:
        tuple: (directory_path, base_filename)
            - directory_path: The fully resolved directory path (Path object)
            - base_filename: The filename component with .md extension

    Raises:
        ValueError: If the resulting filename is empty
    """
    # Check if filename is empty before processing
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
    full_dir_path = VAULT_PATH

    # Add default_path first if it's not empty
    if isinstance(default_path, str) and default_path.strip() != "":
        full_dir_path = full_dir_path / default_path

    # Then add subdirectories if they exist
    if str(subdirs) != ".":
        full_dir_path = full_dir_path / subdirs

    return full_dir_path, base_filename


def _assemble_complete_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
    is_new_note: bool = True,
) -> tuple[Path, str, str]:
    """
    Assemble a complete note by combining file path resolution, metadata generation, and content preparation.

    This function coordinates the entire note preparation process by:
    1. Resolving the file path and filename
    2. Reading existing frontmatter if the file exists
    3. Generating appropriate metadata using FrontmatterManager
    4. Assembling the final note content with frontmatter

    This function acts as a coordinator between path handling and metadata handling,
    preparing everything needed for the actual file writing operation.

    Args:
        text: The content to write to the file
        filename: The name of the file to write
        author: The author name to add to the frontmatter
        default_path: The default directory to save the file
        is_new_note: Whether this is a new note (True) or an update to an existing note (False)

    Returns:
        tuple: (full_dir_path, base_filename, prepared_content)
            - full_dir_path: The complete directory path where the file will be written
            - base_filename: The properly formatted filename (with .md extension)
            - prepared_content: The complete note content with frontmatter
    """
    # Build file path
    full_dir_path, base_filename = _build_file_path(filename, default_path)

    # Check existing frontmatter using FrontmatterManager
    file_path = full_dir_path / base_filename
    frontmatter_manager = FrontmatterManager(default_author=author)
    existing_frontmatter = frontmatter_manager.read_existing_metadata(file_path)

    # Generate metadata using FrontmatterManager
    post = frontmatter_manager.generate_metadata(
        text=text,
        author=author,
        is_new_note=is_new_note,
        existing_frontmatter=existing_frontmatter,
    )

    # Convert Post object to string with frontmatter
    content = frontmatter.dumps(post)

    return full_dir_path, base_filename, content


@handle_file_operations("note creation")
def create_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Create a new note in the Obsidian vault. Fails if the note already exists.

    Args:
        text: The content to write to the file.
        filename: The name of the file to write. If it doesn't have a .md extension, it will be added.
        author: The author name to add to the frontmatter. Default is None.
            If the request is made by an AI assistant, it should include its own model name
            (e.g., 'Claude 3.7 Sonnet', 'GPT-4', etc.).
        default_path: The default directory to save the file. Default is the value of DEFAULT_NOTE_DIR.

    Returns:
        Path: The path to the created file.

    Raises:
        FileExistsError: If the file already exists.
    """
    # Prepare note for writing
    full_dir_path, base_filename, content = _assemble_complete_note(
        text=text,
        filename=filename,
        author=author,
        default_path=default_path,
        is_new_note=True,
    )

    # Create the FileWriteRequest with overwrite=False to ensure we don't overwrite existing files
    file_write_request = FileWriteRequest(
        directory=str(full_dir_path),
        filename=base_filename,
        content=content,
        overwrite=False,
    )

    file_path = write_file(file_write_request)
    logger.info("New note created at %s", file_path)
    return file_path


@handle_file_operations("note editing")
def edit_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Edit an existing note in the Obsidian vault. Fails if the note doesn't exist.

    Args:
        text: The new content to write to the file.
        filename: The name of the file to edit. If it doesn't have a .md extension, it will be added.
        author: The author name to add to the frontmatter. Default is None.
            If the request is made by an AI assistant, it should include its own model name
            (e.g., 'Claude 3.7 Sonnet', 'GPT-4', etc.).
        default_path: The default directory to save the file. Default is the value of DEFAULT_NOTE_DIR.

    Returns:
        Path: The path to the edited file.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    # Prepare note for writing
    full_dir_path, base_filename, content = _assemble_complete_note(
        text=text,
        filename=filename,
        author=author,
        default_path=default_path,
        is_new_note=False,
    )
    file_path_for_logging = full_dir_path / base_filename

    # Check if the file exists before attempting to edit it
    if not file_path_for_logging.exists():
        raise FileNotFoundError(
            f"Cannot edit note. File {file_path_for_logging} does not exist"
        )

    # Create the FileWriteRequest with overwrite=True since we're editing an existing file
    file_write_request = FileWriteRequest(
        directory=str(full_dir_path),
        filename=base_filename,
        content=content,
        overwrite=True,
    )

    file_path = write_file(file_write_request)
    logger.info("Note edited at %s", file_path)
    return file_path


@handle_file_operations("note reading")
def read_note(filepath: str) -> str:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        filepath (str): The full path of the file to read.
    Returns:
        str: The content of the file.
    """
    directory, filename = os.path.split(filepath)
    file_read_request = FileReadRequest(
        directory=directory,
        filename=filename,
    )
    content = read_file(file_read_request)
    logger.info("File read from %s", filepath)
    return content


@handle_file_operations("note delete confirmation")
def get_note_delete_confirmation(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> DeleteConfirmationResult:
    """
    Get confirmation for deleting a note from the Obsidian vault.

    Args:
        filename (str, optional): The name of the file to delete. If it doesn't have a .md extension, it will be added.
        filepath (str, optional): The full path of the file to delete. If provided, filename is ignored.
        default_path (str): The default directory to look for the file. Default is the value of DEFAULT_NOTE_DIR.

    Returns:
        DeleteConfirmationResult: Object with file path and confirmation message.

    Raises:
        ValueError: If neither filename nor filepath is provided, or if input is otherwise invalid.
        FileNotFoundError: If the file doesn't exist.
    """
    request = DeleteNoteRequest(
        filename=filename, filepath=filepath, default_path=default_path
    )

    if request.filepath:
        file_path = Path(request.filepath)
    else:
        if request.filename is None:
            raise ValueError("Filename must be provided if filepath is not specified.")
        full_dir_path, base_filename = _build_file_path(
            request.filename, request.default_path
        )
        file_path = full_dir_path / base_filename

    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    message = f"File found at {file_path}. To delete, call 'perform_note_delete' with the same identification parameters."
    return DeleteConfirmationResult(file_path=str(file_path), message=message)


@handle_file_operations("note deletion")
def perform_note_delete(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Perform the deletion of a note from the Obsidian vault.

    Args:
        filename (str, optional): The name of the file to delete. If it doesn't have a .md extension, it will be added.
        filepath (str, optional): The full path of the file to delete. If provided, filename is ignored.
        default_path (str): The default directory to look for the file. Default is the value of DEFAULT_NOTE_DIR.

    Returns:
        Path: The path to the deleted file.

    Raises:
        ValueError: If neither filename nor filepath is provided, or if input is otherwise invalid.
        FileNotFoundError: If the file doesn't exist.
        (IOError, OSError): If a file system error occurs during deletion.
    """
    request = DeleteNoteRequest(
        filename=filename, filepath=filepath, default_path=default_path
    )

    if request.filepath:
        file_path = Path(request.filepath)
    else:
        assert request.filename is not None  # Ensured by Pydantic model
        full_dir_path, base_filename = _build_file_path(
            request.filename, request.default_path
        )
        file_path = full_dir_path / base_filename

    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    file_delete_request = FileDeleteRequest(
        directory=str(file_path.parent),
        filename=file_path.name,
    )

    deleted_path = delete_file(file_delete_request)
    logger.info("Note deleted successfully at %s", deleted_path)
    return deleted_path


@handle_file_operations("note search")
def search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]:
    """
    Search for a keyword in all files in the Obsidian vault.

    Args:
        query (str): The keyword to search for.
        case_sensitive (bool): Whether the search should be case sensitive. Default is True.
    Returns:
        list[SearchResult]: A list of search results containing file paths, line numbers and context.
    """
    if not query:
        raise ValueError("Query cannot be empty")

    search_config = SearchConfig(
        directory=str(VAULT_PATH),
        keyword=query,
        file_extensions=[".md"],
        case_sensitive=case_sensitive,
    )
    matching_files = search_keyword_in_files(search_config)
    logger.info("Found %s files matching the query: %s", len(matching_files), query)
    return matching_files


class AddTagRequest(BaseModel):
    """
    Request model for adding a tag to a note.

    Attributes:
        tag: The tag string to add to the note.
        filename: The name of the file to modify (e.g., "my_note.md" or "subdir/my_note").
                  Used if `filepath` is not provided. `.md` extension is optional.
        filepath: The full, absolute path to the note file. If provided, `filename` is ignored.
        default_path: The default directory path (relative to vault root) to search for the note
                      if `filename` is used and does not specify a subdirectory.
    """

    tag: str = Field(..., description="The tag string to add to the note.")
    filename: str | None = Field(
        None,
        description='The name of the file to modify (e.g., "my_note.md" or "subdir/my_note"). Used if `filepath` is not provided. `.md` extension is optional.',
    )
    filepath: str | None = Field(
        None,
        description="The full, absolute path to the note file. If provided, `filename` is ignored.",
    )
    default_path: str = Field(
        DEFAULT_NOTE_DIR,
        description="The default directory path (relative to vault root) to search for the note if `filename` is used and does not specify a subdirectory.",
    )

    @field_validator("filename")
    def format_filename(cls, v: str | None) -> str | None:
        """
        Format the filename to ensure it has a .md extension if not None.
        """
        if v is not None:
            FilenameValidator.validate_filename_with_subdirs(v)
            if ".md" not in v:
                v = f"{v}.md"
        return v

    @model_validator(mode="after")
    def validate_input(self) -> "AddTagRequest":
        """
        Validate that at least one of filename or filepath is provided.
        """
        if self.filename is None and self.filepath is None:
            raise ValueError("Either filename or filepath must be provided")
        return self


def _resolve_note_file(
    filename: str | None, filepath: str | None, default_path: str
) -> Path:
    """
    Resolve note file path from filename or filepath.

    Args:
        filename: The filename (may include subdirectories)
        filepath: The full file path
        default_path: Default directory if filename used

    Returns:
        Path: The resolved file path

    Raises:
        ValueError: If neither filename nor filepath provided
    """
    if filepath:
        return Path(filepath)
    elif filename:
        full_dir_path, base_filename = _build_file_path(filename, default_path)
        return full_dir_path / base_filename
    else:
        raise ValueError("Either filename or filepath must be provided")


def _load_note_with_tags(file_path: Path) -> tuple[frontmatter.Post, list[str]]:
    """
    Load note and extract current tags.

    Args:
        file_path: Path to the note file

    Returns:
        tuple: (frontmatter post object, current tags list)

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    content = read_note(str(file_path))
    post = frontmatter.loads(content)
    tags_value = post.metadata.get("tags", [])
    tags = list(tags_value) if isinstance(tags_value, list) else []
    return post, tags


def _save_note_with_updated_tags(
    file_path: Path, post: frontmatter.Post, tags: list[str]
) -> Path:
    """
    Save note with updated tags.

    Args:
        file_path: Path to save the file
        post: Frontmatter post object
        tags: Updated tags list

    Returns:
        Path: The written file path
    """
    author_value = post.metadata.get("author")
    author_str = str(author_value) if author_value is not None else None

    # Use FrontmatterManager directly instead of deprecated wrapper
    frontmatter_manager = FrontmatterManager(default_author=author_str)
    updated_post = frontmatter_manager.generate_metadata(
        text=post.content,
        author=author_str,
        is_new_note=False,
        existing_frontmatter=dict(post.metadata),
        tags=tags,
    )

    content = frontmatter.dumps(updated_post)
    file_write_request = FileWriteRequest(
        directory=str(file_path.parent),
        filename=file_path.name,
        content=content,
        overwrite=True,
    )

    return write_file(file_write_request)


@handle_file_operations("tag addition")
def add_tag(
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Add a specified tag to an existing note in the Obsidian vault.

    The tag is normalized (converted to lowercase, stripped of whitespace) before being added.
    If the normalized tag already exists in the note, it is not added again.
    The note's 'updated' timestamp and potentially its 'tags' list in the frontmatter are modified.

    Args:
        tag (str): The tag to add to the note.
        filename (str, optional): The name of the file to modify. If it doesn't have a .md extension, it will be added.
        filepath (str, optional): The full path of the file to modify. If provided, `filename` is ignored.
        default_path (str): The default directory path (relative to vault root) to search for the note
                            if `filename` is used and does not specify a subdirectory.

    Returns:
        The `Path` object of the modified note file.

    Raises:
        ValueError: If the provided tag is invalid (e.g., contains forbidden characters like ',').
        FileNotFoundError: If the specified note file does not exist.
        IOError, OSError: For underlying file system errors during read or write operations.
    """
    request = AddTagRequest(
        tag=tag,
        filename=filename,
        filepath=filepath,
        default_path=default_path,
    )

    normalized_tag = _normalize_tag(request.tag)
    if not _validate_tag(normalized_tag):
        raise ValueError(f"Invalid tag: {request.tag}")

    file_path = _resolve_note_file(
        request.filename, request.filepath, request.default_path
    )

    post, current_tags = _load_note_with_tags(file_path)
    current_normalized = [_normalize_tag(str(t)) for t in current_tags]

    if normalized_tag not in current_normalized:
        current_tags.append(normalized_tag)
        written_path = _save_note_with_updated_tags(file_path, post, current_tags)
        logger.info("Added tag '%s' to %s", normalized_tag, written_path.name)
    else:
        # Rewrite the file to update the 'updated' field even if the tag already exists
        written_path = _save_note_with_updated_tags(file_path, post, current_tags)
        logger.info("Tag '%s' already exists in %s", normalized_tag, file_path.name)

    return written_path


class RemoveTagRequest(BaseModel):
    """
    Request model for removing a tag from a note.

    Attributes:
        tag: The tag string to remove from the note. Comparison is case-insensitive.
        filename: The name of the file to modify (e.g., "my_note.md" or "subdir/my_note").
                  Used if `filepath` is not provided. `.md` extension is optional.
        filepath: The full, absolute path to the note file. If provided, `filename` is ignored.
        default_path: The default directory path (relative to vault root) to search for the note
                      if `filename` is used and does not specify a subdirectory.
    """

    tag: str = Field(
        ...,
        description="The tag string to remove from the note. Comparison is case-insensitive.",
    )
    filename: str | None = Field(
        None,
        description='The name of the file to modify (e.g., "my_note.md" or "subdir/my_note"). Used if `filepath` is not provided. `.md` extension is optional.',
    )
    filepath: str | None = Field(
        None,
        description="The full, absolute path to the note file. If provided, `filename` is ignored.",
    )
    default_path: str = Field(
        DEFAULT_NOTE_DIR,
        description="The default directory path (relative to vault root) to search for the note if `filename` is used and does not specify a subdirectory.",
    )

    @field_validator("filename")
    def format_filename(cls, v: str | None) -> str | None:
        """
        Format the filename to ensure it has a .md extension if not None.
        """
        if v is not None:
            FilenameValidator.validate_filename_with_subdirs(v)
            if ".md" not in v:
                v = f"{v}.md"
        return v

    @model_validator(mode="after")
    def validate_input(self) -> "RemoveTagRequest":
        """
        Validate that at least one of filename or filepath is provided.
        """
        if self.filename is None and self.filepath is None:
            raise ValueError("Either filename or filepath must be provided")
        return self


@handle_file_operations("tag removal")
def remove_tag(
    tag: str,
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Remove a specified tag from an existing note in the Obsidian vault.

    Tag matching for removal is case-insensitive and ignores leading/trailing whitespace
    (uses normalized form). If the tag is found and removed, the note's 'updated' timestamp
    and its 'tags' list in the frontmatter are modified. If the tag is not found,
    the file is still re-processed and its 'updated' timestamp will change, but the tag list will not.
    If the last tag is removed, the 'tags' key is removed from the frontmatter.

    Args:
        tag (str): The tag to remove from the note.
        filename (str, optional): The name of the file to modify. If it doesn't have a .md extension, it will be added.
        filepath (str, optional): The full path of the file to modify. If provided, `filename` is ignored.
        default_path (str): The default directory path (relative to vault root) to search for the note
                            if `filename` is used and does not specify a subdirectory.

    Returns:
        The `Path` object of the modified note file.

    Raises:
        FileNotFoundError: If the specified note file does not exist.
        IOError, OSError: For underlying file system errors.
    """
    request = RemoveTagRequest(
        tag=tag,
        filename=filename,
        filepath=filepath,
        default_path=default_path,
    )

    tag_to_remove = _normalize_tag(request.tag)

    file_path = _resolve_note_file(
        request.filename, request.filepath, request.default_path
    )

    post, current_tags = _load_note_with_tags(file_path)

    # Remove tag if present
    new_tags = []
    tag_was_removed = False

    for existing_tag in current_tags:
        if _normalize_tag(str(existing_tag)) == tag_to_remove:
            tag_was_removed = True
        else:
            new_tags.append(str(existing_tag))

    written_path = _save_note_with_updated_tags(file_path, post, new_tags)

    if tag_was_removed:
        logger.info("Removed tag '%s' from %s", request.tag, written_path.name)
    else:
        logger.info("Tag '%s' not found in %s", request.tag, written_path.name)

    return written_path


class RenameTagRequest(BaseModel):
    """
    Request model for renaming a tag across multiple notes.

    Attributes:
        old_tag: The current tag string to be replaced. Case-insensitive matching.
        new_tag: The new tag string to replace the old tag.
        directory: Optional path to a directory within the vault to limit the scope of renaming.
                   If `None`, the entire vault is scanned.
    """

    old_tag: str = Field(
        ...,
        description="The current tag string to be replaced. Case-insensitive matching.",
    )
    new_tag: str = Field(..., description="The new tag string to replace the old tag.")
    directory: str | None = Field(
        None,
        description="Optional path to a directory within the vault. If None, the entire vault is scanned.",
    )


def _rename_tag_in_file(file_path: Path, old_tag_normalized: str, new_tag: str) -> bool:
    """
    Rename a tag in a single file.

    Args:
        file_path: Path to the note file
        old_tag_normalized: Normalized old tag to replace
        new_tag: New tag to add

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        post, current_tags = _load_note_with_tags(file_path)

        if not current_tags:
            return False

        new_tags = []
        old_tag_found = False
        new_tag_normalized = _normalize_tag(new_tag)

        # Remove old tag and check if new tag already exists
        for tag in current_tags:
            tag_normalized = _normalize_tag(str(tag))
            if tag_normalized == old_tag_normalized:
                old_tag_found = True
            else:
                new_tags.append(str(tag))

        if old_tag_found:
            # Add new tag if not already present
            if new_tag_normalized not in [_normalize_tag(t) for t in new_tags]:
                new_tags.append(new_tag)

            # Check if tags actually changed
            old_normalized = {_normalize_tag(str(t)) for t in current_tags}
            new_normalized = {_normalize_tag(t) for t in new_tags}

            if old_normalized != new_normalized:
                _save_note_with_updated_tags(file_path, post, new_tags)
                return True

    except Exception as e:
        logger.error("Error processing file %s: %s", file_path, e)

    return False


@handle_file_operations("tag renaming")
def rename_tag(
    old_tag: str,
    new_tag: str,
    directory: str | None = None,
) -> list[Path]:
    """
    Rename a tag in all notes within a specified directory (or the entire vault).

    This function searches for all occurrences of `old_tag` (case-insensitive, normalized)
    and replaces them with `new_tag`. The `new_tag` itself is stored in its normalized form.
    If `new_tag` (normalized) already exists in a note's tags, the `old_tag` is simply removed
    to avoid duplicates. Only files that are actually changed (tags modified) will have their
    'updated' timestamp changed and be included in the returned list.

    Args:
        old_tag (str): The current tag string to be replaced. Case-insensitive matching.
        new_tag (str): The new tag string to replace the old tag.
        directory (str | None): Optional path to a directory within the vault to limit the scope of renaming.
                                If `None`, the entire vault is scanned.

    Returns:
        A list of `Path` objects for each note file that was modified.

    Raises:
        ValueError: If `new_tag` is invalid (e.g., contains forbidden characters, or is empty after normalization).
        FileNotFoundError: If the specified `directory` (if provided) does not exist.
        IOError, OSError: For underlying file system errors during directory traversal or file operations.
    """
    request = RenameTagRequest(
        old_tag=old_tag,
        new_tag=new_tag,
        directory=directory,
    )

    normalized_new_tag = _normalize_tag(request.new_tag)
    if not _validate_tag(normalized_new_tag):
        raise ValueError(f"Invalid new_tag: {request.new_tag}")

    normalized_old_tag = _normalize_tag(request.old_tag)

    if normalized_old_tag == normalized_new_tag:
        logger.info("Old and new tags are the same after normalization")
        return []

    effective_directory = Path(request.directory or str(VAULT_PATH))
    if not effective_directory.is_dir():
        raise FileNotFoundError(f"Directory '{effective_directory}' not found")

    # Process all markdown files
    modified_files: list[Path] = []
    md_files = list(effective_directory.rglob("*.md"))

    for file_path in md_files:
        if _rename_tag_in_file(file_path, normalized_old_tag, request.new_tag):
            modified_files.append(file_path)
            logger.info(
                "Renamed tag '%s' to '%s' in %s", old_tag, new_tag, file_path.name
            )

    logger.info("Renamed tag in %d file(s)", len(modified_files))
    return modified_files


class GetTagsRequest(BaseModel):
    """
    Request model for retrieving tags from a specific note.

    Attributes:
        filename: The name of the note file (e.g., "my_note.md" or "subdir/my_note").
                  Used if `filepath` is not provided. `.md` extension is optional.
        filepath: The full, absolute path to the note file. If provided, `filename` is ignored.
        default_path: The default directory path (relative to vault root) to search for the note
                      if `filename` is used and does not specify a subdirectory.
    """

    filename: str | None = Field(
        None,
        description='The name of the note file (e.g., "my_note.md" or "subdir/my_note"). Used if `filepath` is not provided. `.md` extension is optional.',
    )
    filepath: str | None = Field(
        None,
        description="The full, absolute path to the note file. If provided, `filename` is ignored.",
    )
    default_path: str = Field(
        DEFAULT_NOTE_DIR,
        description="The default directory path (relative to vault root) to search for the note if `filename` is used and does not specify a subdirectory.",
    )

    @field_validator("filename")
    def format_filename(cls, v: str | None) -> str | None:
        """
        Format the filename to ensure it has a .md extension if not None.
        """
        if v is not None:
            FilenameValidator.validate_filename_with_subdirs(v)
            if ".md" not in v:
                v = f"{v}.md"
        return v

    @model_validator(mode="after")
    def validate_input(self) -> "GetTagsRequest":
        """
        Validate that at least one of filename or filepath is provided.
        """
        if self.filename is None and self.filepath is None:
            raise ValueError("Either filename or filepath must be provided")
        return self


def _resolve_file_path(
    request: GetTagsRequest,
) -> tuple[Path, str | Path]:
    """
    Resolve the file path from a GetTagsRequest.

    Args:
        request: The request containing filename or filepath.

    Returns:
        Tuple of (resolved file path, logging representation)

    Raises:
        ValueError: If neither filename nor filepath can be determined.
    """
    file_path_for_logging: str | Path = "unknown_file (pre-resolution)"

    # Path resolution logic: filepath takes precedence if both filepath and filename are provided
    if request.filepath:
        file_path = Path(request.filepath)
        if not file_path.name.endswith(".md"):
            logger.debug(
                "Filepath provided to get_tags without .md extension: %s", file_path
            )
        file_path_for_logging = file_path
    elif request.filename:
        full_dir_path, base_filename = _build_file_path(
            request.filename, request.default_path
        )
        file_path = full_dir_path / base_filename
        file_path_for_logging = file_path
    else:
        # This should be caught by Pydantic validation, but checking as a safeguard
        logger.error(
            "Get_tags called with neither filename nor filepath (Pydantic validation missed)."
        )
        raise ValueError("Internal error: filename or filepath must be determined.")

    return file_path, file_path_for_logging


def _extract_tags_from_frontmatter(note_content_str: str, file_path: Path) -> list[str]:
    """
    Extract tags from frontmatter content.

    Args:
        note_content_str: The note content string
        file_path: Path to the file (for logging)

    Returns:
        List of tag strings
    """
    try:
        post = frontmatter.loads(note_content_str)
    except Exception as e:
        logger.warning(
            "Get_tags: Failed to parse frontmatter for file %s: %s. Returning empty list.",
            file_path,
            e,
        )
        return []

    # Retrieve tag data from frontmatter and handle various error cases
    tags_data = post.metadata.get("tags")

    if tags_data is None:
        logger.debug(
            "Get_tags: No 'tags' field in metadata for %s. Returning empty list.",
            file_path,
        )
        return []

    if not isinstance(tags_data, list):
        logger.warning(
            "Get_tags: 'tags' field in %s is not a list (type: %s). Returning empty list.",
            file_path,
            type(tags_data).__name__,
        )
        return []

    # Handle non-string tag elements (may occur in manually edited files)
    processed_tags = []
    for tag_item in tags_data:
        if isinstance(tag_item, str):
            processed_tags.append(tag_item)
        else:
            logger.warning(
                "Get_tags: Non-string item '%s' (type: %s) found in tags list for %s. It will be converted to string.",
                tag_item,
                type(tag_item).__name__,
                file_path,
            )
            processed_tags.append(str(tag_item))

    logger.info(
        "Get_tags: Successfully retrieved tags %s from %s",
        processed_tags,
        file_path,
    )
    return processed_tags


@handle_file_operations("tag retrieval")
def get_tags(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> list[str]:
    """
    Retrieve the list of tags from a specific note's frontmatter.

    This function is designed to be fault-tolerant. It returns an empty list if the
    file is not found, cannot be read, has malformed frontmatter, or if the 'tags'
    field is missing or not a list. Tags are returned with their original casing as
    stored in the note.

    Args:
        filename (str, optional): The name of the note file (e.g., "my_note.md" or "subdir/my_note").
                                  Used if `filepath` is not provided. `.md` extension is optional.
        filepath (str, optional): The full, absolute path to the note file. If provided, `filename` is ignored.
        default_path (str): The default directory path (relative to vault root) to search for the note
                            if `filename` is used and does not specify a subdirectory.

    Returns:
        A list of tag strings. Returns an empty list in case of errors or no tags.

    Raises:
        ValueError: If Pydantic model validation fails (e.g. neither filename nor filepath provided).
                    Does not typically raise exceptions for file access or parsing issues.
    """
    request = GetTagsRequest(
        filename=filename,
        filepath=filepath,
        default_path=default_path,
    )

    # Set a placeholder for logging before the actual file path is resolved
    file_path_for_logging: str | Path = "unknown_file (pre-resolution)"

    try:
        # Resolve the file path
        file_path, file_path_for_logging = _resolve_file_path(request)

        # Check file existence
        if not file_path.exists():
            logger.warning(
                "Get_tags: File %s not found. Returning empty list.", file_path
            )
            return []

        file_path_for_logging = file_path
        note_content_str = read_note(str(file_path))

        # Extract and process tags
        return _extract_tags_from_frontmatter(note_content_str, file_path)

    # All exception cases return an empty list (fault-tolerant design)
    except FileNotFoundError:
        logger.warning(
            "Get_tags: File %s not found (error during read_note). Returning empty list.",
            file_path_for_logging,
        )
        return []
    except (IOError, OSError) as e:
        # File system related errors
        logger.error(
            "Get_tags: File system error for %s: %s. Returning empty list.",
            file_path_for_logging,
            e,
        )
        return []
    except ValueError as e:
        # Pydantic validation errors or other value validation errors
        logger.error("Get_tags: Input error: %s. Returning empty list.", e)
        return []
    except Exception as e:
        # Catch unexpected errors and log detailed information
        logger.error(
            "Get_tags: Unexpected error processing file %s: %s. Returning empty list.",
            file_path_for_logging,
            e,
            exc_info=True,
        )
        return []


class ListAllTagsRequest(BaseModel):
    """
    Request model for listing all unique tags in a directory.

    Attributes:
        directory: Optional path to a directory within the vault. If `None`, the entire vault is scanned.
    """

    directory: str | None = Field(
        None,
        description="Optional path to a directory within the vault. If None, the entire vault is scanned.",
    )


@handle_file_operations("tag listing")
def list_all_tags(directory: str | None = None) -> list[str]:
    """
    List all unique, normalized tags from all Markdown files within a specified directory (or entire vault).

    This function scans notes, retrieves their tags using `get_tags`, normalizes them
    (lowercase, stripped whitespace), and returns a sorted list of unique tags.
    Empty tags (after normalization) are excluded.

    Args:
        directory: Optional path to a directory within the vault. If `None`, the entire vault is scanned.

    Returns:
        A sorted list of unique, normalized tag strings.

    Raises:
        FileNotFoundError: If the specified `directory` (if provided) does not exist or is not a directory.
        IOError, OSError: For underlying file system errors during directory traversal.
    """
    request = ListAllTagsRequest(directory=directory)
    effective_directory_str = (
        request.directory if request.directory else str(VAULT_PATH)
    )
    effective_directory_path = Path(effective_directory_str)

    if not effective_directory_path.is_dir():
        logger.error(
            "List_all_tags: Directory '%s' does not exist or is not a directory.",
            effective_directory_path,
        )
        raise FileNotFoundError(
            f"Directory '{effective_directory_path}' not found or is not a directory."
        )

    all_tags_set: set[str] = set()
    files_processed_count = 0
    tags_found_count = 0

    for file_path in effective_directory_path.rglob("*.md"):
        files_processed_count += 1
        tags_in_file = get_tags(
            filename=None, filepath=str(file_path), default_path=DEFAULT_NOTE_DIR
        )
        for tag in tags_in_file:
            normalized_tag = _normalize_tag(tag)
            if normalized_tag:
                all_tags_set.add(normalized_tag)
                tags_found_count += 1

    sorted_tags_list = sorted(list(all_tags_set))

    logger.info(
        "List_all_tags: Processed %d files in '%s'. Found %d unique normalized tags (from %d total tag instances). Tags: %s",
        files_processed_count,
        effective_directory_path,
        len(sorted_tags_list),
        tags_found_count,
        sorted_tags_list
        if len(sorted_tags_list) < 20
        else str(sorted_tags_list[:20]) + "...",  # Avoid overly long log
    )
    return sorted_tags_list


class FindNotesWithTagRequest(BaseModel):
    """
    Request model for finding notes containing a specific tag.

    Attributes:
        tag: The tag string to search for. The search is case-insensitive and uses normalized tags.
        directory: Optional path to a directory within the vault to limit the search scope.
                   If `None`, the entire vault is scanned.
    """

    tag: str = Field(
        ...,
        description="The tag to search for. Search is case-insensitive and uses normalized tags.",
    )
    directory: str | None = Field(
        None,
        description="Optional path to a directory. If None, the entire vault is scanned.",
    )


@handle_file_operations("tag search")
def find_notes_with_tag(tag: str, directory: str | None = None) -> list[str]:
    """
    Find all notes (returned as a list of file paths) that contain a specific tag.

    The search is performed within a specified directory or the entire vault.
    Tag matching is case-insensitive and uses normalized forms (lowercase, stripped whitespace).
    If the target tag normalizes to an empty string, no files will be returned.

    Args:
        tag: The tag to search for. Search is case-insensitive and uses normalized tags.
        directory: Optional path to a directory within the vault to limit the search scope.
                   If `None`, the entire vault is scanned.

    Returns:
        A list of string paths for each note file containing the specified tag.

    Raises:
        FileNotFoundError: If the specified `directory` (if provided) does not exist or is not a directory.
        IOError, OSError: For underlying file system errors during directory traversal.
    """
    request = FindNotesWithTagRequest(tag=tag, directory=directory)
    effective_directory_str = (
        request.directory if request.directory else str(VAULT_PATH)
    )
    effective_directory_path = Path(effective_directory_str)

    if not effective_directory_path.is_dir():
        logger.error(
            "Find_notes_with_tag: Directory '%s' does not exist or is not a directory.",
            effective_directory_path,
        )
        raise FileNotFoundError(
            f"Directory '{effective_directory_path}' not found or is not a directory."
        )

    normalized_target_tag = _normalize_tag(request.tag)

    if not normalized_target_tag:
        logger.warning(
            "Find_notes_with_tag: The provided tag '%s' is empty after normalization. "
            "Cannot search for an empty tag. Returning empty list.",
            request.tag,
        )
        return []

    matching_files_paths: list[str] = []
    files_processed_count = 0

    for file_path in effective_directory_path.rglob("*.md"):
        files_processed_count += 1
        tags_in_file = get_tags(
            filename=None, filepath=str(file_path), default_path=DEFAULT_NOTE_DIR
        )

        normalized_tags_in_file = [_normalize_tag(t) for t in tags_in_file]

        if normalized_target_tag in normalized_tags_in_file:
            matching_files_paths.append(str(file_path))

    logger.info(
        "Find_notes_with_tag: Processed %d files in '%s'. Found %d notes with tag '%s'.",
        files_processed_count,
        effective_directory_path,
        len(matching_files_paths),
        request.tag,  # Log original tag for clarity
    )
    return matching_files_paths


# ============================================================================
# Service Layer Integration
# ============================================================================

# Global service instance for backward compatibility
_service_instance: MinervaService | None = None


def _get_service() -> "MinervaService":
    """
    Get or create the global service instance.

    This function provides lazy initialization of the service instance
    to maintain backward compatibility with existing function-based API.
    """
    global _service_instance
    if _service_instance is None:
        from minerva.service import create_minerva_service

        _service_instance = create_minerva_service()
    return _service_instance


def get_service_instance() -> "MinervaService":
    """
    Get the current service instance.

    This function allows access to the service instance for testing
    and advanced use cases while maintaining the function-based API.

    Returns:
        MinervaService: The current service instance
    """
    return _get_service()


def set_service_instance(service: "MinervaService") -> None:
    """
    Set a custom service instance.

    This function allows dependency injection for testing by replacing
    the default service instance with a custom one.

    Args:
        service: Custom service instance to use
    """
    global _service_instance
    _service_instance = service
