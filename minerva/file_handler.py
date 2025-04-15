import os
from pathlib import Path

from pydantic import BaseModel, field_validator, Field

FORBIDDEN_CHARS = '<>:"/\\|?*'
ENCODING = "utf-8"


class FileWriteRequest(BaseModel):
    """
    Request model for writing to a file.
    """

    directory: str = Field(description="Directory to write the file in")
    filename: str = Field(description="Name of the file to write")
    content: str = Field(description="Content to write to the file")
    overwrite: bool = Field(
        default=False, description="Overwrite the file if it exists"
    )

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


class FileReadRequest(BaseModel):
    """
    Request model for reading from a file.
    """

    directory: str = Field(description="Directory to read the file from")
    filename: str = Field(description="Name of the file to read")

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


def write_file(request: FileWriteRequest) -> Path:
    """
    Write the content to a file in the specified directory.
    """
    directory = Path(request.directory)
    # Check if the directory is absolute
    if not directory.is_absolute():
        raise ValueError("Directory must be an absolute path")

    # Ensure the directory exists
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)

    # Construct the full file path
    file_path = directory / request.filename
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
    directory = Path(request.directory)
    # Check if the directory is absolute
    if not directory.is_absolute():
        raise ValueError("Directory must be an absolute path")

    # Construct the full file path
    file_path = directory / request.filename

    # Check if the file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Read the content from the file
    with open(file_path, "r", encoding=ENCODING) as f:
        content = f.read()
    return content
