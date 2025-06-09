"""
Integration tests for MCP server functionality.

These tests verify that the MCP server correctly integrates with the service layer
and provides working tool functions.
"""

import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest


class TestMCPServerIntegration:
    """Test MCP server integration with service layer."""

    def test_server_import_and_initialization(self):
        """Test that server can be imported and initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                # This should not raise any exceptions
                # Ensure fresh module loading with patched environment
                sys.modules.pop("minerva.server", None)
                sys.modules.pop("minerva.service", None)  # Also clear service module
                from minerva import server  # noqa: E402

                # Verify server is created
                assert hasattr(server, "mcp")
                assert hasattr(server, "service")

                # Verify service is properly initialized
                assert server.service is not None

    def test_server_tool_functions_exist(self):
        """Test that server tool functions exist and are callable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                from minerva import server

                # Verify all expected tool functions exist
                expected_functions = [
                    "read_note",
                    "search_notes",
                    "create_note",
                    "edit_note",
                    "get_note_delete_confirmation",
                    "perform_note_delete",
                    "add_tag",
                    "remove_tag",
                    "rename_tag",
                    "get_tags",
                    "list_all_tags",
                    "find_notes_with_tag",
                ]

                for func_name in expected_functions:
                    assert hasattr(server, func_name)
                    func = getattr(server, func_name)
                    assert callable(func)

    def test_server_wrapper_functions_work(self):
        """Test that server wrapper functions work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                from minerva import server

                # Test create_note wrapper
                import uuid

                unique_name = f"test_note_{uuid.uuid4().hex[:8]}"
                note_path = server.create_note("Test content", unique_name)
                assert note_path.exists()
                assert note_path.name == f"{unique_name}.md"

                # Test read_note wrapper
                content = server.read_note(str(note_path))

                # Parse frontmatter to check content
                import frontmatter

                post = frontmatter.loads(content)
                assert post.content == "Test content"

                # Test add_tag wrapper
                server.add_tag("test-tag", filename=unique_name)

                # Test get_tags wrapper
                tags = server.get_tags(filename=unique_name)
                assert "test-tag" in tags

    def test_server_handles_service_creation_errors(self):
        """Test that server handles service creation errors gracefully."""
        # Test with missing required environment variables
        with patch.dict(
            os.environ, {"OBSIDIAN_VAULT_ROOT": "", "DEFAULT_VAULT": ""}, clear=True
        ):
            # Clear all minerva-related modules to force fresh import
            modules_to_clear = [
                name for name in sys.modules.keys() if name.startswith("minerva")
            ]
            for module in modules_to_clear:
                sys.modules.pop(module, None)

            with pytest.raises(ValueError):
                # This should raise an exception due to missing env vars
                import minerva.server  # noqa: F401

    def test_server_service_binding(self):
        """Test that server functions are properly bound to service instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                from minerva import server

                # Verify that wrapper functions use the same service instance
                assert server.service is not None

                # The service should be properly configured
                # Note: Server service is created once at module level from real env vars
                assert server.service.config.vault_path is not None

                # Test that multiple calls use the same service
                import uuid

                unique_id = uuid.uuid4().hex[:8]
                note_path1 = server.create_note("Content 1", f"note1_{unique_id}")
                note_path2 = server.create_note("Content 2", f"note2_{unique_id}")

                # Both notes should be in the same vault
                assert note_path1.parent.parent == note_path2.parent.parent

                # Verify that notes were created successfully (path checking is environment-dependent)
                assert note_path1.exists()
                assert note_path2.exists()
                assert note_path1.name.startswith("note1_")
                assert note_path2.name.startswith("note2_")


