"""
Tests for the unified validation module.

This module tests all the validation logic that has been centralized
in the validators module to ensure consistency and correctness.
"""

import pytest
from minerva.validators import FilenameValidator, TagValidator, PathValidator


class TestFilenameValidator:
    """Test cases for FilenameValidator."""

    def test_validate_filename_valid_cases(self):
        """Test that valid filenames pass validation."""
        valid_filenames = [
            "test.md",
            "my_note.txt",
            "document-with-dashes.md",
            "file123.md",
            "test file with spaces.md",
            "日本語.md",  # Unicode characters
            "file.with.dots.md",
        ]

        for filename in valid_filenames:
            result = FilenameValidator.validate_filename(filename)
            assert result == filename

    def test_validate_filename_empty_string(self):
        """Test that empty filenames raise ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            FilenameValidator.validate_filename("")

    def test_validate_filename_absolute_path(self):
        """Test that absolute paths raise ValueError."""
        # Test Unix-style absolute paths (no forbidden characters)
        absolute_paths = [
            "/absolute/path/file.md",
            "/root/file.md",
        ]

        for path in absolute_paths:
            with pytest.raises(ValueError, match="Filename cannot be an absolute path"):
                FilenameValidator.validate_filename(path)

    def test_validate_filename_windows_absolute_path(self):
        """Test that Windows absolute paths fail on forbidden characters."""
        # Windows paths contain backslashes which are forbidden, so they fail on that check first
        with pytest.raises(ValueError, match="Filename contains forbidden characters"):
            FilenameValidator.validate_filename("C:\\Windows\\file.txt")

    def test_validate_filename_forbidden_characters(self):
        """Test that filenames with forbidden characters raise ValueError."""
        forbidden_chars = '<>:"/\\|?*'

        for char in forbidden_chars:
            filename = f"test{char}file.md"
            with pytest.raises(
                ValueError, match="Filename contains forbidden characters"
            ):
                FilenameValidator.validate_filename(filename)

    def test_validate_filename_multiple_forbidden_characters(self):
        """Test filenames with multiple forbidden characters."""
        filename = "test<>file*.md"
        with pytest.raises(ValueError, match="Filename contains forbidden characters"):
            FilenameValidator.validate_filename(filename)

    def test_validate_filename_with_subdirs_valid_cases(self):
        """Test valid filenames with subdirectories."""
        valid_filenames = [
            "test.md",
            "folder/test.md",
            "deep/nested/file.md",
            "folder-with-dashes/file_with_underscores.md",
            "日本語/ファイル.md",  # Unicode directories and files
        ]

        for filename in valid_filenames:
            result = FilenameValidator.validate_filename_with_subdirs(filename)
            assert result == filename

    def test_validate_filename_with_subdirs_empty(self):
        """Test that empty filenames raise ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            FilenameValidator.validate_filename_with_subdirs("")

    def test_validate_filename_with_subdirs_absolute_path(self):
        """Test that absolute paths raise ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be an absolute path"):
            FilenameValidator.validate_filename_with_subdirs("/absolute/path/file.md")

    def test_validate_filename_with_subdirs_forbidden_chars(self):
        """Test that filenames with forbidden characters (except /) raise ValueError."""
        forbidden_chars = '<>:"|\\?*'  # Excluding forward slash

        for char in forbidden_chars:
            filename = f"test{char}file.md"
            with pytest.raises(
                ValueError, match="Filename contains forbidden characters"
            ):
                FilenameValidator.validate_filename_with_subdirs(filename)

            # Also test in subdirectory names
            filename = f"sub{char}dir/file.md"
            with pytest.raises(
                ValueError, match="Filename contains forbidden characters"
            ):
                FilenameValidator.validate_filename_with_subdirs(filename)

    def test_validate_filename_with_subdirs_empty_filename(self):
        """Test that empty filenames raise ValueError."""
        # Empty string
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            FilenameValidator.validate_filename_with_subdirs("")

        # Single dot which resolves to empty name
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            FilenameValidator.validate_filename_with_subdirs(".")


class TestTagValidator:
    """Test cases for TagValidator."""

    def test_validate_tag_valid_cases(self):
        """Test that valid tags pass validation."""
        valid_tags = [
            "python",
            "data-science",
            "machine_learning",
            "tag123",
            "Tag With Spaces",
            "日本語タグ",  # Unicode characters
        ]

        for tag in valid_tags:
            result = TagValidator.validate_tag(tag)
            assert result == tag

    def test_validate_tag_empty_string(self):
        """Test that empty tags raise ValueError."""
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            TagValidator.validate_tag("")

    def test_validate_tag_whitespace_only(self):
        """Test that whitespace-only tags raise ValueError."""
        whitespace_tags = ["   ", "\t", "\n", " \t \n "]

        for tag in whitespace_tags:
            with pytest.raises(ValueError, match="Tag cannot be empty"):
                TagValidator.validate_tag(tag)

    def test_validate_tag_forbidden_characters(self):
        """Test that tags with forbidden characters raise ValueError."""
        forbidden_chars = ",<>/?'\"`"  # Removed space - spaces are allowed in tags

        for char in forbidden_chars:
            tag = f"test{char}tag"
            with pytest.raises(ValueError, match="Tag contains forbidden characters"):
                TagValidator.validate_tag(tag)

    def test_normalize_tag_valid_cases(self):
        """Test tag normalization functionality."""
        test_cases = [
            ("Python", "python"),
            ("  Data Science  ", "data science"),
            ("MACHINE_LEARNING", "machine_learning"),
            ("\tTagged\n", "tagged"),
            ("MiXeD CaSe", "mixed case"),
        ]

        for input_tag, expected in test_cases:
            result = TagValidator.normalize_tag(input_tag)
            assert result == expected

    def test_validate_normalized_tag_valid_cases(self):
        """Test validation of normalized tags."""
        valid_normalized_tags = [
            "python",
            "data-science",
            "machine_learning",
            "tag123",
            "valid tag",
        ]

        for tag in valid_normalized_tags:
            assert TagValidator.validate_normalized_tag(tag) is True

    def test_validate_normalized_tag_invalid_cases(self):
        """Test validation of invalid normalized tags."""
        invalid_normalized_tags = [
            "",  # Empty
            "tag,with,comma",
            "tag<with>brackets",
            "tag/with/slash",
            "tag?with?question",
            "tag'with'quote",
            'tag"with"doublequote',
        ]

        for tag in invalid_normalized_tags:
            assert TagValidator.validate_normalized_tag(tag) is False


class TestPathValidator:
    """Test cases for PathValidator."""

    def test_validate_directory_path_absolute_paths(self):
        """Test validation of absolute directory paths."""
        import os

        if os.name == "nt":  # Windows
            absolute_paths = [
                "C:\\Users\\test",
                "D:\\Projects\\minerva",
                "\\\\server\\share",  # UNC path
            ]
        else:  # Unix-like systems
            absolute_paths = [
                "/home/user",
                "/tmp",
                "/var/log",
            ]

        for path in absolute_paths:
            result = PathValidator.validate_directory_path(path)
            assert result == path

    def test_validate_directory_path_relative_paths(self):
        """Test that relative paths raise ValueError."""
        relative_paths = [
            "relative/path",
            "./current/dir",
            "../parent/dir",
            "just_a_folder",
        ]

        for path in relative_paths:
            with pytest.raises(ValueError, match="Directory must be an absolute path"):
                PathValidator.validate_directory_path(path)

    def test_validate_directory_exists_nonexistent(self):
        """Test validation of non-existent directories."""
        non_existent_paths = [
            "/this/path/does/not/exist",
            "/tmp/definitely_not_a_real_directory_12345",
        ]

        for path in non_existent_paths:
            with pytest.raises(ValueError, match=f"Directory {path} does not exist"):
                PathValidator.validate_directory_exists(path)

    def test_validate_directory_exists_valid(self):
        """Test validation of existing directories."""
        import tempfile

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            result = PathValidator.validate_directory_exists(temp_dir)
            assert result == temp_dir

    def test_validate_directory_exists_file_not_directory(self):
        """Test that passing a file path (not directory) raises ValueError."""
        import tempfile

        # Create a temporary file
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(
                ValueError, match=f"Directory {temp_file.name} does not exist"
            ):
                PathValidator.validate_directory_exists(temp_file.name)


class TestValidatorIntegration:
    """Integration tests to ensure validators work together properly."""

    def test_filename_and_tag_validators_consistency(self):
        """Test that filename and tag validators have consistent behavior."""
        # Test cases that should be valid for both
        common_valid = [
            "test123",
            "valid_name",
            "hyphen-name",
        ]

        for name in common_valid:
            # Both should pass validation
            FilenameValidator.validate_filename(name)
            TagValidator.validate_tag(name)

    def test_forbidden_character_overlap(self):
        """Test overlap between filename and tag forbidden characters."""
        # Characters forbidden in both
        common_forbidden = ["<", ">", "/", "?", '"']

        for char in common_forbidden:
            test_name = f"test{char}name"

            with pytest.raises(ValueError):
                FilenameValidator.validate_filename(test_name)

            with pytest.raises(ValueError):
                TagValidator.validate_tag(test_name)
