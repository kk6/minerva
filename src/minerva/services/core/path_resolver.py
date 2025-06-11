"""
Path resolution utilities for service modules.

This module provides utilities for path validation, normalization,
and handling edge cases with file paths.
"""

import logging
import os
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


class PathResolver:
    """
    Utility class for resolving and validating file paths.

    This class provides methods for normalizing paths, validating path
    components, and handling common edge cases in file path operations.
    """

    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """
        Normalize a path to a consistent format.

        Args:
            path: The path to normalize

        Returns:
            Path: Normalized path object

        Raises:
            ValueError: If the path is invalid
        """
        if not path:
            raise ValueError("Path cannot be empty")

        path_obj = Path(path)

        # Resolve to absolute path if it's relative
        if not path_obj.is_absolute():
            path_obj = path_obj.resolve()

        return path_obj

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate a filename for common issues.

        Args:
            filename: The filename to validate

        Returns:
            str: Validated filename

        Raises:
            ValueError: If the filename is invalid
        """
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty or whitespace")

        filename = filename.strip()

        # Check for invalid characters
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in invalid_chars:
            if char in filename:
                raise ValueError(f"Filename cannot contain '{char}' character")

        # Check for reserved names on Windows
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            raise ValueError(f"Filename '{filename}' uses a reserved name")

        # Check length (255 characters is a common filesystem limit)
        if len(filename) > 255:
            raise ValueError("Filename is too long (maximum 255 characters)")

        return filename

    @staticmethod
    def validate_path_components(path: Union[str, Path]) -> None:
        """
        Validate all components of a path.

        Args:
            path: The path to validate

        Raises:
            ValueError: If any path component is invalid
        """
        path_obj = Path(path)

        for part in path_obj.parts:
            if part in (".", ".."):
                continue  # These are valid relative path components
            PathResolver.validate_filename(part)

    @staticmethod
    def ensure_extension(filename: str, extension: str = ".md") -> str:
        """
        Ensure a filename has the specified extension.

        Args:
            filename: The filename to check
            extension: The extension to ensure (default: .md)

        Returns:
            str: Filename with extension
        """
        if not filename.endswith(extension):
            return f"{filename}{extension}"
        return filename

    @staticmethod
    def split_path_and_filename(filepath: str) -> tuple[str, str]:
        """
        Split a filepath into directory and filename components.

        Args:
            filepath: The full file path

        Returns:
            tuple: (directory, filename)
        """
        return os.path.split(filepath)

    @staticmethod
    def is_safe_path(base_path: Path, target_path: Path) -> bool:
        """
        Check if target_path is safely within base_path (no directory traversal).

        Args:
            base_path: The base directory path
            target_path: The target path to check

        Returns:
            bool: True if the target path is safe, False otherwise
        """
        try:
            # Resolve both paths to absolute paths
            base_resolved = base_path.resolve()
            target_resolved = target_path.resolve()

            # Check if target is within base
            return (
                base_resolved in target_resolved.parents
                or base_resolved == target_resolved
            )
        except (OSError, ValueError):
            return False

    @staticmethod
    def create_safe_path(base_path: Path, relative_path: str) -> Path:
        """
        Create a safe path by joining base_path with relative_path.

        Args:
            base_path: The base directory path
            relative_path: The relative path component

        Returns:
            Path: Safe combined path

        Raises:
            ValueError: If the resulting path would be outside base_path
        """
        # Normalize the relative path to prevent directory traversal
        relative_path = relative_path.replace("\\", "/").strip("/")

        # Split into components and validate each
        components = [comp for comp in relative_path.split("/") if comp and comp != "."]

        # Remove any '..' components for security
        safe_components = [comp for comp in components if comp != ".."]

        if not safe_components:
            return base_path

        # Validate each component
        for component in safe_components:
            PathResolver.validate_filename(component)

        # Create the final path
        result_path = base_path
        for component in safe_components:
            result_path = result_path / component

        # Verify the result is safe
        if not PathResolver.is_safe_path(base_path, result_path):
            raise ValueError(f"Path '{relative_path}' would escape base directory")

        return result_path
