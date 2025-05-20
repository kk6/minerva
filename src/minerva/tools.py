import logging
import os
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
    def format_filename(cls, v):
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
    confirm: bool = Field(
        False,
        description="Whether to confirm the deletion. If False, only returns what would be deleted without actually deleting.",
    )

    @field_validator("filename")
    def format_filename(cls, v):
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
    def validate_input(cls, model):
        """
        Validate that at least one of filename or filepath is provided.
        """
        if model.filename is None and model.filepath is None:
            raise ValueError("Either filename or filepath must be provided")
        return model


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
) -> frontmatter.Post:
    """
    Generate or update YAML frontmatter metadata for a note.

    This function processes only the metadata portion of a note (frontmatter),
    handling both creation of new metadata and updating of existing metadata.
    It does not perform any file operations or path manipulations.

    Args:
        text: The text content of the note (with or without existing frontmatter)
        author: The author name to include in the metadata
        is_new_note: Whether this is a new note (True) or an update to existing note (False)
        existing_frontmatter: Existing frontmatter data from the file (if any)

    Returns:
        frontmatter.Post: Post object with properly processed frontmatter

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

    return post


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
                return post.metadata
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
    except Exception as e:
        logger.warning("Failed to read existing file %s for metadata: %s", file_path, e)
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
    try:
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

    except Exception as e:
        logger.error("Error creating note: %s", e)
        raise


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
    try:
        # Prepare note for writing
        full_dir_path, base_filename, content = _assemble_complete_note(
            text=text,
            filename=filename,
            author=author,
            default_path=default_path,
            is_new_note=False,
        )

        # Check if the file exists before attempting to edit it
        file_path = full_dir_path / base_filename
        if not file_path.exists():
            raise FileNotFoundError(
                "Cannot edit note. File %s does not exist", file_path
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

    except Exception as e:
        logger.error("Error editing note: %s", e)
        raise


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

        # Create directory if it doesn't exist
        if not full_dir_path.exists():
            full_dir_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory: %s", full_dir_path)

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
    except Exception as e:
        logger.error("Error writing file: %s", e)
        raise


def read_note(filepath: str) -> str:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        filepath (str): The full path of the file to read.
    Returns:
        str: The content of the file.
    """
    directory, filename = os.path.split(filepath)
    try:
        file_read_request = FileReadRequest(
            directory=directory,
            filename=filename,
        )
        content = read_file(file_read_request)
        logger.info("File read from %s", filepath)
    except Exception as e:
        logger.error("Error reading file: %s", e)
        raise

    return content


def delete_note(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
    confirm: bool = False,
) -> Path | DeleteConfirmationResult:
    """
    Delete a note from the Obsidian vault.

    Args:
        filename (str, optional): The name of the file to delete. If it doesn't have a .md extension, it will be added.
        filepath (str, optional): The full path of the file to delete. If provided, filename is ignored.
        default_path (str): The default directory to look for the file. Default is the value of DEFAULT_NOTE_DIR.
        confirm (bool): Whether to confirm the deletion. Default is False, which means only return what would be deleted.

    Returns:
        Path | DeleteConfirmationResult:
            - Path: The path to the deleted file if confirm is True.
            - DeleteConfirmationResult: Object with file path and confirmation message if confirm is False.

    Raises:
        ValueError: If neither filename nor filepath is provided.
        FileNotFoundError: If the file doesn't exist.
    """
    # Validate input parameters using the request model
    request = DeleteNoteRequest(
        filename=filename,
        filepath=filepath,
        default_path=default_path,
        confirm=confirm,
    )

    try:
        # Handle case when filepath is directly provided
        if request.filepath:
            file_path = Path(request.filepath)
        # Handle case when filename is provided
        else:
            # filename is guaranteed to be not None here due to model validation
            assert request.filename is not None
            # Build file path
            full_dir_path, base_filename = _build_file_path(
                request.filename, request.default_path
            )
            file_path = full_dir_path / base_filename

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        # If confirm is False, only return what would be deleted
        if not request.confirm:
            message = f"このファイルを削除しますか？: {file_path}\n削除するには confirm=True を指定してください。"
            return DeleteConfirmationResult(
                file_path=str(file_path),
                message=message,
            )

        # Proceed with deletion
        file_delete_request = FileDeleteRequest(
            directory=str(file_path.parent),
            filename=file_path.name,
        )

        # Delete the file
        deleted_path = delete_file(file_delete_request)
        logger.info("Note deleted at %s", deleted_path)
        return deleted_path

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        raise
    except Exception as e:
        logger.error("Error deleting note: %s", e)
        raise


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

    try:
        search_config = SearchConfig(
            directory=str(VAULT_PATH),
            keyword=query,
            file_extensions=[".md"],
            case_sensitive=case_sensitive,
        )
        matching_files = search_keyword_in_files(search_config)
        logger.info("Found %s files matching the query: %s", len(matching_files), query)
    except PermissionError as e:
        logger.error("Permission denied during search: %s", e)
        raise PermissionError(f"Permission denied when searching files: {e}") from e
    except IOError as e:
        logger.error("File I/O error during search: %s", e)
        raise IOError(f"Failed to search files in vault: {e}") from e
    except ValueError as e:
        logger.error("Invalid value in search operation: %s", e)
        raise ValueError(f"Invalid search parameters: {e}") from e
    except Exception as e:
        logger.error("Unexpected error searching files: %s", e)
        raise RuntimeError(f"Unexpected error occurred during search: {e}") from e

    return matching_files
