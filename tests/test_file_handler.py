import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from minerva.file_handler import (
    FileWriteRequest,
    FileReadRequest,
    read_file,
    write_file,
    FORBIDDEN_CHARS,
    ENCODING,
)


@pytest.fixture
def temp_dir():
    """Fixture that provides a temporary directory for file operations.

    Yields:
        str: Path to a temporary directory that is automatically cleaned up.
    """
    with TemporaryDirectory() as tempdir:
        yield tempdir


class TestFileHandler:
    """Test suite for file handler functions."""

    def test_write_file_success(self, temp_dir):
        """Test writing a file successfully.

        Expects:
            - File is created at the expected path
            - File exists in the filesystem
            - File content matches the input
        """
        request = FileWriteRequest(
            directory=temp_dir,
            filename="test.txt",
            content="Hello, World!",
            overwrite=True,
        )
        file_path = write_file(request)
        assert file_path == Path(temp_dir) / "test.txt"
        assert file_path.exists()
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_write_file_overwrite_false(self, temp_dir):
        """Test writing a file with overwrite set to False."""
        file_path = Path(temp_dir) / "existing.txt"
        # Create a file to ensure it exists
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("Hello, World!")

        # Create a request to write the file with overwrite set to False
        request = FileWriteRequest(
            directory=temp_dir,
            filename="existing.txt",
            content="New Content",
            overwrite=False,
        )
        # Attempt to write the file with overwrite set to False
        with pytest.raises(FileExistsError):
            write_file(request)

        # Check that the original content is still there
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_write_file_overwrite_true(self, temp_dir):
        """Test writing a file with overwrite set to True."""
        file_path = Path(temp_dir) / "existing.txt"
        # Create a file to ensure it exists
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("Hello, World!")

        # Create a request to write the file with overwrite set to True
        request = FileWriteRequest(
            directory=temp_dir,
            filename="existing.txt",
            content="New Content",
            overwrite=True,
        )
        # Write the file with overwrite set to True
        write_file(request)

        # Check that the content has been updated
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "New Content"

    def test_write_file_invalid_directory(self):
        """Test writing a file with an invalid directory."""

        with pytest.raises(ValueError) as excinfo:
            request = FileWriteRequest(
                directory="invalid_directory",
                filename="test.txt",
                content="Hello, World!",
                overwrite=True,
            )
            write_file(request)
        assert str(excinfo.value) == "Directory must be an absolute path"

    def test_write_file_invalid_filename(self, temp_dir):
        """Test writing a file with an invalid filename."""
        with pytest.raises(ValueError) as excinfo:
            FileWriteRequest(
                directory=temp_dir,
                filename="invalid/filename.txt",
                content="Hello, World!",
                overwrite=True,
            )

        assert f"Filename contains forbidden characters: {FORBIDDEN_CHARS}" in str(
            excinfo.value
        )

    def test_read_file_success(self, temp_dir):
        """Test reading a file successfully."""
        file_path = Path(temp_dir) / "test.txt"
        # Create a file to read
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("Hello, World!")

        request = FileReadRequest(
            directory=temp_dir,
            filename="test.txt",
        )
        content = read_file(request)
        assert content == "Hello, World!"

    def test_read_file_not_found(self, temp_dir):
        """Test reading a file that does not exist."""
        request = FileReadRequest(
            directory=temp_dir,
            filename="non_existent.txt",
        )
        with pytest.raises(FileNotFoundError):
            read_file(request)

    def test_read_file_invalid_directory(self):
        """Test reading a file with an invalid directory."""
        with pytest.raises(ValueError) as excinfo:
            request = FileReadRequest(
                directory="invalid_directory",
                filename="test.txt",
            )
            read_file(request)
        assert str(excinfo.value) == "Directory must be an absolute path"

    @pytest.mark.parametrize(
        "filename,expected_message",
        [
            ("", "Filename cannot be empty"),
            ("/absolute/path/to/file.txt", "Filename cannot be an absolute path"),
            (
                f"test{FORBIDDEN_CHARS[0]}file.txt",
                f"Filename contains forbidden characters: {FORBIDDEN_CHARS}",
            ),
        ],
    )
    def test_invalid_filename_validation(self, temp_dir, filename, expected_message):
        """Test validation of invalid filenames.

        Tests various invalid filename scenarios using parametrization.

        Expects:
            - ValueError is raised with the appropriate message for each invalid case
        """
        with pytest.raises(ValueError) as excinfo:
            FileReadRequest(
                directory=temp_dir,
                filename=filename,
            )
        assert expected_message in str(excinfo.value)

    def test_read_file_invalid_encoding(self, temp_dir):
        """Test reading a file with invalid encoding."""
        file_path = Path(temp_dir) / "test.txt"
        # Create a file with invalid encoding
        with open(file_path, "wb") as f:
            f.write(b"\x80\x81\x82")

        request = FileReadRequest(
            directory=temp_dir,
            filename="test.txt",
        )
        with pytest.raises(UnicodeDecodeError):
            read_file(request)
