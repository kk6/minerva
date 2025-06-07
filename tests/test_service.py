"""
Tests for the MinervaService class and dependency injection functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from minerva.config import MinervaConfig
from minerva.service import MinervaService, create_minerva_service
from minerva.frontmatter_manager import FrontmatterManager


class TestMinervaConfig:
    """Test MinervaConfig class functionality."""

    def test_from_env_valid(self):
        """Test configuration creation from valid environment variables."""
        with patch.dict(
            "os.environ",
            {
                "OBSIDIAN_VAULT_ROOT": "/test/vault",
                "DEFAULT_VAULT": "test_vault",
                "DEFAULT_NOTE_DIR": "notes",
                "DEFAULT_NOTE_AUTHOR": "Test Author",
            },
        ):
            config = MinervaConfig.from_env()

            assert config.vault_path == Path("/test/vault/test_vault")
            assert config.default_note_dir == "notes"
            assert config.default_author == "Test Author"
            assert config.encoding == "utf-8"

    def test_from_env_missing_required(self):
        """Test configuration creation with missing required environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="Required environment variables not set"
            ):
                MinervaConfig.from_env()

    def test_from_env_defaults(self):
        """Test configuration creation with defaults for optional variables."""
        with patch.dict(
            "os.environ",
            {"OBSIDIAN_VAULT_ROOT": "/test/vault", "DEFAULT_VAULT": "test_vault"},
            clear=True,
        ):
            config = MinervaConfig.from_env()

            assert config.default_note_dir == "default_notes"
            assert config.default_author == "Minerva"

    def test_from_legacy_globals(self):
        """Test configuration creation from legacy globals."""
        with patch("minerva.config.VAULT_PATH", Path("/legacy/path")):
            with patch("minerva.config.DEFAULT_NOTE_DIR", "legacy_notes"):
                with patch("minerva.config.DEFAULT_NOTE_AUTHOR", "Legacy Author"):
                    config = MinervaConfig.from_legacy_globals()

                    assert config.vault_path == Path("/legacy/path")
                    assert config.default_note_dir == "legacy_notes"
                    assert config.default_author == "Legacy Author"


