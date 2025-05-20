from unittest import mock

import pytest
import frontmatter

from minerva import tools


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
        assert "T" in str(post.metadata["created"])  # ISO format contains 'T'
