from unittest import mock

import pytest
import frontmatter

from minerva import tools


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
        assert "T" in str(post.metadata["updated"])  # ISO format contains 'T'
