import functools
import logging
import os
import re  # Added for tag validation
from datetime import datetime
from pathlib import Path

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

from minerva.config import VAULT_PATH, DEFAULT_NOTE_AUTHOR, DEFAULT_NOTE_DIR

# Set up logging
logger = logging.getLogger(__name__)


def handle_file_operations(operation_name: str):
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

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
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


class WriteNoteRequest(BaseModel):
    """
    Request model for writing a note to a file.

    This model contains the text to write, the filename, and an overwrite flag.

    Attributes:
        text (str): The content to write to the file.
        filename (str): The name of the file to write. If it doesn't have a .md extension, it will be added.
        is_overwrite (bool): Whether to overwrite the file if it exists.
        author (str): The author name to add to the frontmatter. Default is None.
        default_dir (str): The default directory to save the file. Default is the value of DEFAULT_NOTE_DIR.
    """

    text: str = Field(..., description="The content to write to the file.")
    filename: str = Field(..., description="The name of the file to write.")
    is_overwrite: bool = Field(
        False,
        description="Whether to overwrite the file if it exists.",
    )
    author: str | None = Field(
        None, description="The author name to add to the frontmatter."
    )
    default_path: str = Field(
        DEFAULT_NOTE_DIR, description="The default path to save the file."
    )

    @field_validator("filename")
    def format_filename(cls, v: str) -> str:
        """
        Format the filename to ensure it has a .md extension.
        """
        if not v:
            raise ValueError("Filename cannot be empty")
        if ".md" not in v:
            v = f"{v}.md"
        return v


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
            if not v:
                raise ValueError("Filename cannot be empty")
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


def _generate_note_metadata(
    text: str,
    author: str | None = None,
    is_new_note: bool = True,
    existing_frontmatter: dict | None = None,
    tags: list[str] | None = None,
) -> frontmatter.Post:
    """
    Generate or update YAML frontmatter metadata for a note.

    This function processes only the metadata portion of a note (frontmatter),
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
        This function only handles the metadata portion of a note.
        It does not perform any file path resolution or file I/O operations.
    """
    # Get current time in ISO format
    now = datetime.now().isoformat()

    # Check and load frontmatter
    has_frontmatter = text.startswith("---\n")
    if has_frontmatter:
        # Load existing frontmatter
        post = frontmatter.loads(text)
    else:
        # Create new frontmatter object
        post = frontmatter.Post(text)

    # Copy existing frontmatter if available
    if existing_frontmatter:
        # Copy all existing metadata except special fields we handle manually
        # This preserves custom fields that might be present in the existing frontmatter
        for key, value in existing_frontmatter.items():
            # Skip fields we'll handle separately: author, created, updated, tags
            if key not in ["author", "created", "updated", "tags"]:
                post.metadata[key] = value

    # Add author information
    post.metadata["author"] = author or DEFAULT_NOTE_AUTHOR

    # Preserve created field from existing frontmatter
    if existing_frontmatter and "created" in existing_frontmatter:
        post.metadata["created"] = existing_frontmatter["created"]

    # Add created field for new notes (don't overwrite if exists)
    if is_new_note and "created" not in post.metadata:
        post.metadata["created"] = now

    # Add updated field for note updates (always update with current time)
    if not is_new_note:
        post.metadata["updated"] = now

    # Handle tags
    if tags is not None:  # tags were explicitly provided
        processed_tags = []
        if isinstance(tags, list):
            seen_tags = set()
            for tag in tags:
                normalized_tag = _normalize_tag(str(tag))  # Ensure tag is a string
                if _validate_tag(normalized_tag):
                    if normalized_tag not in seen_tags:
                        processed_tags.append(normalized_tag)
                        seen_tags.add(normalized_tag)
                else:
                    logger.warning(
                        "Invalid tag '%s' (normalized: '%s') removed. Tags cannot contain: ,<>/?'\"",
                        tag,
                        normalized_tag,
                    )

        if processed_tags:
            post.metadata["tags"] = processed_tags
        elif (
            "tags" in post.metadata
        ):  # Explicitly provided empty list of tags means clear existing tags
            del post.metadata["tags"]
    # If tags argument is None, existing tags in post.metadata (if any) are preserved.

    return post


