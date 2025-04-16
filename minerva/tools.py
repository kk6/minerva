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


def write_note(request: WriteNoteRequest) -> Path | None:
    """
    Write a note to a file in the Obsidian vault.

    Args:
        request (WriteNoteRequest): The request object containing the text, filename, and overwrite flag.
    Returns:
        file_path (Path): The path to the written file.
    """
    file_path = None
    try:
        file_write_request = FileWriteRequest(
            directory=str(VAULT_PATH),
            filename=f"{request.filename}.md",
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


def read_note(request: ReadNoteRequest) -> str | None:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        request (ReadNoteRequest): The request object containing the filepath.
    Returns:
        content (str): The content of the file.
    """
    content = None
    directory, filename = os.path.split(request.filepath)
    try:
        rile_read_request = FileReadRequest(
            directory=directory,
            filename=filename,
        )
        content = read_file(rile_read_request)
        logger.info(f"File read from {filename}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

    # Return the content
    return content


def search_notes(request: SearchNoteRequest) -> list[SearchResult]:
    """
    Search for a keyword in all files in the Obsidian vault.

    Args:
        request (SearchNoteRequest): The request object containing the query and case sensitivity flag.
    Returns:
        matching_files (list[SearchResult]): A list of paths to the files containing the keyword.
    """
    if not request.query:
        raise ValueError("Query cannot be empty")

    matching_files = []
    try:
        search_config = SearchConfig(
            directory=str(VAULT_PATH),
            keyword=request.query,
            file_extensions=[".md"],
            case_sensitive=request.case_sensitive,
        )
        matching_files = search_keyword_in_files(search_config)
        logger.info(f"Files found: {matching_files}")
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise

    # Return the list of matching files
    return matching_files
