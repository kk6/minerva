from unittest import mock

import pytest
import frontmatter

from minerva import tools


class TestWriteNote:
    @pytest.fixture
    def write_note_request(self):
        return tools.WriteNoteRequest(
            text="Sample text",
            filename="sample_note",
            is_overwrite=False,
            author=None,
            default_path="",
        )

    @pytest.fixture
    def mock_write_setup(self, tmp_path):
        """Fixture providing common mock setup for write tests."""
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}

    @pytest.mark.parametrize(
        "is_overwrite,old_content,should_raise,expected_exception",
        [
            (False, None, False, None),  # Create new file case
            (True, "old content", False, None),  # Overwrite existing file case
            (
                False,
                "old content",
                True,
                FileExistsError,
            ),  # No overwrite, file exists case
        ],
        ids=["create-new", "overwrite", "no-overwrite"],
    )
    def test_write_note_file_cases(
        self,
        mock_write_setup,
        write_note_request,
        is_overwrite,
        old_content,
        should_raise,
        expected_exception,
    ):
        """Test writing a note for create, overwrite, and no-overwrite cases.

        This test uses AAA (Arrange-Act-Assert) pattern to verify write_note behavior
        in three scenarios: creating a new file, overwriting an existing file, and
        attempting to write to an existing file without overwrite permission.

        Arrange:
            - Setup mock for write_file function
            - Configure test case with overwrite flag and existing file content
        Act:
            - Call write_note with the configured request
        Assert:
            - Verify expected exception is raised when should_raise is True
            - Verify file is correctly written when should_raise is False
            - Confirm write_file was called with expected parameters
        """
        # ==================== Arrange ====================
        # Extract mocks and paths from fixture
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        test_file = tmp_path / f"{write_note_request.filename}.md"

        # Create file with old content if test requires it
        if old_content is not None:
            test_file.write_text(old_content)

        # Configure request with overwrite flag from test case
        write_note_request.is_overwrite = is_overwrite

        # Configure mock based on test case
        if should_raise:
            # Setup mock to raise exception for negative test case
            mock_write_file.side_effect = FileExistsError(
                "File exists and overwrite is False"
            )

            # ==================== Act & Assert (exception case) ====================
            # For exception cases, we need to use pytest.raises context manager
            # which combines the Act and Assert steps
            with pytest.raises(
                FileExistsError, match="File exists and overwrite is False"
            ):
                # Act - Execute the function being tested
                tools.write_note(**write_note_request.model_dump())

            # ==================== Additional Assertions ====================
            # Verify the mock was called correctly
            mock_write_file.assert_called_once()
        else:
            # ==================== Additional Arrange (success case) ====================
            # Setup return value for successful case
            mock_write_file.return_value = test_file

            # ==================== Act ====================
            # Execute the function being tested
            result = tools.write_note(**write_note_request.model_dump())

            # ==================== Assert ====================
            # Verify the result matches expected output
            assert result == test_file
            # Verify the mock was called exactly once
            mock_write_file.assert_called_once()

    def test_write_note_creates_file_params(self, mock_write_setup, write_note_request):
        """Verify that correct parameters are passed to write_file."""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        expected_path = tmp_path / f"{write_note_request.filename}.md"
        mock_write_file.return_value = expected_path
        result = tools.write_note(**write_note_request.model_dump())
        assert result == expected_path
        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == write_note_request.filename
        # Content now includes frontmatter
        assert "---" in called_request.content
        assert "author:" in called_request.content
        assert "Sample text" in called_request.content
        assert called_request.overwrite == write_note_request.is_overwrite

    def test_write_note_raises_exception(self, mock_write_setup, write_note_request):
        """Verify that exceptions from write_file are propagated."""
        mock_write_file = mock_write_setup["mock_write_file"]
        mock_write_file.side_effect = Exception("File write error")
        with pytest.raises(Exception, match="File write error"):
            tools.write_note(**write_note_request.model_dump())
        mock_write_file.assert_called_once()

    @pytest.mark.parametrize(
        "filename,expected_message,expected_exception",
        [
            ("invalid|filename", "forbidden characters", "pydantic.ValidationError"),
            ("", "cannot be empty", "ValueError"),
        ],
    )
    def test_write_note_invalid_filename(
        self,
        mock_write_setup,
        write_note_request,
        filename,
        expected_message,
        expected_exception,
    ):
        """If the filename is invalid, ValidationError or ValueError is raised and write_file is not called."""
        import pydantic

        mock_write_file = mock_write_setup["mock_write_file"]
        write_note_request.filename = filename
        if expected_exception == "pydantic.ValidationError":
            with pytest.raises(pydantic.ValidationError, match=expected_message):
                tools.write_note(**write_note_request.model_dump())
        else:
            with pytest.raises(ValueError, match=expected_message):
                tools.write_note(**write_note_request.model_dump())
        mock_write_file.assert_not_called()

    def test_write_note_with_subdirectory_path(
        self, mock_write_setup, write_note_request
    ):
        """Test to verify that paths with subdirectories are processed correctly"""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        # Update filename to include subdirectory
        write_note_request.filename = "subdir/note_in_subdir"
        expected_dir_path = tmp_path / "subdir"
        expected_file_path = expected_dir_path / "note_in_subdir.md"

        mock_write_file.return_value = expected_file_path

        result = tools.write_note(**write_note_request.model_dump())
        assert result == expected_file_path

        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]

        # Verify that subdirectory is properly separated and directory path and filename are set correctly
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "note_in_subdir.md"

        # Instead of comparing raw content, extract content from frontmatter
        post = frontmatter.loads(called_request.content)
        assert post.content == write_note_request.text

    def test_write_note_with_author(self, mock_write_setup):
        """Test to verify that author is properly included in frontmatter"""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        expected_path = tmp_path / "author_note.md"
        mock_write_file.return_value = expected_path

        result = tools.write_note(
            text="Content with author",
            filename="author_note",
            is_overwrite=False,
            author="Test Author",
        )
        assert result == expected_path

        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]

        # Parse frontmatter and verify author
        post = frontmatter.loads(called_request.content)
        assert post.metadata["author"] == "Test Author"
        assert post.content == "Content with author"

    def test_write_note_with_existing_frontmatter(self, mock_write_setup):
        """Test to verify that existing frontmatter is preserved"""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        # Content with existing frontmatter
        frontmatter_content = """---
title: Existing Title
tags: [test, frontmatter]
---
Content with existing frontmatter"""

        expected_path = tmp_path / "frontmatter_note.md"
        mock_write_file.return_value = expected_path

        result = tools.write_note(
            text=frontmatter_content,
            filename="frontmatter_note",
            is_overwrite=False,
            author="New Author",
        )
        assert result == expected_path

        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]

        # Parse frontmatter and verify all properties
        post = frontmatter.loads(called_request.content)
        assert post.metadata["title"] == "Existing Title"
        assert post.metadata["tags"] == ["test", "frontmatter"]
        assert post.metadata["author"] == "New Author"
        assert post.content == "Content with existing frontmatter"

    def test_write_note_with_default_path(self, mock_write_setup):
        """Test to verify that default_path is used when no subdirectory is specified"""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        expected_dir_path = tmp_path / "default_dir"
        expected_file_path = expected_dir_path / "default_path_note.md"
        mock_write_file.return_value = expected_file_path

        result = tools.write_note(
            text="Content with default path",
            filename="default_path_note",
            is_overwrite=False,
            default_path="default_dir",
        )
        assert result == expected_file_path

        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]

        # Verify directory path includes default_path
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "default_path_note.md"


