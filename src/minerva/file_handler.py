import logging
import os
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator, Field

from minerva.validators import FilenameValidator, PathValidator

ENCODING = "utf-8"

logger = logging.getLogger(__name__)


class FileOperationRequest(BaseModel):
    """
    Base request model for file operations.
    """

    directory: str = Field(description="Directory for the file operation")
    filename: str = Field(description="Name of the file")

    @field_validator("filename")
    def validate_filename(cls, v: str) -> str:
        """
        Validate the filename.
        """
        return FilenameValidator.validate_filename(v)


class FileWriteRequest(FileOperationRequest):
    """
    Request model for writing to a file.
    """

    content: str = Field(description="Content to write to the file")
    overwrite: bool = Field(
        default=False, description="Overwrite the file if it exists"
    )


class FileReadRequest(FileOperationRequest):
    """
    Request model for reading from a file.
    """


class FileDeleteRequest(FileOperationRequest):
    """
    Request model for deleting a file.
    """


class SearchConfig(BaseModel):
    """
    Configuration model for search operations.
    """

    directory: str = Field(description="Directory to search in")
    keyword: str = Field(description="Keyword to search for in the files")
    case_sensitive: bool = Field(
        default=True, description="Whether the search is case sensitive"
    )
    file_extensions: Optional[list[str]] = Field(
        default=None,
        description="List of file extensions to include in the search",
    )

    @field_validator("directory")
    def directory_must_exist(cls, v: str) -> str:
        """
        Validate that the directory exists.
        """
        return PathValidator.validate_directory_exists(v)

    @field_validator("file_extensions")
    def format_extensions(cls, v: list[str]) -> list[str]:
        """
        Format the file extensions to include the dot.
        """
        return [f".{ext.lower().lstrip('.')}" for ext in v]


class SearchResult(BaseModel):
    """
    Model for search results.
    """

    file_path: str = Field(description="Path to the file")
    line_number: Optional[int] = Field(
        default=None, description="Line number where the keyword was found"
    )
    context: Optional[str] = Field(
        default=None, description="Context around the found keyword"
    )


class SemanticSearchResult(BaseModel):
    """
    Model for semantic search results using vector similarity.
    """

    file_path: str = Field(description="Path to the file")
    title: Optional[str] = Field(
        default=None,
        description="Title of the note (extracted from frontmatter or filename)",
    )
    content_preview: str = Field(description="Preview of the relevant content")
    similarity_score: float = Field(
        description="Similarity score between 0.0 and 1.0", ge=0.0, le=1.0
    )
    metadata: Optional[dict] = Field(
        default=None, description="Additional metadata from the note"
    )


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary.
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except (IOError, PermissionError) as e:
        logger.warning("Error checking if file is binary: %s", e)
        return False


def _process_file_for_search(
    file_path: Path, pattern: re.Pattern, config: SearchConfig
) -> SearchResult | None:
    """
    Process a single file for search and return a match if found.

    Args:
        file_path: Path to the file to search
        pattern: Compiled regex pattern to search for
        config: Search configuration

    Returns:
        SearchResult if a match is found, None otherwise
    """
    try:
        # Open the file and search for the keyword
        with open(file_path, "r", encoding=ENCODING) as file:
            for line_num, line in enumerate(file, 1):
                if config.case_sensitive:
                    found = config.keyword in line
                else:
                    found = pattern.search(line) is not None

                if found:
                    return SearchResult(
                        file_path=str(file_path),
                        line_number=line_num,
                        context=line.strip(),
                    )
    except (UnicodeDecodeError, PermissionError):
        # Ignore read errors and continue
        sanitized_path = str(file_path).replace("\n", "_").replace("\r", "_")
        logger.warning("Could not read file %s. Skipping.", sanitized_path)

    return None


def search_keyword_in_files(config: SearchConfig) -> list[SearchResult]:
    """
    Search for a keyword in files within a directory.

    Note: This function returns only the first match in each file.

    Args:
        config (SearchConfig): Configuration for the search operation.
    Returns:
        list[SearchResult]: List of search results containing file paths and line numbers.
            Each file will have at most one entry in the results.
    """
    matching_files = []

    if config.case_sensitive:
        # Compile the pattern only once for case-sensitive search
        pattern = re.compile(re.escape(config.keyword))
    else:
        # Compile the pattern only once for case-insensitive search
        pattern = re.compile(re.escape(config.keyword), re.IGNORECASE)

    try:
        # Recursively search the directory
        for root, _, files in os.walk(config.directory):
            for file_name in files:
                # Check if the file matches the specified extensions
                if config.file_extensions is not None:
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext not in config.file_extensions:
                        continue

                file_path = Path(root) / file_name

                # Skip binary files
                if is_binary_file(file_path):
                    continue

                result = _process_file_for_search(file_path, pattern, config)
                if result:
                    matching_files.append(result)

    except OSError as e:
        logger.error(
            "OS error during search for keyword '%s' in directory '%s': %s",
            config.keyword,
            config.directory,
            e,
        )
        raise
    except Exception as e:  # Keep for truly unexpected
        logger.error(
            "Unexpected error during search for keyword '%s' in directory '%s': %s",
            config.keyword,
            config.directory,
            e,
        )
        raise

    return matching_files


def _get_validated_file_path(directory: str, filename: str) -> Path:
    """
    Validate and return the full file path.
    """
    PathValidator.validate_directory_path(directory)
    return Path(directory) / filename


def write_file(request: FileWriteRequest) -> Path:
    """
    Write the content to a file in the specified directory.
    Args:
        request (FileWriteRequest): Request object containing directory, filename, and content.
    Returns:
        file_path (Path): Path to the written file.
    Raises:
        FileExistsError: If the file already exists and overwrite is set to False.
    """
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Ensure the directory exists
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists() and not request.overwrite:
        raise FileExistsError(
            f"File {file_path} already exists and overwrite is set to False"
        )

    # Write the content to the file
    with open(file_path, "w", encoding=ENCODING) as f:
        f.write(request.content)
    return file_path


def read_file(request: FileReadRequest) -> str:
    """
    Read the content from a file in the specified directory.
    Args:
        request (FileReadRequest): Request object containing directory and filename.
    Returns:
        content (str): Content of the file.
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Check if the file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Read the content from the file
    with open(file_path, "r", encoding=ENCODING) as f:
        content = f.read()
    return content


def delete_file(request: FileDeleteRequest) -> Path:
    """
    Delete a file in the specified directory.

    Args:
        request (FileDeleteRequest): Request object containing directory and filename.
    Returns:
        file_path (Path): Path to the deleted file.
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Check if the file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Delete the file
    try:
        file_path.unlink()
        logger.info("File %s deleted successfully", file_path)
    except OSError as e:
        logger.warning(
            "Failed to delete file %s. Error type: %s. Error message: %s"
            "This might be due to insufficient permissions, the file being in use, or other OS-level issues.",
            file_path,
            type(e).__name__,
            e,
        )
        raise
    return file_path
