import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from minerva.file_handler import FileWriteRequest, write_file, FORBIDDEN_CHARS


class TestFileHandler:
    """Test suite for file handler functions."""

    def test_write_file_success(self):
        """Test writing a file successfully."""
        with TemporaryDirectory() as tempdir:
            request = FileWriteRequest(
                directory=tempdir,
                filename="test.txt",
                content="Hello, World!",
                overwrite=True,
            )
            file_path = write_file(request)
            assert file_path == Path(tempdir) / "test.txt"
            assert file_path.exists()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == "Hello, World!"

    def test_write_file_overwrite_false(self):
        """Test writing a file with overwrite set to False."""
        with TemporaryDirectory() as tempdir:
            file_path = Path(tempdir) / "existing.txt"
            # Create a file to ensure it exists
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Hello, World!")

            # Create a request to write the file with overwrite set to False
            request = FileWriteRequest(
                directory=tempdir,
                filename="existing.txt",
                content="New Content",
                overwrite=False,
            )
            # Attempt to write the file with overwrite set to False
            with pytest.raises(FileExistsError):
                write_file(request)

            # Check that the original content is still there
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == "Hello, World!"

    def test_write_file_overwrite_true(self):
        """Test writing a file with overwrite set to True."""
        with TemporaryDirectory() as tempdir:
            file_path = Path(tempdir) / "existing.txt"
            # Create a file to ensure it exists
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Hello, World!")

            # Create a request to write the file with overwrite set to True
            request = FileWriteRequest(
                directory=tempdir,
                filename="existing.txt",
                content="New Content",
                overwrite=True,
            )
            # Write the file with overwrite set to True
            write_file(request)

            # Check that the content has been updated
            with open(file_path, "r", encoding="utf-8") as f:
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

    def test_write_file_invalid_filename(self):
        """Test writing a file with an invalid filename."""
        with TemporaryDirectory() as tempdir:
            with pytest.raises(ValueError) as excinfo:
                FileWriteRequest(
                    directory=tempdir,
                    filename="invalid/filename.txt",
                    content="Hello, World!",
                    overwrite=True,
                )

            assert f"Filename contains forbidden characters: {FORBIDDEN_CHARS}" in str(
                excinfo.value
            )
