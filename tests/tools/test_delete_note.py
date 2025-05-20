from unittest import mock
import pytest

from minerva import tools


class TestDeleteNote:
    @pytest.fixture
    def mock_setup(self, tmp_path):
        """Fixture providing common mock setup for delete tests."""
        with (
            mock.patch("minerva.tools.delete_file") as mock_delete_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
            mock.patch("pathlib.Path.exists") as mock_exists,
        ):
            yield {
                "mock_delete_file": mock_delete_file,
                "tmp_path": tmp_path,
                "mock_exists": mock_exists,
            }

    def test_delete_note_by_filename(self, mock_setup):
        """Test deleting a note by filename."""
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        test_file = tmp_path / "delete_test.md"

        # Mock file existence check
        mock_exists.return_value = True
        mock_delete_file.return_value = test_file

        result = tools.delete_note(
            filename="delete_test",
            default_path="",  # Set to empty string to avoid subdirectory creation
            confirm=True,  # Confirm deletion
        )

        assert result == test_file
        mock_delete_file.assert_called_once()

        # Verify parameters passed to delete_file
        called_request = mock_delete_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == "delete_test.md"

    def test_delete_note_by_filepath(self, mock_setup):
        """Test deleting a note by filepath."""
        mock_delete_file = mock_setup["mock_delete_file"]
        tmp_path = mock_setup["tmp_path"]
        test_file = tmp_path / "delete_test.md"
        test_filepath = str(test_file)

        # Mock file existence check
        mock_exists = mock_setup["mock_exists"]
        mock_exists.return_value = True
        mock_delete_file.return_value = test_file

        result = tools.delete_note(
            filepath=test_filepath,
            confirm=True,  # Confirm deletion
        )

        assert result == test_file
        mock_delete_file.assert_called_once()

        # Verify parameters passed to delete_file
        called_request = mock_delete_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == "delete_test.md"

    def test_delete_note_nonexistent_file(self, mock_setup):
        """Test attempting to delete a note that doesn't exist raises an error."""
        mock_setup["mock_delete_file"]
        mock_exists = mock_setup["mock_exists"]

        # Mock file existence check
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            tools.delete_note(
                filename="nonexistent_note",
                default_path="",  # Set to empty string to avoid subdirectory creation
                confirm=True,  # Confirm deletion
            )

    def test_delete_note_missing_parameters(self):
        """Test calling delete_note without required parameters."""
        import pydantic

        with pytest.raises(
            pydantic.ValidationError,
            match="Either filename or filepath must be provided",
        ):
            tools.delete_note()

    def test_delete_note_with_subdirectory(self, mock_setup):
        """Test deleting a note in a subdirectory."""
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        expected_dir_path = tmp_path / "subdir"
        expected_file_path = expected_dir_path / "subdir_note.md"

        # Mock file existence check
        mock_exists.return_value = True
        mock_delete_file.return_value = expected_file_path

        result = tools.delete_note(
            filename="subdir/subdir_note",
            default_path="",  # Set to empty string to avoid subdirectory creation
            confirm=True,  # Confirm deletion
        )

        assert result == expected_file_path
        mock_delete_file.assert_called_once()

        # Verify directory and filename
        called_request = mock_delete_file.call_args[0][0]
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "subdir_note.md"

    def test_delete_note_confirmation(self, mock_setup):
        """Test delete note confirmation without actually deleting."""
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        test_file = tmp_path / "delete_test.md"

        # Mock file existence check
        mock_exists.return_value = True

        # Call delete_note with confirm=False (default)
        result = tools.delete_note(
            filename="delete_test",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify we get a confirmation result, not a file path
        assert isinstance(result, tools.DeleteConfirmationResult)
        assert result.file_path == str(test_file)
        assert "このファイルを削除しますか？" in result.message
        assert "confirm=True" in result.message


class TestIntegrationDeleteNote:
    """Integration tests that test the actual file operations."""

    @pytest.fixture
    def setup_vault(self, tmp_path):
        """Set up a temporary vault directory."""
        with mock.patch("minerva.tools.VAULT_PATH", tmp_path):
            yield tmp_path

    def test_integration_delete_note(self, setup_vault):
        """Integration test for deleting a note."""
        vault_path = setup_vault
        filename = "delete_test"
        file_path = vault_path / f"{filename}.md"

        # Create a note to delete
        tools.create_note(
            text="This note will be deleted",
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file exists
        assert file_path.exists()

        # Delete the note
        deleted_path = tools.delete_note(
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
            confirm=True,  # Confirm deletion
        )

        # Verify file was deleted
        assert deleted_path == file_path
        assert not file_path.exists()

    def test_integration_delete_note_by_filepath(self, setup_vault):
        """Integration test for deleting a note by filepath."""
        vault_path = setup_vault
        filename = "delete_by_path_test"
        file_path = vault_path / f"{filename}.md"

        # Create a note to delete
        tools.create_note(
            text="This note will be deleted by filepath",
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file exists
        assert file_path.exists()

        # Delete the note using filepath
        deleted_path = tools.delete_note(
            filepath=str(file_path),
            confirm=True,  # Confirm deletion
        )

        # Verify file was deleted
        assert deleted_path == file_path
        assert not file_path.exists()

    def test_integration_delete_nonexistent_note(self, setup_vault):
        """Integration test verifying delete_note fails for nonexistent notes."""
        nonexistent_filename = "does_not_exist"

        # Attempt to delete a nonexistent note
        with pytest.raises(FileNotFoundError):
            tools.delete_note(
                filename=nonexistent_filename,
                default_path="",  # Set to empty string to avoid subdirectory creation
                confirm=True,  # Confirm deletion
            )

    def test_integration_create_delete_workflow(self, setup_vault):
        """Integration test for create -> delete workflow."""
        vault_path = setup_vault
        filename = "workflow_test"
        file_path = vault_path / f"{filename}.md"

        # Step 1: Create a new note
        tools.create_note(
            text="This note will be created then deleted",
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify creation worked
        assert file_path.exists()

        # Step 2: Delete the created note
        tools.delete_note(
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
            confirm=True,  # Confirm deletion
        )

        # Verify deletion worked
        assert not file_path.exists()

    def test_integration_delete_note_in_subdirectory(self, setup_vault):
        """Integration test for deleting a note in a subdirectory."""
        vault_path = setup_vault
        subdir = "test_subdir"
        filename = f"{subdir}/subdir_note"
        file_path = vault_path / subdir / "subdir_note.md"

        # Create a note in a subdirectory
        tools.create_note(
            text="This note in a subdirectory will be deleted",
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file exists
        assert file_path.exists()

        # Delete the note
        deleted_path = tools.delete_note(
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
            confirm=True,  # Confirm deletion
        )

        # Verify file was deleted
        assert deleted_path == file_path
        assert not file_path.exists()
        # Subdirectory should still exist
        assert (vault_path / subdir).exists()

    def test_integration_delete_note_confirmation(self, setup_vault):
        """Integration test for delete note confirmation."""
        vault_path = setup_vault
        filename = "confirm_test"
        file_path = vault_path / f"{filename}.md"

        # Create a note to delete
        tools.create_note(
            text="This note will be confirmed for deletion",
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file exists
        assert file_path.exists()

        # Call delete_note with confirm=False (default)
        result = tools.delete_note(
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify we get a confirmation result, not a file path
        assert isinstance(result, tools.DeleteConfirmationResult)
        assert result.file_path == str(file_path)
        assert "このファイルを削除しますか？" in result.message

        # File should still exist
        assert file_path.exists()

        # Now confirm and delete
        deleted_path = tools.delete_note(
            filename=filename,
            default_path="",
            confirm=True,
        )

        # Verify file was deleted
        assert deleted_path == file_path
        assert not file_path.exists()
