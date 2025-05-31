"""
Test private functions in the tools module.

These tests specifically target private functions (those prefixed with _)
in the tools module to ensure complete coverage of functionality.
"""

from unittest import mock
import pytest
from pathlib import Path

from minerva import tools


class TestBuildFilePath:
    """Tests for the _build_file_path function."""

    def test_simple_filename(self):
        """Test with a simple filename."""
        filename = "test_note"
        default_path = "notes"

        with mock.patch("minerva.tools.VAULT_PATH", Path("/test/vault")):
            full_dir_path, base_filename = tools._build_file_path(
                filename, default_path
            )

        assert full_dir_path == Path("/test/vault/notes")
        assert base_filename == "test_note.md"

    def test_filename_with_extension(self):
        """Test with a filename that already has .md extension."""
        filename = "test_note.md"
        default_path = "notes"

        with mock.patch("minerva.tools.VAULT_PATH", Path("/test/vault")):
            full_dir_path, base_filename = tools._build_file_path(
                filename, default_path
            )

        assert full_dir_path == Path("/test/vault/notes")
        assert base_filename == "test_note.md"

    def test_filename_with_subdirectory(self):
        """Test with a filename that includes a subdirectory."""
        filename = "subdir/test_note"
        default_path = "notes"

        with mock.patch("minerva.tools.VAULT_PATH", Path("/test/vault")):
            full_dir_path, base_filename = tools._build_file_path(
                filename, default_path
            )

        assert full_dir_path == Path("/test/vault/notes/subdir")
        assert base_filename == "test_note.md"

    def test_empty_default_path(self):
        """Test with an empty default path."""
        filename = "test_note"
        default_path = ""

        with mock.patch("minerva.tools.VAULT_PATH", Path("/test/vault")):
            full_dir_path, base_filename = tools._build_file_path(
                filename, default_path
            )

        assert full_dir_path == Path("/test/vault")
        assert base_filename == "test_note.md"


class TestAssembleCompleteNote:
    """Tests for the _assemble_complete_note function."""

    @pytest.fixture
    def mock_dependencies(self, tmp_path):
        """Mock the dependencies of _assemble_complete_note."""
        with (
            mock.patch("minerva.tools._build_file_path") as mock_build_path,
            mock.patch("minerva.tools.FrontmatterManager") as mock_fm_manager,
        ):
            # Set up default mock behaviors
            mock_build_path.return_value = (tmp_path, "test_note.md")

            # Mock FrontmatterManager instance
            mock_manager = mock.Mock()
            mock_fm_manager.return_value = mock_manager

            # Mock read_existing_metadata
            mock_manager.read_existing_metadata.return_value = {}

            # Mock generate_metadata
            mock_post = mock.Mock()
            mock_manager.generate_metadata.return_value = mock_post

            # Mock frontmatter.dumps
            with mock.patch("minerva.tools.frontmatter.dumps") as mock_dumps:
                mock_dumps.return_value = "Mock content with frontmatter"

                yield {
                    "mock_build_path": mock_build_path,
                    "mock_fm_manager": mock_fm_manager,
                    "mock_manager": mock_manager,
                    "mock_dumps": mock_dumps,
                    "tmp_path": tmp_path,
                }

    def test_new_note_assembly(self, mock_dependencies):
        """Test assembling a new note."""
        mock_build_path = mock_dependencies["mock_build_path"]
        mock_manager = mock_dependencies["mock_manager"]
        mock_dumps = mock_dependencies["mock_dumps"]
        tmp_path = mock_dependencies["tmp_path"]

        text = "This is a test note."
        filename = "test_note"
        author = "Test Author"
        default_path = "notes"

        dir_path, base_filename, content = tools._assemble_complete_note(
            text, filename, author, default_path, is_new_note=True
        )

        # Verify each dependency was called correctly
        mock_build_path.assert_called_once_with(filename, default_path)
        mock_manager.read_existing_metadata.assert_called_once_with(
            tmp_path / "test_note.md"
        )
        mock_manager.generate_metadata.assert_called_once_with(
            text=text,
            author=author,
            is_new_note=True,
            existing_frontmatter={},
        )
        mock_dumps.assert_called_once()

        # Verify the returned values
        assert dir_path == tmp_path
        assert base_filename == "test_note.md"
        assert content == "Mock content with frontmatter"

    def test_existing_note_update(self, mock_dependencies):
        """Test assembling an update to an existing note."""
        mock_build_path = mock_dependencies["mock_build_path"]
        mock_manager = mock_dependencies["mock_manager"]
        mock_dumps = mock_dependencies["mock_dumps"]
        tmp_path = mock_dependencies["tmp_path"]

        # Set up existing frontmatter
        existing_frontmatter = {"created": "2022-12-31T12:00:00", "tags": ["test"]}
        mock_manager.read_existing_metadata.return_value = existing_frontmatter

        text = "This is an updated test note."
        filename = "test_note"
        author = "Test Author"
        default_path = "notes"

        dir_path, base_filename, content = tools._assemble_complete_note(
            text, filename, author, default_path, is_new_note=False
        )

        # Verify each dependency was called correctly
        mock_build_path.assert_called_once_with(filename, default_path)
        mock_manager.read_existing_metadata.assert_called_once_with(
            tmp_path / "test_note.md"
        )
        mock_manager.generate_metadata.assert_called_once_with(
            text=text,
            author=author,
            is_new_note=False,
            existing_frontmatter=existing_frontmatter,
        )
        mock_dumps.assert_called_once()

        # Verify the returned values
        assert dir_path == tmp_path
        assert base_filename == "test_note.md"
        assert content == "Mock content with frontmatter"
