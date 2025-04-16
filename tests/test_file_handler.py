import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import pydantic

from minerva.file_handler import (
    FileWriteRequest,
    FileReadRequest,
    read_file,
    write_file,
    FORBIDDEN_CHARS,
    ENCODING,
    SearchConfig,
    is_binary_file,
    search_keyword_in_files,
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

    def test_is_binary_file(self, temp_dir):
        """Test detecting binary files."""
        # Create a text file
        text_file_path = Path(temp_dir) / "text.txt"
        with open(text_file_path, "w", encoding=ENCODING) as f:
            f.write("Hello, World!")

        # Create a binary file
        binary_file_path = Path(temp_dir) / "binary.bin"
        with open(binary_file_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        assert not is_binary_file(text_file_path)
        assert is_binary_file(binary_file_path)

    def test_is_binary_file_permission_error(self, mocker, temp_dir):
        """is_binary_fileでPermissionError/IOErrorが発生した場合はFalseを返す"""
        from minerva.file_handler import is_binary_file

        dummy_path = Path(temp_dir) / "dummy.txt"
        dummy_path.touch()
        mocker.patch("builtins.open", side_effect=PermissionError)
        assert is_binary_file(dummy_path) is False
        mocker.patch("builtins.open", side_effect=IOError)
        assert is_binary_file(dummy_path) is False

    def test_search_keyword_basic(self, temp_dir):
        """Test basic keyword search functionality."""
        # Create test files
        file1 = Path(temp_dir) / "file1.txt"
        with open(file1, "w", encoding=ENCODING) as f:
            f.write("This is a test file with a keyword: apple")

        file2 = Path(temp_dir) / "file2.txt"
        with open(file2, "w", encoding=ENCODING) as f:
            f.write("This file doesn't have the keyword")

        config = SearchConfig(directory=temp_dir, keyword="apple", case_sensitive=True)

        results = search_keyword_in_files(config)
        assert len(results) == 1
        assert results[0].file_path == str(file1)
        assert results[0].line_number == 1
        assert "keyword: apple" in results[0].context

    def test_search_keyword_case_sensitivity(self, temp_dir):
        """Test case sensitivity in keyword search."""
        # Create test file
        file_path = Path(temp_dir) / "case.txt"
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("This file has APPLE and apple")

        # Case sensitive search should find only lowercase
        config1 = SearchConfig(directory=temp_dir, keyword="apple", case_sensitive=True)
        results1 = search_keyword_in_files(config1)
        assert len(results1) == 1
        assert "apple" in results1[0].context

        # Case insensitive search should find both
        config2 = SearchConfig(
            directory=temp_dir, keyword="apple", case_sensitive=False
        )
        results2 = search_keyword_in_files(config2)
        assert len(results2) == 1
        assert "APPLE and apple" in results2[0].context

    def test_search_with_file_extensions(self, temp_dir):
        """Test search with file extension filtering."""
        # Create files with different extensions
        txt_file = Path(temp_dir) / "file.txt"
        with open(txt_file, "w", encoding=ENCODING) as f:
            f.write("This is a text file with keyword")

        py_file = Path(temp_dir) / "file.py"
        with open(py_file, "w", encoding=ENCODING) as f:
            f.write("# This is a Python file with keyword")

        # Search only in .txt files
        config = SearchConfig(
            directory=temp_dir,
            keyword="keyword",
            case_sensitive=True,
            file_extensions=[".txt"],
        )

        results = search_keyword_in_files(config)
        assert len(results) == 1
        assert results[0].file_path == str(txt_file)

    def test_search_config_validation(self, temp_dir):
        """Test validation in SearchConfig."""
        # Test valid config
        config = SearchConfig(directory=temp_dir, keyword="test", case_sensitive=True)
        assert config.directory == temp_dir
        assert config.keyword == "test"
        assert config.case_sensitive is True

        # Test file extensions formatting
        config = SearchConfig(
            directory=temp_dir, keyword="test", file_extensions=["txt", "py"]
        )
        assert config.file_extensions == [".txt", ".py"]

        # To test conversion from string to list, appropriate preprocessing is needed
        extensions_str = "txt,py"
        extensions_list = extensions_str.split(",")
        config = SearchConfig(
            directory=temp_dir, keyword="test", file_extensions=extensions_list
        )
        assert config.file_extensions == [".txt", ".py"]

        # Test directory validation
        with pytest.raises(ValueError):
            SearchConfig(directory="non_existent_dir", keyword="test")

    @pytest.mark.parametrize("bad_ext", [123, {"py": 1}, ["txt", 123]])
    def test_search_config_file_extensions_type_error(self, temp_dir, bad_ext):
        """SearchConfigのfile_extensionsに不正な型を渡すとValueError"""
        with pytest.raises(ValueError):
            SearchConfig(directory=temp_dir, keyword="test", file_extensions=bad_ext)

    def test_search_with_multiple_files(self, temp_dir):
        """Test search across multiple files."""
        # Create multiple files with the keyword
        for i in range(3):
            file_path = Path(temp_dir) / f"file{i}.txt"
            with open(file_path, "w", encoding=ENCODING) as f:
                f.write(f"This is file {i} with the keyword")

        config = SearchConfig(
            directory=temp_dir, keyword="keyword", case_sensitive=True
        )

        results = search_keyword_in_files(config)
        assert len(results) == 3
        # Verify each file is found
        found_files = [result.file_path for result in results]
        for i in range(3):
            assert str(Path(temp_dir) / f"file{i}.txt") in found_files

    def test_get_validated_file_path_relative(self, temp_dir):
        """_get_validated_file_pathで相対パスを渡すとValueError"""
        from minerva.file_handler import _get_validated_file_path

        with pytest.raises(ValueError, match="Directory must be an absolute path"):
            _get_validated_file_path("relative/path", "file.txt")

    @pytest.mark.parametrize("bad_dir", [None, 123, 3.14, [], {}])
    def test_file_operation_request_invalid_directory_type(self, bad_dir):
        """directoryがstr型でない場合はValidationError（Pydantic v2仕様）"""
        from minerva.file_handler import FileWriteRequest

        with pytest.raises(
            pydantic.ValidationError, match="Input should be a valid string"
        ):
            FileWriteRequest(
                directory=bad_dir,
                filename="test.txt",
                content="dummy",
                overwrite=True,
            )
