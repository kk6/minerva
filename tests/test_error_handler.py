"""Tests for error handling utilities module."""

import logging
import time
from pathlib import Path

import pytest

from minerva.error_handler import (
    MinervaErrorHandler,
    handle_file_operations,
    validate_inputs,
    log_performance,
    safe_operation,
)
from minerva.exceptions import (
    NoteExistsError,
    NoteNotFoundError,
    ValidationError,
    VaultError,
)


class TestMinervaErrorHandler:
    """Test cases for MinervaErrorHandler class."""

    def test_init_without_vault_path(self):
        """Test initializing error handler without vault path."""
        handler = MinervaErrorHandler()

        assert handler.vault_path is None
        assert handler.performance_threshold_ms == 1000

    def test_init_with_vault_path(self):
        """Test initializing error handler with vault path."""
        vault_path = Path("/test/vault")
        handler = MinervaErrorHandler(vault_path=vault_path)

        assert handler.vault_path == vault_path

    def test_sanitize_path_empty(self):
        """Test sanitizing empty path."""
        handler = MinervaErrorHandler()

        result = handler.sanitize_path("")
        assert result == "<empty>"

        result = handler.sanitize_path(None)
        assert result == "<empty>"

    def test_sanitize_path_relative(self):
        """Test sanitizing relative path."""
        handler = MinervaErrorHandler()

        result = handler.sanitize_path("notes/test.md")
        assert result == "notes/test.md"

    def test_sanitize_path_with_vault_path(self):
        """Test sanitizing path with vault context."""
        vault_path = Path("/home/user/vault")
        handler = MinervaErrorHandler(vault_path=vault_path)

        # Path inside vault
        result = handler.sanitize_path("/home/user/vault/notes/test.md")
        assert result == "<vault>/notes/test.md"

        # Path outside vault
        result = handler.sanitize_path("/etc/passwd")
        assert result == "<external>/passwd"

    def test_sanitize_long_path(self):
        """Test sanitizing very long path."""
        handler = MinervaErrorHandler()
        long_path = "a/b/c/d/e/f/g.md"

        result = handler.sanitize_path(long_path)
        assert result == "a/.../f/g.md"

    def test_create_error_context(self):
        """Test creating error context."""
        handler = MinervaErrorHandler()

        context = handler.create_error_context(
            "test_operation",
            file_path="/test/path.md",
            user_id=123,
            password="secret123",
        )

        assert context["operation"] == "test_operation"
        assert context["file_path"] == "/test/path.md"  # Short path, not sanitized
        assert context["user_id"] == "123"
        assert context["password"] == "<redacted>"

    def test_create_error_context_with_none_values(self):
        """Test creating error context with None values."""
        handler = MinervaErrorHandler()

        context = handler.create_error_context(
            "test_operation", file_path=None, optional_param=None
        )

        assert context["file_path"] == "<empty>"  # None values get sanitized to <empty>
        assert context["optional_param"] is None


class TestHandleFileOperationsDecorator:
    """Test cases for handle_file_operations decorator."""

    @handle_file_operations()
    def _test_function_that_raises_file_not_found(self):
        """Test function that raises FileNotFoundError."""
        raise FileNotFoundError("Test file not found")

    @handle_file_operations()
    def _test_function_that_raises_file_exists(self):
        """Test function that raises FileExistsError."""
        raise FileExistsError("Test file exists")

    @handle_file_operations()
    def _test_function_that_raises_permission_error(self):
        """Test function that raises PermissionError."""
        raise PermissionError("Test permission denied")

    @handle_file_operations()
    def _test_function_that_raises_io_error(self):
        """Test function that raises IOError."""
        raise IOError("Test I/O error")

    @handle_file_operations()
    def _test_function_that_succeeds(self):
        """Test function that succeeds."""
        return "success"

    def test_file_not_found_conversion(self, caplog):
        """Test FileNotFoundError conversion to NoteNotFoundError."""
        with pytest.raises(NoteNotFoundError) as exc_info:
            self._test_function_that_raises_file_not_found()

        assert "File not found: Test file not found" in str(exc_info.value)
        assert exc_info.value.operation is not None
        assert "File not found" in caplog.text

    def test_file_exists_conversion(self, caplog):
        """Test FileExistsError conversion to NoteExistsError."""
        with pytest.raises(NoteExistsError) as exc_info:
            self._test_function_that_raises_file_exists()

        assert "File already exists: Test file exists" in str(exc_info.value)
        assert exc_info.value.operation is not None
        assert "File already exists" in caplog.text

    def test_permission_error_conversion(self, caplog):
        """Test PermissionError conversion to VaultError."""
        with pytest.raises(VaultError) as exc_info:
            self._test_function_that_raises_permission_error()

        assert "Permission denied: Test permission denied" in str(exc_info.value)
        assert exc_info.value.operation is not None
        assert "Permission denied" in caplog.text

    def test_io_error_conversion(self, caplog):
        """Test IOError conversion to VaultError."""
        with pytest.raises(VaultError) as exc_info:
            self._test_function_that_raises_io_error()

        assert "I/O error: Test I/O error" in str(exc_info.value)
        assert exc_info.value.operation is not None
        assert "I/O error" in caplog.text

    def test_successful_operation(self):
        """Test that successful operations pass through unchanged."""
        result = self._test_function_that_succeeds()
        assert result == "success"


