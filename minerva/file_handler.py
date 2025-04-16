import logging
import os
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator, Field

FORBIDDEN_CHARS = '<>:"/\\|?*'
ENCODING = "utf-8"

logger = logging.getLogger(__name__)


class FileOperationRequest(BaseModel):
    """
    Base request model for file operations.
    """

    directory: str = Field(description="Directory for the file operation")
    filename: str = Field(description="Name of the file")

    @field_validator("directory")
    def validate_directory(cls, v):
        """
        Validate the directory path.
        """
        if not isinstance(v, str):
            raise ValueError("Directory must be a string")
        return v

    @field_validator("filename")
    def validate_filename(cls, v):
        """
        Validate the filename.
        """
        if not v:
            raise ValueError("Filename cannot be empty")
        if os.path.isabs(v):
            raise ValueError("Filename cannot be an absolute path")
        if not isinstance(v, str):
            raise ValueError("Filename must be a string")
        if any(char in v for char in FORBIDDEN_CHARS):
            raise ValueError(
                f"Filename contains forbidden characters: {FORBIDDEN_CHARS}"
            )
        return v


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
    def directory_must_exist(cls, v):
        """
        Validate that the directory exists.
        """
        if not isinstance(v, str):
            raise ValueError("Directory must be a string")
        path = Path(v)
        if not path.is_dir():
            raise ValueError(f"Directory {v} does not exist")
        return v

    @field_validator("file_extensions")
    def format_extensions(cls, v):
        """
        Format the file extensions to include the dot.
        """
        if v is None:
            return None
        if isinstance(v, str):
            extensions = [f".{ext.lower().lstrip('.')}" for ext in v.split(",")]
            return extensions
        return [f".{ext.lower().lstrip('.')}" for ext in v]


class SearchResult(BaseModel):
    """
    Model for search results.
    """

    file_path: str = Field(description="Path to the file")
    line_number: Optional[int] = Field(
        description="Line number where the keyword was found"
    )
    context: Optional[str] = Field(description="Context around the found keyword")


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary.
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except (IOError, PermissionError) as e:
        logger.warning(f"Error checking if file is binary: {e}")
        return False


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

    # Create a regex pattern if case sensitivity is disabled
    if not config.case_sensitive:
        # Use re.escape to safely handle meta characters as regex
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

                try:
                    # Open the file and search for the keyword
                    with open(file_path, "r", encoding=ENCODING) as file:
                        for line_num, line in enumerate(file, 1):
                            if config.case_sensitive:
                                found = config.keyword in line
                            else:
                                found = pattern.search(line) is not None

                            if found:
                                result = SearchResult(
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    context=line.strip(),
                                )
                                matching_files.append(result)
                                break  # Stop after finding first match in this file
                except (UnicodeDecodeError, PermissionError):
                    # Ignore read errors and continue
                    logger.warning(f"Could not read file {file_path}. Skipping.")

    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise

    return matching_files


def _get_validated_file_path(directory: str, filename: str) -> Path:
    """
    Validate and return the full file path.
    """
    dirpath = Path(directory)
    # Check if the directory is absolute
    if not dirpath.is_absolute():
        raise ValueError("Directory must be an absolute path")

    return dirpath / filename


def write_file(request: FileWriteRequest) -> Path:
    """
    Write the content to a file in the specified directory.
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
    """
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Check if the file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Read the content from the file
    with open(file_path, "r", encoding=ENCODING) as f:
        content = f.read()
    return content
