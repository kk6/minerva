"""
Tests for alias functionality in Minerva.

This module tests the alias management features including adding, removing,
retrieving, and searching aliases in notes.
"""

import pytest
import tempfile
from pathlib import Path
import frontmatter

from minerva.services.service_manager import ServiceManager as MinervaService
from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager


class TestAliasValidation:
    """Test alias validation functionality."""

    def test_validate_alias_valid_cases(self, service_with_temp_dir):
        """Test that valid aliases pass validation."""
        service, _ = service_with_temp_dir

        # These should not raise any exceptions
        service._validate_alias("simple alias")
        service._validate_alias("meeting-notes")
        service._validate_alias("Project Alpha")
        service._validate_alias("a" * 100)  # Maximum length

    def test_validate_alias_invalid_cases(self, service_with_temp_dir):
        """Test that invalid aliases are rejected."""
        service, _ = service_with_temp_dir

        # Empty or whitespace
        with pytest.raises(ValueError, match="cannot be empty"):
            service._validate_alias("")
        with pytest.raises(ValueError, match="cannot be empty"):
            service._validate_alias("   ")

        # Too long
        with pytest.raises(ValueError, match="cannot exceed 100 characters"):
            service._validate_alias("a" * 101)

        # Forbidden characters
        forbidden_chars = ["|", "#", "^", "[", "]"]
        for char in forbidden_chars:
            with pytest.raises(ValueError, match=f"cannot contain '\\{char}'"):
                service._validate_alias(f"alias{char}name")

    def test_normalize_alias(self, service_with_temp_dir):
        """Test alias normalization for comparison."""
        service, _ = service_with_temp_dir

        assert service._normalize_alias("Test Alias") == "test alias"
        assert service._normalize_alias("  spaced  ") == "spaced"
        assert service._normalize_alias("UPPER") == "upper"


class TestAliasOperations:
    """Test basic alias operations on notes."""

    def test_add_alias_to_note_without_frontmatter(self, service_with_temp_dir):
        """Test adding alias to note without existing frontmatter."""
        service, temp_dir = service_with_temp_dir

        # Create note without frontmatter
        note_path = temp_dir / "test_note.md"
        note_path.write_text("This is a simple note without frontmatter.")

        # Add alias
        result_path = service.add_alias("test alias", filename="test_note.md")

        # Verify alias was added
        aliases = service.get_aliases(filename="test_note.md")
        assert "test alias" in aliases
        assert result_path == note_path

    def test_add_alias_to_note_with_existing_frontmatter(self, service_with_temp_dir):
        """Test adding alias to note with existing frontmatter."""
        service, temp_dir = service_with_temp_dir

        # Create note with frontmatter
        content = """---
author: Test Author
tags:
  - test
---
Content here."""

        note_path = temp_dir / "test_note.md"
        note_path.write_text(content)

        # Add alias
        service.add_alias("new alias", filename="test_note.md")

        # Verify alias was added and existing metadata preserved
        post = frontmatter.loads(note_path.read_text())
        assert "new alias" in post.metadata.get("aliases", [])
        assert post.metadata.get("author") == "Test Author"
        assert "test" in post.metadata.get("tags", [])

    def test_add_multiple_aliases(self, service_with_temp_dir):
        """Test adding multiple aliases to the same note."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Add multiple aliases
        service.add_alias("first alias", filename="test_note.md")
        service.add_alias("second alias", filename="test_note.md")
        service.add_alias("third alias", filename="test_note.md")

        # Verify all aliases are present
        aliases = service.get_aliases(filename="test_note.md")
        assert len(aliases) == 3
        assert "first alias" in aliases
        assert "second alias" in aliases
        assert "third alias" in aliases

    def test_add_duplicate_alias(self, service_with_temp_dir):
        """Test adding duplicate alias (should not create duplicates)."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Add same alias twice
        service.add_alias("test alias", filename="test_note.md")
        service.add_alias("test alias", filename="test_note.md")

        # Should only appear once
        aliases = service.get_aliases(filename="test_note.md")
        assert aliases.count("test alias") == 1

    def test_add_case_insensitive_duplicate(self, service_with_temp_dir):
        """Test adding case-insensitive duplicate alias."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Add aliases with different cases
        service.add_alias("Test Alias", filename="test_note.md")
        service.add_alias("test alias", filename="test_note.md")

        # Should only have one alias (the first one added)
        aliases = service.get_aliases(filename="test_note.md")
        assert len(aliases) == 1
        assert aliases[0] == "Test Alias"  # Preserves original casing

    def test_remove_alias(self, service_with_temp_dir):
        """Test removing an alias from a note."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Add aliases
        service.add_alias("keep this", filename="test_note.md")
        service.add_alias("remove this", filename="test_note.md")

        # Remove one alias
        service.remove_alias("remove this", filename="test_note.md")

        # Verify correct alias was removed
        aliases = service.get_aliases(filename="test_note.md")
        assert "keep this" in aliases
        assert "remove this" not in aliases

    def test_remove_nonexistent_alias(self, service_with_temp_dir):
        """Test removing an alias that doesn't exist."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Try to remove non-existent alias (should not raise error)
        result_path = service.remove_alias("nonexistent", filename="test_note.md")
        assert result_path == note_path

    def test_get_aliases_empty(self, service_with_temp_dir):
        """Test getting aliases from note with no aliases."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        aliases = service.get_aliases(filename="test_note.md")
        assert aliases == []

    def test_get_aliases_nonexistent_file(self, service_with_temp_dir):
        """Test getting aliases from non-existent file."""
        service, _ = service_with_temp_dir

        # The @safe_operation decorator returns [] for missing files instead of raising
        # This is the expected behavior for the service layer
        aliases = service.get_aliases(filename="nonexistent.md")
        assert aliases == []