class TestValidateInputsDecorator:
    """Test cases for validate_inputs decorator."""

    def _validator_not_empty(self, *args, **kwargs):
        """Validator that checks if text is not empty."""
        text = kwargs.get("text") or (args[0] if args else None)
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty")

    def _validator_positive_number(self, *args, **kwargs):
        """Validator that checks if number is positive."""
        number = kwargs.get("number") or (args[1] if len(args) > 1 else None)
        if number is not None and number <= 0:
            raise ValidationError("Number must be positive")

    @validate_inputs()
    def _test_function_no_validators(self, text: str) -> str:
        """Test function with no validators."""
        return f"processed: {text}"

    @validate_inputs(_validator_not_empty)
    def _test_function_with_validator(self, text: str) -> str:
        """Test function with single validator."""
        return f"processed: {text}"

    @validate_inputs(_validator_not_empty, _validator_positive_number)
    def _test_function_with_multiple_validators(self, text: str, number: int) -> str:
        """Test function with multiple validators."""
        return f"processed: {text}, {number}"

    def test_no_validators_success(self):
        """Test function with no validators succeeds."""
        result = self._test_function_no_validators("test")
        assert result == "processed: test"

    def test_single_validator_success(self):
        """Test function with validator that passes."""
        result = self._test_function_with_validator("valid text")
        assert result == "processed: valid text"

    def test_single_validator_failure(self):
        """Test function with validator that fails."""
        with pytest.raises(ValidationError) as exc_info:
            self._test_function_with_validator("")

        assert "Text cannot be empty" in str(exc_info.value)

    def test_multiple_validators_success(self):
        """Test function with multiple validators that pass."""
        result = self._test_function_with_multiple_validators("valid text", 5)
        assert result == "processed: valid text, 5"

    def test_multiple_validators_first_fails(self):
        """Test function with first validator failing."""
        with pytest.raises(ValidationError) as exc_info:
            self._test_function_with_multiple_validators("", 5)

        assert "Text cannot be empty" in str(exc_info.value)

    def test_multiple_validators_second_fails(self):
        """Test function with second validator failing."""
        with pytest.raises(ValidationError) as exc_info:
            self._test_function_with_multiple_validators("valid text", -1)

        assert "Number must be positive" in str(exc_info.value)

    def test_value_error_conversion(self):
        """Test that ValueError is converted to ValidationError."""

        @validate_inputs()
        def test_function():
            raise ValueError("Test value error")

        with pytest.raises(ValidationError) as exc_info:
            test_function()

        assert "Invalid input: Test value error" in str(exc_info.value)


class TestLogPerformanceDecorator:
    """Test cases for log_performance decorator."""

    @log_performance(threshold_ms=100)
    def _fast_function(self):
        """Function that executes quickly."""
        return "fast"

    @log_performance(threshold_ms=100)
    def _slow_function(self):
        """Function that executes slowly."""
        time.sleep(0.15)  # 150ms
        return "slow"

    @log_performance(threshold_ms=100)
    def _failing_function(self):
        """Function that raises an exception."""
        time.sleep(0.05)  # 50ms
        raise ValueError("Test error")

    def test_fast_function_no_log(self, caplog):
        """Test that fast functions don't generate performance logs."""
        with caplog.at_level(logging.INFO):
            result = self._fast_function()

        assert result == "fast"
        # Should not log performance for fast operations
        assert "Slow operation" not in caplog.text

    def test_slow_function_logs_performance(self, caplog):
        """Test that slow functions generate performance logs."""
        with caplog.at_level(logging.INFO):
            result = self._slow_function()

        assert result == "slow"
        assert "Slow operation" in caplog.text
        assert "completed in" in caplog.text

    def test_failing_function_logs_error(self, caplog):
        """Test that failing functions log execution time in error."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                self._failing_function()

        assert "Operation" in caplog.text
        assert "failed after" in caplog.text


class TestSafeOperationDecorator:
    """Test cases for safe_operation decorator."""

    @safe_operation(default_return="default")
    def _function_that_fails(self):
        """Function that always raises an exception."""
        raise ValueError("Test error")

    @safe_operation(default_return="default")
    def _function_that_succeeds(self):
        """Function that always succeeds."""
        return "success"

    @safe_operation(default_return="default", reraise_types=(TypeError,))
    def _function_with_reraise(self, error_type: str):
        """Function that raises different types of errors."""
        if error_type == "type":
            raise TypeError("Type error")
        elif error_type == "value":
            raise ValueError("Value error")
        return "success"

    @safe_operation(default_return=[], log_errors=False)
    def _function_with_no_logging(self):
        """Function that fails but doesn't log."""
        raise ValueError("Test error")

    def test_successful_operation(self):
        """Test that successful operations return normally."""
        result = self._function_that_succeeds()
        assert result == "success"

    def test_failed_operation_returns_default(self, caplog):
        """Test that failed operations return default value."""
        with caplog.at_level(logging.WARNING):
            result = self._function_that_fails()

        assert result == "default"
        assert "Safe operation" in caplog.text
        assert "returning default" in caplog.text

    def test_reraise_specific_types(self):
        """Test that specific exception types are re-raised."""
        with pytest.raises(TypeError):
            self._function_with_reraise("type")

        # ValueError should be caught and return default
        result = self._function_with_reraise("value")
        assert result == "default"

    def test_no_logging_option(self, caplog):
        """Test that log_errors=False prevents error logging."""
        with caplog.at_level(logging.WARNING):
            result = self._function_with_no_logging()

        assert result == []
        # Should not log anything
        assert caplog.text == ""
