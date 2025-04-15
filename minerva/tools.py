import logging
import os
from pathlib import Path

from minerva.file_handler import (
    FileWriteRequest,
    write_file,
    FileReadRequest,
    read_file,
    SearchConfig,
    SearchResult,
    search_keyword_in_files,
)

from .config import VAULT_PATH

# Set up logging
logger = logging.getLogger(__name__)


def write_note(text: str, filename: str, is_overwrite: bool = False) -> Path | None:
    """
    Write a note to a file in the Obsidian vault.

    Args:
        text (str): The content to write to the file.
        filename (str): The name of the file to write.
        is_overwrite (bool): Whether to overwrite the file if it exists. Defaults to False.
    Returns:
        file_path (Path): The path to the written file.
    """
    file_path = None
    try:
        request = FileWriteRequest(
            directory=str(VAULT_PATH),
            filename=f"{filename}.md",
            content=text,
            overwrite=is_overwrite,
        )
        file_path = write_file(request)
        logger.info(f"File written to {file_path}")
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        raise

    # Return the file path
    return file_path


def read_note(filepath: str) -> str | None:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        filepath (str): The full path of the file to read.
    Returns:
        content (str): The content of the file.
    """
    content = None
    directory, filename = os.path.split(filepath)
    try:
        request = FileReadRequest(
            directory=directory,
            filename=filename,
        )
        content = read_file(request)
        logger.info(f"File read from {filename}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

    # Return the content
    return content


def search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]:
    """
    Search for a keyword in all files in the Obsidian vault.

    Args:
        query (str): The keyword to search for.
        case_sensitive (bool): Whether the search should be case sensitive. Defaults to True.
    Returns:
        matching_files (list[SearchResult]): A list of paths to the files containing the keyword.
    """
    if not query:
        raise ValueError("Query cannot be empty")

    matching_files = []
    try:
        search_config = SearchConfig(
            directory=str(VAULT_PATH),
            keyword=query,
            file_extensions=[".md"],
            case_sensitive=case_sensitive,
        )
        matching_files = search_keyword_in_files(search_config)
        logger.info(f"Files found: {matching_files}")
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise

    # Return the list of matching files
    return matching_files
