from unittest import mock
import pytest
import pydantic

from minerva import tools
from minerva.tools import DeleteConfirmationResult


class TestDeleteNoteFunctions: # Renamed class
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

    # Adapted test_delete_note_by_filename
    def test_get_confirmation_by_filename(self, mock_setup):
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        mock_delete_file = mock_setup["mock_delete_file"] # Get mock_delete_file to assert it's NOT called
        test_file_path = tmp_path / "delete_test.md"

        mock_exists.return_value = True

        result = tools.get_note_delete_confirmation(filename="delete_test", default_path="")
        
        assert isinstance(result, DeleteConfirmationResult)
        assert result.file_path == str(test_file_path)
        assert f"File found at {str(test_file_path)}. To delete, call 'perform_note_delete' with the same identification parameters." in result.message
        mock_delete_file.assert_not_called()

    def test_perform_delete_by_filename(self, mock_setup):
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        test_file = tmp_path / "delete_test.md"

        mock_exists.return_value = True
        mock_delete_file.return_value = test_file

        result = tools.perform_note_delete(filename="delete_test", default_path="")

        assert result == test_file
        mock_delete_file.assert_called_once()
        called_request = mock_delete_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == "delete_test.md"

    # Adapted test_delete_note_by_filepath
    def test_get_confirmation_by_filepath(self, mock_setup):
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        mock_delete_file = mock_setup["mock_delete_file"]
        test_file_path_str = str(tmp_path / "delete_test.md")

        mock_exists.return_value = True

        result = tools.get_note_delete_confirmation(filepath=test_file_path_str)

        assert isinstance(result, DeleteConfirmationResult)
        assert result.file_path == test_file_path_str
        assert f"File found at {test_file_path_str}. To delete, call 'perform_note_delete' with the same identification parameters." in result.message
        mock_delete_file.assert_not_called()

    def test_perform_delete_by_filepath(self, mock_setup):
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        test_file = tmp_path / "delete_test.md"
        test_filepath_str = str(test_file)

        mock_exists.return_value = True
        mock_delete_file.return_value = test_file

        result = tools.perform_note_delete(filepath=test_filepath_str)

        assert result == test_file
        mock_delete_file.assert_called_once()
        called_request = mock_delete_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == "delete_test.md"

    # Adapted test_delete_note_nonexistent_file
    def test_get_confirmation_nonexistent_file(self, mock_setup):
        mock_exists = mock_setup["mock_exists"]
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            tools.get_note_delete_confirmation(filename="nonexistent_note", default_path="")
        mock_delete_file.assert_not_called()

    def test_perform_delete_nonexistent_file(self, mock_setup):
        mock_exists = mock_setup["mock_exists"]
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            tools.perform_note_delete(filename="nonexistent_note", default_path="")
        mock_delete_file.assert_not_called()


    # Adapted test_delete_note_missing_parameters
    def test_get_confirmation_missing_parameters(self):
        with pytest.raises(
            pydantic.ValidationError,
            match="Either filename or filepath must be provided",
        ):
            tools.get_note_delete_confirmation()
            
    def test_perform_delete_missing_parameters(self):
        with pytest.raises(
            pydantic.ValidationError,
            match="Either filename or filepath must be provided",
        ):
            tools.perform_note_delete()

    # Adapted test_delete_note_with_subdirectory
    def test_get_confirmation_with_subdirectory(self, mock_setup):
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        mock_delete_file = mock_setup["mock_delete_file"]
        expected_dir_path = tmp_path / "subdir"
        expected_file_path = expected_dir_path / "subdir_note.md"

        mock_exists.return_value = True

        result = tools.get_note_delete_confirmation(filename="subdir/subdir_note", default_path="")
        
        assert isinstance(result, DeleteConfirmationResult)
        assert result.file_path == str(expected_file_path)
        assert f"File found at {str(expected_file_path)}. To delete, call 'perform_note_delete' with the same identification parameters." in result.message
        mock_delete_file.assert_not_called()

    def test_perform_delete_with_subdirectory(self, mock_setup):
        mock_delete_file = mock_setup["mock_delete_file"]
        mock_exists = mock_setup["mock_exists"]
        tmp_path = mock_setup["tmp_path"]
        expected_dir_path = tmp_path / "subdir"
        expected_file_path = expected_dir_path / "subdir_note.md"

        mock_exists.return_value = True
        mock_delete_file.return_value = expected_file_path

        result = tools.perform_note_delete(filename="subdir/subdir_note", default_path="")

        assert result == expected_file_path
        mock_delete_file.assert_called_once()
        called_request = mock_delete_file.call_args[0][0]
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "subdir_note.md"

    # Original test_delete_note_confirmation is removed as its logic is now split.

