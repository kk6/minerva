"""
Tests for AliasOperations service module.
"""

import re
import pytest
from typing import Any
from unittest.mock import Mock, patch
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.alias_operations import AliasOperations


class TestAliasOperations:
    """Test cases for AliasOperations class."""

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
    def alias_operations(self, mock_config, mock_frontmatter_manager):
        """Create an AliasOperations instance for testing."""
        return AliasOperations(mock_config, mock_frontmatter_manager)

    def test_inherits_from_base_service(self, alias_operations):
        """Test that AliasOperations properly inherits from BaseService."""
        assert hasattr(alias_operations, "config")
        assert hasattr(alias_operations, "frontmatter_manager")
        assert hasattr(alias_operations, "error_handler")
        assert hasattr(alias_operations, "_log_operation_start")
        assert hasattr(alias_operations, "_log_operation_success")
        assert hasattr(alias_operations, "_log_operation_error")

    def test_validate_alias_valid(self, alias_operations):
        """Test alias validation for valid alias."""
        result = alias_operations._validate_alias("valid-alias")
        assert result == "valid-alias"

    def test_validate_alias_whitespace_trimming(self, alias_operations):
        """Test alias validation trims whitespace."""
        result = alias_operations._validate_alias("  valid-alias  ")
        assert result == "valid-alias"

    def test_validate_alias_empty(self, alias_operations):
        """Test alias validation for empty alias."""
        with pytest.raises(
            ValueError, match="Alias cannot be empty or only whitespace"
        ):
            alias_operations._validate_alias("")

    def test_validate_alias_whitespace_only(self, alias_operations):
        """Test alias validation for whitespace-only alias."""
        with pytest.raises(
            ValueError, match="Alias cannot be empty or only whitespace"
        ):
            alias_operations._validate_alias("   ")

    def test_validate_alias_too_long(self, alias_operations):
        """Test alias validation for alias exceeding length limit."""
        long_alias = "a" * 101
        with pytest.raises(ValueError, match="Alias cannot exceed 100 characters"):
            alias_operations._validate_alias(long_alias)

    def test_validate_alias_forbidden_characters(self, alias_operations):
        """Test alias validation for forbidden characters."""
        forbidden_chars = ["|", "#", "^", "[", "]"]
        for char in forbidden_chars:
            with pytest.raises(
                ValueError, match=f"Alias cannot contain '{re.escape(char)}' character"
            ):
                alias_operations._validate_alias(f"invalid{char}alias")

    def test_normalize_alias(self, alias_operations):
        """Test alias normalization."""
        result = alias_operations._normalize_alias("  Test Alias  ")
        assert result == "test alias"

    # Note: _resolve_note_file was removed and replaced with resolve_note_file from core.file_operations
    # File resolution is now tested in tests/services/core/test_file_operations.py

    def test_load_note_with_frontmatter_success(self, alias_operations):
        """Test successfully loading note with frontmatter."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")

        # Mock the FrontmatterOperations method
        mock_post = Mock()
        mock_frontmatter: dict[str, Any] = {
            "aliases": ["alias1", "alias2"],
            "tags": ["tag1", "tag2"],
        }

        with patch.object(
            alias_operations._frontmatter_ops,
            "_load_note_with_frontmatter",
            return_value=(mock_post, mock_frontmatter),
        ):
            # Act
            post, frontmatter_dict = alias_operations._load_note_with_frontmatter(
                file_path
            )

        # Assert
        assert post == mock_post
        assert frontmatter_dict == mock_frontmatter

    def test_load_note_with_frontmatter_file_not_found(self, alias_operations):
        """Test loading note when file doesn't exist."""
        file_path = Path("/test/vault/notes/nonexistent.md")

        # Mock the FrontmatterOperations method to raise FileNotFoundError
        with patch.object(
            alias_operations._frontmatter_ops,
            "_load_note_with_frontmatter",
            side_effect=FileNotFoundError(f"File {file_path} does not exist"),
        ):
            with pytest.raises(FileNotFoundError, match="File .* does not exist"):
                alias_operations._load_note_with_frontmatter(file_path)

    @patch.object(AliasOperations, "_load_note_with_frontmatter")
    def test_get_aliases_from_file_success(self, mock_load, alias_operations):
        """Test successfully getting aliases from file."""
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter: dict[str, Any] = {"aliases": ["alias1", "alias2"]}
        mock_load.return_value = (mock_post, mock_frontmatter)

        result = alias_operations._get_aliases_from_file(file_path)

        assert result == ["alias1", "alias2"]
        mock_load.assert_called_once_with(file_path)

    @patch.object(AliasOperations, "_load_note_with_frontmatter")
    def test_get_aliases_from_file_no_aliases(self, mock_load, alias_operations):
        """Test getting aliases from file with no aliases."""
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter: dict[str, Any] = {}
        mock_load.return_value = (mock_post, mock_frontmatter)

        result = alias_operations._get_aliases_from_file(file_path)

        assert result == []

    @patch.object(AliasOperations, "_load_note_with_frontmatter")
    def test_get_aliases_from_file_non_list_aliases(self, mock_load, alias_operations):
        """Test getting aliases from file with non-list aliases value."""
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_frontmatter: dict[str, Any] = {"aliases": "single_alias"}
        mock_load.return_value = (mock_post, mock_frontmatter)

        result = alias_operations._get_aliases_from_file(file_path)

        assert result == []

    def test_save_note_with_updated_aliases(self, alias_operations):
        """Test saving note with updated aliases."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_post.metadata = {"author": "Test Author"}
        mock_post.content = "Test content"
        aliases = ["alias1", "alias2"]

        # Mock the FrontmatterOperations method
        with patch.object(
            alias_operations._frontmatter_ops,
            "_save_note_with_updated_frontmatter",
            return_value=file_path,
        ) as mock_save:
            # Act
            result = alias_operations._save_note_with_updated_aliases(
                file_path, mock_post, aliases
            )

        # Assert
        assert result == file_path
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        updated_frontmatter = call_args[2]  # Third argument is frontmatter dict
        assert updated_frontmatter["aliases"] == aliases
        assert updated_frontmatter["author"] == "Test Author"

    def test_save_note_with_updated_aliases_empty_list(self, alias_operations):
        """Test saving note with empty aliases list."""
        # Arrange
        file_path = Path("/test/vault/notes/test.md")
        mock_post = Mock()
        mock_post.metadata = {"author": "Test Author", "aliases": ["old_alias"]}
        mock_post.content = "Test content"
        aliases: list[str] = []

        # Mock the FrontmatterOperations method
        with patch.object(
            alias_operations._frontmatter_ops,
            "_save_note_with_updated_frontmatter",
            return_value=file_path,
        ) as mock_save:
            # Act
            result = alias_operations._save_note_with_updated_aliases(
                file_path, mock_post, aliases
            )

        # Assert
        assert result == file_path
        # Verify aliases were removed from metadata
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        updated_frontmatter = call_args[2]  # Third argument is frontmatter dict
        assert "aliases" not in updated_frontmatter
        assert updated_frontmatter["author"] == "Test Author"

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_normalize_alias")
    def test_check_alias_conflicts_no_conflicts(
        self, mock_normalize, mock_get_aliases, alias_operations
    ):
        """Test checking alias conflicts with no conflicts."""
        mock_normalize.side_effect = lambda x: x.lower()
        mock_get_aliases.return_value = ["other_alias"]

        # Mock the vault_path's rglob method
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [
                Path("/test/vault/notes/note1.md"),
                Path("/test/vault/notes/note2.md"),
            ]

            result = alias_operations._check_alias_conflicts("new_alias")

            assert result == []

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_normalize_alias")
    def test_check_alias_conflicts_filename_conflict(
        self, mock_normalize, mock_get_aliases, alias_operations
    ):
        """Test checking alias conflicts with filename conflict."""
        mock_normalize.side_effect = lambda x: x.lower()
        conflict_file = Path("/test/vault/notes/test_alias.md")
        mock_get_aliases.return_value = []

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [conflict_file]

            result = alias_operations._check_alias_conflicts("test_alias")

            assert result == [str(conflict_file)]

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_normalize_alias")
    def test_check_alias_conflicts_alias_conflict(
        self, mock_normalize, mock_get_aliases, alias_operations
    ):
        """Test checking alias conflicts with existing alias conflict."""
        mock_normalize.side_effect = lambda x: x.lower()
        conflict_file = Path("/test/vault/notes/note1.md")
        mock_get_aliases.return_value = ["existing_alias"]

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [conflict_file]

            result = alias_operations._check_alias_conflicts("existing_alias")

            assert result == [str(conflict_file)]

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_normalize_alias")
    def test_check_alias_conflicts_exclude_file(
        self, mock_normalize, mock_get_aliases, alias_operations
    ):
        """Test checking alias conflicts excluding a specific file."""
        mock_normalize.side_effect = lambda x: x.lower()
        exclude_file = Path("/test/vault/notes/test_alias.md")

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [exclude_file]

            result = alias_operations._check_alias_conflicts(
                "test_alias", exclude_file=exclude_file
            )

            assert result == []

    @patch.object(AliasOperations, "_save_note_with_updated_aliases")
    @patch.object(AliasOperations, "_load_note_with_frontmatter")
    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_check_alias_conflicts")
    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch.object(AliasOperations, "_validate_alias")
    def test_add_alias_success(
        self,
        mock_validate,
        mock_resolve,
        mock_check_conflicts,
        mock_get_aliases,
        mock_load,
        mock_save,
        alias_operations,
    ):
        """Test successfully adding an alias."""
        # Arrange
        alias = "new-alias"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_validate.return_value = "new-alias"
        mock_resolve.return_value = file_path
        mock_check_conflicts.return_value = []
        mock_get_aliases.return_value = ["existing-alias"]
        mock_post = Mock()
        mock_frontmatter: dict[str, Any] = {}
        mock_load.return_value = (mock_post, mock_frontmatter)
        mock_save.return_value = file_path

        # Act
        result = alias_operations.add_alias(alias, filename=filename)

        # Assert
        assert result == file_path
        mock_validate.assert_called_with(alias)
        mock_resolve.assert_called_with(alias_operations.config, filename, None, None)
        mock_check_conflicts.assert_called_with("new-alias", exclude_file=file_path)
        mock_save.assert_called_with(
            file_path, mock_post, ["existing-alias", "new-alias"]
        )

    @patch.object(AliasOperations, "_validate_alias")
    def test_add_alias_invalid_alias(self, mock_validate, alias_operations):
        """Test adding invalid alias."""
        mock_validate.side_effect = ValueError("Invalid alias")

        with pytest.raises(ValueError, match="Invalid alias"):
            alias_operations.add_alias("invalid,alias", filename="test")

    @patch.object(AliasOperations, "_check_alias_conflicts")
    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch.object(AliasOperations, "_validate_alias")
    def test_add_alias_conflicts_not_allowed(
        self, mock_validate, mock_resolve, mock_check_conflicts, alias_operations
    ):
        """Test adding alias with conflicts not allowed."""
        mock_validate.return_value = "conflicting-alias"
        mock_resolve.return_value = Path("/test/vault/notes/test.md")
        mock_check_conflicts.return_value = ["/test/vault/notes/conflict.md"]

        with pytest.raises(ValueError, match="Alias 'conflicting-alias' conflicts"):
            alias_operations.add_alias(
                "conflicting-alias", filename="test", allow_conflicts=False
            )

    @patch.object(AliasOperations, "_save_note_with_updated_aliases")
    @patch.object(AliasOperations, "_load_note_with_frontmatter")
    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_check_alias_conflicts")
    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch.object(AliasOperations, "_validate_alias")
    def test_add_alias_already_exists(
        self,
        mock_validate,
        mock_resolve,
        mock_check_conflicts,
        mock_get_aliases,
        mock_load,
        mock_save,
        alias_operations,
    ):
        """Test adding alias that already exists."""
        # Arrange
        alias = "existing-alias"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_validate.return_value = "existing-alias"
        mock_resolve.return_value = file_path
        mock_check_conflicts.return_value = []
        mock_get_aliases.return_value = ["existing-alias"]

        # Mock _normalize_alias to return the same value for comparison
        with patch.object(
            alias_operations, "_normalize_alias", return_value="existing-alias"
        ):
            # Act
            result = alias_operations.add_alias(alias, filename=filename)

            # Assert
            assert result == file_path
            # Should not call save since alias already exists
            mock_save.assert_not_called()

    @patch.object(AliasOperations, "_save_note_with_updated_aliases")
    @patch.object(AliasOperations, "_load_note_with_frontmatter")
    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch.object(AliasOperations, "_normalize_alias")
    def test_remove_alias_success(
        self,
        mock_normalize,
        mock_resolve,
        mock_get_aliases,
        mock_load,
        mock_save,
        alias_operations,
    ):
        """Test successfully removing an alias."""
        # Arrange
        alias = "remove-alias"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_normalize.side_effect = lambda x: x.lower()
        mock_resolve.return_value = file_path
        mock_get_aliases.return_value = ["keep-alias", "remove-alias"]
        mock_post = Mock()
        mock_frontmatter: dict[str, Any] = {}
        mock_load.return_value = (mock_post, mock_frontmatter)
        mock_save.return_value = file_path

        # Act
        result = alias_operations.remove_alias(alias, filename=filename)

        # Assert
        assert result == file_path
        mock_save.assert_called_with(file_path, mock_post, ["keep-alias"])

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch.object(AliasOperations, "_normalize_alias")
    def test_remove_alias_not_found(
        self, mock_normalize, mock_resolve, mock_get_aliases, alias_operations
    ):
        """Test removing alias that doesn't exist."""
        # Arrange
        alias = "nonexistent-alias"
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_normalize.side_effect = lambda x: x.lower()
        mock_resolve.return_value = file_path
        mock_get_aliases.return_value = ["existing-alias"]

        # Act
        result = alias_operations.remove_alias(alias, filename=filename)

        # Assert
        assert result == file_path

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_aliases_success(
        self, mock_exists, mock_resolve, mock_get_aliases, alias_operations
    ):
        """Test successfully getting aliases."""
        # Arrange
        filename = "test_note"
        file_path = Path("/test/vault/notes/test_note.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = True
        mock_get_aliases.return_value = ["alias1", "alias2"]

        # Act
        result = alias_operations.get_aliases(filename=filename)

        # Assert
        assert result == ["alias1", "alias2"]
        mock_resolve.assert_called_with(alias_operations.config, filename, None, None)
        mock_get_aliases.assert_called_with(file_path)

    @patch("minerva.services.alias_operations.resolve_note_file")
    @patch("pathlib.Path.exists")
    def test_get_aliases_file_not_found(
        self, mock_exists, mock_resolve, alias_operations
    ):
        """Test getting aliases when file doesn't exist."""
        filename = "nonexistent"
        file_path = Path("/test/vault/notes/nonexistent.md")

        mock_resolve.return_value = file_path
        mock_exists.return_value = False

        # Due to @safe_operation decorator, returns empty list instead of raising exception
        result = alias_operations.get_aliases(filename=filename)
        assert result == []

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_validate_alias")
    @patch.object(AliasOperations, "_normalize_alias")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.rglob")
    def test_search_by_alias_success(
        self,
        mock_rglob,
        mock_is_dir,
        mock_normalize,
        mock_validate,
        mock_get_aliases,
        alias_operations,
    ):
        """Test successfully searching for notes by alias."""
        # Arrange
        target_alias = "target-alias"
        mock_validate.return_value = "target-alias"
        mock_normalize.side_effect = lambda x: x.lower()
        mock_is_dir.return_value = True
        file1 = Path("/test/vault/notes/note1.md")
        file2 = Path("/test/vault/notes/note2.md")
        mock_rglob.return_value = [file1, file2]
        mock_get_aliases.side_effect = [
            ["alias1", "target-alias"],
            ["alias2", "other-alias"],
        ]

        # Act
        result = alias_operations.search_by_alias(target_alias)

        # Assert
        assert result == [str(file1)]  # Only file1 has the target alias
        mock_validate.assert_called_with(target_alias)

    @patch.object(AliasOperations, "_validate_alias")
    @patch("pathlib.Path.is_dir")
    def test_search_by_alias_directory_not_found(
        self, mock_is_dir, mock_validate, alias_operations
    ):
        """Test searching by alias in nonexistent directory."""
        mock_validate.return_value = "alias"
        mock_is_dir.return_value = False

        with pytest.raises(FileNotFoundError):
            alias_operations.search_by_alias("alias", "/nonexistent")

    @patch.object(AliasOperations, "_get_aliases_from_file")
    @patch.object(AliasOperations, "_validate_alias")
    @patch.object(AliasOperations, "_normalize_alias")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.rglob")
    def test_search_by_alias_with_exception(
        self,
        mock_rglob,
        mock_is_dir,
        mock_normalize,
        mock_validate,
        mock_get_aliases,
        alias_operations,
    ):
        """Test searching by alias when an exception occurs processing a file."""
        # Arrange
        target_alias = "target-alias"
        mock_validate.return_value = "target-alias"
        mock_normalize.side_effect = lambda x: x.lower()
        mock_is_dir.return_value = True
        file1 = Path("/test/vault/notes/note1.md")
        file2 = Path("/test/vault/notes/note2.md")
        mock_rglob.return_value = [file1, file2]
        mock_get_aliases.side_effect = [Exception("Test error"), ["target-alias"]]

        # Act
        result = alias_operations.search_by_alias(target_alias)

        # Assert
        assert result == [str(file2)]  # Only file2 processed successfully


class TestAliasOperationsIntegration:
    """Integration tests for AliasOperations with real file operations."""

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
    def alias_operations(self, config):
        """Create an AliasOperations instance for testing."""
        frontmatter_manager = FrontmatterManager("Test Author")
        return AliasOperations(config, frontmatter_manager)

    def test_resolve_note_file_integration(self, alias_operations):
        """Test file resolution integration using the core function."""
        from minerva.services.core.file_operations import resolve_note_file

        # Test with filename
        result = resolve_note_file(alias_operations.config, "test_note", None, None)
        expected = alias_operations.config.vault_path / "notes" / "test_note.md"
        assert result == expected

        # Test with filepath
        filepath = "/custom/path/note.md"
        result = resolve_note_file(alias_operations.config, None, filepath, None)
        assert result == Path(filepath)

    def test_validate_and_normalize_alias_integration(self, alias_operations):
        """Test alias validation and normalization with real validator."""
        # Test valid alias
        validated = alias_operations._validate_alias("Valid Alias")
        assert validated == "Valid Alias"

        normalized = alias_operations._normalize_alias("Valid Alias")
        assert normalized == "valid alias"

        # Test invalid alias (with forbidden character)
        with pytest.raises(ValueError, match="Alias cannot contain"):
            alias_operations._validate_alias("invalid|alias")