class TestAliasConflicts:
    """Test alias conflict detection and prevention."""

    def test_add_alias_conflicts_with_filename(self, service_with_temp_dir):
        """Test that alias conflicts with existing filename are detected."""
        service, temp_dir = service_with_temp_dir

        # Create two notes
        note1_path = temp_dir / "existing_note.md"
        note1_path.write_text("First note.")

        note2_path = temp_dir / "another_note.md"
        note2_path.write_text("Second note.")

        # Try to add alias that conflicts with existing filename
        with pytest.raises(ValueError, match="conflicts with existing"):
            service.add_alias("existing_note", filename="another_note.md")

    def test_add_alias_conflicts_with_existing_alias(self, service_with_temp_dir):
        """Test that alias conflicts with existing alias are detected."""
        service, temp_dir = service_with_temp_dir

        # Create two notes
        note1_path = temp_dir / "note1.md"
        note1_path.write_text("First note.")

        note2_path = temp_dir / "note2.md"
        note2_path.write_text("Second note.")

        # Add alias to first note
        service.add_alias("shared alias", filename="note1.md")

        # Try to add same alias to second note
        with pytest.raises(ValueError, match="conflicts with existing"):
            service.add_alias("shared alias", filename="note2.md")

    def test_add_alias_allow_conflicts(self, service_with_temp_dir):
        """Test adding alias with conflicts when explicitly allowed."""
        service, temp_dir = service_with_temp_dir

        # Create two notes
        note1_path = temp_dir / "note1.md"
        note1_path.write_text("First note.")

        note2_path = temp_dir / "note2.md"
        note2_path.write_text("Second note.")

        # Add alias to first note
        service.add_alias("shared alias", filename="note1.md")

        # Add same alias to second note with conflicts allowed
        result_path = service.add_alias(
            "shared alias", filename="note2.md", allow_conflicts=True
        )

        # Should succeed
        assert result_path == note2_path
        aliases = service.get_aliases(filename="note2.md")
        assert "shared alias" in aliases

    def test_add_alias_no_self_conflict(self, service_with_temp_dir):
        """Test that adding alias to same file doesn't cause self-conflict."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Add alias
        service.add_alias("test alias", filename="test_note.md")

        # Adding same alias again should not raise conflict error
        result_path = service.add_alias("test alias", filename="test_note.md")
        assert result_path == note_path


class TestAliasSearch:
    """Test searching notes by alias."""

    def test_search_by_alias_single_match(self, service_with_temp_dir):
        """Test searching for alias with single match."""
        service, temp_dir = service_with_temp_dir

        # Create note with alias
        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")
        service.add_alias("unique alias", filename="test_note.md")

        # Search for alias
        results = service.search_by_alias("unique alias")
        assert len(results) == 1
        assert str(note_path) in results

    def test_search_by_alias_multiple_matches(self, service_with_temp_dir):
        """Test searching for alias with multiple matches."""
        service, temp_dir = service_with_temp_dir

        # Create multiple notes with same alias (using allow_conflicts)
        note1_path = temp_dir / "note1.md"
        note1_path.write_text("First note.")
        service.add_alias("common alias", filename="note1.md")

        note2_path = temp_dir / "note2.md"
        note2_path.write_text("Second note.")
        service.add_alias("common alias", filename="note2.md", allow_conflicts=True)

        # Search for alias
        results = service.search_by_alias("common alias")
        assert len(results) == 2
        assert str(note1_path) in results
        assert str(note2_path) in results

    def test_search_by_alias_case_insensitive(self, service_with_temp_dir):
        """Test that alias search is case-insensitive."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")
        service.add_alias("Test Alias", filename="test_note.md")

        # Search with different case
        results = service.search_by_alias("test alias")
        assert len(results) == 1
        assert str(note_path) in results

    def test_search_by_alias_no_matches(self, service_with_temp_dir):
        """Test searching for non-existent alias."""
        service, temp_dir = service_with_temp_dir

        # Create note without the searched alias
        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")
        service.add_alias("different alias", filename="test_note.md")

        # Search for non-existent alias
        results = service.search_by_alias("nonexistent alias")
        assert results == []

    def test_search_by_alias_empty_query(self, service_with_temp_dir):
        """Test searching with empty alias."""
        service, _ = service_with_temp_dir

        with pytest.raises(ValueError, match="cannot be empty"):
            service.search_by_alias("")

    def test_search_by_alias_in_subdirectory(self, service_with_temp_dir):
        """Test searching for alias within specific directory."""
        service, temp_dir = service_with_temp_dir

        # Create subdirectory with note
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        note_path = subdir / "test_note.md"
        note_path.write_text("Test content.")

        # Add alias using relative path
        service.add_alias("subdir alias", filepath=str(note_path))

        # Search within subdirectory
        results = service.search_by_alias("subdir alias", directory=str(subdir))
        assert len(results) == 1
        assert str(note_path) in results

        # Search in wrong directory should find nothing
        other_dir = temp_dir / "other"
        other_dir.mkdir()
        results = service.search_by_alias("subdir alias", directory=str(other_dir))
        assert results == []


