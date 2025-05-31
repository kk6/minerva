"""Tests for FrontmatterManager class."""

import pytest
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory
import frontmatter

from minerva.frontmatter_manager import FrontmatterManager
from minerva.config import DEFAULT_NOTE_AUTHOR


class TestFrontmatterManagerBasic:
    """Test basic functionality of FrontmatterManager class."""

    def test_initialization_default_author(self):
        """Test FrontmatterManager initialization with default author.

        Arrange:
            - Create FrontmatterManager without author parameter
        Act:
            - Check the default_author attribute
        Assert:
            - Default author should be set to system default
        """
        # ==================== Arrange ====================
        # No specific arrangement needed

        # ==================== Act ====================
        manager = FrontmatterManager()

        # ==================== Assert ====================
        assert manager.default_author == DEFAULT_NOTE_AUTHOR

    def test_initialization_custom_author(self):
        """Test FrontmatterManager initialization with custom author.

        Arrange:
            - Create FrontmatterManager with custom author
        Act:
            - Check the default_author attribute
        Assert:
            - Custom author should be set
        """
        # ==================== Arrange ====================
        custom_author = "Test Author"

        # ==================== Act ====================
        manager = FrontmatterManager(default_author=custom_author)

        # ==================== Assert ====================
        assert manager.default_author == custom_author

    def test_generate_metadata_new_note(self):
        """Test generating metadata for a new note.

        Arrange:
            - Create FrontmatterManager
            - Prepare text content without frontmatter
        Act:
            - Generate metadata for new note
        Assert:
            - Post object should contain correct metadata
            - Created field should be present
            - Author should be set
        """
        # ==================== Arrange ====================
        manager = FrontmatterManager(default_author="Test Author")
        text = "This is test content"

        # ==================== Act ====================
        post = manager.generate_metadata(
            text=text,
            author="Custom Author",
            is_new_note=True,
            existing_frontmatter=None,
            tags=None,
        )

        # ==================== Assert ====================
        assert post.content == text
        assert post.metadata["author"] == "Custom Author"
        assert "created" in post.metadata
        assert "updated" not in post.metadata  # Not set for new notes
        assert isinstance(post.metadata["created"], str)

    def test_generate_metadata_existing_note(self):
        """Test generating metadata for an existing note.

        Arrange:
            - Create FrontmatterManager
            - Prepare text content and existing frontmatter
        Act:
            - Generate metadata for existing note
        Assert:
            - Updated field should be present
            - Created field should be preserved from existing frontmatter
        """
        # ==================== Arrange ====================
        manager = FrontmatterManager(default_author="Test Author")
        text = "This is updated content"
        existing_frontmatter = {
            "created": "2025-01-01T00:00:00",
            "author": "Original Author",
        }

        # ==================== Act ====================
        post = manager.generate_metadata(
            text=text,
            author="Updated Author",
            is_new_note=False,
            existing_frontmatter=existing_frontmatter,
            tags=None,
        )

        # ==================== Assert ====================
        assert post.content == text
        assert post.metadata["author"] == "Updated Author"
        assert post.metadata["created"] == "2025-01-01T00:00:00"
        assert "updated" in post.metadata

    def test_generate_metadata_with_tags(self):
        """Test generating metadata with tags.

        Arrange:
            - Create FrontmatterManager
            - Prepare text content and tags
        Act:
            - Generate metadata with tags
        Assert:
            - Tags should be present and normalized
        """
        # ==================== Arrange ====================
        manager = FrontmatterManager()
        text = "Content with tags"
        tags = ["Python", "testing", "AI"]

        # ==================== Act ====================
        post = manager.generate_metadata(text=text, is_new_note=True, tags=tags)

        # ==================== Assert ====================
        assert "tags" in post.metadata
        assert post.metadata["tags"] == ["python", "testing", "ai"]

    def test_generate_metadata_empty_tags(self):
        """Test generating metadata with empty tags list.

        Arrange:
            - Create FrontmatterManager
            - Prepare text content and empty tags list
        Act:
            - Generate metadata with empty tags
        Assert:
            - Tags field should not be present
        """
        # ==================== Arrange ====================
        manager = FrontmatterManager()
        text = "Content without tags"
        tags: list[str] = []

        # ==================== Act ====================
        post = manager.generate_metadata(text=text, is_new_note=True, tags=tags)

        # ==================== Assert ====================
        assert "tags" not in post.metadata

    def test_read_existing_metadata_with_frontmatter(self):
        """Test reading existing metadata from a file with frontmatter.

        Arrange:
            - Create temporary file with frontmatter
            - Create FrontmatterManager
        Act:
            - Read existing metadata
        Assert:
            - Metadata should be correctly extracted
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
created: '2025-01-01T00:00:00'
tags:
  - test
  - markdown
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            metadata = manager.read_existing_metadata(temp_file)

            # ==================== Assert ====================
            assert metadata is not None
            assert metadata["author"] == "Test Author"
            assert metadata["created"] == "2025-01-01T00:00:00"
            assert metadata["tags"] == ["test", "markdown"]

    def test_read_existing_metadata_no_frontmatter(self):
        """Test reading metadata from a file without frontmatter.

        Arrange:
            - Create temporary file without frontmatter
            - Create FrontmatterManager
        Act:
            - Read existing metadata
        Assert:
            - Empty dict should be returned
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = "This is content without frontmatter"

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            metadata = manager.read_existing_metadata(temp_file)

            # ==================== Assert ====================
            assert metadata == {}

    def test_read_existing_metadata_nonexistent_file(self):
        """Test reading metadata from a nonexistent file.

        Arrange:
            - Create path to nonexistent file
            - Create FrontmatterManager
        Act:
            - Read existing metadata
        Assert:
            - None should be returned
        """
        # ==================== Arrange ====================
        nonexistent_file = Path("/nonexistent/file.md")
        manager = FrontmatterManager()

        # ==================== Act ====================
        metadata = manager.read_existing_metadata(nonexistent_file)

        # ==================== Assert ====================
        assert metadata is None

    def test_update_tags(self):
        """Test updating tags in an existing note.

        Arrange:
            - Create temporary file with frontmatter and tags
            - Create FrontmatterManager
        Act:
            - Update tags
        Assert:
            - File should be updated with new tags
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
tags:
  - old-tag
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()
            new_tags = ["new-tag", "another-tag"]

            # ==================== Act ====================
            manager.update_tags(temp_file, new_tags)

            # ==================== Assert ====================
            with open(temp_file, "r", encoding="utf-8") as f:
                updated_content = f.read()

            post = frontmatter.loads(updated_content)
            assert post.metadata["tags"] == ["new-tag", "another-tag"]
            assert "updated" in post.metadata

    def test_add_tag_new_tag(self):
        """Test adding a new tag to a note.

        Arrange:
            - Create temporary file with existing tags
            - Create FrontmatterManager
        Act:
            - Add new tag
        Assert:
            - New tag should be added to existing tags
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
tags:
  - existing-tag
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            manager.add_tag(temp_file, "new-tag")

            # ==================== Assert ====================
            tags = manager.get_tags(temp_file)
            assert "existing-tag" in tags
            assert "new-tag" in tags

    def test_add_tag_duplicate(self):
        """Test adding a tag that already exists.

        Arrange:
            - Create temporary file with existing tag
            - Create FrontmatterManager
        Act:
            - Add existing tag
        Assert:
            - Tag should not be duplicated
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
tags:
  - existing-tag
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            manager.add_tag(temp_file, "existing-tag")

            # ==================== Assert ====================
            tags = manager.get_tags(temp_file)
            assert tags.count("existing-tag") == 1

    def test_remove_tag_existing(self):
        """Test removing an existing tag from a note.

        Arrange:
            - Create temporary file with multiple tags
            - Create FrontmatterManager
        Act:
            - Remove one tag
        Assert:
            - Tag should be removed, others should remain
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
tags:
  - tag1
  - tag2
  - tag3
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            manager.remove_tag(temp_file, "tag2")

            # ==================== Assert ====================
            tags = manager.get_tags(temp_file)
            assert "tag1" in tags
            assert "tag2" not in tags
            assert "tag3" in tags

    def test_remove_tag_nonexistent(self):
        """Test removing a tag that doesn't exist.

        Arrange:
            - Create temporary file with tags
            - Create FrontmatterManager
        Act:
            - Remove nonexistent tag
        Assert:
            - No error should occur, existing tags should remain
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
tags:
  - tag1
  - tag2
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            manager.remove_tag(temp_file, "nonexistent-tag")

            # ==================== Assert ====================
            tags = manager.get_tags(temp_file)
            assert "tag1" in tags
            assert "tag2" in tags

    def test_get_tags_with_tags(self):
        """Test getting tags from a note that has tags.

        Arrange:
            - Create temporary file with tags
            - Create FrontmatterManager
        Act:
            - Get tags
        Assert:
            - Correct tags should be returned
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
tags:
  - tag1
  - tag2
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            tags = manager.get_tags(temp_file)

            # ==================== Assert ====================
            assert tags == ["tag1", "tag2"]

    def test_get_tags_no_tags(self):
        """Test getting tags from a note without tags.

        Arrange:
            - Create temporary file without tags
            - Create FrontmatterManager
        Act:
            - Get tags
        Assert:
            - Empty list should be returned
        """
        # ==================== Arrange ====================
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            content = """---
author: Test Author
---
This is test content"""

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            manager = FrontmatterManager()

            # ==================== Act ====================
            tags = manager.get_tags(temp_file)

            # ==================== Assert ====================
            assert tags == []

    def test_get_tags_nonexistent_file(self):
        """Test getting tags from a nonexistent file.

        Arrange:
            - Create path to nonexistent file
            - Create FrontmatterManager
        Act:
            - Get tags
        Assert:
            - Empty list should be returned
        """
        # ==================== Arrange ====================
        nonexistent_file = Path("/nonexistent/file.md")
        manager = FrontmatterManager()

        # ==================== Act ====================
        tags = manager.get_tags(nonexistent_file)

        # ==================== Assert ====================
        assert tags == []


