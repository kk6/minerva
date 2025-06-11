"""
Tests for file operations utilities.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.exceptions import ValidationError
from minerva.services.core.file_operations import (
    validate_filename,
    validate_text_content,
    build_file_path,
    assemble_complete_note,
    resolve_note_file,
    load_note_with_frontmatter,
)


class TestValidationFunctions:
    """Test cases for validation functions."""

    def test_validate_filename_with_valid_filename(self):
        """Test filename validation with valid filename."""
        # Arrange
        args = (Mock(), "content", "valid_filename.md")

        # Act & Assert - should not raise
        validate_filename(*args)

    def test_validate_filename_with_empty_filename(self):
        """Test filename validation with empty filename."""
        # Arrange
        args = (Mock(), "content", "")

        # Act & Assert
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            validate_filename(*args)

    def test_validate_filename_with_whitespace_only(self):
        """Test filename validation with whitespace-only filename."""
        # Arrange
        args = (Mock(), "content", "   ")

        # Act & Assert
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            validate_filename(*args)

    def test_validate_filename_from_kwargs(self):
        """Test filename validation from keyword arguments."""
        # Arrange
        kwargs = {"filename": ""}

        # Act & Assert
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            validate_filename(**kwargs)

    def test_validate_text_content_with_valid_content(self):
        """Test text content validation with valid content."""
        # Arrange
        args = (Mock(), "valid content", "filename.md")

        # Act & Assert - should not raise
        validate_text_content(*args)

    def test_validate_text_content_with_empty_content(self):
        """Test text content validation with empty content."""
        # Arrange
        args = (Mock(), "", "filename.md")

        # Act & Assert
        with pytest.raises(ValidationError, match="Text content cannot be empty"):
            validate_text_content(*args)

    def test_validate_text_content_with_whitespace_only(self):
        """Test text content validation with whitespace-only content."""
        # Arrange
        args = (Mock(), "   ", "filename.md")

        # Act & Assert
        with pytest.raises(ValidationError, match="Text content cannot be empty"):
            validate_text_content(*args)

    def test_validate_text_content_from_kwargs(self):
        """Test text content validation from keyword arguments."""
        # Arrange
        kwargs = {"text": ""}

        # Act & Assert
        with pytest.raises(ValidationError, match="Text content cannot be empty"):
            validate_text_content(**kwargs)


class TestBuildFilePath:
    """Test cases for build_file_path function."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        return config

    def test_build_file_path_simple_filename(self, mock_config):
        """Test building file path with simple filename."""
        # Arrange
        filename = "test_note"

        # Act
        dir_path, base_filename = build_file_path(mock_config, filename)

        # Assert
        assert dir_path == Path("/test/vault/notes")
        assert base_filename == "test_note.md"

    def test_build_file_path_with_extension(self, mock_config):
        """Test building file path with .md extension already present."""
        # Arrange
        filename = "test_note.md"

        # Act
        dir_path, base_filename = build_file_path(mock_config, filename)

        # Assert
        assert dir_path == Path("/test/vault/notes")
        assert base_filename == "test_note.md"

    def test_build_file_path_with_subdirectory(self, mock_config):
        """Test building file path with subdirectory."""
        # Arrange
        filename = "subdir/test_note"

        # Act
        dir_path, base_filename = build_file_path(mock_config, filename)

        # Assert
        assert dir_path == Path("/test/vault/notes/subdir")
        assert base_filename == "test_note.md"

    def test_build_file_path_with_custom_default_path(self, mock_config):
        """Test building file path with custom default path."""
        # Arrange
        filename = "test_note"
        default_path = "custom"

        # Act
        dir_path, base_filename = build_file_path(mock_config, filename, default_path)

        # Assert
        assert dir_path == Path("/test/vault/custom")
        assert base_filename == "test_note.md"

    def test_build_file_path_empty_filename_raises_error(self, mock_config):
        """Test that empty filename raises ValueError."""
        # Arrange
        filename = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            build_file_path(mock_config, filename)

    def test_build_file_path_empty_default_path(self, mock_config):
        """Test building file path with empty default path."""
        # Arrange
        filename = "test_note"
        default_path = ""

        # Act
        dir_path, base_filename = build_file_path(mock_config, filename, default_path)

        # Assert
        assert dir_path == Path("/test/vault/notes")  # Falls back to config default
        assert base_filename == "test_note.md"