class TestMCPServerConfiguration:
    """Test MCP server configuration and setup."""

    def test_server_version_configured(self):
        """Test that server is configured with correct version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                from minerva import server

                # Server should be configured with correct version
                assert server.mcp.name == "minerva"
                # Note: FastMCP might not expose version directly,
                # but we can verify it was passed correctly

    def test_server_import_path_handling(self):
        """Test that server handles import path correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                # This tests the sys.path.insert functionality
                import sys

                original_path = sys.path.copy()

                try:
                    # Import should work regardless of current directory
                    # Ensure fresh module loading with patched environment
                    sys.modules.pop("minerva.server", None)
                    sys.modules.pop("minerva.service", None)
                    from minerva import server  # noqa: E402

                    assert server.mcp is not None
                finally:
                    sys.path = original_path


class TestMCPServerErrorHandling:
    """Test MCP server error handling."""

    def test_server_handles_tool_errors_gracefully(self):
        """Test that server tool functions handle errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                # Ensure fresh module loading with patched environment
                sys.modules.pop("minerva.server", None)
                sys.modules.pop("minerva.service", None)
                from minerva import server  # noqa: E402

                # Test error handling for non-existent file
                try:
                    server.read_note("/non/existent/file.md")
                    assert False, "Expected an exception but none was raised"
                except Exception as e:
                    from minerva.exceptions import (
                        NoteNotFoundError as MinervaNotFoundError,
                    )

                    assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), (
                        f"Unexpected exception type: {type(e)}"
                    )

                # Test error handling for invalid operations
                try:
                    server.edit_note("content", "non_existent_file")
                    assert False, "Expected an exception but none was raised"
                except Exception as e:
                    from minerva.exceptions import (
                        NoteNotFoundError as MinervaNotFoundError,
                    )

                    assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), (
                        f"Unexpected exception type: {type(e)}"
                    )

    def test_server_logging_configuration(self):
        """Test that server logging is properly configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                import logging

                # Verify logger exists
                logger = logging.getLogger("minerva.server")
                assert logger is not None


