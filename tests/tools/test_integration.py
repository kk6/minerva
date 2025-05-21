from unittest import mock
import time

import pytest
import frontmatter

from minerva import tools


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
            - Write a note and get the file path
            - Read the note from the same path
        Assert:
            - File exists on disk
            - Content read from the file matches what was written (after parsing frontmatter)
        """
        # Arrange
        test_content = "This is a test note"

        # Act - Part 1: Writing
        file_path = tools.write_note(
            text=test_content, filename="integration_test", is_overwrite=False
        )

        # Assert - Part 1: File was created
        assert file_path.exists()

        # Act - Part 2: Reading
        content = tools.read_note(str(file_path))

        # Assert - Part 2: Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_search_notes(self, setup_vault):
        """Test searching notes in the vault."""
        # Search case sensitive
        results1 = tools.search_notes(query="apple", case_sensitive=True)
        assert len(results1) == 1
        assert "note1.md" in results1[0].file_path

        # Search case insensitive
        results2 = tools.search_notes(query="apple", case_sensitive=False)
        assert len(results2) == 2

        # Verify both files are found (note1 and note3)
        found_files = [result.file_path for result in results2]
        assert any("note1.md" in path for path in found_files)
        assert any("note3.md" in path for path in found_files)

    def test_integration_write_with_overwrite(self, setup_vault):
        """Test overwriting an existing note."""

        # Create initial note
        initial_content = "Initial content"
        filename = "overwrite_test"

        file_path = tools.write_note(
            text=initial_content, filename=filename, is_overwrite=False
        )
        assert file_path.exists()

        # Try to overwrite with is_overwrite=False (should fail)
        with pytest.raises(Exception):
            tools.write_note(text="New content", filename=filename, is_overwrite=False)

        # Verify content is still the original
        content = tools.read_note(str(file_path))

        # Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == initial_content

        # Overwrite with is_overwrite=True (should succeed)
        new_content = "New content"
        tools.write_note(text=new_content, filename=filename, is_overwrite=True)

        # Verify content is updated
        content = tools.read_note(str(file_path))
        post = frontmatter.loads(content)
        assert post.content == new_content

    def test_edge_case_empty_file(self, setup_vault):
        """Test reading and searching an empty file."""
        vault_path = setup_vault

        # Create an empty file
        empty_file = vault_path / "empty.md"
        empty_file.touch()

        # Read empty file
        content = tools.read_note(str(empty_file))
        assert content == ""

        # Search in empty files
        results = tools.search_notes(query="anything", case_sensitive=True)
        # Empty file should not match any keyword
        assert not any(result.file_path == str(empty_file) for result in results)

    def test_integration_write_to_subdirectory(self, setup_vault):
        """Test for creating a file in a subdirectory"""
        vault_path = setup_vault

        # Create a note with a path that includes a subdirectory
        test_content = "This is a note in a subdirectory"

        file_path = tools.write_note(
            text=test_content, filename="subdir/note_in_subdir", is_overwrite=False
        )

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "subdir" / "note_in_subdir.md"
        assert file_path == expected_path

        # Verify the content of the created file
        content = tools.read_note(str(file_path))

        # Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_write_to_nested_subdirectory(self, setup_vault):
        """Test for creating a file in multiple levels of nested subdirectories"""
        vault_path = setup_vault

        # Create a note with a path that includes multiple levels of subdirectories
        test_content = "This is a note in a nested subdirectory"

        file_path = tools.write_note(
            text=test_content,
            filename="level1/level2/level3/deep_note",
            is_overwrite=False,
        )

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "level1" / "level2" / "level3" / "deep_note.md"
        assert file_path == expected_path

        # Verify the content of the created file
        content = tools.read_note(str(file_path))

        # Parse frontmatter and check content
        post = frontmatter.loads(content)
        assert post.content == test_content

    def test_integration_subdirectory_creation(self, setup_vault):
        """Test to verify that non-existent subdirectories are automatically created"""
        vault_path = setup_vault

        # Subdirectory path
        subdir_path = vault_path / "auto_created_dir"

        # Verify that the subdirectory does not exist
        assert not subdir_path.exists()

        file_path = tools.write_note(
            text="Testing automatic directory creation",
            filename="auto_created_dir/auto_note",
            is_overwrite=False,
        )

        # Verify that the subdirectory was automatically created
        assert subdir_path.exists()
        assert subdir_path.is_dir()

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = subdir_path / "auto_note.md"
        assert file_path == expected_path

    def test_integration_write_with_frontmatter(self, setup_vault):
        """Test writing a note with frontmatter."""

        file_path = tools.write_note(
            text="This is a test note with frontmatter",
            filename="frontmatter_test",
            is_overwrite=False,
            author="Integration Test",
        )
        assert file_path.exists()

        # Read the file and verify frontmatter
        with open(file_path, "r") as f:
            content = f.read()

        # Verify frontmatter exists
        assert content.startswith("---")

        # Parse frontmatter
        post = frontmatter.loads(content)
        assert post.metadata["author"] == "Integration Test"
        assert post.content == "This is a test note with frontmatter"

    def test_integration_write_with_default_dir(self, setup_vault):
        """Test writing a note using the default directory."""
        vault_path = setup_vault

        file_path = tools.write_note(
            text="This is a note in the default directory",
            filename="default_dir_note",
            is_overwrite=False,
            default_path="default_notes",
        )
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "default_notes" / "default_dir_note.md"
        assert file_path == expected_path

        # Verify the content of the created file
        content = tools.read_note(str(file_path))

        # Parse frontmatter
        post = frontmatter.loads(content)
        assert post.content == "This is a note in the default directory"

    def test_integration_create_note(self, setup_vault):
        """Integration test for creating a new note."""
        vault_path = setup_vault
        filename = "create_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        test_content = "This is a new note created with create_note"

        # Create a new note
        created_path = tools.create_note(
            text=test_content,
            filename=filename,
            author="Create Test",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file was created at the expected path
        assert created_path.exists()
        assert created_path == file_path

        # Read the content back and verify
        content = tools.read_note(str(created_path))
        post = frontmatter.loads(content)
        assert post.content == test_content
        assert post.metadata["author"] == "Create Test"

        # Attempt to create the same note again (should fail)
        with pytest.raises(FileExistsError):
            tools.create_note(
                text="This should fail",
                filename=filename,
                default_path="",  # Set to empty string to avoid subdirectory creation
            )

    def test_integration_edit_note(self, setup_vault):
        """Integration test for editing an existing note."""
        vault_path = setup_vault
        filename = "edit_test"
        file_path = vault_path / f"{filename}.md"

        # Create an initial note with write_note
        initial_content = "Initial note content"
        tools.write_note(
            text=initial_content,
            filename=filename,
            is_overwrite=False,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file exists with initial content
        assert file_path.exists()
        initial_read = tools.read_note(str(file_path))
        initial_post = frontmatter.loads(initial_read)
        assert initial_post.content == initial_content

        # Edit the note
        updated_content = "Updated content with edit_note"
        edited_path = tools.edit_note(
            text=updated_content,
            filename=filename,
            author="Editor",
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify file was edited
        assert edited_path == file_path
        updated_read = tools.read_note(str(edited_path))
        updated_post = frontmatter.loads(updated_read)
        assert updated_post.content == updated_content
        assert updated_post.metadata["author"] == "Editor"

    def test_integration_edit_nonexistent_note(self, setup_vault):
        """Integration test verifying edit_note fails for nonexistent notes."""
        nonexistent_filename = "does_not_exist"

        # Attempt to edit a nonexistent note
        with pytest.raises(FileNotFoundError):
            tools.edit_note(
                text="This should fail",
                filename=nonexistent_filename,
                default_path="",  # Set to empty string to avoid subdirectory creation
            )

    def test_integration_create_edit_workflow(self, setup_vault):
        """Integration test for create -> edit workflow."""
        vault_path = setup_vault
        filename = "workflow_test"
        file_path = vault_path / f"{filename}.md"

        # Step 1: Create a new note
        initial_content = "Initial content via create_note"
        tools.create_note(
            text=initial_content,
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify creation worked
        assert file_path.exists()

        # Step 2: Edit the created note
        updated_content = "Updated via edit_note"
        tools.edit_note(
            text=updated_content,
            filename=filename,
            default_path="",  # Set to empty string to avoid subdirectory creation
        )

        # Verify edit worked
        content = tools.read_note(str(file_path))
        post = frontmatter.loads(content)
        assert post.content == updated_content

    def test_integration_date_metadata(self, setup_vault):
        """Integration test for date metadata in frontmatter."""
        vault_path = setup_vault
        filename = "date_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        # Step 1: Create a new note
        test_content = "This is a test for date metadata"
        tools.create_note(
            text=test_content,
            filename=filename,
            default_path="",
        )

        # Verify created date was added
        content1 = tools.read_note(str(file_path))
        post1 = frontmatter.loads(content1)
        assert "created" in post1.metadata
        assert "T" in str(post1.metadata["created"])  # ISO format includes 'T'
        assert "updated" not in post1.metadata  # Should not have updated field yet

        # Wait a short time to ensure distinct timestamps
        time.sleep(0.1)

        # Step 2: Edit the same note
        updated_content = "This content was updated"
        tools.edit_note(
            text=updated_content,
            filename=filename,
            default_path="",
        )

        # Verify updated date was added while preserving created date
        content2 = tools.read_note(str(file_path))
        post2 = frontmatter.loads(content2)
        assert "created" in post2.metadata
        assert "updated" in post2.metadata
        assert "T" in str(post2.metadata["updated"])

        # Created date should be preserved from original creation
        assert post2.metadata["created"] == post1.metadata["created"]
        # Updated date should be different (newer) than created date
        assert post2.metadata["updated"] != post2.metadata["created"]

    def test_integration_write_note_date_handling(self, setup_vault):
        """Integration test for date handling in write_note function."""
        vault_path = setup_vault
        filename = "write_date_test"
        file_path = vault_path / f"{filename}.md"

        # Ensure file doesn't exist initially
        if file_path.exists():
            file_path.unlink()

        # Step 1: Create a new note with write_note
        test_content = "This is a test for write_note date metadata"
        tools.write_note(
            text=test_content,
            filename=filename,
            is_overwrite=False,
            default_path="",
        )

        # Verify created date was added
        content1 = tools.read_note(str(file_path))
        post1 = frontmatter.loads(content1)
        assert "created" in post1.metadata
        assert "T" in str(post1.metadata["created"])  # ISO format includes 'T'
        assert "updated" not in post1.metadata  # Should not have updated field yet

        # Wait a short time to ensure distinct timestamps
        time.sleep(0.1)

        # Step 2: Update the same note with write_note
        updated_content = "This content was updated with write_note"
        tools.write_note(
            text=updated_content,
            filename=filename,
            is_overwrite=True,
            default_path="",
        )

        # Verify updated date was added while preserving created date
        content2 = tools.read_note(str(file_path))
        post2 = frontmatter.loads(content2)
        assert "created" in post2.metadata
        assert "updated" in post2.metadata
        assert "T" in str(post2.metadata["updated"])

        # Created date should be preserved from original creation
        assert post2.metadata["created"] == post1.metadata["created"]
        # Updated date should be different (newer) than created date
        assert post2.metadata["updated"] != post2.metadata["created"]
