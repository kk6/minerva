"""
Test private functions in the tools module.

These tests specifically target private functions (those prefixed with _)
in the tools module to ensure complete coverage of functionality.
"""

from unittest import mock
import pytest
from pathlib import Path

from minerva import tools


class TestReadExistingFrontmatter:
    """Tests for the _read_existing_frontmatter function."""

    @pytest.fixture
    def mock_path(self):
        """Create a mock Path object."""
        mock_path = mock.Mock(spec=Path)
        mock_path.exists.return_value = True
        return mock_path

    def test_file_not_exists(self):
        """Test behavior when file doesn't exist."""
        mock_path = mock.Mock(spec=Path)
        mock_path.exists.return_value = False

        result = tools._read_existing_frontmatter(mock_path)

        assert result is None
        mock_path.exists.assert_called_once()

    def test_file_with_frontmatter(self, mock_path):
        """Test reading a file that has frontmatter."""
        content = """---
title: Test Note
author: Test Author
created: 2023-01-01T12:00:00
---
This is a test note content.
"""
        mock_open = mock.mock_open(read_data=content)

        with mock.patch("builtins.open", mock_open):
            result = tools._read_existing_frontmatter(mock_path)

        assert result is not None
        assert result.get("title") == "Test Note"
        assert result.get("author") == "Test Author"
        assert result.get("created") == "2023-01-01T12:00:00"
        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")

    def test_file_without_frontmatter(self, mock_path):
        """Test reading a file that doesn't have frontmatter."""
        content = "This is a test note content with no frontmatter."
        mock_open = mock.mock_open(read_data=content)

        with mock.patch("builtins.open", mock_open):
            result = tools._read_existing_frontmatter(mock_path)

        assert result == {}  # Empty dict when no frontmatter
        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")

    def test_permission_error(self, mock_path):
        """Test behavior when a permission error occurs."""
        mock_open = mock.mock_open()
        mock_open.side_effect = PermissionError("Permission denied")

        with mock.patch("builtins.open", mock_open):
            with pytest.raises(PermissionError, match="Permission denied"):
                tools._read_existing_frontmatter(mock_path)

        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")

    def test_unicode_decode_error(self, mock_path):
        """Test behavior when a unicode decode error occurs."""
        mock_open = mock.mock_open()
        mock_open.side_effect = UnicodeDecodeError(
            "utf-8", b"\x80", 0, 1, "invalid start byte"
        )

        with mock.patch("builtins.open", mock_open):
            result = tools._read_existing_frontmatter(mock_path)

        assert result is None  # Returns None on UnicodeDecodeError
        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")

    def test_io_error(self, mock_path):
        """Test behavior when an IO error occurs."""
        mock_open = mock.mock_open()
        mock_open.side_effect = IOError("IO Error")

        with mock.patch("builtins.open", mock_open):
            result = tools._read_existing_frontmatter(mock_path)

        assert result is None  # Returns None on IOError
        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")

    def test_os_error(self, mock_path):
        """Test behavior when an OS error occurs."""
        mock_open = mock.mock_open()
        mock_open.side_effect = OSError("OS Error")

        with mock.patch("builtins.open", mock_open):
            result = tools._read_existing_frontmatter(mock_path)

        assert result is None  # Returns None on OSError
        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")

    def test_unexpected_error(self, mock_path):
        """Test behavior when an unexpected error occurs."""
        mock_open = mock.mock_open()
        mock_open.side_effect = Exception("Unexpected error")

        with mock.patch("builtins.open", mock_open):
            result = tools._read_existing_frontmatter(mock_path)

        assert result is None  # Returns None on unexpected errors
        mock_path.exists.assert_called_once()
        mock_open.assert_called_once_with(mock_path, "r")


class TestBuildFilePath:
    """Tests for the _build_file_path function."""

    @pytest.fixture
    def mock_vault_path(self, tmp_path):
        """Set up mock VAULT_PATH."""
        with mock.patch("minerva.tools.VAULT_PATH", tmp_path):
            yield tmp_path

    def test_empty_filename(self, mock_vault_path):
        """Test behavior with an empty filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            tools._build_file_path("")

    def test_add_md_extension(self, mock_vault_path):
        """Test .md extension is added when missing."""
        dir_path, filename = tools._build_file_path("test_note")

        assert filename == "test_note.md"
        assert dir_path == mock_vault_path / tools.DEFAULT_NOTE_DIR

    def test_with_existing_md_extension(self, mock_vault_path):
        """Test existing .md extension is preserved."""
        dir_path, filename = tools._build_file_path("test_note.md")

        assert filename == "test_note.md"
        assert dir_path == mock_vault_path / tools.DEFAULT_NOTE_DIR

    def test_with_subdirectory(self, mock_vault_path):
        """Test filename with subdirectory path."""
        dir_path, filename = tools._build_file_path("subdir/test_note")

        assert filename == "test_note.md"
        assert dir_path == mock_vault_path / "subdir"

    def test_with_default_path(self, mock_vault_path):
        """Test default_path is used when no subdirectory in filename."""
        custom_default = "custom_dir"
        dir_path, filename = tools._build_file_path(
            "test_note", default_path=custom_default
        )

        assert filename == "test_note.md"
        assert dir_path == mock_vault_path / custom_default

    def test_with_empty_default_path(self, mock_vault_path):
        """Test with an empty default_path."""
        dir_path, filename = tools._build_file_path("test_note", default_path="")

        assert filename == "test_note.md"
        assert dir_path == mock_vault_path  # Should be just the vault path


class TestGenerateNoteMetadata:
    """Tests for the _generate_note_metadata function."""

    def test_new_note_without_frontmatter(self):
        """Test generating metadata for a new note without existing frontmatter."""
        text = "This is a test note without frontmatter."
        author = "Test Author"

        with mock.patch("minerva.tools.DEFAULT_NOTE_AUTHOR", "Default Author"):
            with mock.patch("minerva.tools.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-01T12:00:00"
                )
                post = tools._generate_note_metadata(text, author, is_new_note=True)

        assert post.content == text
        assert post.metadata["author"] == author
        assert post.metadata["created"] == "2023-01-01T12:00:00"
        assert "updated" not in post.metadata

    def test_new_note_with_frontmatter(self):
        """Test generating metadata for a new note with existing frontmatter."""
        text = """---
