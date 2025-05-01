from unittest import mock
import time

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


class TestCreateNote:
    @pytest.fixture
    def mock_write_setup(self, tmp_path):
        """Fixture providing common mock setup for write tests."""
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}

    def test_create_note_new_file(self, mock_write_setup):
        """Test creating a new note when file doesn't exist."""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        test_file = tmp_path / "new_note.md"
        mock_write_file.return_value = test_file

        result = tools.create_note(
            text="New note content",
            filename="new_note",
            author="Test Author",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        assert result == test_file
        mock_write_file.assert_called_once()

        # Verify parameters passed to write_file
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == "new_note.md"
        assert (
            called_request.overwrite is False
        )  # Should always be False for create_note

        # Check frontmatter
        post = frontmatter.loads(called_request.content)
        assert post.metadata["author"] == "Test Author"
        assert post.content == "New note content"

    def test_create_note_existing_file(self, mock_write_setup):
        """Test attempting to create a note that already exists raises an error."""
        mock_write_file = mock_write_setup["mock_write_file"]
        mock_write_file.side_effect = FileExistsError("File already exists")

        with pytest.raises(FileExistsError, match="File already exists"):
            tools.create_note(
                text="This should fail",
                filename="existing_note",
                default_path="",  # Set to empty string to avoid subdirectory creation
            )

        mock_write_file.assert_called_once()

        # Verify overwrite is False
        called_request = mock_write_file.call_args[0][0]
        assert called_request.overwrite is False

    def test_create_note_with_subdirectory(self, mock_write_setup):
        """Test creating a note in a subdirectory."""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        expected_dir_path = tmp_path / "subdir"
        expected_file_path = expected_dir_path / "subdir_note.md"
        mock_write_file.return_value = expected_file_path

        result = tools.create_note(
            text="Note in subdirectory",
            filename="subdir/subdir_note",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        assert result == expected_file_path
        mock_write_file.assert_called_once()

        # Verify directory and filename
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "subdir_note.md"

    def test_create_note_adds_created_date(self, mock_write_setup):
        """Test that create_note adds 'created' field to frontmatter."""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        test_file = tmp_path / "date_test.md"
        mock_write_file.return_value = test_file

        tools.create_note(
            text="Note with created date",
            filename="date_test",
            default_path="",
        )

        # Verify parameters passed to write_file
        called_request = mock_write_file.call_args[0][0]

        # Parse frontmatter and check for created field
        post = frontmatter.loads(called_request.content)
        assert "created" in post.metadata
        # Verify the created date is in ISO format
        assert "T" in post.metadata["created"]  # ISO日時形式には "T" が含まれる


class TestEditNote:
    @pytest.fixture
    def mock_write_setup(self, tmp_path):
        """Fixture providing common mock setup for write tests."""
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
            mock.patch("pathlib.Path.exists") as mock_exists,
        ):
            yield {
                "mock_write_file": mock_write_file,
                "tmp_path": tmp_path,
                "mock_exists": mock_exists,
            }

    def test_edit_note_existing_file(self, mock_write_setup):
        """Test editing an existing note."""
        mock_write_file = mock_write_setup["mock_write_file"]
        mock_exists = mock_write_setup["mock_exists"]
        tmp_path = mock_write_setup["tmp_path"]
        test_file = tmp_path / "edit_note.md"

        # Mock file existence check
        mock_exists.return_value = True
        mock_write_file.return_value = test_file

        result = tools.edit_note(
            text="Updated content",
            filename="edit_note",
            author="Editor",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        assert result == test_file
        mock_write_file.assert_called_once()

        # Verify parameters passed to write_file
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == "edit_note.md"
        assert called_request.overwrite is True  # Should always be True for edit_note

        # Check frontmatter
        post = frontmatter.loads(called_request.content)
        assert post.metadata["author"] == "Editor"
        assert post.content == "Updated content"

    def test_edit_note_nonexistent_file(self, mock_write_setup):
        """Test attempting to edit a note that doesn't exist raises an error."""
        mock_exists = mock_write_setup["mock_exists"]
        mock_write_file = mock_write_setup["mock_write_file"]

        # Mock file existence check to return False
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="does not exist"):
            tools.edit_note(
                text="This should fail",
                filename="nonexistent_note",
                default_path="",  # Set to empty string to avoid subdirectory creation
            )

        # write_file should not be called if the file doesn't exist
        mock_write_file.assert_not_called()

    def test_edit_note_with_default_path(self, mock_write_setup):
        """Test editing a note with a custom default path."""
        mock_write_file = mock_write_setup["mock_write_file"]
        mock_exists = mock_write_setup["mock_exists"]
        tmp_path = mock_write_setup["tmp_path"]
        custom_dir = "custom_dir"
        expected_dir_path = tmp_path / custom_dir
        expected_file_path = expected_dir_path / "custom_note.md"

        # Mock file existence check
        mock_exists.return_value = True
        mock_write_file.return_value = expected_file_path

        result = tools.edit_note(
            text="Note with custom path",
            filename="custom_note",
            default_path=custom_dir,
        )

        assert result == expected_file_path
        mock_write_file.assert_called_once()

        # Verify directory includes custom path
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "custom_note.md"

    def test_edit_note_adds_updated_date(self, mock_write_setup):
        """Test that edit_note adds 'updated' field to frontmatter."""
        mock_write_file = mock_write_setup["mock_write_file"]
        mock_exists = mock_write_setup["mock_exists"]
        tmp_path = mock_write_setup["tmp_path"]
        test_file = tmp_path / "date_update_test.md"

        # Mock file existence check
        mock_exists.return_value = True
        mock_write_file.return_value = test_file

        tools.edit_note(
            text="Note with updated date",
            filename="date_update_test",
            default_path="",
        )

        # Verify parameters passed to write_file
        called_request = mock_write_file.call_args[0][0]

        # Parse frontmatter and check for updated field
        post = frontmatter.loads(called_request.content)
        assert "updated" in post.metadata
        # Verify the updated date is in ISO format
        assert "T" in post.metadata["updated"]  # ISO日時形式には "T" が含まれる


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

    def test_integration_create_note(self, setup_vault):
        """Integration test for creating a new note."""
        vault_path = setup_vault
        filename = "create_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        test_content = "This is a new note created with create_note"

        # Create a new note
        created_path = tools.create_note(
            text=test_content,
            filename=filename,
            author="Create Test",
            default_path="",  # Set to empty string to avoid subdirectory creationして、デフォルトのサブディレクトリを使用しない
        )

        # Verify file was created at the expected path
        assert created_path.exists()
        assert created_path == file_path

        # Read the content back and verify
        content = tools.read_note(str(created_path))
        post = frontmatter.loads(content)
        assert post.content == test_content
        assert post.metadata["author"] == "Create Test"

        # Attempt to create the same note again (should fail)
        with pytest.raises(FileExistsError):
            tools.create_note(
                text="This should fail",
                filename=filename,
                default_path="",  # Set to empty string to avoid subdirectory creation
            )

    def test_integration_edit_note(self, setup_vault):
        """Integration test for editing an existing note."""
        vault_path = setup_vault
        filename = "edit_test"
        file_path = vault_path / f"{filename}.md"

        # Create an initial note with write_note
        initial_content = "Initial note content"
        tools.write_note(
            text=initial_content,
            filename=filename,
            is_overwrite=False,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file exists with initial content
        assert file_path.exists()
        initial_read = tools.read_note(str(file_path))
        initial_post = frontmatter.loads(initial_read)
        assert initial_post.content == initial_content

        # Edit the note
        updated_content = "Updated content with edit_note"
        edited_path = tools.edit_note(
            text=updated_content,
            filename=filename,
            author="Editor",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file was edited
        assert edited_path == file_path
        updated_read = tools.read_note(str(edited_path))
        updated_post = frontmatter.loads(updated_read)
        assert updated_post.content == updated_content
        assert updated_post.metadata["author"] == "Editor"

    def test_integration_edit_nonexistent_note(self, setup_vault):
        """Integration test verifying edit_note fails for nonexistent notes."""
        nonexistent_filename = "does_not_exist"

        # Attempt to edit a nonexistent note
        with pytest.raises(FileNotFoundError):
            tools.edit_note(
                text="This should fail",
                filename=nonexistent_filename,
                default_path="",  # Set to empty string to avoid subdirectory creation
            )

    def test_integration_create_edit_workflow(self, setup_vault):
        """Integration test for create -> edit workflow."""
        vault_path = setup_vault
        filename = "workflow_test"
        file_path = vault_path / f"{filename}.md"

        # Step 1: Create a new note
        initial_content = "Initial content via create_note"
        tools.create_note(
            text=initial_content,
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify creation worked
        assert file_path.exists()

        # Step 2: Edit the created note
        updated_content = "Updated via edit_note"
        tools.edit_note(
            text=updated_content,
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify edit worked
        content = tools.read_note(str(file_path))
        post = frontmatter.loads(content)
        assert post.content == updated_content

    def test_integration_date_metadata(self, setup_vault):
        """Integration test for date metadata in frontmatter."""
        vault_path = setup_vault
        filename = "date_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        # Step 1: Create a new note
        test_content = "This is a test for date metadata"
        tools.create_note(
            text=test_content,
            filename=filename,
            default_path="",
        )

        # Verify created date was added
        content1 = tools.read_note(str(file_path))
        post1 = frontmatter.loads(content1)
        assert "created" in post1.metadata
        assert "T" in post1.metadata["created"]  # ISO format includes 'T'
        assert "updated" not in post1.metadata  # Should not have updated field yet

        # Wait a short time to ensure distinct timestamps
        time.sleep(0.1)

        # Step 2: Edit the same note
        updated_content = "This content was updated"
        tools.edit_note(
            text=updated_content,
            filename=filename,
            default_path="",
        )

        # Verify updated date was added while preserving created date
        content2 = tools.read_note(str(file_path))
        post2 = frontmatter.loads(content2)
        assert "created" in post2.metadata
        assert "updated" in post2.metadata
        assert "T" in post2.metadata["updated"]

        # Created date should be preserved from original creation
        assert post2.metadata["created"] == post1.metadata["created"]
        # Updated date should be different (newer) than created date
        assert post2.metadata["updated"] != post2.metadata["created"]

    def test_integration_write_note_date_handling(self, setup_vault):
        """Integration test for date handling in write_note function."""
        vault_path = setup_vault
        filename = "write_date_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        # Step 1: Create a new note with write_note
        test_content = "This is a test for write_note date metadata"
        tools.write_note(
            text=test_content,
            filename=filename,
            is_overwrite=False,
            default_path="",
        )

        # Verify created date was added
        content1 = tools.read_note(str(file_path))
        post1 = frontmatter.loads(content1)
        assert "created" in post1.metadata
        assert "T" in post1.metadata["created"]  # ISO format includes 'T'
        assert "updated" not in post1.metadata  # Should not have updated field yet

        # Wait a short time to ensure distinct timestamps
        time.sleep(0.1)

        # Step 2: Update the same note with write_note
        updated_content = "This content was updated with write_note"
        tools.write_note(
            text=updated_content,
            filename=filename,
            is_overwrite=True,
            default_path="",
        )

        # Verify updated date was added while preserving created date
        content2 = tools.read_note(str(file_path))
        post2 = frontmatter.loads(content2)
        assert "created" in post2.metadata
        assert "updated" in post2.metadata
        assert "T" in post2.metadata["updated"]

        # Created date should be preserved from original creation
        assert post2.metadata["created"] == post1.metadata["created"]
        # Updated date should be different (newer) than created date
        assert post2.metadata["updated"] != post2.metadata["created"]