class TestAliasIntegration:
    """Test alias functionality integration with other features."""

    def test_aliases_preserved_during_tag_operations(self, service_with_temp_dir):
        """Test that aliases are preserved when modifying tags."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Test content.")

        # Add alias and tag
        service.add_alias("test alias", filename="test_note.md")
        service.add_tag("test-tag", filename="test_note.md")

        # Verify both are present
        aliases = service.get_aliases(filename="test_note.md")
        tags = service.get_tags(filename="test_note.md")
        assert "test alias" in aliases
        assert "test-tag" in tags

        # Remove tag, aliases should remain
        service.remove_tag("test-tag", filename="test_note.md")
        aliases_after = service.get_aliases(filename="test_note.md")
        assert "test alias" in aliases_after

    def test_aliases_preserved_during_note_edit(self, service_with_temp_dir):
        """Test that aliases are preserved when editing note content."""
        service, temp_dir = service_with_temp_dir

        note_path = temp_dir / "test_note.md"
        note_path.write_text("Original content.")

        # Add alias
        service.add_alias("preserved alias", filename="test_note.md")

        # Edit note content
        service.edit_note("New content.", filename="test_note.md")

        # Verify alias is preserved
        aliases = service.get_aliases(filename="test_note.md")
        assert "preserved alias" in aliases

        # Verify content was updated
        content = service.read_note(str(note_path))
        assert "New content." in content


@pytest.fixture
def service_with_temp_dir():
    """Create a MinervaService with a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = MinervaConfig(
            vault_path=temp_path, default_note_dir="", default_author="Test Author"
        )
        frontmatter_manager = FrontmatterManager("Test Author")
        service = MinervaService(config, frontmatter_manager)

        yield service, temp_path