class TestMinervaService:
    """Test MinervaService class functionality."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return MinervaConfig(
            vault_path=Path("/test/vault"),
            default_note_dir="test_notes",
            default_author="Test Author",
        )

    @pytest.fixture
    def frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def service(self, config, frontmatter_manager):
        """Create a MinervaService instance for testing."""
        return MinervaService(config, frontmatter_manager)

    def test_init(self, config, frontmatter_manager):
        """Test MinervaService initialization."""
        service = MinervaService(config, frontmatter_manager)

        assert service.config == config
        assert service.frontmatter_manager == frontmatter_manager

    def test_build_file_path_simple(self, service):
        """Test file path building with simple filename."""
        dir_path, filename = service._build_file_path("test_note")

        expected_path = Path("/test/vault/test_notes")
        assert dir_path == expected_path
        assert filename == "test_note.md"

    def test_build_file_path_with_md_extension(self, service):
        """Test file path building with .md extension already present."""
        dir_path, filename = service._build_file_path("test_note.md")

        expected_path = Path("/test/vault/test_notes")
        assert dir_path == expected_path
        assert filename == "test_note.md"

    def test_build_file_path_with_subdirs(self, service):
        """Test file path building with subdirectories."""
        dir_path, filename = service._build_file_path("subdir/test_note")

        expected_path = Path("/test/vault/test_notes/subdir")
        assert dir_path == expected_path
        assert filename == "test_note.md"

    def test_build_file_path_custom_default(self, service):
        """Test file path building with custom default path."""
        dir_path, filename = service._build_file_path("test_note", "custom_dir")

        expected_path = Path("/test/vault/custom_dir")
        assert dir_path == expected_path
        assert filename == "test_note.md"

    def test_build_file_path_empty_filename(self, service):
        """Test file path building with empty filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            service._build_file_path("")

    @patch("minerva.file_handler.write_file")
    @patch("frontmatter.dumps")
    def test_create_note(self, mock_dumps, mock_write_file, service):
        """Test note creation."""
        # Arrange
        mock_dumps.return_value = "content with frontmatter"
        mock_write_file.return_value = Path("/test/vault/test_notes/test.md")
        service.frontmatter_manager.read_existing_metadata.return_value = None
        service.frontmatter_manager.generate_metadata.return_value = Mock()

        # Act
        result = service.create_note("test content", "test")

        # Assert
        assert result == Path("/test/vault/test_notes/test.md")
        service.frontmatter_manager.generate_metadata.assert_called_once()
        mock_write_file.assert_called_once()

    @patch("minerva.file_handler.write_file")
    @patch("frontmatter.dumps")
    def test_edit_note_existing(self, mock_dumps, mock_write_file, service):
        """Test editing an existing note."""
        # Arrange
        mock_dumps.return_value = "updated content with frontmatter"
        mock_write_file.return_value = Path("/test/vault/test_notes/test.md")
        service.frontmatter_manager.read_existing_metadata.return_value = {
            "author": "Test"
        }
        service.frontmatter_manager.generate_metadata.return_value = Mock()

        with patch("pathlib.Path.exists", return_value=True):
            # Act
            result = service.edit_note("updated content", "test")

            # Assert
            assert result == Path("/test/vault/test_notes/test.md")
            service.frontmatter_manager.generate_metadata.assert_called_once()

    def test_edit_note_not_found(self, service):
        """Test editing a non-existent note."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                service.edit_note("content", "nonexistent")

    @patch("minerva.file_handler.read_file")
    def test_read_note(self, mock_read_file, service):
        """Test reading a note."""
        # Arrange
        mock_read_file.return_value = "note content"

        # Act
        result = service.read_note("/test/path/note.md")

        # Assert
        assert result == "note content"
        mock_read_file.assert_called_once()

    def test_search_notes_interface(self, service):
        """Test search notes interface and input validation."""
        # Test that the method exists and has correct signature
        assert hasattr(service, "search_notes")
        assert callable(service.search_notes)

    def test_search_notes_empty_query(self, service):
        """Test searching with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            service.search_notes("")

    def test_get_note_delete_confirmation_with_filename(self, service):
        """Test getting delete confirmation with filename."""
        with patch("pathlib.Path.exists", return_value=True):
            result = service.get_note_delete_confirmation(filename="test")

            assert "file_path" in result
            assert "message" in result
            assert "test.md" in result["file_path"]

    def test_get_note_delete_confirmation_file_not_found(self, service):
        """Test getting delete confirmation for non-existent file."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                service.get_note_delete_confirmation(filename="nonexistent")

    def test_get_note_delete_confirmation_no_params(self, service):
        """Test getting delete confirmation with no parameters."""
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            service.get_note_delete_confirmation()

    @patch("minerva.file_handler.delete_file")
    def test_perform_note_delete(self, mock_delete_file, service):
        """Test performing note deletion."""
        # Arrange
        mock_delete_file.return_value = Path("/test/vault/test_notes/test.md")

        with patch("pathlib.Path.exists", return_value=True):
            # Act
            result = service.perform_note_delete(filename="test")

            # Assert
            assert result == Path("/test/vault/test_notes/test.md")
            mock_delete_file.assert_called_once()

    def test_normalize_tag(self, service):
        """Test tag normalization."""
        with patch(
            "minerva.validators.TagValidator.normalize_tag", return_value="normalized"
        ):
            result = service._normalize_tag("Test Tag")
            assert result == "normalized"

    def test_validate_tag_valid(self, service):
        """Test tag validation for valid tag."""
        with patch("minerva.validators.TagValidator.validate_tag"):
            result = service._validate_tag("valid_tag")
            assert result is True

    def test_validate_tag_invalid(self, service):
        """Test tag validation for invalid tag."""
        with patch(
            "minerva.validators.TagValidator.validate_tag", side_effect=ValueError()
        ):
            result = service._validate_tag("invalid,tag")
            assert result is False

    def test_resolve_note_file_with_filepath(self, service):
        """Test resolving note file with filepath."""
        result = service._resolve_note_file(None, "/test/path/note.md", None)
        assert result == Path("/test/path/note.md")

    def test_resolve_note_file_with_filename(self, service):
        """Test resolving note file with filename."""
        result = service._resolve_note_file("test", None, None)
        expected = Path("/test/vault/test_notes/test.md")
        assert result == expected

    def test_resolve_note_file_no_params(self, service):
        """Test resolving note file with no parameters."""
        with pytest.raises(
            ValueError, match="Either filename or filepath must be provided"
        ):
            service._resolve_note_file(None, None, None)


class TestCreateMinervaService:
    """Test the factory function for creating MinervaService."""

    @patch("minerva.service.MinervaConfig.from_env")
    @patch("minerva.service.FrontmatterManager")
    def test_create_minerva_service(self, mock_fm_class, mock_config_from_env):
        """Test creating MinervaService with factory function."""
        # Arrange
        mock_config = Mock()
        mock_config.default_author = "Test Author"
        mock_config_from_env.return_value = mock_config
        mock_fm = Mock()
        mock_fm_class.return_value = mock_fm

        # Act
        service = create_minerva_service()

        # Assert
        assert isinstance(service, MinervaService)
        assert service.config == mock_config
        assert service.frontmatter_manager == mock_fm
        mock_config_from_env.assert_called_once()
        mock_fm_class.assert_called_once_with("Test Author")


class TestServiceIntegration:
    """Integration tests for service layer functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "test_vault"
        self.vault_path.mkdir(parents=True)

        self.config = MinervaConfig(
            vault_path=self.vault_path,
            default_note_dir="notes",
            default_author="Test Author",
        )

        self.frontmatter_manager = FrontmatterManager("Test Author")
        self.service = MinervaService(self.config, self.frontmatter_manager)

    def teardown_method(self):
        """Clean up test environment."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_and_read_note_integration(self):
        """Test creating and reading a note using the service."""
        # Create a note
        note_path = self.service.create_note("Test content", "integration_test")

        # Verify the note was created
        assert note_path.exists()
        assert "integration_test.md" in str(note_path)

        # Read the note back
        content = self.service.read_note(str(note_path))
        assert "Test content" in content
        assert "author: Test Author" in content

    def test_path_building_integration(self):
        """Test that path building works correctly in real environment."""
        dir_path, filename = self.service._build_file_path("test/nested/note")

        expected_dir = self.vault_path / "notes" / "test" / "nested"
        assert dir_path == expected_dir
        assert filename == "note.md"

    def test_search_notes_integration(self):
        """Test search functionality with real files."""
        # Create test files with content
        note1_path = self.service.create_note("This is a test note", "search_test1")
        note2_path = self.service.create_note("Another document", "search_test2")

        # Search for a term that should match
        results = self.service.search_notes("test")

        # Should find at least one match
        assert len(results) >= 1

        # Clean up
        note1_path.unlink(missing_ok=True)
        note2_path.unlink(missing_ok=True)


class TestMinervaServiceTagOperations:
    """Test MinervaService tag operations with real files."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "test_vault"
        self.vault_path.mkdir(parents=True)

        self.config = MinervaConfig(
            vault_path=self.vault_path,
            default_note_dir="notes",
            default_author="Test Author",
        )

        self.frontmatter_manager = FrontmatterManager("Test Author")
        self.service = MinervaService(self.config, self.frontmatter_manager)

    def teardown_method(self):
        """Clean up test environment."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_tag_operations_integration(self):
        """Test complete tag operations workflow."""
        # Create a note
        note_path = self.service.create_note("Test content", "tag_test")

        # Add tags
        self.service.add_tag("test-tag", filename="tag_test")
        self.service.add_tag("python", filename="tag_test")

        # Get tags
        tags = self.service.get_tags(filename="tag_test")
        assert "test-tag" in tags
        assert "python" in tags

        # Remove a tag
        self.service.remove_tag("test-tag", filename="tag_test")

        # Verify tag was removed
        tags = self.service.get_tags(filename="tag_test")
        assert "test-tag" not in tags
        assert "python" in tags

        # Clean up
        note_path.unlink(missing_ok=True)

    def test_get_tags_nonexistent_file(self):
        """Test getting tags from non-existent file."""
        tags = self.service.get_tags(filename="nonexistent")
        assert tags == []

    def test_add_tag_invalid(self):
        """Test adding invalid tag."""
        # Create a note first
        note_path = self.service.create_note("Test content", "invalid_tag_test")

        # Try to add invalid tag
        with pytest.raises(ValueError):
            self.service.add_tag("invalid,tag", filename="invalid_tag_test")

        # Clean up
        note_path.unlink(missing_ok=True)

    def test_tag_operations_with_filepath(self):
        """Test tag operations using filepath instead of filename."""
        # Create a note
        note_path = self.service.create_note("Test content", "filepath_test")

        # Add tag using filepath
        self.service.add_tag("filepath-tag", filepath=str(note_path))

        # Get tags using filepath
        tags = self.service.get_tags(filepath=str(note_path))
        assert "filepath-tag" in tags

        # Remove tag using filepath
        self.service.remove_tag("filepath-tag", filepath=str(note_path))

        # Verify removal
        tags = self.service.get_tags(filepath=str(note_path))
        assert "filepath-tag" not in tags

        # Clean up
        note_path.unlink(missing_ok=True)


class TestMinervaServiceErrorCases:
    """Test MinervaService error handling."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return MinervaConfig(
            vault_path=Path("/test/vault"),
            default_note_dir="test_notes",
            default_author="Test Author",
        )

    @pytest.fixture
    def frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def service(self, config, frontmatter_manager):
        """Create a MinervaService instance for testing."""
        return MinervaService(config, frontmatter_manager)

    def test_assemble_complete_note_without_author(self, service):
        """Test assembling note without explicit author."""
        service.frontmatter_manager.read_existing_metadata.return_value = None
        service.frontmatter_manager.generate_metadata.return_value = Mock()

        with patch("frontmatter.dumps", return_value="test content"):
            service._assemble_complete_note("test", "note", None, None, True)

            # Should use default author from config
            service.frontmatter_manager.generate_metadata.assert_called_once()
            call_args = service.frontmatter_manager.generate_metadata.call_args
            assert call_args[1]["author"] == "Test Author"

    def test_assemble_complete_note_custom_default_path(self, service):
        """Test assembling note with custom default path."""
        service.frontmatter_manager.read_existing_metadata.return_value = None
        service.frontmatter_manager.generate_metadata.return_value = Mock()

        with patch("frontmatter.dumps", return_value="test content"):
            dir_path, filename, content = service._assemble_complete_note(
                "test", "note", "Author", "custom", True
            )

            expected_path = Path("/test/vault/custom")
            assert dir_path == expected_path

    def test_load_note_with_tags_file_not_found(self, service):
        """Test loading tags from non-existent file."""
        file_path = Path("/nonexistent/file.md")

        with pytest.raises(FileNotFoundError):
            service._load_note_with_tags(file_path)

    def test_save_note_with_updated_tags_no_author(self, service):
        """Test saving note when post has no author."""
        mock_post = Mock()
        mock_post.metadata = {}
        mock_post.content = "test content"

        service.frontmatter_manager.generate_metadata.return_value = mock_post

        with patch("frontmatter.dumps", return_value="content"):
            with patch("minerva.file_handler.write_file") as mock_write:
                mock_write.return_value = Path("/test/path")

                result = service._save_note_with_updated_tags(
                    Path("/test/path"), mock_post, ["tag1"]
                )

                assert result == Path("/test/path")
                mock_write.assert_called_once()