class TestAssembleCompleteNote:
    """Test cases for assemble_complete_note function."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        return config

    @pytest.fixture
    def mock_frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        manager = Mock(spec=FrontmatterManager)
        manager.read_existing_metadata.return_value = {}

        # Mock the generate_metadata method to return a proper post object
        mock_post = Mock()
        mock_post.content = "test content"
        mock_post.metadata = {"author": "Test Author", "tags": []}
        manager.generate_metadata.return_value = mock_post

        return manager

    @patch("minerva.services.core.file_operations.frontmatter.dumps")
    def test_assemble_complete_note_new_note(
        self, mock_dumps, mock_config, mock_frontmatter_manager
    ):
        """Test assembling a complete note for a new note."""
        # Arrange
        text = "Test content"
        filename = "test_note"
        author = "Custom Author"
        mock_dumps.return_value = "---\nauthor: Custom Author\n---\nTest content"

        # Act
        dir_path, base_filename, content = assemble_complete_note(
            mock_config,
            mock_frontmatter_manager,
            text,
            filename,
            author,
            is_new_note=True,
        )

        # Assert
        assert dir_path == Path("/test/vault/notes")
        assert base_filename == "test_note.md"
        assert content == "---\nauthor: Custom Author\n---\nTest content"
        mock_frontmatter_manager.read_existing_metadata.assert_called_once()
        mock_frontmatter_manager.generate_metadata.assert_called_once_with(
            text=text, author=author, is_new_note=True, existing_frontmatter={}
        )

    @patch("minerva.services.core.file_operations.frontmatter.dumps")
    def test_assemble_complete_note_existing_note(
        self, mock_dumps, mock_config, mock_frontmatter_manager
    ):
        """Test assembling a complete note for an existing note."""
        # Arrange
        text = "Updated content"
        filename = "existing_note"
        existing_metadata = {"author": "Original Author", "created": "2023-01-01"}
        mock_frontmatter_manager.read_existing_metadata.return_value = existing_metadata
        mock_dumps.return_value = "---\nauthor: Original Author\n---\nUpdated content"

        # Act
        dir_path, base_filename, content = assemble_complete_note(
            mock_config, mock_frontmatter_manager, text, filename, is_new_note=False
        )

        # Assert
        assert dir_path == Path("/test/vault/notes")
        assert base_filename == "existing_note.md"
        assert content == "---\nauthor: Original Author\n---\nUpdated content"
        mock_frontmatter_manager.generate_metadata.assert_called_once_with(
            text=text,
            author=mock_config.default_author,
            is_new_note=False,
            existing_frontmatter=existing_metadata,
        )


class TestResolveNoteFile:
    """Test cases for resolve_note_file function."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        return config

    def test_resolve_note_file_with_filepath(self, mock_config):
        """Test resolving note file with filepath provided."""
        # Arrange
        filepath = "/test/vault/notes/test_note.md"

        # Act
        result = resolve_note_file(mock_config, None, filepath, None)

        # Assert
        assert result == Path(filepath)

    def test_resolve_note_file_with_filename(self, mock_config):
        """Test resolving note file with filename provided."""
        # Arrange
        filename = "test_note"

        # Act
        result = resolve_note_file(mock_config, filename, None, None)

        # Assert
        assert result == Path("/test/vault/notes/test_note.md")

    def test_resolve_note_file_with_filename_and_default_path(self, mock_config):
        """Test resolving note file with filename and custom default path."""
        # Arrange
        filename = "test_note"
        default_path = "custom"

        # Act
        result = resolve_note_file(mock_config, filename, None, default_path)

        # Assert
        assert result == Path("/test/vault/custom/test_note.md")

    def test_resolve_note_file_no_filename_or_filepath_raises_error(self, mock_config):
        """Test that missing both filename and filepath raises ValueError."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            resolve_note_file(mock_config, None, None, None)


class TestLoadNoteWithFrontmatter:
    """Test cases for load_note_with_frontmatter function."""

    def test_load_note_with_frontmatter_success(self):
        """Test successfully loading note with frontmatter."""
        # Arrange
        file_path = Path("/test/note.md")
        file_content = "---\nauthor: Test Author\ntags: [test]\n---\nNote content"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                # Act
                post, metadata = load_note_with_frontmatter(file_path)

                # Assert
                assert post.content == "Note content"
                assert metadata["author"] == "Test Author"
                assert metadata["tags"] == ["test"]

    def test_load_note_with_frontmatter_file_not_found(self):
        """Test loading note when file doesn't exist."""
        # Arrange
        file_path = Path("/test/nonexistent.md")

        with patch("pathlib.Path.exists", return_value=False):
            # Act & Assert
            with pytest.raises(FileNotFoundError, match="File .* does not exist"):
                load_note_with_frontmatter(file_path)

    def test_load_note_with_frontmatter_no_frontmatter(self):
        """Test loading note without frontmatter."""
        # Arrange
        file_path = Path("/test/note.md")
        file_content = "Just plain content without frontmatter"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                # Act
                post, metadata = load_note_with_frontmatter(file_path)

                # Assert
                assert post.content == file_content
                assert metadata == {}
