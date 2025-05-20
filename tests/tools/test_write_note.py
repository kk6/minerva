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