def _normalize_tag(tag: str) -> str:
    """
    Converts a tag to its normalized form: lowercase and stripped of leading/trailing whitespace.
    """
    return tag.lower().strip()


_FORBIDDEN_TAG_CHARS_PATTERN = re.compile(r"[,<>/?'\"]")


def _validate_tag(tag: str) -> bool:
    """
    Checks if a tag contains any forbidden characters or is empty after normalization.

    Forbidden characters are: `,` `<` `>` `/` `?` `'` `"`

    Args:
        tag: The tag string to validate. (Assumed to be already normalized for emptiness check)

    Returns:
        True if the tag is valid, False otherwise.
    """
    if not tag:  # Empty tags (e.g., after normalization of "   ") are not allowed
        return False
    return not bool(_FORBIDDEN_TAG_CHARS_PATTERN.search(tag))


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
    if str(subdirs) != ".":  # If subdirectory is specified
        full_dir_path = full_dir_path / subdirs
    elif isinstance(default_path, str) and default_path.strip() != "":
        full_dir_path = full_dir_path / default_path

    return full_dir_path, base_filename


def _read_existing_frontmatter(file_path: Path) -> dict | None:
    """
    Read and extract frontmatter metadata from an existing file.

    This function focuses only on retrieving the YAML frontmatter metadata
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
        with open(file_path, "r") as f:
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
            "I/O or OS error reading existing file %s for metadata: %s", file_path, e
        )
        return None
    except Exception as e:
        logger.warning(
            "Unexpected error processing file %s for metadata: %s", file_path, e
        )
        return None


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
    3. Generating appropriate metadata
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

    # Check existing frontmatter
    file_path = full_dir_path / base_filename
    existing_frontmatter = _read_existing_frontmatter(file_path)

    # Generate metadata
    post = _generate_note_metadata(
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


def write_note(
    text: str,
    filename: str,
    is_overwrite: bool = False,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Write a note to a file in the Obsidian vault.

    This function is maintained for backward compatibility.
    For new code, consider using create_note() or edit_note() for more explicit intent.

    Args:
        text: The content to write to the file.
        filename: The name of the file to write. If it doesn't have a .md extension, it will be added.
        is_overwrite: Whether to overwrite the file if it exists. Default is False.
        author: The author name to add to the frontmatter. Default is None.
            If the request is made by an AI assistant, it should include its own model name
            (e.g., 'Claude 3.7 Sonnet', 'GPT-4', etc.).
        default_path: The default directory to save the file. Default is the value of DEFAULT_NOTE_DIR.


    Returns:
        Path: The path to the written file.

    Note:
        When this function is called by an AI assistant, the AI should always pass its own
        model name in the 'author' parameter to be included in the frontmatter of the created note.

    Deprecated:
        This function is maintained for backward compatibility.
        For new code, consider using create_note() or edit_note() for more explicit intent.
    """
    request = WriteNoteRequest(
        text=text,
        filename=filename,
        is_overwrite=is_overwrite,
        author=author,
        default_path=default_path,
    )

    file_path = None  # Ensure file_path is always defined for exception handling
    try:
        # Determine if this is a new note based on file existence
        full_dir_path, base_filename = _build_file_path(
            request.filename, request.default_path
        )
        file_path = full_dir_path / base_filename
        is_new_note = not file_path.exists()

        # Prepare note for writing - reuse the common function
        full_dir_path, base_filename, content = _assemble_complete_note(
            text=request.text,
            filename=request.filename,
            author=request.author,
            default_path=request.default_path,
            is_new_note=is_new_note,
        )

        # Create the file write request
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=request.is_overwrite,
        )
        file_path = write_file(file_write_request)
        logger.info("File written to %s", file_path)
        return file_path
    except FileExistsError:
        logger.error(
            "Error writing file: File %s already exists and overwrite is false.",
            file_path if file_path is not None else filename,
        )
        raise
    except FileNotFoundError:
        logger.error(
            "Error writing file: File %s not found.",
            file_path if file_path is not None else filename,
        )
        raise
    except (IOError, OSError) as e:
        logger.error(
            "Error writing file %s: File system error: %s",
            file_path if file_path is not None else filename,
            e,
        )
        raise
    except ValueError as e:  # Catches errors from Pydantic, _build_file_path, etc.
        logger.error(
            "Error writing file (input filename '%s'): Invalid input or path: %s",
            filename,
            e,
        )
        raise
    except Exception as e:
        logger.error(
            "Error writing file (input filename '%s'): An unexpected error occurred: %s",
            filename,
            e,
        )
        raise


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
            if not v:
                raise ValueError("Filename cannot be empty if provided")
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
    # 1. Determine the target file path
    if request.filepath:
        file_path = Path(request.filepath)
        # Ensure filename part of filepath also has .md if it's a direct path
        if not file_path.name.endswith(".md"):
            # This case should ideally be handled by user providing correct filepath,
            # but as a safeguard or if filename validator didn't run for filepath:
            logger.warning(
                "Filepath provided without .md extension. Consider adding .md for consistency: %s",
                file_path,
            )

        base_filename = file_path.name
        full_dir_path = file_path.parent
    elif (
        request.filename
    ):  # filename must be present if filepath is not, due to model validation
        # request.filename is already validated by Pydantic to have .md
        full_dir_path, base_filename = _build_file_path(
            request.filename, request.default_path
        )
        file_path = full_dir_path / base_filename
    else:
        # This case should be caught by Pydantic's model_validator, but as a safeguard:
        raise ValueError(
            "Logic error: Either filename or filepath must be determined by this point."
        )

    if not file_path.exists():
        logger.error("Error adding tag: File %s not found.", file_path)
        raise FileNotFoundError(f"File {file_path} does not exist")

    # 2. Normalize the input tag
    normalized_tag = _normalize_tag(request.tag)

    # 3. Validate the normalized tag
    if not _validate_tag(normalized_tag):
        logger.error("Error adding tag: Invalid tag '%s'", request.tag)
        raise ValueError(f"Invalid tag: {request.tag} (normalized: {normalized_tag})")

    # 4. Read the entire note content
    # read_note expects a string path
    note_content_str = read_note(str(file_path))

    # 5. Load the front matter and content
    post = frontmatter.loads(note_content_str)
    existing_metadata = dict(
        post.metadata
    )  # for _generate_note_metadata and author extraction

    # 6. Get the current list of tags
    tags_value = existing_metadata.get("tags", [])
    current_tags = list(tags_value) if isinstance(tags_value, list) else []
    # Ensure all existing tags are also normalized for comparison, though _generate_note_metadata will re-normalize
    current_tags_normalized = [_normalize_tag(str(t)) for t in current_tags]

    # 7. If the normalized new tag is not already in the current tags list, append it.
    if normalized_tag not in current_tags_normalized:
        # Add the original (but validated and normalized) new tag to the list that will be passed
        # to _generate_note_metadata. _generate_note_metadata will handle final normalization.
        current_tags.append(normalized_tag)  # Add the normalized tag
        tags_to_set = current_tags
    else:
        tags_to_set = current_tags  # No change, pass existing tags

    # 8. Call _generate_note_metadata
    # Preserve original author if available
    author_value = existing_metadata.get("author")
    # Ensure author is str or None for type correctness
    author_str = str(author_value) if author_value is not None else None

    updated_post_obj = _generate_note_metadata(
        text=post.content,  # Pass only the body content
        author=author_str,
        is_new_note=False,  # This is an edit
        existing_frontmatter=existing_metadata,  # Pass all existing metadata
        tags=tags_to_set,  # Pass the potentially updated list of tags
    )

    # 9. Serialize the updated post object
    updated_content_str = frontmatter.dumps(updated_post_obj)

    # 10. Construct a FileWriteRequest
    file_write_request = FileWriteRequest(
        directory=str(full_dir_path),
        filename=base_filename,
        content=updated_content_str,
        overwrite=True,
    )

    # 11. Use file_handler.write_file()
    written_path = write_file(file_write_request)

    # 12. Log an informational message
    logger.info("Successfully added tag '%s' to note %s", normalized_tag, written_path)

    # 13. Return the Path object
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
            if not v:
                raise ValueError("Filename cannot be empty if provided")
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
    # 1. Determine the target file path
    if request.filepath:
        file_path = Path(request.filepath)
        if not file_path.name.endswith(".md"):
            logger.warning(
                "Filepath provided without .md extension for remove_tag. Consider adding .md for consistency: %s",
                file_path,
            )
        base_filename = file_path.name
        full_dir_path = file_path.parent
    elif request.filename:  # Ensured by Pydantic
        full_dir_path, base_filename = _build_file_path(
            request.filename, request.default_path
        )
        file_path = full_dir_path / base_filename
    else:
        raise ValueError(
            "Logic error: Filename or filepath determination failed despite Pydantic validation."
        )

    if not file_path.exists():
        logger.error("Error removing tag: File %s not found.", file_path)
        raise FileNotFoundError(f"File {file_path} does not exist")

    # 2. Normalize the input tag to be removed
    tag_to_remove_normalized = _normalize_tag(request.tag)

    # It's not strictly necessary to validate tag_to_remove_normalized with _validate_tag,
    # as an invalidly formatted tag is unlikely to be present in the metadata if it was added
    # via controlled functions. If it's empty after normalization, it won't match anything.

    # 3. Read the entire note content
    note_content_str = read_note(str(file_path))

    # 4. Load the front matter and content
    post = frontmatter.loads(note_content_str)
    existing_metadata = dict(post.metadata)

    # 5. Tag Removal
    tags_value = existing_metadata.get("tags", [])
    current_tags = list(tags_value) if isinstance(tags_value, list) else []
    new_tags_list = []
    tag_was_removed = False

    if not current_tags:
        logger.info(
            "No tags found in note %s. Tag '%s' not removed.",
            file_path,
            request.tag,
        )
    else:
        for existing_tag_obj in current_tags:
            existing_tag_str = str(existing_tag_obj)  # Ensure it's a string
            if _normalize_tag(existing_tag_str) == tag_to_remove_normalized:
                tag_was_removed = True
            else:
                new_tags_list.append(
                    existing_tag_str
                )  # Keep original form if not removed

    # 6. Call _generate_note_metadata
    author_value = existing_metadata.get("author")
    # Ensure author is str or None for type correctness
    author_str = str(author_value) if author_value is not None else None

    updated_post_obj = _generate_note_metadata(
        text=post.content,
        author=author_str,
        is_new_note=False,
        existing_frontmatter=existing_metadata,
        tags=new_tags_list,  # Pass the new list (might be empty or unchanged)
    )

    # 7. Serialize the updated post object
    updated_content_str = frontmatter.dumps(updated_post_obj)

    # 8. Construct a FileWriteRequest
    file_write_request = FileWriteRequest(
        directory=str(full_dir_path),
        filename=base_filename,
        content=updated_content_str,
        overwrite=True,
    )

    # 9. Use file_handler.write_file()
    written_path = write_file(file_write_request)

    # 10. Log an informational message
    if tag_was_removed:
        logger.info(
            "Successfully removed tag '%s' from note %s. New tags: %s",
            request.tag,
            written_path,
            new_tags_list,
        )
    else:
        logger.info(
            "Tag '%s' not found in note %s. Tags remain: %s",
            request.tag,
            written_path,
            current_tags,
        )

    # 11. Return the Path object
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
    effective_directory_str = (
        request.directory if request.directory else str(VAULT_PATH)
    )
    effective_directory = Path(effective_directory_str)

    # Log the effective directory for debugging
    logger.debug("Using directory for rename_tag: %s", effective_directory)

    if not effective_directory.is_dir():
        logger.error(
            "Rename tag error: Directory '%s' does not exist or is not a directory.",
            effective_directory,
        )
        # Directory must exist for this operation
        raise FileNotFoundError(
            f"Directory '{effective_directory}' not found or is not a directory."
        )

    normalized_old_tag = _normalize_tag(request.old_tag)
    # new_tag_original_case = request.new_tag # Keep original for adding
    normalized_new_tag = _normalize_tag(request.new_tag)

    if not _validate_tag(normalized_new_tag):
        logger.error(
            "Rename tag error: Invalid new_tag format for '%s'", request.new_tag
        )
        raise ValueError(
            f"Invalid new_tag: {request.new_tag} (normalized: {normalized_new_tag})"
        )

    if normalized_old_tag == normalized_new_tag:
        logger.info(
            "Rename tag: Old tag '%s' and new tag '%s' are the same after normalization. No operation needed.",
            request.old_tag,
            request.new_tag,
        )
        return []

    modified_files_paths: list[Path] = []

    # Log the files found for debugging
    md_files = list(effective_directory.rglob("*.md"))
    logger.debug("Found %d markdown files in %s", len(md_files), effective_directory)

    for file_path in md_files:
        try:
            note_content_str = read_note(str(file_path))
            post = frontmatter.loads(note_content_str)
            existing_metadata = dict(
                post.metadata
            )  # Make a copy for modification checks

            current_tags_original = existing_metadata.get("tags")
            if not isinstance(
                current_tags_original, list
            ):  # Handles None or malformed tags
                if (
                    current_tags_original is not None
                ):  # Log if tags field exists but isn't a list
                    logger.warning(
                        "Skipping file %s: 'tags' field is not a list.", file_path
                    )
                continue  # Skip if no tags list or malformed

            # Ensure all items are strings for normalization
            current_tags_str_list = [str(t) for t in current_tags_original]

            final_tags_for_file: list[str] = []
            old_tag_found_in_file = False

            for tag_in_note in current_tags_str_list:
                if _normalize_tag(tag_in_note) == normalized_old_tag:
                    old_tag_found_in_file = True
                    # Don't add old_tag to final_tags_for_file
                else:
                    final_tags_for_file.append(tag_in_note)  # Preserve original casing

            if old_tag_found_in_file:
                # Check if normalized_new_tag is already in the list (excluding old_tag instances)
                # This ensures we add the new_tag (original case) only if it's not already effectively there.
                is_new_tag_already_present = False
                for t in final_tags_for_file:
                    if _normalize_tag(t) == normalized_new_tag:
                        is_new_tag_already_present = True
                        break

                if not is_new_tag_already_present:
                    final_tags_for_file.append(
                        request.new_tag
                    )  # Add with original requested casing

                # Now, final_tags_for_file contains other tags + new_tag (if old was found and new wasn't already there)
                # _generate_note_metadata will handle normalization and deduplication of this final list.

                author_value = existing_metadata.get("author")
                # Ensure author is str or None for type correctness
                author_str = str(author_value) if author_value is not None else None

                updated_post_obj = _generate_note_metadata(
                    text=post.content,
                    author=author_str,
                    is_new_note=False,
                    existing_frontmatter=existing_metadata,  # Important to pass the original for 'created'
                    tags=final_tags_for_file,
                )
                updated_content_str = frontmatter.dumps(updated_post_obj)

                # Only write if tags have actually changed
                # Direct comparison of normalized tag sets to determine if a change occurred
                current_normalized_tags = {
                    _normalize_tag(tag) for tag in current_tags_str_list
                }
                final_normalized_tags = {
                    _normalize_tag(tag) for tag in final_tags_for_file
                }

                # Check if normalized tag sets differ, which would indicate a real change
                if current_normalized_tags != final_normalized_tags:
                    file_write_request = FileWriteRequest(
                        directory=str(file_path.parent),
                        filename=file_path.name,
                        content=updated_content_str,
                        overwrite=True,
                    )
                    written_path = write_file(file_write_request)
                    modified_files_paths.append(written_path)
                    logger.info(
                        "Renamed tag '%s' to '%s' in note %s. New tags: %s",
                        request.old_tag,
                        request.new_tag,
                        written_path,
                        updated_post_obj.metadata.get("tags", []),
                    )
                else:
                    logger.info(
                        "Skipping file %s: old_tag '%s' found, but effective tags list unchanged (e.g. new_tag was already present or old_tag was the only one and new_tag is empty).",
                        file_path,
                        request.old_tag,
                    )

        except FileNotFoundError:
            logger.warning(
                "File %s not found during rename_tag operation (possibly deleted mid-operation). Skipping.",
                file_path,
            )
        except Exception as e:
            logger.error(
                "Error processing file %s during rename_tag: %s. Skipping this file.",
                file_path,
                e,
                exc_info=True,  # Add stack trace for better debugging
            )
            # Continue to the next file

    logger.info(
        "Finished renaming tag '%s' to '%s'. Modified %d file(s).",
        request.old_tag,
        request.new_tag,
        len(modified_files_paths),
    )
    return modified_files_paths


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
            if not v:
                raise ValueError("Filename cannot be empty if provided")
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
    file_path_for_logging: str | Path = "unknown_file (pre-resolution)"
    try:
        # 1. Path Resolution
        if request.filepath:
            file_path = Path(request.filepath)
            # Basic check for .md, similar to other functions, but less critical for read-only
            if not file_path.name.endswith(".md"):
                logger.debug(
                    "Filepath provided to get_tags without .md extension: %s", file_path
                )
            file_path_for_logging = file_path
        elif request.filename:  # Ensured by Pydantic
            # _build_file_path might raise ValueError for empty filename, caught by general Exception later
            # or handled by Pydantic validator if filename is None but not empty string.
            full_dir_path, base_filename = _build_file_path(
                request.filename, request.default_path
            )
            file_path = full_dir_path / base_filename
            file_path_for_logging = file_path
        else:
            # This should be caught by Pydantic, but as a safeguard for direct calls or logic errors.
            logger.error(
                "Get_tags called with neither filename nor filepath (Pydantic validation missed)."
            )
            raise ValueError("Internal error: filename or filepath must be determined.")

        # Check existence before read_note, though read_note also checks.
        # This allows for a more specific log message if it's just "not found" vs. "read error".
        if not file_path.exists():
            logger.warning(
                "Get_tags: File %s not found. Returning empty list.", file_path
            )
            return []
        file_path_for_logging = file_path  # Update for more accurate logging path

        # 2. Note Reading
        note_content_str = read_note(
            str(file_path)
        )  # read_note handles its own FileNotFoundError and IOErrors

        # 3. Frontmatter Parsing
        try:
            post = frontmatter.loads(note_content_str)
        except (
            Exception
        ) as e:  # Catching broad Exception for python-frontmatter parsing issues
            logger.warning(
                "Get_tags: Failed to parse frontmatter for file %s: %s. Returning empty list.",
                file_path,
                e,
            )
            return []

        # 4. Tag Retrieval
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

        # Ensure all elements are strings, preserving original case
        # This handles cases where tags might be numbers or other types if manually edited.
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

    except FileNotFoundError:  # This will catch FileNotFoundError from read_note if path.exists() was true but read_note failed
        logger.warning(
            "Get_tags: File %s not found (error during read_note). Returning empty list.",
            file_path_for_logging,
        )
        return []
    except (IOError, OSError) as e:  # Catch IO errors from read_note or path operations
        logger.error(
            "Get_tags: File system error for %s: %s. Returning empty list.",
            file_path_for_logging,
            e,
        )
        return []
    except (
        ValueError
    ) as e:  # Catch Pydantic validation errors if somehow bypassed or other ValueErrors
        logger.error("Get_tags: Input error: %s. Returning empty list.", e)
        return []
    except Exception as e:
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
def list_all_tags(directory: str | None) -> list[str]:
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
def find_notes_with_tag(tag: str, directory: str | None) -> list[str]:
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
