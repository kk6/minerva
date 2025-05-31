"""Example test file demonstrating MinervaTestHelper usage.

This file shows how to use the new unified test helpers
and serves as a template for migrating existing tests.
"""

import pytest
from pathlib import Path


class TestMinervaTestHelperExample:
    """Example test class using MinervaTestHelper."""

    def test_create_note_with_helper(self, tmp_path, minerva_test_helper):
        """Example: Creating a note using the test helper."""
        # ==================== Arrange ====================
        note_path = minerva_test_helper.create_temp_note(
            tmp_path,
            "example.md",
            "This is an example note",
            {"tags": ["example"], "author": "Test Author"}
        )

        # ==================== Act ====================
        # File should exist
        content = note_path.read_text()

        # ==================== Assert ====================
        minerva_test_helper.assert_file_exists(note_path)
        minerva_test_helper.assert_note_content(
            note_path,
            "This is an example note",
            {"tags": ["example"], "author": "Test Author"}
        )

    def test_frontmatter_validation(self, tmp_path, minerva_test_helper):
        """Example: Validating frontmatter fields."""
        # ==================== Arrange ====================
        note_path = minerva_test_helper.create_temp_note(
            tmp_path,
            "frontmatter_example.md",
            "Content with metadata",
            {
                "tags": ["tag1", "tag2"],
                "author": "Test Author",
                "created": "2025-01-01T12:00:00",
                "priority": 5
            }
        )

        # ==================== Act & Assert ====================
        minerva_test_helper.assert_frontmatter_fields(
            note_path,
            {
                "author": "Test Author",
                "tags": ["tag1", "tag2"],
                "priority": 5,
                "created": str,  # Type check
            }
        )

    def test_sample_notes_fixture(self, sample_notes, minerva_test_helper):
        """Example: Using the sample_notes fixture."""
        # ==================== Arrange ====================
        # sample_notes fixture provides pre-created notes

        # ==================== Act ====================
        note_count = len(sample_notes)

        # ==================== Assert ====================
        assert note_count > 0, "Should have created sample notes"
        
        # Verify all notes exist
        for note_path in sample_notes:
            minerva_test_helper.assert_file_exists(note_path)

    def test_vault_setup(self, tmp_path, minerva_test_helper):
        """Example: Setting up a test vault."""
        # ==================== Arrange & Act ====================
        vault_path = minerva_test_helper.setup_test_vault(tmp_path)

        # ==================== Assert ====================
        assert vault_path.exists()
        assert (vault_path / "notes").exists()
        assert (vault_path / "archive").exists()
        assert (vault_path / "templates").exists()

    def test_migration_example_old_vs_new(self, tmp_path, minerva_test_helper):
        """Example: Comparison of old vs new test patterns."""
        
        # ==================== Old Pattern ====================
        # old_note = tmp_path / "old.md"
        # with open(old_note, "w") as f:
        #     f.write("---\nauthor: Test\n---\nContent")
        # content = old_note.read_text()
        # assert "Content" in content
        
        # ==================== New Pattern ====================
        new_note = minerva_test_helper.create_temp_note(
            tmp_path,
            "new.md",
            "Content",
            {"author": "Test"}
        )
        
        minerva_test_helper.assert_note_content(
            new_note,
            "Content",
            {"author": "Test"}
        )

    def test_backward_compatibility_fixtures(self, temp_dir, mock_write_setup):
        """Example: Using legacy fixtures alongside new helpers."""
        # ==================== Arrange ====================
        # temp_dir and mock_write_setup are legacy fixtures from conftest.py
        # They still work for backward compatibility
        
        # ==================== Act & Assert ====================
        assert Path(temp_dir).exists()
        assert "mock_write_file" in mock_write_setup
        assert "tmp_path" in mock_write_setup