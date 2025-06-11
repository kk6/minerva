"""
Tests for BaseService class.
"""

import pytest
from unittest.mock import Mock
from pathlib import Path

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.services.core.base_service import BaseService


class TestBaseService:
    """Test cases for BaseService class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=MinervaConfig)
        config.vault_path = Path("/test/vault")
        config.default_note_dir = "notes"
        config.default_author = "Test Author"
        return config

    @pytest.fixture
    def mock_frontmatter_manager(self):
        """Create a mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)

    @pytest.fixture
    def base_service(self, mock_config, mock_frontmatter_manager):
        """Create a BaseService instance for testing."""
        return BaseService(mock_config, mock_frontmatter_manager)

    def test_init(self, base_service, mock_config, mock_frontmatter_manager):
        """Test BaseService initialization."""
        # Arrange & Act & Assert
        assert base_service.config == mock_config
        assert base_service.frontmatter_manager == mock_frontmatter_manager
        assert base_service.error_handler is not None
        assert base_service.error_handler.vault_path == mock_config.vault_path

    def test_log_operation_start(self, base_service, caplog):
        """Test operation start logging."""
        # Arrange
        operation = "test_operation"
        params = {"key": "value", "number": 42}

        # Set log level to DEBUG to capture debug messages
        caplog.set_level("DEBUG")

        # Act
        base_service._log_operation_start(operation, **params)

        # Assert
        assert "Starting test_operation operation" in caplog.text
        assert "key" in caplog.text
        assert "value" in caplog.text

    def test_log_operation_success_with_result(self, base_service, caplog):
        """Test operation success logging with result."""
        # Arrange
        operation = "test_operation"
        result = "/path/to/file.md"

        # Set log level to DEBUG to capture debug messages
        caplog.set_level("DEBUG")

        # Act
        base_service._log_operation_success(operation, result)

        # Assert
        assert "Successfully completed test_operation operation" in caplog.text
        assert "/path/to/file.md" in caplog.text

    def test_log_operation_success_without_result(self, base_service, caplog):
        """Test operation success logging without result."""
        # Arrange
        operation = "test_operation"

        # Set log level to DEBUG to capture debug messages
        caplog.set_level("DEBUG")

        # Act
        base_service._log_operation_success(operation)

        # Assert
        assert "Successfully completed test_operation operation" in caplog.text

    def test_log_operation_error(self, base_service, caplog):
        """Test operation error logging."""
        # Arrange
        operation = "test_operation"
        error = ValueError("Test error message")

        # Act
        base_service._log_operation_error(operation, error)

        # Assert
        assert "Error in test_operation operation" in caplog.text
        assert "Test error message" in caplog.text