class TestFrontmatterManagerEdgeCases:
    """Test edge cases and error handling in FrontmatterManager."""

    def test_generate_metadata_with_invalid_tags(self):
        """Test generating metadata with invalid tags."""
        manager = FrontmatterManager()

        # Test with a mix of valid and invalid tags
        text = "Test content"
        tags = ["valid-tag", "invalid,tag", "another-valid"]

        # Mock logger to verify warning
        with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
            post = manager.generate_metadata(text=text, is_new_note=True, tags=tags)

            # Check that invalid tag was logged and dropped
            mock_logger.warning.assert_called_with(
                "Invalid tag '%s' dropped: %s", "invalid,tag", mock.ANY
            )

            # Check that only valid tags were kept
            assert "tags" in post.metadata
            assert len(post.metadata["tags"]) == 2
            assert "valid-tag" in post.metadata["tags"]
            assert "another-valid" in post.metadata["tags"]
            assert "invalid,tag" not in post.metadata["tags"]

    def test_generate_metadata_all_invalid_tags(self):
        """Test generating metadata with all invalid tags."""
        manager = FrontmatterManager()

        # Test with only invalid tags
        text = "Test content"
        tags = ["invalid,tag1", "invalid/tag2"]

        # Mock logger to verify warnings
        with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
            post = manager.generate_metadata(text=text, is_new_note=True, tags=tags)

            # Check that warnings were logged for both tags
            assert mock_logger.warning.call_count == 2

            # Check that tags field is removed when all tags are invalid
            assert "tags" not in post.metadata

    def test_read_existing_metadata_unicode_error(self):
        """Test reading metadata from a file that can't be decoded as text."""
        manager = FrontmatterManager()

        # Mock file that raises UnicodeDecodeError
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = UnicodeDecodeError(
                "utf-8", b"\x80", 0, 1, "invalid start byte"
            )

            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
                    result = manager.read_existing_metadata(Path("/fake/path.md"))

                    # Check warning was logged
                    mock_logger.warning.assert_called_with(
                        "File %s cannot be decoded as text (possibly binary): %s",
                        mock.ANY,
                        mock.ANY,
                    )

                    # Check None is returned
                    assert result is None

    def test_read_existing_metadata_io_error(self):
        """Test reading metadata from a file with IO error."""
        manager = FrontmatterManager()

        # Mock file that raises IOError
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = IOError("Test IO error")

            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
                    result = manager.read_existing_metadata(Path("/fake/path.md"))

                    # Check warning was logged
                    mock_logger.warning.assert_called_with(
                        "I/O or OS error reading existing file %s for metadata: %s",
                        mock.ANY,
                        mock.ANY,
                    )

                    # Check None is returned
                    assert result is None

    def test_read_existing_metadata_generic_exception(self):
        """Test reading metadata with an unexpected exception."""
        manager = FrontmatterManager()

        # Mock file that raises a generic exception
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = Exception("Unexpected error")

            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
                    result = manager.read_existing_metadata(Path("/fake/path.md"))

                    # Check warning was logged
                    mock_logger.warning.assert_called_with(
                        "Unexpected error processing file %s for metadata: %s",
                        mock.ANY,
                        mock.ANY,
                    )

                    # Check None is returned
                    assert result is None

    def test_update_tags_io_error_on_read(self):
        """Test update_tags with IO error during file reading."""
        manager = FrontmatterManager()

        # Mock file that raises IOError on read
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = IOError("Test IO error")

            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
                    with pytest.raises(IOError):
                        manager.update_tags(Path("/fake/path.md"), ["tag1"])

                    # Check error was logged
                    mock_logger.error.assert_called_with(
                        "Error reading file %s: %s", mock.ANY, mock.ANY
                    )

    def test_update_tags_io_error_on_write(self):
        """Test update_tags with IO error during file writing."""
        manager = FrontmatterManager()

        # First mock successful read
        mock_content = "---\ntags: []\n---\nTest content"
        mock_read = mock.mock_open(read_data=mock_content)

        # Then create a mock that fails on second open (for writing)
        def open_effect(*args, **kwargs):
            if "w" in args[1]:  # Writing mode
                raise IOError("Test IO error on write")
            return mock_read()

        with mock.patch("builtins.open", side_effect=open_effect):
            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("minerva.frontmatter_manager.logger") as mock_logger:
                    # Mock read_existing_metadata to return empty dict
                    with mock.patch.object(
                        manager, "read_existing_metadata", return_value={}
                    ):
                        with pytest.raises(IOError):
                            manager.update_tags(Path("/fake/path.md"), ["tag1"])

                        # Check error was logged
                        mock_logger.error.assert_called_with(
                            "Error writing file %s: %s", mock.ANY, mock.ANY
                        )


