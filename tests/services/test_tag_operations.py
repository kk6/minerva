"""
Tests for TagOperations service module.
"""

import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.tag_operations import TagOperations
from minerva.exceptions import NoteNotFoundError


class TestTagOperations:
    """Test cases for TagOperations class."""

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
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def tag_operations(self, mock_config, mock_frontmatter_manager):
        """Create a TagOperations instance for testing."""
        return TagOperations(mock_config, mock_frontmatter_manager)

    def test_inherits_from_base_service(self, tag_operations):
        """Test that TagOperations properly inherits from BaseService."""
        assert hasattr(tag_operations, "config")
        assert hasattr(tag_operations, "frontmatter_manager")
        assert hasattr(tag_operations, "error_handler")
        assert hasattr(tag_operations, "_log_operation_start")
        assert hasattr(tag_operations, "_log_operation_success")
        assert hasattr(tag_operations, "_log_operation_error")

    @patch("minerva.validators.TagValidator.normalize_tag")
    def test_normalize_tag(self, mock_normalize, tag_operations):
        """Test tag normalization."""
        mock_normalize.return_value = "normalized-tag"

        result = tag_operations._normalize_tag("Test Tag")

        assert result == "normalized-tag"
        mock_normalize.assert_called_once_with("Test Tag")

    @patch("minerva.validators.TagValidator.validate_tag")
    def test_validate_tag_valid(self, mock_validate, tag_operations):
        """Test tag validation for valid tag."""
        mock_validate.return_value = None  # No exception raised

        result = tag_operations._validate_tag("valid-tag")

        assert result is True
        mock_validate.assert_called_once_with("valid-tag")

    @patch("minerva.validators.TagValidator.validate_tag")
    def test_validate_tag_invalid(self, mock_validate, tag_operations):
        """Test tag validation for invalid tag."""
        mock_validate.side_effect = ValueError("Invalid tag")

        result = tag_operations._validate_tag("invalid,tag")

        assert result is False
        mock_validate.assert_called_once_with("invalid,tag")

    def test_resolve_note_file_with_filepath(self, tag_operations):
        """Test resolving note file with filepath."""
        result = tag_operations._resolve_note_file(None, "/test/path/note.md", None)
        assert result == Path("/test/path/note.md")

    def test_resolve_note_file_with_filename(self, tag_operations, mock_config):
        """Test resolving note file with filename."""
        result = tag_operations._resolve_note_file("test_note", None, None)
        expected = Path("/test/vault/notes/test_note.md")
        assert result == expected

    def test_resolve_note_file_with_filename_and_default_path(
        self, tag_operations, mock_config
    ):
        """Test resolving note file with filename and custom default path."""
        result = tag_operations._resolve_note_file("test_note", None, "custom")
        expected = Path("/test/vault/custom/test_note.md")
        assert result == expected

    def test_resolve_note_file_no_params(self, tag_operations):
        """Test resolving note file with no parameters."""
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            tag_operations._resolve_note_file(None, None, None)

    def test_resolve_note_file_empty_filename(self, tag_operations):
        """Test resolving note file with empty filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            tag_operations._resolve_note_file("", None, None)

    @patch("minerva.services.note_operations.NoteOperations")
    @patch("frontmatter.loads")
    @patch("pathlib.Path.exists")
    def test_load_note_with_tags_success(
        self, mock_exists, mock_loads, mock_note_ops_class, tag_operations
    ):
        """Test successfully loading note with tags."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_exists.return_value = True

        mock_note_ops = Mock()
        mock_note_ops.read_note.return_value = "---\ntags: [tag1, tag2]\n---\nContent"
        mock_note_ops_class.return_value = mock_note_ops

        mock_post = Mock()
        mock_post.metadata = {"tags": ["tag1", "tag2"]}
        mock_loads.return_value = mock_post

        # Act
        post, tags = tag_operations._load_note_with_tags(file_path)

        # Assert
        assert post == mock_post
        assert tags == ["tag1", "tag2"]
        mock_note_ops.read_note.assert_called_once_with(str(file_path))

    @patch("pathlib.Path.exists")
    def test_load_note_with_tags_file_not_found(self, mock_exists, tag_operations):
        """Test loading note when file doesn't exist."""
        file_path = Path("/test/vault/notes/nonexistent.md")
        mock_exists.return_value = False

        with pytest.raises(NoteNotFoundError, match="File .* does not exist"):
            tag_operations._load_note_with_tags(file_path)

    def test_save_note_with_updated_tags(self, tag_operations):
        """Test saving note with updated tags."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_post.metadata = {"author": "Test Author"}
        mock_post.content = "Test content"
        tags = ["tag1", "tag2"]

        # Mock the FrontmatterOperations method
        with patch.object(
            tag_operations._frontmatter_ops,
            "_save_note_with_updated_frontmatter",
            return_value=file_path,
        ) as mock_save:
            # Act
            result = tag_operations._save_note_with_updated_tags(
                file_path, mock_post, tags
            )

        # Assert
        assert result == file_path
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        updated_frontmatter = call_args[2]  # Third argument is frontmatter dict
        assert updated_frontmatter["tags"] == tags
        assert updated_frontmatter["author"] == "Test Author"

    @patch.object(TagOperations, "_save_note_with_updated_tags")
    @patch.object(TagOperations, "_load_note_with_tags")
    @patch.object(TagOperations, "_resolve_note_file")
    @patch.object(TagOperations, "_validate_tag")
    @patch.object(TagOperations, "_normalize_tag")
    def test_add_tag_success(
        self,
        mock_normalize,
        mock_validate,
        mock_resolve,
        mock_load,
        mock_save,
        tag_operations,
    ):
        """Test successfully adding a tag."""
        # Arrange
        tag = "new-tag"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_normalize.side_effect = [
            "new-tag",
            "existing-tag",
        ]  # First call for validation, second for current tags
        mock_validate.return_value = True
        mock_resolve.return_value = file_path

        mock_post = Mock()
        current_tags = ["existing-tag"]
        mock_load.return_value = (mock_post, current_tags)
        mock_save.return_value = file_path

        # Act
        result = tag_operations.add_tag(tag, filename=filename)

        # Assert
        assert result == file_path
        mock_validate.assert_called_with(tag)
        mock_resolve.assert_called_with(filename, None, None)
        mock_load.assert_called_with(file_path)
        mock_save.assert_called_with(file_path, mock_post, ["existing-tag", "new-tag"])

    @patch.object(TagOperations, "_validate_tag")
    @patch.object(TagOperations, "_normalize_tag")
    def test_add_tag_invalid_tag(self, mock_normalize, mock_validate, tag_operations):
        """Test adding invalid tag."""
        mock_normalize.return_value = "invalid,tag"
        mock_validate.return_value = False

        with pytest.raises(ValueError, match="Invalid tag: invalid,tag"):
            tag_operations.add_tag("invalid,tag", filename="test")

    @patch.object(TagOperations, "_save_note_with_updated_tags")
    @patch.object(TagOperations, "_load_note_with_tags")
    @patch.object(TagOperations, "_resolve_note_file")
    @patch.object(TagOperations, "_normalize_tag")
    def test_add_tag_already_exists(
        self, mock_normalize, mock_resolve, mock_load, mock_save, tag_operations
    ):
        """Test adding tag that already exists."""
        # Arrange
        tag = "existing-tag"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_normalize.return_value = "existing-tag"
        mock_resolve.return_value = file_path

        mock_post = Mock()
        current_tags = ["existing-tag"]
        mock_load.return_value = (mock_post, current_tags)
        mock_save.return_value = file_path

        with patch.object(tag_operations, "_validate_tag", return_value=True):
            # Act
            result = tag_operations.add_tag(tag, filename=filename)

            # Assert
            assert result == file_path
            # Should still save to update the 'updated' field
            mock_save.assert_called_with(file_path, mock_post, ["existing-tag"])

    @patch.object(TagOperations, "_save_note_with_updated_tags")
    @patch.object(TagOperations, "_load_note_with_tags")
    @patch.object(TagOperations, "_resolve_note_file")
    @patch.object(TagOperations, "_normalize_tag")
    def test_remove_tag_success(
        self, mock_normalize, mock_resolve, mock_load, mock_save, tag_operations
    ):
        """Test successfully removing a tag."""
        # Arrange
        tag = "remove-tag"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        # Mock multiple calls to _normalize_tag
        mock_normalize.side_effect = ["remove-tag", "keep-tag", "remove-tag"]
        mock_resolve.return_value = file_path

        mock_post = Mock()
        current_tags = ["keep-tag", "remove-tag"]
        mock_load.return_value = (mock_post, current_tags)
        mock_save.return_value = file_path

        # Act
        result = tag_operations.remove_tag(tag, filename=filename)

        # Assert
        assert result == file_path
        mock_save.assert_called_with(file_path, mock_post, ["keep-tag"])

    @patch.object(TagOperations, "_save_note_with_updated_tags")
    @patch.object(TagOperations, "_load_note_with_tags")
    @patch.object(TagOperations, "_resolve_note_file")
    @patch.object(TagOperations, "_normalize_tag")
    def test_remove_tag_not_found(
        self, mock_normalize, mock_resolve, mock_load, mock_save, tag_operations
    ):
        """Test removing tag that doesn't exist."""
        # Arrange
        tag = "nonexistent-tag"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        # Mock multiple calls to _normalize_tag
        mock_normalize.side_effect = ["nonexistent-tag", "existing-tag"]
        mock_resolve.return_value = file_path

        mock_post = Mock()
        current_tags = ["existing-tag"]
        mock_load.return_value = (mock_post, current_tags)
        mock_save.return_value = file_path

        # Act
        result = tag_operations.remove_tag(tag, filename=filename)

        # Assert
        assert result == file_path
        mock_save.assert_called_with(file_path, mock_post, ["existing-tag"])

    @patch.object(TagOperations, "_load_note_with_tags")
    @patch.object(TagOperations, "_resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_tags_success(
        self, mock_exists, mock_resolve, mock_load, tag_operations
    ):
        """Test successfully getting tags."""
        # Arrange
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = True

        mock_post = Mock()
        tags = ["tag1", "tag2"]
        mock_load.return_value = (mock_post, tags)

        # Act
        result = tag_operations.get_tags(filename=filename)

        # Assert
        assert result == tags
        mock_resolve.assert_called_with(filename, None, None)
        mock_load.assert_called_with(file_path)

    @patch.object(TagOperations, "_resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_tags_file_not_found(self, mock_exists, mock_resolve, tag_operations):
        """Test getting tags when file doesn't exist."""
        filename = "nonexistent"
        file_path = Path("/test/vault/notes/nonexistent.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = False

        # Due to @safe_operation decorator, returns empty list instead of raising exception
        result = tag_operations.get_tags(filename=filename)
        assert result == []

    @patch.object(TagOperations, "_rename_tag_in_file")
    @patch.object(TagOperations, "_validate_tag")
    @patch.object(TagOperations, "_normalize_tag")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.rglob")
    def test_rename_tag_success(
        self,
        mock_rglob,
        mock_is_dir,
        mock_normalize,
        mock_validate,
        mock_rename_file,
        tag_operations,
    ):
        """Test successfully renaming tags."""
        # Arrange
        old_tag = "old-tag"
        new_tag = "new-tag"

        mock_normalize.side_effect = ["new-tag", "old-tag", "old-tag"]
        mock_validate.return_value = True
        mock_is_dir.return_value = True

        file1 = Path("/test/vault/notes/note1.md")
        file2 = Path("/test/vault/notes/note2.md")
        mock_rglob.return_value = [file1, file2]
        mock_rename_file.side_effect = [True, False]  # Only first file modified

        # Act
        result = tag_operations.rename_tag(old_tag, new_tag)

        # Assert
        assert result == [file1]
        assert mock_validate.call_count == 2  # Called for both old and new tags
        mock_rename_file.assert_has_calls(
            [call(file1, "old-tag", "new-tag"), call(file2, "old-tag", "new-tag")]
        )

    @patch.object(TagOperations, "_validate_tag")
    @patch.object(TagOperations, "_normalize_tag")
    def test_rename_tag_invalid_new_tag(
        self, mock_normalize, mock_validate, tag_operations
    ):
        """Test renaming to invalid new tag."""
        mock_normalize.side_effect = [
            "invalid,tag",
            "old-tag",
        ]  # new_tag first, then old_tag
        mock_validate.side_effect = [False, True]  # new invalid, old valid

        with pytest.raises(ValueError, match="Invalid new_tag: invalid,tag"):
            tag_operations.rename_tag("old-tag", "invalid,tag")

    @patch.object(TagOperations, "_validate_tag")
    @patch.object(TagOperations, "_normalize_tag")
    def test_rename_tag_invalid_old_tag(
        self, mock_normalize, mock_validate, tag_operations
    ):
        """Test renaming from invalid old tag."""
        mock_normalize.side_effect = [
            "new-tag",
            "invalid,tag",
        ]  # new_tag first, then old_tag
        mock_validate.side_effect = [True, False]  # new valid, old invalid

        with pytest.raises(ValueError, match="Invalid old_tag: invalid,tag"):
            tag_operations.rename_tag("invalid,tag", "new-tag")

    @patch.object(TagOperations, "_normalize_tag")
    def test_rename_tag_same_normalized(self, mock_normalize, tag_operations):
        """Test renaming tag to same normalized form."""
        mock_normalize.return_value = "same-tag"

        with patch.object(tag_operations, "_validate_tag", return_value=True):
            result = tag_operations.rename_tag("same-tag", "same-tag")
            assert result == []

    @patch.object(TagOperations, "_validate_tag")
    @patch.object(TagOperations, "_normalize_tag")
    @patch("pathlib.Path.is_dir")
    def test_rename_tag_directory_not_found(
        self, mock_is_dir, mock_normalize, mock_validate, tag_operations
    ):
        """Test renaming tag in nonexistent directory."""
        mock_normalize.side_effect = ["new-tag", "old-tag"]
        mock_validate.return_value = True
        mock_is_dir.return_value = False

        with pytest.raises(FileNotFoundError):
            tag_operations.rename_tag("old-tag", "new-tag", "/nonexistent")

    @patch.object(TagOperations, "_save_note_with_updated_tags")
    @patch.object(TagOperations, "_load_note_with_tags")
    @patch.object(TagOperations, "_normalize_tag")
    def test_rename_tag_in_file_success(
        self, mock_normalize, mock_load, mock_save, tag_operations
    ):
        """Test successfully renaming tag in a single file."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        old_tag_normalized = "old-tag"
        new_tag = "new-tag"

        mock_post = Mock()
        current_tags = ["keep-tag", "old-tag"]
        mock_load.return_value = (mock_post, current_tags)

        # Mock normalize_tag to return appropriate values for the logic
        def normalize_side_effect(tag):
            if tag == "new-tag":
                return "new-tag"
            elif tag == "keep-tag":
                return "keep-tag"
            elif tag == "old-tag":
                return "old-tag"
            else:
                return str(tag).lower()

        mock_normalize.side_effect = normalize_side_effect

        # Act
        result = tag_operations._rename_tag_in_file(
            file_path, old_tag_normalized, new_tag
        )

        # Assert
        assert result is True
        mock_save.assert_called_with(file_path, mock_post, ["keep-tag", "new-tag"])

    @patch.object(TagOperations, "_load_note_with_tags")
    def test_rename_tag_in_file_no_tags(self, mock_load, tag_operations):
        """Test renaming tag in file with no tags."""
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_load.return_value = (mock_post, [])

        result = tag_operations._rename_tag_in_file(file_path, "old-tag", "new-tag")
        assert result is False

    @patch.object(TagOperations, "_load_note_with_tags")
    def test_rename_tag_in_file_exception(self, mock_load, tag_operations):
        """Test renaming tag when exception occurs."""
        file_path = Path("/test/vault/notes/test.md")
        mock_load.side_effect = Exception("Test error")

        result = tag_operations._rename_tag_in_file(file_path, "old-tag", "new-tag")
        assert result is False

    @patch.object(TagOperations, "get_tags")
    @patch.object(TagOperations, "_normalize_tag")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.rglob")
    def test_list_all_tags_success(
        self, mock_rglob, mock_is_dir, mock_normalize, mock_get_tags, tag_operations
    ):
        """Test successfully listing all tags."""
        # Arrange
        mock_is_dir.return_value = True
        file1 = Path("/test/vault/notes/note1.md")
        file2 = Path("/test/vault/notes/note2.md")
        mock_rglob.return_value = [file1, file2]

        mock_get_tags.side_effect = [["tag1", "tag2"], ["tag2", "tag3"]]
        mock_normalize.side_effect = ["tag1", "tag2", "tag2", "tag3"]

        # Act
        result = tag_operations.list_all_tags()

        # Assert
        assert result == ["tag1", "tag2", "tag3"]
        mock_get_tags.assert_has_calls(
            [
                call(filename=None, filepath=str(file1)),
                call(filename=None, filepath=str(file2)),
            ]
        )

    @patch("pathlib.Path.is_dir")
    def test_list_all_tags_directory_not_found(self, mock_is_dir, tag_operations):
        """Test listing tags in nonexistent directory."""
        mock_is_dir.return_value = False

        with pytest.raises(FileNotFoundError):
            tag_operations.list_all_tags("/nonexistent")

    @patch.object(TagOperations, "get_tags")
    @patch.object(TagOperations, "_normalize_tag")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.rglob")
    def test_find_notes_with_tag_success(
        self, mock_rglob, mock_is_dir, mock_normalize, mock_get_tags, tag_operations
    ):
        """Test successfully finding notes with specific tag."""
        # Arrange
        target_tag = "target-tag"
        mock_is_dir.return_value = True
        file1 = Path("/test/vault/notes/note1.md")
        file2 = Path("/test/vault/notes/note2.md")
        mock_rglob.return_value = [file1, file2]

        mock_normalize.side_effect = [
            "target-tag",
            "tag1",
            "target-tag",
            "tag2",
            "other-tag",
        ]
        mock_get_tags.side_effect = [["tag1", "target-tag"], ["tag2", "other-tag"]]

        # Act
        result = tag_operations.find_notes_with_tag(target_tag)

        # Assert
        assert result == [str(file1)]  # Only file1 has the target tag
        mock_get_tags.assert_has_calls(
            [
                call(filename=None, filepath=str(file1)),
                call(filename=None, filepath=str(file2)),
            ]
        )

    @patch.object(TagOperations, "_normalize_tag")
    @patch("pathlib.Path.is_dir")
    def test_find_notes_with_tag_empty_after_normalization(
        self, mock_is_dir, mock_normalize, tag_operations
    ):
        """Test finding notes with tag that becomes empty after normalization."""
        mock_is_dir.return_value = True
        mock_normalize.return_value = ""

        result = tag_operations.find_notes_with_tag("   ")
        assert result == []

    @patch("pathlib.Path.is_dir")
    def test_find_notes_with_tag_directory_not_found(self, mock_is_dir, tag_operations):
        """Test finding notes in nonexistent directory."""
        mock_is_dir.return_value = False

        with pytest.raises(FileNotFoundError):
            tag_operations.find_notes_with_tag("tag", "/nonexistent")


class TestTagOperationsIntegration:
    """Integration tests for TagOperations with real file operations."""

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault for testing."""
        vault_path = tmp_path / "test_vault"
        vault_path.mkdir(parents=True)
        return vault_path

    @pytest.fixture
    def config(self, temp_vault):
        """Create a test configuration."""
        return MinervaConfig(
            vault_path=temp_vault,
            default_note_dir="notes",
            default_author="Test Author",
        )

    @pytest.fixture
    def tag_operations(self, config):
        """Create a TagOperations instance for testing."""
        frontmatter_manager = FrontmatterManager("Test Author")
        return TagOperations(config, frontmatter_manager)

    def test_resolve_note_file_integration(self, tag_operations):
        """Test file resolution with actual paths."""
        # Test with filename
        result = tag_operations._resolve_note_file("test_note", None, None)
        expected = tag_operations.config.vault_path / "notes" / "test_note.md"
        assert result == expected

        # Test with filepath
        filepath = "/custom/path/note.md"
        result = tag_operations._resolve_note_file(None, filepath, None)
        assert result == Path(filepath)

    def test_normalize_and_validate_tag_integration(self, tag_operations):
        """Test tag normalization and validation with real validator."""
        # Test valid tag
        normalized = tag_operations._normalize_tag("Test Tag")
        assert (
            normalized == "test tag"
        )  # TagValidator converts to lowercase with spaces

        valid = tag_operations._validate_tag("valid-tag")
        assert valid is True

        # Test invalid tag (with comma)
        invalid = tag_operations._validate_tag("invalid,tag")
        assert invalid is False
