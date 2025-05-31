"""Demonstration and usage examples for MinervaTestHelper."""

from tests.helpers import MinervaTestHelper


class TestMinervaTestHelperExample:
    """Test class demonstrating usage examples for MinervaTestHelper."""

    def test_basic_note_creation(self, tmp_path, minerva_test_helper):
        """Example of basic note creation.

        Demonstrates a basic test pattern using the new helper.
        """
        # ==================== Arrange ====================
        content = "This is a test note"
        filename = "test_note.md"

        # ==================== Act ====================
        note_path = minerva_test_helper.create_temp_note(tmp_path, filename, content)

        # ==================== Assert ====================
        minerva_test_helper.assert_file_exists(note_path)
        minerva_test_helper.assert_note_content(note_path, content)

    def test_note_with_frontmatter(self, tmp_path, minerva_test_helper):
        """Example of creating a note with frontmatter."""
        # ==================== Arrange ====================
        content = "Note with metadata"
        frontmatter_data = {
            "title": "Test Note",
            "tags": ["test", "example"],
            "author": "Test Author",
        }

        # ==================== Act ====================
        note_path = minerva_test_helper.create_temp_note(
            tmp_path, "metadata_note.md", content, frontmatter_data
        )

        # ==================== Assert ====================
        minerva_test_helper.assert_note_content(note_path, content, frontmatter_data)

        # Check the types of frontmatter fields
        minerva_test_helper.assert_frontmatter_fields(
            note_path, {"title": str, "tags": list, "author": "Test Author"}
        )

    def test_vault_setup_with_sample_notes(self, tmp_path, minerva_test_helper):
        """Example of setting up a Vault environment and creating sample notes."""
        # ==================== Arrange & Act ====================
        vault_dir = minerva_test_helper.setup_test_vault(tmp_path)
        sample_notes = minerva_test_helper.create_sample_notes(vault_dir)

        # ==================== Assert ====================
        # Check Vault directory structure
        assert vault_dir.exists()
        assert (vault_dir / "test_notes").exists()
        assert (vault_dir / "archive").exists()

        # Check sample notes
        assert len(sample_notes) == 2
        for note_path in sample_notes:
            minerva_test_helper.assert_file_exists(note_path)

    def test_migration_from_old_pattern(self, tmp_path):
        """Example of migrating from the old test pattern."""
        # ==================== Old pattern (commented out) ====================
        # file_path = Path(tmp_path) / "old_style.md"
        # with open(file_path, "w", encoding="utf-8") as f:
        #     f.write("Old style content")
        # assert file_path.exists()

        # ==================== New pattern ====================
        # The following instance creation examples serve only as usage examples for MinervaTestHelper.
        # In practice, fixtures (called `minerva_test_helper`) are already provided in conftest.py,
        # so please use those instead.
        helper = MinervaTestHelper()

        note_path = helper.create_temp_note(
            tmp_path, "new_style.md", "New style content"
        )

        helper.assert_file_exists(note_path)
        helper.assert_note_content(note_path, "New style content")

    def test_with_fixture_integration(
        self, test_vault, sample_notes, minerva_test_helper
    ):
        """Example of integration with common fixtures."""
        # ==================== Assert ====================
        # Check Vault structure using test_vault fixture
        assert test_vault.exists()
        assert (test_vault / "test_notes").exists()

        # Check sample notes using sample_notes fixture
        assert len(sample_notes) == 2

        # Check each note's existence
        for note_path in sample_notes:
            minerva_test_helper.assert_file_exists(note_path)

        # Check frontmatter of the first note
        minerva_test_helper.assert_frontmatter_fields(sample_notes[0], {"tags": list})
