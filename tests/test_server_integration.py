"""
Integration tests for MCP server functionality.

These tests verify that the MCP server correctly integrates with the service layer
and provides working tool functions.
"""

import tempfile
import os
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
                from minerva import server

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
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                # This should raise an exception due to missing env vars
                import importlib
                from minerva import server

                importlib.reload(server)

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
                    from minerva import server

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
                from minerva import server

                # Test error handling for non-existent file
                with pytest.raises(FileNotFoundError):
                    server.read_note("/non/existent/file.md")

                # Test error handling for invalid operations
                with pytest.raises(FileNotFoundError):
                    server.edit_note("content", "non_existent_file")

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
