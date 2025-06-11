"""
Tests for path resolution utilities.
"""

import pytest
from pathlib import Path

from minerva.services.core.path_resolver import PathResolver


class TestPathResolver:
    """Test cases for PathResolver class."""

    def test_normalize_path_relative_to_absolute(self):
        """Test normalizing relative path to absolute."""
        # Arrange
        relative_path = "test/path"

        # Act
        result = PathResolver.normalize_path(relative_path)

        # Assert
        assert result.is_absolute()
        assert str(result).endswith("test/path")

    def test_normalize_path_already_absolute(self):
        """Test normalizing already absolute path."""
        # Arrange
        absolute_path = "/absolute/test/path"

        # Act
        result = PathResolver.normalize_path(absolute_path)

        # Assert
        assert result.is_absolute()
        assert str(result) == absolute_path

    def test_normalize_path_empty_raises_error(self):
        """Test that empty path raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Path cannot be empty"):
            PathResolver.normalize_path("")

    def test_normalize_path_none_raises_error(self):
        """Test that None path raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Path cannot be empty"):
            PathResolver.normalize_path(None)

    def test_validate_filename_valid(self):
        """Test validating valid filename."""
        # Arrange
        filename = "valid_filename.md"

        # Act
        result = PathResolver.validate_filename(filename)

        # Assert
        assert result == filename

    def test_validate_filename_with_whitespace(self):
        """Test validating filename with leading/trailing whitespace."""
        # Arrange
        filename = "  valid_filename.md  "

        # Act
        result = PathResolver.validate_filename(filename)

        # Assert
        assert result == "valid_filename.md"

    def test_validate_filename_empty_raises_error(self):
        """Test that empty filename raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            PathResolver.validate_filename("")

    def test_validate_filename_whitespace_only_raises_error(self):
        """Test that whitespace-only filename raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            PathResolver.validate_filename("   ")

    @pytest.mark.parametrize("invalid_char", ["<", ">", ":", '"', "|", "?", "*"])
    def test_validate_filename_invalid_characters(self, invalid_char):
        """Test that filenames with invalid characters raise ValueError."""
        # Arrange
        filename = f"test{invalid_char}file.md"

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"Filename cannot contain '{invalid_char}'"
        ):
            PathResolver.validate_filename(filename)

    @pytest.mark.parametrize(
        "reserved_name", ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
    )
    def test_validate_filename_reserved_names(self, reserved_name):
        """Test that reserved names raise ValueError."""
        # Arrange
        filename = f"{reserved_name}.md"

        # Act & Assert
        with pytest.raises(ValueError, match="uses a reserved name"):
            PathResolver.validate_filename(filename)

    def test_validate_filename_too_long(self):
        """Test that overly long filename raises ValueError."""
        # Arrange
        filename = "a" * 256  # 256 characters, over the 255 limit

        # Act & Assert
        with pytest.raises(ValueError, match="Filename is too long"):
            PathResolver.validate_filename(filename)

    def test_validate_path_components_valid_path(self):
        """Test validating path with valid components."""
        # Arrange
        path = "valid/path/to/file.md"

        # Act & Assert - should not raise
        PathResolver.validate_path_components(path)

    def test_validate_path_components_with_relative_components(self):
        """Test validating path with relative components."""
        # Arrange
        path = "../parent/./current/file.md"

        # Act & Assert - should not raise (. and .. are valid)
        PathResolver.validate_path_components(path)

    def test_validate_path_components_invalid_component(self):
        """Test validating path with invalid component."""
        # Arrange
        path = "valid/path*/to/file.md"  # * is invalid

        # Act & Assert
        with pytest.raises(ValueError, match="Filename cannot contain"):
            PathResolver.validate_path_components(path)

    def test_ensure_extension_without_extension(self):
        """Test ensuring extension when not present."""
        # Arrange
        filename = "test_file"

        # Act
        result = PathResolver.ensure_extension(filename)

        # Assert
        assert result == "test_file.md"

    def test_ensure_extension_with_extension(self):
        """Test ensuring extension when already present."""
        # Arrange
        filename = "test_file.md"

        # Act
        result = PathResolver.ensure_extension(filename)

        # Assert
        assert result == "test_file.md"

    def test_ensure_extension_custom_extension(self):
        """Test ensuring custom extension."""
        # Arrange
        filename = "test_file"
        extension = ".txt"

        # Act
        result = PathResolver.ensure_extension(filename, extension)

        # Assert
        assert result == "test_file.txt"

    def test_split_path_and_filename(self):
        """Test splitting path into directory and filename."""
        # Arrange
        filepath = "/path/to/file.md"

        # Act
        directory, filename = PathResolver.split_path_and_filename(filepath)

        # Assert
        assert directory == "/path/to"
        assert filename == "file.md"

    def test_split_path_and_filename_no_directory(self):
        """Test splitting filename without directory."""
        # Arrange
        filepath = "file.md"

        # Act
        directory, filename = PathResolver.split_path_and_filename(filepath)

        # Assert
        assert directory == ""
        assert filename == "file.md"

    def test_is_safe_path_within_base(self):
        """Test checking if path is safely within base path."""
        # Arrange
        base_path = Path("/base/vault")
        target_path = Path("/base/vault/notes/file.md")

        # Act
        result = PathResolver.is_safe_path(base_path, target_path)

        # Assert
        assert result is True

    def test_is_safe_path_equals_base(self):
        """Test checking if path equals base path."""
        # Arrange
        base_path = Path("/base/vault")
        target_path = Path("/base/vault")

        # Act
        result = PathResolver.is_safe_path(base_path, target_path)

        # Assert
        assert result is True

    def test_is_safe_path_outside_base(self):
        """Test checking if path is outside base path."""
        # Arrange
        base_path = Path("/base/vault")
        target_path = Path("/different/path")

        # Act
        result = PathResolver.is_safe_path(base_path, target_path)

        # Assert
        assert result is False

    def test_is_safe_path_traversal_attack(self):
        """Test checking path traversal attack."""
        # Arrange
        base_path = Path("/base/vault")
        target_path = Path("/base/vault/../../../etc/passwd")

        # Act
        result = PathResolver.is_safe_path(base_path, target_path)

        # Assert
        assert result is False

    def test_create_safe_path_simple(self):
        """Test creating safe path with simple relative path."""
        # Arrange
        base_path = Path("/base/vault")
        relative_path = "notes/file.md"

        # Act
        result = PathResolver.create_safe_path(base_path, relative_path)

        # Assert
        assert result == Path("/base/vault/notes/file.md")

    def test_create_safe_path_with_cleanup(self):
        """Test creating safe path with path cleanup."""
        # Arrange
        base_path = Path("/base/vault")
        relative_path = "notes/./file.md"

        # Act
        result = PathResolver.create_safe_path(base_path, relative_path)

        # Assert
        assert result == Path("/base/vault/notes/file.md")

    def test_create_safe_path_removes_traversal(self):
        """Test creating safe path removes directory traversal."""
        # Arrange
        base_path = Path("/base/vault")
        relative_path = "notes/../../../etc/passwd"

        # Act
        result = PathResolver.create_safe_path(base_path, relative_path)

        # Assert
        assert result == Path("/base/vault/notes/etc/passwd")

    def test_create_safe_path_empty_relative(self):
        """Test creating safe path with empty relative path."""
        # Arrange
        base_path = Path("/base/vault")
        relative_path = ""

        # Act
        result = PathResolver.create_safe_path(base_path, relative_path)

        # Assert
        assert result == base_path

    def test_create_safe_path_invalid_component(self):
        """Test creating safe path with invalid component."""
        # Arrange
        base_path = Path("/base/vault")
        relative_path = "notes/file*.md"

        # Act & Assert
        with pytest.raises(ValueError, match="Filename cannot contain"):
            PathResolver.create_safe_path(base_path, relative_path)

    def test_create_safe_path_normalizes_slashes(self):
        """Test creating safe path normalizes different slash types."""
        # Arrange
        base_path = Path("/base/vault")
        relative_path = "notes\\subfolder/file.md"

        # Act
        result = PathResolver.create_safe_path(base_path, relative_path)

        # Assert
        assert result == Path("/base/vault/notes/subfolder/file.md")