class TestReadNote:
    @pytest.fixture
    def read_note_request(self, tmp_path):
        return tools.ReadNoteRequest(
            filepath=str(tmp_path / "note.md"),
        )

    @pytest.fixture
    def mock_read_setup(self):
        """Fixture providing common mock setup for read tests."""
        with mock.patch("minerva.tools.read_file") as mock_read_file:
            yield {"mock_read_file": mock_read_file}

    def test_read_note_returns_content(self, mock_read_setup, read_note_request):
        """Test reading a note returns the content.

        Expects:
            - read_file is called with correct parameters
            - The function returns the expected content
            - The file path is properly extracted from the request
        """
        mock_read_file = mock_read_setup["mock_read_file"]
        expected_content = "sample content"

        mock_read_file.return_value = expected_content

        result = tools.read_note(read_note_request.filepath)

        assert result == expected_content
        mock_read_file.assert_called_once()

        # Enhanced verification: Check that read_file is called with the correct parameters
        import os

        directory, filename = os.path.split(read_note_request.filepath)
        called_request = mock_read_file.call_args[0][0]
        assert called_request.directory == directory
        assert called_request.filename == filename

    def test_read_note_raises_exception(self, mock_read_setup, read_note_request):
        """Test reading a note raises an exception.

        Expects:
            - When read_file raises an exception, it's propagated to the caller
            - The read_file function is still called once
        """
        mock_read_file = mock_read_setup["mock_read_file"]

        mock_read_file.side_effect = Exception("File read error")

        with pytest.raises(Exception, match="File read error"):
            tools.read_note(read_note_request.filepath)

        mock_read_file.assert_called_once()


