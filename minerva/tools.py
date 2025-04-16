import logging
import os
from pathlib import Path

from pydantic import BaseModel, Field

from minerva.file_handler import (
    FileWriteRequest,
    write_file,
    FileReadRequest,
    read_file,
    SearchConfig,
    SearchResult,
    search_keyword_in_files,
)

from minerva.config import VAULT_PATH

# Set up logging
logger = logging.getLogger(__name__)


class WriteNoteRequest(BaseModel):
    """
    Request model for writing a note to a file.

    This model contains the text to write, the filename, and an overwrite flag.

    Attributes:
        text (str): The content to write to the file.
        filename (str): The name of the file to write.
        is_overwrite (bool): Whether to overwrite the file if it exists.
    """

    text: str = Field(..., description="The content to write to the file.")
    filename: str = Field(..., description="The name of the file to write.")
    is_overwrite: bool = Field(
        False,
        description="Whether to overwrite the file if it exists.",
    )


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


def write_note(request: WriteNoteRequest) -> Path:
    """
    Write a note to a file in the Obsidian vault.

    Args:
        request (WriteNoteRequest): The request object containing the text, filename, and overwrite flag.
    Returns:
        Path: The path to the written file.
    """
    if not request.filename:
        raise ValueError("Filename cannot be empty")

    # If the filename contains path separators, separate into subdirectory and filename
    path_parts = Path(request.filename)

    # Get subdirectory path and filename
    subdirs = path_parts.parent
    base_filename = path_parts.name

    if not base_filename:
        raise ValueError("Filename cannot be empty")

    # Create the final directory path (connecting the vault root directory and subdirectory path)
    full_dir_path = VAULT_PATH
    if str(subdirs) != '.':  # If a subdirectory is specified
        full_dir_path = full_dir_path / subdirs

    # Create directory if it doesn't exist
    if not full_dir_path.exists():
        full_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_dir_path}")

    try:
        file_write_request = FileWriteRequest(
            directory=str(full_dir_path),
            filename=f"{base_filename}.md",
            content=request.text,
            overwrite=request.is_overwrite,
        )
        file_path = write_file(file_write_request)
        logger.info(f"File written to {file_path}")
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        raise

    # Return the file path
    return file_path


def read_note(request: ReadNoteRequest) -> str:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        request (ReadNoteRequest): The request object containing the filepath.
    Returns:
        str: The content of the file.
    """
    directory, filename = os.path.split(request.filepath)
    try:
        file_read_request = FileReadRequest(
            directory=directory,
            filename=filename,
        )
        content = read_file(file_read_request)
        logger.info(f"File read from {request.filepath}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

    return content


def search_notes(request: SearchNoteRequest) -> list[SearchResult]:
    """
    Search for a keyword in all files in the Obsidian vault.

    Args:
        request (SearchNoteRequest): The request object containing the query and case sensitivity flag.
    Returns:
        list[SearchResult]: A list of search results containing file paths, line numbers and context.
    """
    if not request.query:
        raise ValueError("Query cannot be empty")

    try:
        search_config = SearchConfig(
            directory=str(VAULT_PATH),
            keyword=request.query,
            file_extensions=[".md"],
            case_sensitive=request.case_sensitive,
        )
        matching_files = search_keyword_in_files(search_config)
        logger.info(
            f"Found {len(matching_files)} files matching the query: {request.query}"
        )
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise

    return matching_files
