"""Error handling utilities for Minerva.

This module provides decorators, context managers, and utilities for consistent
error handling, logging, and performance monitoring across the application.
"""

import functools
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from .exceptions import (
    NoteExistsError,
    NoteNotFoundError,
    ValidationError,
    VaultError,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class MinervaErrorHandler:
    """Central error handler for Minerva operations.

    Provides consistent error handling, logging, and performance monitoring
    with security-conscious logging that sanitizes sensitive information.
    """

    def __init__(self, vault_path: Optional[Path] = None) -> None:
        """Initialize error handler.

        Args:
            vault_path: Base vault path for path sanitization
        """
        self.vault_path = vault_path
        self.performance_threshold_ms = 1000  # Log operations > 1 second

    def sanitize_path(self, path: Union[str, Path]) -> str:
        """Sanitize file paths for secure logging.

        Removes or masks sensitive parts of file paths to prevent
        information leakage in logs.

        Args:
            path: File path to sanitize

        Returns:
            Sanitized path string safe for logging
        """
        if not path:
            return "<empty>"

        path_obj = Path(path)

        # If we have a vault path, make it relative
        if self.vault_path and path_obj.is_absolute():
            try:
                relative_path = path_obj.relative_to(self.vault_path)
                return f"<vault>/{relative_path}"
            except ValueError:
                # Path is outside vault, mask it more aggressively
                return f"<external>/{path_obj.name}"

        # For relative paths or when no vault_path is set
        if len(path_obj.parts) > 3:
            # Show only first and last few parts for long paths
            return f"{path_obj.parts[0]}/.../{'/'.join(path_obj.parts[-2:])}"

        return str(path_obj)

    def create_error_context(self, operation: str, **kwargs: Any) -> Dict[str, Any]:
        """Create standardized error context.

        Args:
            operation: Name of the operation being performed
            **kwargs: Additional context information

        Returns:
            Sanitized context dictionary
        """
        context = {"operation": operation}

        for key, value in kwargs.items():
            if key in ("path", "filepath", "file_path", "directory"):
                context[key] = self.sanitize_path(value)
            elif key in ("password", "token", "secret", "key"):
                context[key] = "<redacted>"
            else:
                context[key] = str(value) if value is not None else None

        return context


def handle_file_operations() -> Callable[[F], F]:
    """Decorator for consistent file operation error handling.

    Converts standard file system exceptions to appropriate Minerva exceptions
    with consistent logging and context.

    Returns:
        Decorated function with error handling
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = f"{func.__module__}.{func.__name__}"

            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                logger.error("File not found in %s: %s", operation, str(e))
                raise NoteNotFoundError(
                    f"File not found: {e}",
                    context={"original_error": str(e)},
                    operation=operation,
                ) from e

            except FileExistsError as e:
                logger.error("File already exists in %s: %s", operation, str(e))
                raise NoteExistsError(
                    f"File already exists: {e}",
                    context={"original_error": str(e)},
                    operation=operation,
                ) from e

            except PermissionError as e:
                logger.error("Permission denied in %s: %s", operation, str(e))
                raise VaultError(
                    f"Permission denied: {e}",
                    context={"original_error": str(e)},
                    operation=operation,
                ) from e

            except (OSError, IOError) as e:
                logger.error("I/O error in %s: %s", operation, str(e))
                raise VaultError(
                    f"I/O error: {e}",
                    context={"original_error": str(e)},
                    operation=operation,
                ) from e

        return wrapper

    return decorator


def validate_inputs(*validation_functions: Callable[..., None]) -> Callable[[F], F]:
    """Decorator for input validation with consistent error handling.

    Args:
        *validation_functions: Functions that raise ValidationError for invalid inputs

    Returns:
        Decorated function with input validation
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = f"{func.__module__}.{func.__name__}"

            try:
                # Run all validation functions
                for validator in validation_functions:
                    validator(*args, **kwargs)

                return func(*args, **kwargs)

            except ValidationError as e:
                # Re-raise with operation context
                if not e.operation:
                    e.operation = operation
                logger.warning("Validation failed in %s: %s", operation, str(e))
                raise

            except (ValueError, TypeError) as e:
                logger.warning("Input validation failed in %s: %s", operation, str(e))
                raise ValidationError(f"Invalid input: {e}", operation=operation) from e

        return wrapper

    return decorator


def log_performance(threshold_ms: int = 1000) -> Callable[[F], F]:
    """Decorator for performance logging and monitoring.

    Args:
        threshold_ms: Log operations that take longer than this (in milliseconds)

    Returns:
        Decorated function with performance monitoring
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time_ms = (time.time() - start_time) * 1000

                if execution_time_ms > threshold_ms:
                    logger.info(
                        "Slow operation %s completed in %.2fms",
                        operation,
                        execution_time_ms,
                    )

                return result

            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    "Operation %s failed after %.2fms: %s",
                    operation,
                    execution_time_ms,
                    str(e),
                )
                raise

        return wrapper

    return decorator


def safe_operation(
    default_return: Any = None,
    log_errors: bool = True,
    reraise_types: Optional[tuple] = None,
) -> Callable[[F], F]:
    """Decorator for safe operations with graceful error handling.

    Catches exceptions and returns a default value instead of propagating
    the error, with optional selective re-raising.

    Args:
        default_return: Value to return if operation fails
        log_errors: Whether to log caught errors
        reraise_types: Exception types to re-raise instead of catching

    Returns:
        Decorated function with safe error handling
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = f"{func.__module__}.{func.__name__}"

            try:
                return func(*args, **kwargs)

            except Exception as e:
                # Re-raise specific exception types if requested
                if reraise_types and isinstance(e, reraise_types):
                    raise

                if log_errors:
                    logger.warning(
                        "Safe operation %s failed, returning default: %s",
                        operation,
                        str(e),
                    )

                return default_return

        return wrapper

    return decorator
