"""Tests for custom exceptions module."""

from datetime import datetime
from minerva.exceptions import (
    MinervaError,
    ValidationError,
    NoteNotFoundError,
    NoteExistsError,
    TagError,
    VaultError,
    SearchError,
    FrontmatterError,
    ConfigurationError,
)


class TestMinervaError:
    """Test cases for MinervaError base class."""

    def test_basic_error_creation(self):
        """Test creating a basic MinervaError."""
        error = MinervaError("Test error message")

        assert str(error) == "Test error message"
        assert error.context == {}
        assert error.operation is None
        assert isinstance(error.timestamp, datetime)

    def test_error_with_context(self):
        """Test creating error with context."""
        context = {"file_path": "/test/path", "operation_id": 123}
        error = MinervaError("Test error", context=context)

        assert error.context == context

    def test_error_with_operation(self):
        """Test creating error with operation name."""
        error = MinervaError("Test error", operation="test_operation")

        assert error.operation == "test_operation"

    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        context = {"key": "value"}
        error = MinervaError("Test error", context=context, operation="test_op")

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "MinervaError"
        assert error_dict["message"] == "Test error"
        assert error_dict["context"] == context
        assert error_dict["operation"] == "test_op"
        assert "timestamp" in error_dict


class TestCustomExceptions:
    """Test cases for custom exception types."""

    def test_validation_error(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid input")

        assert isinstance(error, MinervaError)
        assert str(error) == "Invalid input"

    def test_note_not_found_error(self):
        """Test NoteNotFoundError creation."""
        error = NoteNotFoundError("Note not found")

        assert isinstance(error, MinervaError)
        assert str(error) == "Note not found"

    def test_note_exists_error(self):
        """Test NoteExistsError creation."""
        error = NoteExistsError("Note already exists")

        assert isinstance(error, MinervaError)
        assert str(error) == "Note already exists"

    def test_tag_error(self):
        """Test TagError creation."""
        error = TagError("Invalid tag")

        assert isinstance(error, MinervaError)
        assert str(error) == "Invalid tag"

    def test_vault_error(self):
        """Test VaultError creation."""
        error = VaultError("Vault access denied")

        assert isinstance(error, MinervaError)
        assert str(error) == "Vault access denied"

    def test_search_error(self):
        """Test SearchError creation."""
        error = SearchError("Search failed")

        assert isinstance(error, MinervaError)
        assert str(error) == "Search failed"

    def test_frontmatter_error(self):
        """Test FrontmatterError creation."""
        error = FrontmatterError("Frontmatter parsing failed")

        assert isinstance(error, MinervaError)
        assert str(error) == "Frontmatter parsing failed"

    def test_configuration_error(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError("Invalid configuration")

        assert isinstance(error, MinervaError)
        assert str(error) == "Invalid configuration"

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from MinervaError."""
        exceptions = [
            ValidationError("test"),
            NoteNotFoundError("test"),
            NoteExistsError("test"),
            TagError("test"),
            VaultError("test"),
            SearchError("test"),
            FrontmatterError("test"),
            ConfigurationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, MinervaError)
            assert isinstance(exc, Exception)
