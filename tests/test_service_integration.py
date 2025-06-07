"""
Tests for service integration with tools.py wrapper functions.
"""

import pytest
from unittest.mock import Mock, patch

from minerva.tools import (
    get_service_instance,
    set_service_instance,
    _get_service,
)


class TestServiceWrappers:
    """Test the service wrapper functions in tools.py."""

    def setup_method(self):
        """Reset service instance before each test."""
        # Reset the global service instance
        import minerva.tools

        minerva.tools._service_instance = None

    def teardown_method(self):
        """Clean up after each test."""
        # Reset the global service instance
        import minerva.tools

        minerva.tools._service_instance = None

    @patch("minerva.service.create_minerva_service")
    def test_get_service_lazy_initialization(self, mock_create_service):
        """Test that service is created lazily."""
        mock_service = Mock()
        mock_create_service.return_value = mock_service

        # First call should create the service
        result = _get_service()

        assert result == mock_service
        mock_create_service.assert_called_once()

        # Second call should return the same instance
        result2 = _get_service()

        assert result2 == mock_service
        # Should not create another service
        mock_create_service.assert_called_once()

    @patch("minerva.service.create_minerva_service")
    def test_get_service_instance(self, mock_create_service):
        """Test get_service_instance function."""
        mock_service = Mock()
        mock_create_service.return_value = mock_service

        result = get_service_instance()

        assert result == mock_service
        mock_create_service.assert_called_once()

    def test_set_service_instance(self):
        """Test setting a custom service instance."""
        mock_service = Mock()

        set_service_instance(mock_service)
        result = get_service_instance()

        assert result == mock_service

    @patch("minerva.service.create_minerva_service")
    def test_service_instance_replacement(self, mock_create_service):
        """Test that setting a service instance replaces the existing one."""
        mock_service1 = Mock()
        mock_service2 = Mock()
        mock_create_service.return_value = mock_service1

        # Get the default service
        result1 = get_service_instance()
        assert result1 == mock_service1

        # Replace with custom service
        set_service_instance(mock_service2)
        result2 = get_service_instance()
        assert result2 == mock_service2
        assert result2 != result1

    @patch("minerva.service.create_minerva_service")
    def test_service_creation_error_handling(self, mock_create_service):
        """Test error handling when service creation fails."""
        mock_create_service.side_effect = ValueError("Service creation failed")

        with pytest.raises(ValueError, match="Service creation failed"):
            _get_service()
