"""Custom exceptions for Minerva.

This module defines the exception hierarchy used throughout the Minerva application
for consistent error handling and classification.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class MinervaError(Exception):
    """Base exception for all Minerva errors.

    Provides structured error context and timestamps for better debugging
    and error tracking.

    Args:
        message: Human-readable error message
        context: Additional context information about the error
        operation: The operation that was being performed when the error occurred
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.context = context or {}
        self.operation = operation
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "context": self.context,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
        }


class ValidationError(MinervaError):
    """Raised when input validation fails.

    Used for invalid parameters, malformed data, or constraint violations.
    """

    pass


class NoteNotFoundError(MinervaError):
    """Raised when a requested note cannot be found.

    This includes cases where the file doesn't exist or is not accessible.
    """

    pass


class NoteExistsError(MinervaError):
    """Raised when attempting to create a note that already exists.

    Used when overwrite=False and the target file already exists.
    """

    pass


class TagError(MinervaError):
    """Raised for tag-related operation failures.

    Includes invalid tag names, tag conflicts, or tag processing errors.
    """

    pass


class VaultError(MinervaError):
    """Raised for vault-level operation failures.

    Includes permission errors, vault configuration issues, or vault access problems.
    """

    pass


class SearchError(MinervaError):
    """Raised for search operation failures.

    Includes malformed queries, search index issues, or search execution errors.
    """

    pass


class FrontmatterError(MinervaError):
    """Raised for frontmatter processing failures.

    Includes parsing errors, validation failures, or frontmatter corruption.
    """

    pass


class ConfigurationError(MinervaError):
    """Raised for configuration-related failures.

    Includes missing environment variables, invalid configuration values,
    or configuration loading errors.
    """

    pass