class TestMinervaServiceValidation:
    """Test MinervaService input validation."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return MinervaConfig(
            vault_path=Path("/test/vault"),
            default_note_dir="test_notes",
            default_author="Test Author",
        )

    @pytest.fixture
    def frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def service(self, config, frontmatter_manager):
        """Create a MinervaService instance for testing."""
        return MinervaService(config, frontmatter_manager)

    def test_build_file_path_empty_default_path(self, service):
        """Test building file path with empty default path."""
        dir_path, filename = service._build_file_path("test", "")

        # Should use config's default_note_dir when default_path is empty
        expected_path = Path("/test/vault/test_notes")
        assert dir_path == expected_path
        assert filename == "test.md"

    def test_build_file_path_none_default_path(self, service):
        """Test building file path with None default path."""
        dir_path, filename = service._build_file_path("test", None)

        # Should use config's default_note_dir
        expected_path = Path("/test/vault/test_notes")
        assert dir_path == expected_path
        assert filename == "test.md"

    def test_build_file_path_filename_only_extension(self, service):
        """Test building file path with filename that's only an extension."""
        dir_path, filename = service._build_file_path(".md")

        # Should handle .md as a valid filename
        expected_path = Path("/test/vault/test_notes")
        assert dir_path == expected_path
        assert filename == ".md"


class TestServiceFactoryFunction:
    """Test the service factory function edge cases."""

    @patch("minerva.service.MinervaConfig.from_env")
    @patch("minerva.service.FrontmatterManager")
    def test_create_minerva_service_config_error(
        self, mock_fm_class, mock_config_from_env
    ):
        """Test factory function when config creation fails."""
        mock_config_from_env.side_effect = ValueError("Config error")

        with pytest.raises(ValueError, match="Config error"):
            create_minerva_service()

    @patch("minerva.service.MinervaConfig.from_env")
    @patch("minerva.service.FrontmatterManager")
    def test_create_minerva_service_fm_error(self, mock_fm_class, mock_config_from_env):
        """Test factory function when FrontmatterManager creation fails."""
        mock_config = Mock()
        mock_config.default_author = "Test Author"
        mock_config_from_env.return_value = mock_config
        mock_fm_class.side_effect = Exception("FM error")

        with pytest.raises(Exception, match="FM error"):
            create_minerva_service()
