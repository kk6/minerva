import logging
import os
from pathlib import Path

import frontmatter
from pydantic import BaseModel, Field, field_validator

from minerva.file_handler import (
    FileWriteRequest,
    write_file,
    FileReadRequest,
    read_file,
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


def _prepare_note_for_writing(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR
) -> tuple[Path, Path, str]:
    """
    Private function to prepare a note for writing.

    Args:
        text: The content to write to the file.
        filename: The name of the file to write.
        author: The author name to add to the frontmatter.
        default_path: The default directory to save the file.

    Returns:
        tuple: (full_dir_path, base_filename, prepared_content)
    """
    # Check frontmatter
    # If the text starts with "---", it is assumed to have frontmatter
    has_frontmatter = text.startswith("---\n")
    if has_frontmatter:
        # If the text already has frontmatter, load it
        post = frontmatter.loads(text)
    else:
        # Create a new frontmatter object
        post = frontmatter.Post(text)

    # Add default frontmatter if it doesn't exist
    post.metadata["author"] = author or DEFAULT_NOTE_AUTHOR

    # Format filename to ensure it has a .md extension
    if ".md" not in filename:
        filename = f"{filename}.md"

    # If the filename contains path separators, separate into subdirectory and filename
    path_parts = Path(filename)

    # Get subdirectory path and filename
    subdirs = path_parts.parent
    base_filename = path_parts.name

    if not base_filename:
        raise ValueError("Filename cannot be empty")

    # Create the final directory path (connecting the vault root directory and subdirectory path)
    full_dir_path = VAULT_PATH
    if str(subdirs) != ".":  # If a subdirectory is specified
        full_dir_path = full_dir_path / subdirs
    elif default_path:
        full_dir_path = full_dir_path / default_path

    # Create directory if it doesn't exist
    if not full_dir_path.exists():
        full_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_dir_path}")

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
        full_dir_path, base_filename, content = _prepare_note_for_writing(
            text=text,
            filename=filename,
            author=author,
            default_path=default_path
        )

        # Create the FileWriteRequest with overwrite=False to ensure we don't overwrite existing files
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=False,  # Never overwrite when creating new notes
        )

        file_path = write_file(file_write_request)
        logger.info(f"New note created at {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error creating note: {e}")
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
        full_dir_path, base_filename, content = _prepare_note_for_writing(
            text=text,
            filename=filename,
            author=author,
            default_path=default_path
        )

        # Check if the file exists before attempting to edit it
        file_path = full_dir_path / base_filename
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot edit note. File {file_path} does not exist")

        # Create the FileWriteRequest with overwrite=True since we're editing an existing file
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=True,  # Always overwrite when editing notes
        )

        file_path = write_file(file_write_request)
        logger.info(f"Note edited at {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error editing note: {e}")
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

    # Check frontmatter
    # If the text starts with "---", it is assumed to have frontmatter
    has_frontmatter = request.text.startswith("---\n")
    if has_frontmatter:
        # If the text already has frontmatter, load it
        post = frontmatter.loads(request.text)
    else:
        # Create a new frontmatter object
        post = frontmatter.Post(request.text)

    # Add default frontmatter if it doesn't exist
    post.metadata["author"] = request.author or DEFAULT_NOTE_AUTHOR

    # If the filename contains path separators, separate into subdirectory and filename
    path_parts = Path(request.filename)

    # Get subdirectory path and filename
    subdirs = path_parts.parent
    base_filename = path_parts.name

    if not base_filename:
        raise ValueError("Filename cannot be empty")

    # Create the final directory path (connecting the vault root directory and subdirectory path)
    full_dir_path = VAULT_PATH
    if str(subdirs) != ".":  # If a subdirectory is specified
        full_dir_path = full_dir_path / subdirs
    elif request.default_path:
        full_dir_path = full_dir_path / request.default_path

    # Create directory if it doesn't exist
    if not full_dir_path.exists():
        full_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_dir_path}")

    try:
        content = frontmatter.dumps(post)
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=base_filename,
            content=content,
            overwrite=request.is_overwrite,
        )
        file_path = write_file(file_write_request)
        logger.info(f"File written to {file_path}")
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        raise

    # Return the file path
    return file_path


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
        logger.info(f"File read from {filepath}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

    return content


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
        logger.info(f"Found {len(matching_files)} files matching the query: {query}")
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise

    return matching_files