class TestSearchNotes:
    @pytest.fixture
    def search_note_request(self):
        return tools.SearchNoteRequest(
            query="keyword",
            case_sensitive=False,
        )

    @pytest.fixture
    def mock_search_setup(self, tmp_path):
        """Fixture providing common mock setup for search tests."""
        with (
            mock.patch("minerva.tools.search_keyword_in_files") as mock_search,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            yield {"mock_search": mock_search, "tmp_path": tmp_path}

    def test_search_notes_returns_results(self, mock_search_setup, search_note_request):
        """Test searching notes returns results.

        Expects:
            - search_keyword_in_files is called with correct configuration
            - The function returns the search results unmodified
            - The search directory is set to VAULT_PATH
        """
        mock_search = mock_search_setup["mock_search"]
        tmp_path = mock_search_setup["tmp_path"]
        fake_result = [mock.Mock()]

        mock_search.return_value = fake_result

        result = tools.search_notes(
            query=search_note_request.query,
            case_sensitive=search_note_request.case_sensitive,
        )

        assert result == fake_result
        mock_search.assert_called_once()

        # Enhanced verification: Check that search_keyword_in_files is called with the correct parameters
        search_config = mock_search.call_args[0][0]
        assert search_config.directory == str(tmp_path)
        assert search_config.keyword == search_note_request.query
        assert search_config.file_extensions == [".md"]
        assert search_config.case_sensitive == search_note_request.case_sensitive

    def test_search_notes_empty_query(self, search_note_request):
        """Test searching notes with an empty query raises an exception.

        Expects:
            - When an empty query is provided, a ValueError is raised with specific message
            - The search function is never called with empty queries
        """
        search_note_request.query = ""

        with pytest.raises(ValueError, match="Query cannot be empty"):
            tools.search_notes(
                query=search_note_request.query,
                case_sensitive=search_note_request.case_sensitive,
            )

    def test_search_notes_raises_exception(
        self, mock_search_setup, search_note_request
    ):
        """Test searching notes raises an exception.

        Expects:
            - When search_keyword_in_files raises an exception, it's propagated to the caller
            - The search_keyword_in_files function is still called once
        """
        mock_search = mock_search_setup["mock_search"]

        mock_search.side_effect = Exception("Search error")

        with pytest.raises(Exception, match="Search error"):
            tools.search_notes(
                query=search_note_request.query,
                case_sensitive=search_note_request.case_sensitive,
            )

        mock_search.assert_called_once()

    @pytest.mark.parametrize(
        "case_sensitive,expected_config",
        [
            (True, True),
            (False, False),
        ],
        ids=["case-sensitive", "case-insensitive"],
    )
    def test_search_notes_case_sensitivity(
        self, mock_search_setup, search_note_request, case_sensitive, expected_config
    ):
        """Test searching notes with different case sensitivity settings.

        Expects:
            - search_keyword_in_files is called with the correct case_sensitive setting
            - The search configuration properly reflects the case sensitivity setting
        """
        mock_search = mock_search_setup["mock_search"]
        fake_result = [mock.Mock()]

        search_note_request.case_sensitive = case_sensitive
        mock_search.return_value = fake_result

        result = tools.search_notes(
            query=search_note_request.query,
            case_sensitive=search_note_request.case_sensitive,
        )

        assert result == fake_result
        search_config = mock_search.call_args[0][0]
        assert search_config.case_sensitive == expected_config


class TestIntegrationTests:
    """Integration tests that test the actual file operations."""

    @pytest.fixture
    def setup_vault(self, tmp_path):
        """Set up a temporary vault directory."""
        with mock.patch("minerva.tools.VAULT_PATH", tmp_path):
            # Create some test files in the vault
            (tmp_path / "note1.md").write_text("This is note 1 with keyword apple")
            (tmp_path / "note2.md").write_text("This is note 2 with keyword banana")
            (tmp_path / "note3.md").write_text("This is note 3 with keyword APPLE")
            yield tmp_path

    def test_integration_write_and_read_note(self, setup_vault):
        """Test writing and then reading a note.

        Arrange:
            - Create a write note request with test content
        Act:
            - Write a note and get the file path
            - Read the note from the same path
        Assert:
            - File exists on disk
            - Content read from the file matches what was written (after parsing frontmatter)
        """
        # Arrange
        test_content = "This is a test note"

        # Act - Part 1: Writing
        file_path = tools.write_note(
            text=test_content, filename="integration_test", is_overwrite=False
        )

        # Assert - Part 1: File was created
        assert file_path.exists()

        # Act - Part 2: Reading
        content = tools.read_note(str(file_path))

        # Assert - Part 2: Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_search_notes(self, setup_vault):
        """Test searching notes in the vault."""
        # Search case sensitive
        results1 = tools.search_notes(query="apple", case_sensitive=True)
        assert len(results1) == 1
        assert "note1.md" in results1[0].file_path

        # Search case insensitive
        results2 = tools.search_notes(query="apple", case_sensitive=False)
        assert len(results2) == 2

        # Verify both files are found (note1 and note3)
        found_files = [result.file_path for result in results2]
        assert any("note1.md" in path for path in found_files)
        assert any("note3.md" in path for path in found_files)

    def test_integration_write_with_overwrite(self, setup_vault):
        """Test overwriting an existing note."""

        # Create initial note
        initial_content = "Initial content"
        filename = "overwrite_test"

        file_path = tools.write_note(
            text=initial_content, filename=filename, is_overwrite=False
        )
        assert file_path.exists()

        # Try to overwrite with is_overwrite=False (should fail)
        with pytest.raises(Exception):
            tools.write_note(text="New content", filename=filename, is_overwrite=False)

        # Verify content is still the original
        content = tools.read_note(str(file_path))

        # Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == initial_content

        # Overwrite with is_overwrite=True (should succeed)
        new_content = "New content"
        tools.write_note(text=new_content, filename=filename, is_overwrite=True)

        # Verify content is updated
        content = tools.read_note(str(file_path))
        post = frontmatter.loads(content)
        assert post.content == new_content

    def test_edge_case_empty_file(self, setup_vault):
        """Test reading and searching an empty file."""
        vault_path = setup_vault

        # Create an empty file
        empty_file = vault_path / "empty.md"
        empty_file.touch()

        # Read empty file
        content = tools.read_note(str(empty_file))
        assert content == ""

        # Search in empty files
        results = tools.search_notes(query="anything", case_sensitive=True)
        # Empty file should not match any keyword
        assert not any(result.file_path == str(empty_file) for result in results)

    def test_integration_write_to_subdirectory(self, setup_vault):
        """Test for creating a file in a subdirectory"""
        vault_path = setup_vault

        # Create a note with a path that includes a subdirectory
        test_content = "This is a note in a subdirectory"

        file_path = tools.write_note(
            text=test_content, filename="subdir/note_in_subdir", is_overwrite=False
        )

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "subdir" / "note_in_subdir.md"
        assert file_path == expected_path

        # Verify the content of the created file
        content = tools.read_note(str(file_path))

        # Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_write_to_nested_subdirectory(self, setup_vault):
        """Test for creating a file in multiple levels of nested subdirectories"""
        vault_path = setup_vault

        # Create a note with a path that includes multiple levels of subdirectories
        test_content = "This is a note in a nested subdirectory"

        file_path = tools.write_note(
            text=test_content,
            filename="level1/level2/level3/deep_note",
            is_overwrite=False,
        )

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "level1" / "level2" / "level3" / "deep_note.md"
        assert file_path == expected_path

        # Verify the content of the created file
        content = tools.read_note(str(file_path))

        # Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_subdirectory_creation(self, setup_vault):
        """Test to verify that non-existent subdirectories are automatically created"""
        vault_path = setup_vault

        # Subdirectory path
        subdir_path = vault_path / "auto_created_dir"

        # Verify that the subdirectory does not exist
        assert not subdir_path.exists()

        file_path = tools.write_note(
            text="Testing automatic directory creation",
            filename="auto_created_dir/auto_note",
            is_overwrite=False,
        )

        # Verify that the subdirectory was automatically created
        assert subdir_path.exists()
        assert subdir_path.is_dir()

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = subdir_path / "auto_note.md"
        assert file_path == expected_path

    def test_integration_write_with_frontmatter(self, setup_vault):
        """Test writing a note with frontmatter."""

        file_path = tools.write_note(
            text="This is a test note with frontmatter",
            filename="frontmatter_test",
            is_overwrite=False,
            author="Integration Test",
        )
        assert file_path.exists()

        # Read the file and verify frontmatter
        with open(file_path, "r") as f:
            content = f.read()

        # Verify frontmatter exists
        assert content.startswith("---")

        # Parse frontmatter
        post = frontmatter.loads(content)
        assert post.metadata["author"] == "Integration Test"
        assert post.content == "This is a test note with frontmatter"

    def test_integration_write_with_default_dir(self, setup_vault):
        """Test writing a note using the default directory."""
        vault_path = setup_vault

        file_path = tools.write_note(
            text="This is a note in the default directory",
            filename="default_dir_note",
            is_overwrite=False,
            default_path="default_notes",
        )
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "default_notes" / "default_dir_note.md"
        assert file_path == expected_path

        # Verify the content of the created file
        content = tools.read_note(str(file_path))

        # Parse frontmatter
        post = frontmatter.loads(content)
        assert post.content == "This is a note in the default directory"