class TestFrontmatterManagerSpecialCases:
    """Test special cases and specific edge conditions in FrontmatterManager."""

    def test_generate_metadata_with_existing_created_date(self):
        """Test generating metadata with an existing created date."""
        manager = FrontmatterManager()

        # Prepare test data with an existing created date
        existing_frontmatter = {
            "created": "2023-01-01T12:00:00",
            "author": "Original Author",
        }

        # Generate metadata with the existing frontmatter, explicitly providing author
        post = manager.generate_metadata(
            text="Test content",
            is_new_note=True,
            author="Original Author",  # Explicitly set author to match existing
            existing_frontmatter=existing_frontmatter,
        )

        # Verify that the original created date is preserved
        assert post.metadata["created"] == "2023-01-01T12:00:00"

    def test_generate_metadata_with_existing_tags_parameter_none(self):
        """Test generating metadata with existing tags but parameter is None."""
        manager = FrontmatterManager()

        # Prepare test data with existing tags
        existing_frontmatter = {
            "created": "2023-01-01T12:00:00",
            "tags": ["existing-tag1", "existing-tag2"],
        }

        # Generate metadata with existing frontmatter but without specifying tags parameter
        post = manager.generate_metadata(
            text="Test content",
            is_new_note=False,
            existing_frontmatter=existing_frontmatter,
            tags=None,  # Explicitly None to preserve existing tags
        )

        # Verify that existing tags are preserved
        assert "tags" in post.metadata
        assert post.metadata["tags"] == ["existing-tag1", "existing-tag2"]

    def test_generate_metadata_with_empty_tags_list(self):
        """Test generating metadata with empty tags list."""
        manager = FrontmatterManager()

        # Prepare test data with existing tags
        existing_frontmatter = {
            "created": "2023-01-01T12:00:00",
            "tags": ["existing-tag1", "existing-tag2"],
        }

        # Generate metadata with empty tags list (should remove tags)
        post = manager.generate_metadata(
            text="Test content",
            is_new_note=False,
            existing_frontmatter=existing_frontmatter,
            tags=[],  # Empty list to remove tags
        )

        # Verify that tags field is removed
        assert "tags" not in post.metadata