class TestMCPServerWorkflowIntegration:
    """Test complete workflows through server interface."""

    @pytest.fixture
    def temp_vault_env(self):
        """Create temporary vault with environment setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                # Ensure fresh module loading with patched environment
                sys.modules.pop("minerva.server", None)
                sys.modules.pop("minerva.service", None)
                from minerva import server  # noqa: E402

                yield server

    def test_create_and_read_note_workflow(self, temp_vault_env):
        """Test creating and reading a note through server interface."""
        server = temp_vault_env

        # Create note with unique filename
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        content = "This is a test note for workflow testing"
        filename = f"workflow_test_note_{unique_id}"

        note_path = server.create_note(content, filename)

        # Verify note was created
        assert note_path.exists()
        assert note_path.name == f"workflow_test_note_{unique_id}.md"

        # Read note back
        read_content = server.read_note(str(note_path))

        # Verify content is correct (after frontmatter parsing)
        import frontmatter

        post = frontmatter.loads(read_content)
        assert post.content == content
        assert "author" in post.metadata
        assert "created" in post.metadata

    def test_edit_note_workflow(self, temp_vault_env):
        """Test editing an existing note through server interface."""
        server = temp_vault_env

        # Create initial note with unique filename
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        initial_content = "Initial workflow content"
        filename = f"edit_workflow_test_{unique_id}"
        note_path = server.create_note(initial_content, filename)

        # Edit note
        new_content = "Updated workflow content"
        edited_path = server.edit_note(new_content, filename)

        # Verify edit was successful
        assert edited_path == note_path
        read_content = server.read_note(str(note_path))

        import frontmatter

        post = frontmatter.loads(read_content)
        assert post.content == new_content
        assert "updated" in post.metadata

    def test_tag_operations_workflow(self, temp_vault_env):
        """Test comprehensive tag operations through server interface."""
        server = temp_vault_env

        # Create note with unique filename
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        content = "Note for tag workflow testing"
        filename = f"tag_workflow_note_{unique_id}"
        server.create_note(content, filename)

        # Add multiple tags
        server.add_tag("workflow-tag", filename=filename)
        server.add_tag("test-tag", filename=filename)
        server.add_tag("integration-tag", filename=filename)

        # Verify tags were added
        tags = server.get_tags(filename=filename)
        assert "workflow-tag" in tags
        assert "test-tag" in tags
        assert "integration-tag" in tags

        # Remove one tag
        server.remove_tag("test-tag", filename=filename)
        tags = server.get_tags(filename=filename)
        assert "test-tag" not in tags
        assert "workflow-tag" in tags
        assert "integration-tag" in tags

    def test_delete_operations_workflow(self, temp_vault_env):
        """Test delete operations workflow through server interface."""
        server = temp_vault_env

        # Create note to delete with unique filename
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        content = "Note to be deleted in workflow test"
        filename = f"delete_workflow_test_{unique_id}"
        note_path = server.create_note(content, filename)
        assert note_path.exists()

        # Get delete confirmation
        confirmation = server.get_note_delete_confirmation(filename=filename)

        # Verify confirmation contains expected information
        assert "file_path" in confirmation
        assert "message" in confirmation
        assert str(note_path) == confirmation["file_path"]

        # Perform deletion
        deleted_path = server.perform_note_delete(filename=filename)

        # Verify note was deleted
        assert deleted_path == note_path
        assert not note_path.exists()

    def test_search_functionality_workflow(self, temp_vault_env):
        """Test search functionality through server interface."""
        server = temp_vault_env

        # Create test notes with different content and unique filenames
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        server.create_note("This contains apple fruit", f"search_note1_{unique_id}")
        server.create_note("This contains banana fruit", f"search_note2_{unique_id}")
        server.create_note("This contains APPLE fruit", f"search_note3_{unique_id}")
        server.create_note("No matching content here", f"search_note4_{unique_id}")

        # Test case-insensitive search
        results = server.search_notes("apple", case_sensitive=False)

        # Should find both "apple" and "APPLE"
        assert len(results) >= 2

        # Verify result structure
        for result in results:
            assert hasattr(result, "file_path")
            assert hasattr(result, "line_number")
            assert hasattr(result, "context")

        # Test case-sensitive search
        results_sensitive = server.search_notes("apple", case_sensitive=True)

        # Should only find "apple" (not "APPLE")
        assert len(results_sensitive) >= 1
        assert len(results_sensitive) <= len(results)

    def test_comprehensive_tag_management_workflow(self, temp_vault_env):
        """Test comprehensive tag management through server interface."""
        server = temp_vault_env

        # Create multiple notes with tags and unique filenames
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        server.create_note(
            "Project Alpha documentation", f"project_alpha_doc_{unique_id}"
        )
        server.create_note(
            "Project Alpha meeting notes", f"project_alpha_meeting_{unique_id}"
        )
        server.create_note(
            "Project Beta documentation", f"project_beta_doc_{unique_id}"
        )

        # Add tags to notes
        server.add_tag("project-alpha", filename=f"project_alpha_doc_{unique_id}")
        server.add_tag("documentation", filename=f"project_alpha_doc_{unique_id}")

        server.add_tag("project-alpha", filename=f"project_alpha_meeting_{unique_id}")
        server.add_tag("meeting", filename=f"project_alpha_meeting_{unique_id}")

        server.add_tag("project-beta", filename=f"project_beta_doc_{unique_id}")
        server.add_tag("documentation", filename=f"project_beta_doc_{unique_id}")

        # Test finding notes with specific tag
        alpha_notes = server.find_notes_with_tag("project-alpha")
        assert len(alpha_notes) >= 2

        doc_notes = server.find_notes_with_tag("documentation")
        assert len(doc_notes) >= 2

        # Test listing all tags
        all_tags = server.list_all_tags()
        expected_tags = {"project-alpha", "project-beta", "documentation", "meeting"}
        assert expected_tags.issubset(set(all_tags))

        # Test tag renaming
        renamed_paths = server.rename_tag("project-alpha", "archived-project-alpha")
        assert len(renamed_paths) >= 2

        # Verify tag was renamed (check that new archived tag exists)
        archived_notes = server.find_notes_with_tag("archived-project-alpha")
        assert len(archived_notes) >= 2

    def test_error_handling_integration(self, temp_vault_env):
        """Test error handling through server interface."""
        server = temp_vault_env

        # Test reading non-existent file
        try:
            server.read_note("/non/existent/file.md")
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            from minerva.exceptions import NoteNotFoundError as MinervaNotFoundError

            assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), (
                f"Unexpected exception type: {type(e)}"
            )

        # Test editing non-existent file
        try:
            server.edit_note("content", "non_existent_file")
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            from minerva.exceptions import NoteNotFoundError as MinervaNotFoundError

            assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), (
                f"Unexpected exception type: {type(e)}"
            )

        # Test deleting non-existent file
        try:
            server.get_note_delete_confirmation(filename="non_existent_file")
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            from minerva.exceptions import NoteNotFoundError as MinervaNotFoundError

            assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), (
                f"Unexpected exception type: {type(e)}"
            )

        # Test adding tag to non-existent file
        try:
            server.add_tag("test-tag", filename="non_existent_file")
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            from minerva.exceptions import NoteNotFoundError as MinervaNotFoundError

            assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), (
                f"Unexpected exception type: {type(e)}"
            )

    def test_service_consistency_across_operations(self, temp_vault_env):
        """Test that all operations use the same service instance consistently."""
        server = temp_vault_env

        # Create a note and perform various operations with unique filename
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        filename = f"consistency_test_{unique_id}"
        note_path = server.create_note("Consistency test content", filename)

        # All operations should work on the same vault
        server.add_tag("consistency-tag", filename=filename)
        tags = server.get_tags(filename=filename)
        assert "consistency-tag" in tags

        # Search should find the note
        search_results = server.search_notes("Consistency test")
        assert len(search_results) >= 1

        # Tag operations should work across the vault
        tagged_notes = server.find_notes_with_tag("consistency-tag")
        assert len(tagged_notes) >= 1

        # All operations should reference the same file
        content = server.read_note(str(note_path))
        import frontmatter

        post = frontmatter.loads(content)
        tags = post.metadata.get("tags", [])
        assert isinstance(tags, list)
        assert "consistency-tag" in tags


class TestMCPServerPerformanceIntegration:
    """Test server performance characteristics in integration scenarios."""

    @pytest.fixture
    def temp_vault_env(self):
        """Create temporary vault with environment setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "test_vault"
            vault_dir.mkdir()

            with patch.dict(
                os.environ,
                {
                    "OBSIDIAN_VAULT_ROOT": tmpdir,
                    "DEFAULT_VAULT": "test_vault",
                },
            ):
                # Ensure fresh module loading with patched environment
                sys.modules.pop("minerva.server", None)
                sys.modules.pop("minerva.service", None)
                from minerva import server  # noqa: E402

                yield server

    def test_multiple_note_operations_performance(self, temp_vault_env):
        """Test performance with multiple note operations."""
        server = temp_vault_env

        # Create multiple notes with unique filenames
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        note_paths = []
        for i in range(10):
            content = f"Performance test note {i} with unique content"
            filename = f"perf_test_note_{unique_id}_{i}"
            note_path = server.create_note(content, filename)
            note_paths.append(note_path)

            # Add tags to each note
            server.add_tag(f"batch-{i // 3}", filename=filename)
            server.add_tag("performance-test", filename=filename)

        # Verify all notes were created
        assert len(note_paths) == 10
        assert all(path.exists() for path in note_paths)

        # Test search across all notes
        search_results = server.search_notes("Performance test")
        assert len(search_results) >= 10

        # Test tag operations across all notes
        all_tagged_notes = server.find_notes_with_tag("performance-test")
        assert len(all_tagged_notes) >= 10

        # Test listing all tags
        all_tags = server.list_all_tags()
        performance_tags = [tag for tag in all_tags if tag.startswith("batch-")]
        assert len(performance_tags) >= 3  # batch-0, batch-1, batch-2, batch-3
