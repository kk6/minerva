import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import pydantic

from minerva.file_handler import (
    FileWriteRequest,
    FileReadRequest,
    FileDeleteRequest,
    read_file,
    write_file,
    delete_file,
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


@pytest.fixture
def create_test_file(temp_dir):
    """Helper fixture for creating test files with specified content.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        function: Helper function that creates a file with specified name and content
    """

    def _create_file(filename, content):
        file_path = Path(temp_dir) / filename
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write(content)
        return file_path

    return _create_file


class TestFileHandler:
    """Test suite for file handler functions."""

    def test_write_file_success(self, temp_dir):
        """Test writing a file successfully.

        Arrange:
            - Create a file write request with test content
        Act:
            - Call write_file with the request
        Assert:
            - File is created at the expected path
            - File exists in the filesystem
            - File content matches the input
        """
        # ==================== Arrange ====================
        request = FileWriteRequest(
            directory=temp_dir,
            filename="test.txt",
            content="Hello, World!",
            overwrite=True,
        )

        # ==================== Act ====================
        file_path = write_file(request)

        # ==================== Assert ====================
        assert file_path == Path(temp_dir) / "test.txt"
        assert file_path.exists()
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_write_file_overwrite_false(self, temp_dir):
        """Test writing a file with overwrite set to False.

        Arrange:
            - Create an existing file with initial content
            - Prepare a request to write to the same file with overwrite=False
        Act & Assert:
            - Verify that FileExistsError is raised when attempting to overwrite
            - Verify that original file content remains unchanged
        """
        # ==================== Arrange ====================
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

        # ==================== Act & Assert ====================
        # Test that exception is raised when overwrite is False
        with pytest.raises(FileExistsError):
            write_file(request)

        # ==================== Additional Assert ====================
        # Check that the original content is still there
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_write_file_overwrite_true(self, temp_dir):
        """Test writing a file with overwrite set to True.

        Arrange:
            - Create an existing file with initial content
            - Prepare a request to write to the same file with overwrite=True
        Act:
            - Call write_file with the request
        Assert:
            - Verify that file content has been updated
        """
        # ==================== Arrange ====================
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

        # ==================== Act ====================
        # Write the file with overwrite set to True
        write_file(request)

        # ==================== Assert ====================
        # Check that the content has been updated
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "New Content"

    def test_write_file_invalid_directory(self):
        """Test writing a file with an invalid directory.

        Arrange:
            - Prepare a request with a relative directory path
        Act & Assert:
            - Verify that ValueError is raised with appropriate message
        """
        # ==================== Arrange ====================
        # Prepare request with invalid (relative) directory
        request = FileWriteRequest(
            directory="invalid_directory",
            filename="test.txt",
            content="Hello, World!",
            overwrite=True,
        )

        # ==================== Act & Assert ====================
        with pytest.raises(ValueError) as excinfo:
            write_file(request)
        assert str(excinfo.value) == "Directory must be an absolute path"

    def test_write_file_invalid_filename(self, temp_dir):
        """Test writing a file with an invalid filename.

        Arrange:
            - Attempt to create a request with a filename containing forbidden characters
        Act & Assert:
            - Verify that ValueError is raised with appropriate message about forbidden characters
        """
        # ==================== Arrange & Act & Assert ====================
        # The validation happens during object creation in this case
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

    def test_write_file_creates_directory(self, temp_dir):
        """Test write_file creates directory structure if it doesn't exist.

        Arrange:
            - Create a path to a non-existent subdirectory
            - Prepare a file write request for that subdirectory
        Act:
            - Call write_file with the request
        Assert:
            - Verify directory structure was created
            - Verify file exists
            - Verify file content matches expected
        """
        # ==================== Arrange ====================
        # Create path to non-existent subdirectory
        sub_dir = Path(temp_dir) / "non_existent_dir" / "sub_dir"

        request = FileWriteRequest(
            directory=str(sub_dir),
            filename="test.txt",
            content="Test content",
            overwrite=True,
        )

        # ==================== Act ====================
        file_path = write_file(request)

        # ==================== Assert ====================
        assert file_path.exists()
        assert file_path.parent.exists()  # Directory should be created

        # Verify content was written correctly
        with open(file_path, "r", encoding=ENCODING) as f:
            content = f.read()
            assert content == "Test content"

    @pytest.mark.parametrize("filename", ["test_unicode_文字.txt", "emoji_😀.txt"])
    def test_write_file_with_international_characters(self, temp_dir, filename):
        """Test writing files with international characters in filename.

        Arrange:
            - Prepare a file write request with a filename containing non-ASCII characters
        Act:
            - Write the file
            - Read the file with the same filename
        Assert:
            - Verify file exists
            - Verify content matches what was written
        """
        # ==================== Arrange ====================
        content = "International character test"
        request = FileWriteRequest(
            directory=temp_dir,
            filename=filename,
            content=content,
            overwrite=True,
        )

        # ==================== Act ====================
        file_path = write_file(request)

        # ==================== Assert (File Creation) ====================
        assert file_path.exists()

        # ==================== Act (Read Back) ====================
        read_request = FileReadRequest(
            directory=temp_dir,
            filename=filename,
        )
        read_content = read_file(read_request)

        # ==================== Assert (Content) ====================
        assert read_content == content

    def test_read_file_success(self, temp_dir):
        """Test reading a file successfully.

        Arrange:
            - Create a file with known content
            - Prepare a read request for the file
        Act:
            - Call read_file with the request
        Assert:
            - Verify content matches what was written
        """
        # ==================== Arrange ====================
        file_path = Path(temp_dir) / "test.txt"
        # Create a file to read
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("Hello, World!")

        request = FileReadRequest(
            directory=temp_dir,
            filename="test.txt",
        )

        # ==================== Act ====================
        content = read_file(request)

        # ==================== Assert ====================
        assert content == "Hello, World!"

    def test_read_file_not_found(self, temp_dir):
        """Test reading a file that does not exist.

        Arrange:
            - Prepare a read request for a non-existent file
        Act & Assert:
            - Verify FileNotFoundError is raised when attempting to read
        """
        # ==================== Arrange ====================
        request = FileReadRequest(
            directory=temp_dir,
            filename="non_existent.txt",
        )

        # ==================== Act & Assert ====================
        with pytest.raises(FileNotFoundError):
            read_file(request)

    def test_read_file_invalid_directory(self):
        """Test reading a file with an invalid directory.

        Arrange:
            - Prepare a read request with a relative (invalid) directory path
        Act & Assert:
            - Verify ValueError is raised with appropriate message
        """
        # ==================== Arrange ====================
        request = FileReadRequest(
            directory="invalid_directory",
            filename="test.txt",
        )

        # ==================== Act & Assert ====================
        with pytest.raises(ValueError) as excinfo:
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

        Arrange:
            - Setup test cases via parameterization for different invalid filename patterns
        Act & Assert:
            - Verify ValueError is raised with the appropriate message for each case
        """
        # ==================== Arrange & Act & Assert ====================
        # The validation happens during object creation
        with pytest.raises(ValueError) as excinfo:
            FileReadRequest(
                directory=temp_dir,
                filename=filename,
            )
        assert expected_message in str(excinfo.value)

    def test_read_file_invalid_encoding(self, temp_dir):
        """Test reading a file with invalid encoding.

        Arrange:
            - Create a binary file with invalid UTF-8 encoding
            - Prepare a read request for the file
        Act & Assert:
            - Verify UnicodeDecodeError is raised when attempting to read
        """
        # ==================== Arrange ====================
        file_path = Path(temp_dir) / "test.txt"
        # Create a file with invalid encoding
        with open(file_path, "wb") as f:
            f.write(b"\x80\x81\x82")

        request = FileReadRequest(
            directory=temp_dir,
            filename="test.txt",
        )

        # ==================== Act & Assert ====================
        with pytest.raises(UnicodeDecodeError):
            read_file(request)

    def test_is_binary_file(self, temp_dir):
        """Test detecting binary files.

        Arrange:
            - Create a text file with normal text content
            - Create a binary file with binary content
        Act & Assert:
            - Verify is_binary_file correctly identifies text file as non-binary
            - Verify is_binary_file correctly identifies binary file as binary
        """
        # ==================== Arrange ====================
        # Create a text file
        text_file_path = Path(temp_dir) / "text.txt"
        with open(text_file_path, "w", encoding=ENCODING) as f:
            f.write("Hello, World!")

        # Create a binary file
        binary_file_path = Path(temp_dir) / "binary.bin"
        with open(binary_file_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # ==================== Act & Assert ====================
        assert not is_binary_file(text_file_path)
        assert is_binary_file(binary_file_path)

    def test_is_binary_file_permission_error(self, mocker, temp_dir):
        """Test handling permission errors when checking if a file is binary.

        Arrange:
            - Create a dummy file
            - Mock open function to raise PermissionError and IOError
        Act & Assert:
            - Verify is_binary_file gracefully handles PermissionError
            - Verify is_binary_file gracefully handles IOError
        """
        # ==================== Arrange ====================
        from minerva.file_handler import is_binary_file

        dummy_path = Path(temp_dir) / "dummy.txt"
        dummy_path.touch()

        # ==================== Act & Assert (PermissionError) ====================
        mocker.patch("builtins.open", side_effect=PermissionError)
        assert is_binary_file(dummy_path) is False

        # ==================== Act & Assert (IOError) ====================
        mocker.patch("builtins.open", side_effect=IOError)
        assert is_binary_file(dummy_path) is False

    def test_search_keyword_basic(self, temp_dir):
        """Test basic keyword search functionality.

        Arrange:
            - Create test files, one with the keyword and one without
            - Set up search configuration with the target keyword
        Act:
            - Execute the search operation
        Assert:
            - Verify correct number of results (only one file should match)
            - Verify the correct file was found
            - Verify line number and context are correct
        """
        # ==================== Arrange ====================
        # Create test files
        file1 = Path(temp_dir) / "file1.txt"
        with open(file1, "w", encoding=ENCODING) as f:
            f.write("This is a test file with a keyword: apple")

        file2 = Path(temp_dir) / "file2.txt"
        with open(file2, "w", encoding=ENCODING) as f:
            f.write("This file doesn't have the keyword")

        config = SearchConfig(directory=temp_dir, keyword="apple", case_sensitive=True)

        # ==================== Act ====================
        results = search_keyword_in_files(config)

        # ==================== Assert ====================
        assert len(results) == 1
        assert results[0].file_path == str(file1)
        assert results[0].line_number == 1
        assert results[0].context is not None
        assert "keyword: apple" in results[0].context

    def test_search_keyword_case_sensitivity(self, temp_dir):
        """Test case sensitivity in keyword search.

        Arrange:
            - Create a test file with both uppercase and lowercase versions of the keyword
        Act:
            - Execute a case-sensitive search for the lowercase keyword
            - Execute a case-insensitive search for the same keyword
        Assert:
            - Verify case-sensitive search only finds exact match
            - Verify case-insensitive search finds both variations
        """
        # ==================== Arrange ====================
        # Create test file
        file_path = Path(temp_dir) / "case.txt"
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("This file has APPLE and apple")

        # ==================== Act & Assert (Case-sensitive) ====================
        # Case sensitive search should find only lowercase
        config1 = SearchConfig(directory=temp_dir, keyword="apple", case_sensitive=True)
        results1 = search_keyword_in_files(config1)

        # ==================== Assert (Case-sensitive) ====================
        assert len(results1) == 1
        assert results1[0].context is not None
        assert "apple" in results1[0].context

        # ==================== Act (Case-insensitive) ====================
        # Case insensitive search should find both
        config2 = SearchConfig(
            directory=temp_dir, keyword="apple", case_sensitive=False
        )
        results2 = search_keyword_in_files(config2)

        # ==================== Assert (Case-insensitive) ====================
        assert len(results2) == 1
        assert results2[0].context is not None
        assert "APPLE and apple" in results2[0].context

    def test_search_with_file_extensions(self, temp_dir):
        """Test search with file extension filtering.

        Arrange:
            - Create files with different extensions but the same keyword
            - Set up search configuration to filter by file extension
        Act:
            - Execute the search operation
        Assert:
            - Verify only files with the specified extension are found
        """
        # ==================== Arrange ====================
        # Create files with different extensions
        txt_file = Path(temp_dir) / "file.txt"
        with open(txt_file, "w", encoding=ENCODING) as f:
            f.write("This is a text file with keyword")

        py_file = Path(temp_dir) / "file.py"
        with open(py_file, "w", encoding=ENCODING) as f:
            f.write("# This is a Python file with keyword")

        # Configure search for only .txt files
        config = SearchConfig(
            directory=temp_dir,
            keyword="keyword",
            case_sensitive=True,
            file_extensions=[".txt"],
        )

        # ==================== Act ====================
        results = search_keyword_in_files(config)

        # ==================== Assert ====================
        assert len(results) == 1
        assert results[0].file_path == str(txt_file)

    def test_search_config_validation(self, temp_dir):
        """Test validation in SearchConfig.

        Arrange & Act & Assert:
            - Test creating valid SearchConfig with basic parameters
            - Test file extension normalization (.txt from txt)
            - Test conversion from comma-separated string to list
            - Test validation of non-existent directory
        """
        # ==================== Arrange & Act & Assert (Valid config) ====================
        # Test valid config
        config = SearchConfig(directory=temp_dir, keyword="test", case_sensitive=True)
        assert config.directory == temp_dir
        assert config.keyword == "test"
        assert config.case_sensitive is True

        # ==================== Arrange & Act & Assert (Extension formatting) ====================
        # Test file extensions formatting
        config = SearchConfig(
            directory=temp_dir, keyword="test", file_extensions=["txt", "py"]
        )
        assert config.file_extensions == [".txt", ".py"]

        # ==================== Arrange & Act & Assert (String to list conversion) ====================
        # To test conversion from string to list, appropriate preprocessing is needed
        extensions_str = "txt,py"
        extensions_list = extensions_str.split(",")
        config = SearchConfig(
            directory=temp_dir,
            keyword="test",
            file_extensions=[str(ext) for ext in extensions_list],
        )
        assert config.file_extensions == [".txt", ".py"]

        # ==================== Arrange & Act & Assert (Directory validation) ====================
        # Test directory validation
        with pytest.raises(ValueError):
            SearchConfig(directory="non_existent_dir", keyword="test")

    @pytest.mark.parametrize("bad_ext", [123, {"py": 1}, ["txt", 123]])
    def test_search_config_file_extensions_type_error(self, temp_dir, bad_ext):
        """Test invalid file extensions type.

        Arrange:
            - Set up test cases for invalid file extension types via parameterization
        Act & Assert:
            - Verify ValueError is raised when invalid extension types are provided
        """
        # ==================== Arrange & Act & Assert ====================
        with pytest.raises(ValueError):
            SearchConfig(directory=temp_dir, keyword="test", file_extensions=bad_ext)

    def test_search_with_multiple_files(self, temp_dir):
        """Test search across multiple files.

        Arrange:
            - Create multiple files all containing the same keyword
            - Set up search configuration
        Act:
            - Execute the search operation
        Assert:
            - Verify all files are found in the results
            - Verify the correct number of results are returned
        """
        # ==================== Arrange ====================
        # Create multiple files with the keyword
        for i in range(3):
            file_path = Path(temp_dir) / f"file{i}.txt"
            with open(file_path, "w", encoding=ENCODING) as f:
                f.write(f"This is file {i} with the keyword")

        config = SearchConfig(
            directory=temp_dir, keyword="keyword", case_sensitive=True
        )

        # ==================== Act ====================
        results = search_keyword_in_files(config)

        # ==================== Assert ====================
        assert len(results) == 3
        # Verify each file is found
        found_files = [result.file_path for result in results]
        for i in range(3):
            assert str(Path(temp_dir) / f"file{i}.txt") in found_files

    def test_get_validated_file_path_relative(self, temp_dir):
        """Test _get_validated_file_path with a relative path.

        Arrange:
            - Prepare a relative path for validation
        Act & Assert:
            - Verify ValueError is raised when a relative path is provided
        """
        # ==================== Arrange ====================
        from minerva.file_handler import _get_validated_file_path

        # ==================== Act & Assert ====================
        with pytest.raises(ValueError, match="Directory must be an absolute path"):
            _get_validated_file_path("relative/path", "file.txt")

    @pytest.mark.parametrize("bad_dir", [None, 123, 3.14, [], {}])
    def test_file_operation_request_invalid_directory_type(self, bad_dir):
        """Test invalid directory type for file operations.

        Arrange:
            - Set up test cases for invalid directory types via parameterization
        Act & Assert:
            - Verify ValidationError is raised with appropriate message
        """
        # ==================== Arrange & Act & Assert ====================
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

    def test_large_file_search(self, temp_dir, create_test_file):
        """Test search in a large file.

        This test verifies that the search functionality works correctly
        with large files (over 1MB in size).

        Arrange:
            - Create a large file with repeated content and a keyword in the middle
            - Set up search configuration
        Act:
            - Execute the search operation
        Assert:
            - Verify the keyword is found in the large file
        """
        # ==================== Arrange ====================
        # Create a large file with repeated content and a keyword in the middle
        large_content = "A" * 500000 + "KEYWORD_TO_FIND" + "B" * 500000
        large_file = create_test_file("large_file.txt", large_content)

        config = SearchConfig(directory=temp_dir, keyword="KEYWORD_TO_FIND")

        # ==================== Act ====================
        results = search_keyword_in_files(config)

        # ==================== Assert ====================
        assert len(results) == 1
        assert results[0].file_path == str(large_file)
        assert results[0].context is not None
        assert "KEYWORD_TO_FIND" in results[0].context

    def test_search_keyword_exception_handling(self, temp_dir, mocker):
        """Test exception handling in search_keyword_in_files.

        This test verifies that exceptions during the search process are
        properly propagated and handled.

        Arrange:
            - Create a test file
            - Mock os.walk to raise an exception
        Act & Assert:
            - Verify the exception is propagated
        """
        # ==================== Arrange ====================
        # Create a test file
        file_path = Path(temp_dir) / "test.txt"
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("Test content")

        # Mock os.walk to raise an exception
        mocker.patch("os.walk", side_effect=PermissionError("Access denied"))

        config = SearchConfig(directory=temp_dir, keyword="test")

        # ==================== Act & Assert ====================
        # The exception should be propagated
        with pytest.raises(Exception):
            search_keyword_in_files(config)

    def test_file_operation_request_base_class(self):
        """Test the base FileOperationRequest class.

        This test verifies that the base class validation works correctly
        and is properly inherited by subclasses.

        Arrange:
            - Prepare test cases for missing required fields
            - Prepare a valid instance
        Act & Assert:
            - Verify ValidationError is raised for missing fields
            - Verify valid instance is created successfully
        """
        # ==================== Arrange & Act & Assert ====================
        from minerva.file_handler import FileOperationRequest

        # Test that directories must be provided (using None instead of empty string)
        with pytest.raises(pydantic.ValidationError):
            FileOperationRequest(directory=None, filename="test.txt")  # type: ignore

        # Test that filenames must be provided
        with pytest.raises(pydantic.ValidationError):
            FileOperationRequest(directory="/tmp", filename=None)  # type: ignore

        # Test valid instance
        request = FileOperationRequest(directory="/tmp", filename="test.txt")
        assert request.directory == "/tmp"
        assert request.filename == "test.txt"

    def test_search_result_model(self):
        """Test the SearchResult model.

        This test verifies that the SearchResult model can be properly
        instantiated and validated.

        Arrange:
            - Prepare test cases for minimal and full instances
            - Prepare test cases for invalid file_path type
        Act & Assert:
            - Verify valid instances are created successfully
            - Verify ValidationError is raised for invalid file_path type
        """
        # ==================== Arrange & Act & Assert ====================
        from minerva.file_handler import SearchResult

        # Test minimal valid instance
        result = SearchResult(file_path="/path/to/file.txt")
        assert result.file_path == "/path/to/file.txt"
        assert result.line_number is None
        assert result.context is None

        # Test full instance
        full_result = SearchResult(
            file_path="/path/to/file.txt", line_number=42, context="This is the context"
        )
        assert full_result.file_path == "/path/to/file.txt"
        assert full_result.line_number == 42
        assert full_result.context == "This is the context"

        # Test invalid file_path type
        with pytest.raises(pydantic.ValidationError):
            SearchResult(file_path=123)  # type: ignore

    def test_search_with_mocked_os_walk(self, temp_dir, mocker, create_test_file):
        """Test search with mocked os.walk functionality.

        This test verifies that search works correctly by mocking the os.walk function
        to simulate a more complex directory structure.

        Arrange:
            - Create a test file that doesn't contain the keyword
            - Mock os.walk to return a more complex directory structure
            - Mock open for virtual files to simulate keyword presence
        Act:
            - Execute the search operation
        Assert:
            - Verify keywords are found only in the mock files
        """
        # ==================== Arrange ====================
        # Create a test file that doesn't contain the keyword
        test_file = create_test_file("test.txt", "This file contains the test phrase")

        # Mock os.walk to return a more complex directory structure
        mock_walk_data = [
            (temp_dir, ["subdir1", "subdir2"], ["test.txt"]),
            (str(Path(temp_dir) / "subdir1"), [], ["file1.txt", "file2.py"]),
            (str(Path(temp_dir) / "subdir2"), [], ["file3.txt"]),
        ]
        mocker.patch("os.walk", return_value=mock_walk_data)

        # Also mock open for the virtual files to make them appear to contain the keyword
        # but only mock for specific paths that don't exist in reality
        real_open = open

        def mock_open(file, *args, **kwargs):
            file_path = str(file)
            if file_path == str(test_file):
                return real_open(file, *args, **kwargs)
            elif "subdir1/file1.txt" in file_path or "subdir1\\file1.txt" in file_path:
                # Handle binary mode read for is_binary_file checks
                if "rb" in args or ("mode" in kwargs and "rb" in kwargs["mode"]):
                    content = b"This contains keyword too"
                    file_obj = mocker.mock_open(read_data=content)()
                else:
                    file_obj = mocker.mock_open(read_data="This contains keyword too")()
                file_obj.name = file_path
                return file_obj
            elif "file2.py" in file_path:
                # This file should NOT contain the keyword
                if "rb" in args or ("mode" in kwargs and "rb" in kwargs["mode"]):
                    content = b"No matching content here"
                    file_obj = mocker.mock_open(read_data=content)()
                else:
                    file_obj = mocker.mock_open(read_data="No matching content here")()
                file_obj.name = file_path
                return file_obj
            elif "subdir2/file3.txt" in file_path or "subdir2\\file3.txt" in file_path:
                # Handle binary mode read for is_binary_file checks
                if "rb" in args or ("mode" in kwargs and "rb" in kwargs["mode"]):
                    content = b"Another keyword instance"
                    file_obj = mocker.mock_open(read_data=content)()
                else:
                    file_obj = mocker.mock_open(read_data="Another keyword instance")()
                file_obj.name = file_path
                return file_obj
            else:
                # Handle binary mode read for is_binary_file checks
                if "rb" in args or ("mode" in kwargs and "rb" in kwargs["mode"]):
                    content = b"No matches here"
                    file_obj = mocker.mock_open(read_data=content)()
                else:
                    file_obj = mocker.mock_open(read_data="No matches here")()
                file_obj.name = file_path
                return file_obj

        mocker.patch("builtins.open", side_effect=mock_open)

        config = SearchConfig(
            directory=temp_dir,
            keyword="keyword",
            case_sensitive=True,
        )

        # ==================== Act ====================
        results = search_keyword_in_files(config)

        # ==================== Assert ====================
        # Should find keywords only in the two mock files (not the real file)
        assert len(results) == 2

        # Check that paths from our mock structure are included
        result_paths = [result.file_path for result in results]
        assert any("file1.txt" in path for path in result_paths)
        assert any("file3.txt" in path for path in result_paths)
        # Real file and file2.py shouldn't be in results
        assert not any(str(test_file) == path for path in result_paths)
        assert not any("file2.py" in path for path in result_paths)

    def test_delete_file_success(self, temp_dir):
        """Test deleting a file successfully.

        Arrange:
            - Create a file to be deleted
            - Prepare a delete request
        Act:
            - Call delete_file with the request
        Assert:
            - Verify the function returns the correct path
            - Verify the file no longer exists in the filesystem
        """
        # ==================== Arrange ====================
        # Create the file to be deleted
        file_path = Path(temp_dir) / "to_delete.txt"
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write("This file will be deleted")

        # Verify the file exists before deletion
        assert file_path.exists()

        # Create a request to delete the file
        request = FileDeleteRequest(
            directory=temp_dir,
            filename="to_delete.txt",
        )

        # ==================== Act ====================
        result_path = delete_file(request)

        # ==================== Assert ====================
        assert result_path == file_path
        assert not file_path.exists()

    def test_delete_file_not_found(self, temp_dir):
        """Test deleting a file that does not exist.

        Arrange:
            - Prepare a delete request for a non-existent file
        Act & Assert:
            - Verify FileNotFoundError is raised when attempting to delete
        """
        # ==================== Arrange ====================
        # Create a request for a non-existent file
        request = FileDeleteRequest(
            directory=temp_dir,
            filename="non_existent.txt",
        )

        # ==================== Act & Assert ====================
        with pytest.raises(FileNotFoundError):
            delete_file(request)

    def test_delete_file_invalid_directory(self):
        """Test deleting a file with an invalid directory.

        Arrange:
            - Prepare a delete request with a relative (invalid) directory path
        Act & Assert:
            - Verify ValueError is raised with appropriate message
        """
        # ==================== Arrange ====================
        # Create a request with an invalid directory
        request = FileDeleteRequest(
            directory="invalid_directory",
            filename="test.txt",
        )

        # ==================== Act & Assert ====================
        with pytest.raises(ValueError) as excinfo:
            delete_file(request)
        assert str(excinfo.value) == "Directory must be an absolute path"

    def test_delete_file_and_check_existence(self, temp_dir):
        """Test deleting a file and verifying it's truly gone.

        Arrange:
            - Create multiple files
            - Prepare a delete request for one of them
        Act:
            - Delete one file
        Assert:
            - Verify the specific file is gone
            - Verify other files are untouched
        """
        # ==================== Arrange ====================
        # Create multiple files
        file1 = Path(temp_dir) / "file1.txt"
        file2 = Path(temp_dir) / "file2.txt"
        file3 = Path(temp_dir) / "file3.txt"

        for file in [file1, file2, file3]:
            with open(file, "w", encoding=ENCODING) as f:
                f.write(f"Content for {file.name}")

        # Verify all files exist
        assert file1.exists() and file2.exists() and file3.exists()

        # Create a request to delete one specific file
        request = FileDeleteRequest(
            directory=temp_dir,
            filename="file2.txt",
        )

        # ==================== Act ====================
        delete_file(request)

        # ==================== Assert ====================
        # File2 should be gone, but file1 and file3 should still exist
        assert file1.exists()
        assert not file2.exists()
        assert file3.exists()
