from unittest import mock
import time

import pytest
import frontmatter

from minerva import tools


def test_module():
    """Module level test to ensure pytest collects this file."""
    assert True


class TestIntegrationTests:
    """Integration tests that test the actual file operations."""

    @pytest.fixture
    def setup_vault(self, tmp_path):
        """Set up a temporary vault directory."""
        with mock.patch("minerva.tools.VAULT_PATH", tmp_path):
            # Create some test files in the vault
            (tmp_path / "note1.md").write_text("This is note 1 with keyword apple")
            (tmp_path / "note2.md").write_text("This is note 2 with keyword banana")
            (tmp_path / "note3.md").write_text("This is note 3 with keyword APPLE")
            yield tmp_path

    def test_integration_write_and_read_note(self, setup_vault):
        """Test writing and then reading a note.

        Arrange:
            - Create a write note request with test content
        Act:
            - Create a note and get the file path
            - Read the note from the same path
        Assert:
            - File exists on disk
            - Content read from the file matches what was written (after parsing frontmatter)
        """
        # Arrange
        test_content = "This is a test note"

        # Act - Part 1: Writing
        file_path = tools.create_note(text=test_content, filename="integration_test")

        # Assert - Part 1: File was created
        assert file_path.exists()

        # Act - Part 2: Reading
        content = tools.read_note(str(file_path))

        # Assert - Part 2: Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_write_with_overwrite(self, setup_vault):
        """Test overwriting an existing note."""

        # Create initial note
        initial_content = "Initial content"
        filename = "overwrite_test"

        # Create the initial note
        file_path = tools.create_note(text=initial_content, filename=filename)

        # Verify the initial note was created
        assert file_path.exists()
        initial_note_content = tools.read_note(str(file_path))
        initial_post = frontmatter.loads(initial_note_content)
        assert initial_post.content == initial_content

        # Attempt to create a note with the same name (should fail)
        new_content = "New content that should replace the original"
        with pytest.raises(FileExistsError):
            tools.create_note(text=new_content, filename=filename)

        # Update using edit_note
        file_path = tools.edit_note(text=new_content, filename=filename)

        # Verify the note was updated
        updated_note_content = tools.read_note(str(file_path))
        updated_post = frontmatter.loads(updated_note_content)
        assert updated_post.content == new_content

    def test_integration_write_to_subdirectory(self, setup_vault):
        """Test for creating a file in a subdirectory"""
        vault_path = setup_vault

        # Create a note with a path that includes a subdirectory
        test_content = "This is a note in a subdirectory"

        file_path = tools.create_note(
            text=test_content, filename="subdir/note_in_subdir", default_path=""
        )

        # Verify the file was created in the correct location
        expected_path = vault_path / "subdir" / "note_in_subdir.md"
        assert file_path == expected_path
        assert file_path.exists()

        # Verify the subdirectory was created
        assert (vault_path / "subdir").exists()
        assert (vault_path / "subdir").is_dir()

        # Verify the content was written correctly
        content = tools.read_note(str(file_path))
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_write_to_nested_subdirectory(self, setup_vault):
        """Test for creating a file in multiple levels of nested subdirectories"""
        vault_path = setup_vault

        # Create a note with a path that includes multiple levels of subdirectories
        test_content = "This is a note in a nested subdirectory"

        file_path = tools.create_note(
            text=test_content,
            filename="level1/level2/level3/deep_note",
            default_path="",
        )

        # Verify the file was created in the correct location
        expected_path = vault_path / "level1" / "level2" / "level3" / "deep_note.md"
        assert file_path == expected_path
        assert file_path.exists()

        # Verify the nested subdirectories were created
        assert (vault_path / "level1").exists()
        assert (vault_path / "level1").is_dir()
        assert (vault_path / "level1" / "level2").exists()
        assert (vault_path / "level1" / "level2").is_dir()
        assert (vault_path / "level1" / "level2" / "level3").exists()
        assert (vault_path / "level1" / "level2" / "level3").is_dir()

        # Verify the content was written correctly
        content = tools.read_note(str(file_path))
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_subdirectory_creation(self, setup_vault):
        """Test to verify that non-existent subdirectories are automatically created"""
        vault_path = setup_vault

        # Subdirectory path
        subdir_path = vault_path / "auto_created_dir"

        # Verify that the subdirectory does not exist
        assert not subdir_path.exists()

        file_path = tools.create_note(
            text="Testing automatic directory creation",
            filename="auto_created_dir/auto_note",
            default_path="",
        )

        # Verify that the subdirectory now exists
        assert subdir_path.exists()
        assert subdir_path.is_dir()

        # Verify the file was created
        assert file_path.exists()
        assert file_path == subdir_path / "auto_note.md"

    def test_integration_write_with_frontmatter(self, setup_vault):
        """Test writing a note with frontmatter."""

        file_path = tools.create_note(
            text="This is a test note with frontmatter",
            filename="frontmatter_test",
            author="Integration Test",
        )

        # Verify the file was created
        assert file_path.exists()

        # Read and parse the content
        with open(file_path, "r") as f:
            content = f.read()

        post = frontmatter.loads(content)

        # Verify the frontmatter contains the author
        assert post.metadata["author"] == "Integration Test"

        # Verify it also contains created date (automatically added)
        assert "created" in post.metadata

    def test_integration_write_with_default_dir(self, setup_vault):
        """Test writing a note using the default directory."""
        vault_path = setup_vault

        file_path = tools.create_note(
            text="This is a note in the default directory",
            filename="default_dir_note",
            default_path="default_notes",
        )

        # Verify the file was created in the correct location
        expected_path = vault_path / "default_notes" / "default_dir_note.md"
        assert file_path == expected_path
        assert file_path.exists()

        # Verify the default_notes directory was created
        default_dir = vault_path / "default_notes"
        assert default_dir.exists()
        assert default_dir.is_dir()

    def test_integration_read_nonexistent_note(self, setup_vault):
        """Test reading a note that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            tools.read_note(str(setup_vault / "nonexistent.md"))

    def test_integration_search_notes(self, setup_vault):
        """Test searching notes for a keyword."""
        # Search for 'apple' case-sensitive
        results = tools.search_notes("apple", case_sensitive=True)

        # Should find only note1.md
        assert len(results) == 1
        assert "note1.md" in results[0].file_path

        # Search for 'apple' case-insensitive
        results = tools.search_notes("apple", case_sensitive=False)

        # Should find both note1.md and note3.md
        assert len(results) == 2
        file_paths = [r.file_path for r in results]
        assert any("note1.md" in path for path in file_paths)
        assert any("note3.md" in path for path in file_paths)

    def test_integration_edit_note(self, setup_vault):
        """Integration test for editing an existing note."""
        vault_path = setup_vault
        filename = "edit_test"
        file_path = vault_path / f"{filename}.md"

        # Create an initial note with create_note
        initial_content = "Initial note content"
        tools.create_note(
            text=initial_content,
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file was created with expected content
        assert file_path.exists()
        initial_file_content = tools.read_note(str(file_path))
        initial_post = frontmatter.loads(initial_file_content)
        assert initial_post.content == initial_content

        # Now edit the note
        updated_content = "Updated note content"
        tools.edit_note(
            text=updated_content,
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify the note was updated
        updated_file_content = tools.read_note(str(file_path))
        updated_post = frontmatter.loads(updated_file_content)
        assert updated_post.content == updated_content

        # Verify frontmatter contains updated field
        assert "updated" in updated_post.metadata

    def test_integration_edit_nonexistent_note(self, setup_vault):
        """Integration test for editing a note that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            tools.edit_note(
                text="Attempting to edit a non-existent note",
                filename="nonexistent",
                default_path="",
            )

    def test_integration_create_note_date_handling(self, setup_vault):
        """Integration test for date handling in create_note function."""
        vault_path = setup_vault
        filename = "create_date_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        # Step 1: Create a new note
        test_content = "This is a test for create_note date metadata"
        tools.create_note(
            text=test_content,
            filename=filename,
            default_path="",
        )

        # Read and parse the file
        with open(file_path, "r") as f:
            content = f.read()
        post = frontmatter.loads(content)

        # Verify frontmatter has created date but no updated date
        assert "created" in post.metadata
        assert "updated" not in post.metadata

        # Verify content matches
        assert post.content == test_content

        # Wait a moment to ensure timestamps would be different
        time.sleep(0.1)

        # Step 2: Edit the note
        updated_content = "This is updated content for date handling test"
        tools.edit_note(
            text=updated_content,
            filename=filename,
            default_path="",
        )

        # Read and parse the updated file
        with open(file_path, "r") as f:
            updated_file_content = f.read()
        updated_post = frontmatter.loads(updated_file_content)

        # Verify frontmatter now has both created and updated dates
        assert "created" in updated_post.metadata
        assert "updated" in updated_post.metadata

        # Verify created date is unchanged and updated date is different/newer
        assert updated_post.metadata["created"] == post.metadata["created"]
        assert updated_post.metadata["updated"] != post.metadata["created"]