title: Test Note
tags: [test, note]
---
This is a test note with frontmatter.
"""
        author = "Test Author"

        with mock.patch("minerva.tools.DEFAULT_NOTE_AUTHOR", "Default Author"):
            with mock.patch("minerva.tools.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-01T12:00:00"
                )
                post = tools._generate_note_metadata(text, author, is_new_note=True)

        assert "This is a test note with frontmatter." in post.content
        assert post.metadata["author"] == author
        assert post.metadata["title"] == "Test Note"
        assert post.metadata["tags"] == ["test", "note"]
        assert post.metadata["created"] == "2023-01-01T12:00:00"
        assert "updated" not in post.metadata

    def test_update_existing_note(self):
        """Test generating metadata for an update to an existing note."""
        text = "This is an updated test note."
        author = "Test Author"

        with mock.patch("minerva.tools.DEFAULT_NOTE_AUTHOR", "Default Author"):
            with mock.patch("minerva.tools.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-02T12:00:00"
                )
                post = tools._generate_note_metadata(text, author, is_new_note=False)

        assert post.content == text
        assert post.metadata["author"] == author
        assert "created" not in post.metadata  # Created should not be added for updates
        assert post.metadata["updated"] == "2023-01-02T12:00:00"

    def test_preserve_existing_created_date(self):
        """Test that existing created date is preserved."""
        text = "This is a test note."
        author = "Test Author"
        existing_frontmatter = {"created": "2022-12-31T12:00:00", "tags": ["test"]}

        with mock.patch("minerva.tools.DEFAULT_NOTE_AUTHOR", "Default Author"):
            with mock.patch("minerva.tools.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-02T12:00:00"
                )
                post = tools._generate_note_metadata(
                    text,
                    author,
                    is_new_note=False,
                    existing_frontmatter=existing_frontmatter,
                )

        assert post.content == text
        assert post.metadata["author"] == author
        assert post.metadata["created"] == "2022-12-31T12:00:00"  # Should be preserved
        assert post.metadata["updated"] == "2023-01-02T12:00:00"  # Should be updated

    def test_default_author_when_none_provided(self):
        """Test that DEFAULT_NOTE_AUTHOR is used when no author is provided."""
        text = "This is a test note."

        with mock.patch("minerva.tools.DEFAULT_NOTE_AUTHOR", "Default Author"):
            with mock.patch("minerva.tools.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-01T12:00:00"
                )
                post = tools._generate_note_metadata(
                    text, author=None, is_new_note=True
                )

        assert post.content == text
        assert post.metadata["author"] == "Default Author"
        assert post.metadata["created"] == "2023-01-01T12:00:00"


class TestAssembleCompleteNote:
    """Tests for the _assemble_complete_note function."""

    @pytest.fixture
    def mock_dependencies(self, tmp_path):
        """Mock the dependencies of _assemble_complete_note."""
        with (
            mock.patch("minerva.tools._build_file_path") as mock_build_path,
            mock.patch(
                "minerva.tools._read_existing_frontmatter"
            ) as mock_read_frontmatter,
            mock.patch(
                "minerva.tools._generate_note_metadata"
            ) as mock_generate_metadata,
            mock.patch("minerva.tools.frontmatter.dumps") as mock_dumps,
        ):
            # Set up default mock behaviors
            mock_build_path.return_value = (tmp_path, "test_note.md")
            mock_read_frontmatter.return_value = {}
            mock_generate_metadata.return_value = mock.Mock()
            mock_dumps.return_value = "Mock content with frontmatter"

            yield {
                "mock_build_path": mock_build_path,
                "mock_read_frontmatter": mock_read_frontmatter,
                "mock_generate_metadata": mock_generate_metadata,
                "mock_dumps": mock_dumps,
                "tmp_path": tmp_path,
            }

    def test_new_note_assembly(self, mock_dependencies):
        """Test assembling a new note."""
        mock_build_path = mock_dependencies["mock_build_path"]
        mock_read_frontmatter = mock_dependencies["mock_read_frontmatter"]
        mock_generate_metadata = mock_dependencies["mock_generate_metadata"]
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
        mock_read_frontmatter.assert_called_once_with(tmp_path / "test_note.md")
        mock_generate_metadata.assert_called_once_with(
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
        mock_read_frontmatter = mock_dependencies["mock_read_frontmatter"]
        mock_generate_metadata = mock_dependencies["mock_generate_metadata"]
        mock_dumps = mock_dependencies["mock_dumps"]
        tmp_path = mock_dependencies["tmp_path"]

        # Set up existing frontmatter
        existing_frontmatter = {"created": "2022-12-31T12:00:00", "tags": ["test"]}
        mock_read_frontmatter.return_value = existing_frontmatter

        text = "This is an updated test note."
        filename = "test_note"
        author = "Test Author"
        default_path = "notes"

        dir_path, base_filename, content = tools._assemble_complete_note(
            text, filename, author, default_path, is_new_note=False
        )

        # Verify each dependency was called correctly
        mock_build_path.assert_called_once_with(filename, default_path)
        mock_read_frontmatter.assert_called_once_with(tmp_path / "test_note.md")
        mock_generate_metadata.assert_called_once_with(
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
