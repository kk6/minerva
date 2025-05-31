"""Tests for FrontmatterManager class."""

import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import frontmatter

from minerva.frontmatter import FrontmatterManager
from minerva.config import DEFAULT_NOTE_AUTHOR


class TestFrontmatterManager:
    """Test FrontmatterManager class."""

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
            tags=None
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
            "author": "Original Author"
        }

        # ==================== Act ====================
        post = manager.generate_metadata(
            text=text,
            author="Updated Author",
            is_new_note=False,
            existing_frontmatter=existing_frontmatter,
            tags=None
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
        post = manager.generate_metadata(
            text=text,
            is_new_note=True,
            tags=tags
        )

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
        tags = []

        # ==================== Act ====================
        post = manager.generate_metadata(
            text=text,
            is_new_note=True,
            tags=tags
        )

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