class TestIntegrationDeleteNote:
    """Integration tests that test the actual file operations."""

    @pytest.fixture
    def setup_vault(self, tmp_path):
        """Set up a temporary vault directory."""
        with mock.patch("minerva.tools.VAULT_PATH", tmp_path):
            yield tmp_path

    def test_integration_delete_note(self, setup_vault):
        vault_path = setup_vault
        filename = "delete_test"
        file_path = vault_path / f"{filename}.md"

        tools.create_note(
            text="This note will be deleted",
            filename=filename,
            default_path="",
        )
        assert file_path.exists()

        confirmation_result = tools.get_note_delete_confirmation(filename=filename, default_path="")
        assert confirmation_result.file_path == str(file_path)
        assert file_path.exists() # File should still exist

        deleted_path = tools.perform_note_delete(filename=filename, default_path="")
        assert deleted_path == file_path
        assert not file_path.exists()

    def test_integration_delete_note_by_filepath(self, setup_vault):
        vault_path = setup_vault
        filename = "delete_by_path_test"
        file_path = vault_path / f"{filename}.md"

        tools.create_note(
            text="This note will be deleted by filepath",
            filename=filename,
            default_path="",
        )
        assert file_path.exists()

        confirmation_result = tools.get_note_delete_confirmation(filepath=str(file_path))
        assert confirmation_result.file_path == str(file_path)
        assert file_path.exists()

        deleted_path = tools.perform_note_delete(filepath=str(file_path))
        assert deleted_path == file_path
        assert not file_path.exists()

    def test_integration_delete_nonexistent_note(self, setup_vault):
        nonexistent_filename = "does_not_exist"

        with pytest.raises(FileNotFoundError):
            tools.get_note_delete_confirmation(filename=nonexistent_filename, default_path="")
        
        with pytest.raises(FileNotFoundError):
            tools.perform_note_delete(filename=nonexistent_filename, default_path="")

    def test_integration_create_delete_workflow(self, setup_vault):
        vault_path = setup_vault
        filename = "workflow_test"
        file_path = vault_path / f"{filename}.md"

        tools.create_note(
            text="This note will be created then deleted",
            filename=filename,
            default_path="",
        )
        assert file_path.exists()

        # Optional: get confirmation
        confirmation = tools.get_note_delete_confirmation(filename=filename, default_path="")
        assert confirmation.file_path == str(file_path)
        assert file_path.exists()

        tools.perform_note_delete(filename=filename, default_path="")
        assert not file_path.exists()

    def test_integration_delete_note_in_subdirectory(self, setup_vault):
        vault_path = setup_vault
        subdir = "test_subdir"
        filename = f"{subdir}/subdir_note"
        file_path = vault_path / subdir / "subdir_note.md"

        tools.create_note(
            text="This note in a subdirectory will be deleted",
            filename=filename,
            default_path="",
        )
        assert file_path.exists()

        confirmation = tools.get_note_delete_confirmation(filename=filename, default_path="")
        assert confirmation.file_path == str(file_path)
        assert file_path.exists()

        deleted_path = tools.perform_note_delete(filename=filename, default_path="")
        assert deleted_path == file_path
        assert not file_path.exists()
        assert (vault_path / subdir).exists()


    def test_integration_get_confirmation_and_perform_delete(self, setup_vault): # Renamed
        vault_path = setup_vault
        filename = "confirm_test"
        file_path = vault_path / f"{filename}.md"

        tools.create_note(
            text="This note will be confirmed for deletion",
            filename=filename,
            default_path="",
        )
        assert file_path.exists()

        result = tools.get_note_delete_confirmation(filename=filename, default_path="")
        
        assert isinstance(result, DeleteConfirmationResult)
        assert result.file_path == str(file_path)
        assert f"File found at {str(file_path)}. To delete, call 'perform_note_delete' with the same identification parameters." in result.message
        assert file_path.exists() # File should still exist

        deleted_path = tools.perform_note_delete(filename=filename, default_path="")
        assert deleted_path == file_path
        assert not file_path.exists()
