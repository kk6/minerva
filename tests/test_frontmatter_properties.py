"""
Property-based tests for FrontmatterManager using Hypothesis.

This module contains property-based tests to discover edge cases in frontmatter
processing, tag validation, and metadata generation that might not be caught
by traditional unit tests.
"""

import string
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import given, assume, strategies as st
import frontmatter

from minerva.frontmatter_manager import FrontmatterManager


class TestFrontmatterManagerProperties:
    """Property-based tests for FrontmatterManager class."""

    @given(st.text(min_size=1, max_size=100))
    def test_generate_metadata_preserves_content(self, content: str):
        """Property: generate_metadata should preserve content regardless of input."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        # Exclude frontmatter delimiters to avoid parsing confusion
        assume("---" not in content)

        # Act
        result = manager.generate_metadata(content)

        # Assert
        assert result.content == content

    @given(
        st.text(min_size=0, max_size=50, alphabet=string.ascii_letters + string.digits)
    )
    def test_generate_metadata_always_adds_author(self, author_name: str):
        """Property: generate_metadata should always add author when provided."""
        # Arrange
        manager = FrontmatterManager()
        content = "Test content"
        assume(author_name.strip())  # Exclude empty authors

        # Act
        result = manager.generate_metadata(content, author=author_name)

        # Assert
        assert "author" in result.metadata
        assert result.metadata["author"] == author_name

    @given(st.text(min_size=1, max_size=100))
    def test_generate_metadata_new_note_gets_created_timestamp(self, content: str):
        """Property: new notes should always get a 'created' timestamp."""
        # Arrange
        manager = FrontmatterManager("Test Author")

        # Act
        result = manager.generate_metadata(content, is_new_note=True)

        # Assert
        assert "created" in result.metadata
        # Should be a valid ISO format timestamp
        created_value = result.metadata["created"]
        assert isinstance(created_value, str)
        datetime.fromisoformat(created_value)

    @given(st.text(min_size=1, max_size=100))
    def test_generate_metadata_existing_note_gets_updated_timestamp(self, content: str):
        """Property: existing notes should always get an 'updated' timestamp."""
        # Arrange
        manager = FrontmatterManager("Test Author")

        # Act
        result = manager.generate_metadata(content, is_new_note=False)

        # Assert
        assert "updated" in result.metadata
        # Should be a valid ISO format timestamp
        updated_value = result.metadata["updated"]
        assert isinstance(updated_value, str)
        datetime.fromisoformat(updated_value)

    @given(
        st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=string.ascii_letters + string.digits + "-_",
            ),
            min_size=0,
            max_size=10,
        )
    )
    def test_generate_metadata_processes_valid_tags(self, tags: list[str]):
        """Property: valid tags should be processed and normalized."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        content = "Test content"
        # Filter out any tags that might be invalid
        valid_tags = [tag for tag in tags if tag.strip()]
        assume(len(valid_tags) > 0)  # Only test with at least one valid tag

        # Act
        result = manager.generate_metadata(content, tags=valid_tags)

        # Assert
        if valid_tags:
            assert "tags" in result.metadata
            result_tags = result.metadata["tags"]
            assert isinstance(result_tags, list)
            # All result tags should be normalized (lowercase, stripped)
            for tag in result_tags:
                assert tag == tag.lower().strip()

    @given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
    def test_generate_metadata_empty_tags_removes_tags_field(self, _: list[str]):
        """Property: providing empty tags list should remove tags field."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        content = "Test content"
        empty_tags: list[str] = []

        # Act
        result = manager.generate_metadata(content, tags=empty_tags)

        # Assert
        assert "tags" not in result.metadata

    @given(st.text(min_size=1, max_size=100))
    def test_generate_metadata_with_existing_frontmatter_preserves_custom_fields(
        self, content: str
    ):
        """Property: existing custom fields should be preserved."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        existing_metadata = {
            "custom_field": "custom_value",
            "another_field": 42,
            "created": "2023-01-01T00:00:00",
        }

        # Act
        result = manager.generate_metadata(
            content, existing_frontmatter=existing_metadata, is_new_note=False
        )

        # Assert
        assert result.metadata["custom_field"] == "custom_value"
        assert result.metadata["another_field"] == 42
        assert (
            result.metadata["created"] == "2023-01-01T00:00:00"
        )  # Should preserve existing created

    @given(st.text(min_size=1, max_size=50, alphabet=string.printable))
    def test_load_post_handles_arbitrary_content(self, content: str):
        """Property: _load_post should handle any printable content."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        # Exclude content that would break YAML parsing
        assume("\x00" not in content)  # Null bytes break YAML
        assume("---\n" not in content[:10])  # Avoid accidental frontmatter

        # Act
        result = manager._load_post(content)

        # Assert
        assert isinstance(result, frontmatter.Post)
        assert result.content == content

    def test_read_existing_metadata_handles_nonexistent_files(self):
        """Property: reading metadata from non-existent files should return None."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        nonexistent_path = Path("/nonexistent/file/path.md")

        # Act
        result = manager.read_existing_metadata(nonexistent_path)

        # Assert
        assert result is None

    @given(st.text(min_size=1, max_size=100))
    def test_read_existing_metadata_handles_files_without_frontmatter(
        self, content: str
    ):
        """Property: files without frontmatter should return empty dict."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        # Ensure content doesn't accidentally create frontmatter
        assume(not content.startswith("---\n"))

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text(content, encoding="utf-8")

            # Act
            result = manager.read_existing_metadata(test_file)

            # Assert
            assert result == {}

    @given(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=string.ascii_letters + string.digits + "-_",
        )
    )
    def test_add_tag_creates_file_operations(self, tag: str):
        """Property: add_tag should work with any valid tag."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        assume(tag.strip())  # Only test non-empty tags

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("# Test Note\n\nContent", encoding="utf-8")

            # Act
            manager.add_tag(test_file, tag)

            # Assert
            tags = manager.get_tags(test_file)
            normalized_tag = tag.strip().lower()
            normalized_existing = [t.strip().lower() for t in tags]
            assert normalized_tag in normalized_existing

    @given(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=string.ascii_letters + string.digits + "-_",
        )
    )
    def test_remove_tag_handles_nonexistent_tags(self, tag: str):
        """Property: removing non-existent tags should not cause errors."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        assume(tag.strip())

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("# Test Note\n\nContent", encoding="utf-8")

            # Act & Assert - should not raise
            manager.remove_tag(test_file, tag)

    @given(
        st.lists(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=string.ascii_letters + string.digits + "-_",
            ),
            min_size=1,
            max_size=5,
        )
    )
    def test_update_tags_replaces_all_tags(self, tags: list[str]):
        """Property: update_tags should replace all existing tags."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        valid_tags = [tag for tag in tags if tag.strip()]
        assume(len(valid_tags) > 0)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            # Create file with some initial tags
            initial_content = """---
tags: ["old-tag", "another-old-tag"]
---
# Test Note

Content"""
            test_file.write_text(initial_content, encoding="utf-8")

            # Act
            manager.update_tags(test_file, valid_tags)

            # Assert
            result_tags = manager.get_tags(test_file)
            # Should contain our new tags (possibly normalized)
            assert len(result_tags) == len(
                set(tag.strip().lower() for tag in valid_tags)
            )

    def test_get_tags_returns_empty_for_files_without_tags(self):
        """Property: files without tags should return empty list."""
        # Arrange
        manager = FrontmatterManager("Test Author")

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("# Test Note\n\nContent", encoding="utf-8")

            # Act
            result = manager.get_tags(test_file)

            # Assert
            assert result == []

    @given(st.text(min_size=1, max_size=100))
    def test_generate_metadata_handles_yaml_special_characters(self, content: str):
        """Property: content with YAML special characters should be handled safely."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        # Add some YAML special characters to test
        yaml_special_content = f"{content}: [test] {{key}}: value"

        # Act & Assert - should not raise YAML parsing errors
        result = manager.generate_metadata(yaml_special_content)
        assert result.content == yaml_special_content


class TestFrontmatterManagerTagProperties:
    """Property-based tests specifically for tag-related operations."""

    @given(
        st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=string.ascii_letters + string.digits + "-_",
            ),
            min_size=2,
            max_size=5,
        )
    )
    def test_tag_operations_are_case_insensitive(self, tags: list[str]):
        """Property: tag operations should be case-insensitive."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        assume(len(tags) >= 2)
        base_tag = tags[0].strip()
        assume(base_tag)

        # Create variations of the same tag with different cases
        tag_lower = base_tag.lower()
        tag_upper = base_tag.upper()
        tag_mixed = "".join(
            c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(base_tag)
        )

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("# Test Note\n\nContent", encoding="utf-8")

            # Act
            manager.add_tag(test_file, tag_lower)
            manager.add_tag(test_file, tag_upper)  # Should not duplicate
            manager.add_tag(test_file, tag_mixed)  # Should not duplicate

            # Assert
            result_tags = manager.get_tags(test_file)
            normalized_tags = [tag.strip().lower() for tag in result_tags]
            # Should only have one instance of the tag (case-insensitive)
            assert normalized_tags.count(base_tag.lower()) == 1

    @given(
        st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits)
    )
    def test_tag_normalization_is_idempotent(self, tag: str):
        """Property: tag normalization should be idempotent."""
        # Arrange
        manager = FrontmatterManager("Test Author")
        assume(tag.strip())

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("# Test Note\n\nContent", encoding="utf-8")

            # Act
            manager.add_tag(test_file, tag)
            tags_after_first = manager.get_tags(test_file)

            # Add the same tag again
            manager.add_tag(test_file, tag)
            tags_after_second = manager.get_tags(test_file)

            # Assert
            assert tags_after_first == tags_after_second  # Should be identical
