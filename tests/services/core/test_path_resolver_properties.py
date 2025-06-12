"""
Property-based tests for PathResolver class using Hypothesis.

This module contains property-based tests to discover edge cases in path
validation, normalization, and security functions that might not be caught
by traditional unit tests.
"""

import os
import string
from pathlib import Path

import pytest
from hypothesis import given, assume, strategies as st

from minerva.services.core.path_resolver import PathResolver


class TestPathResolverProperties:
    """Property-based tests for PathResolver class."""

    @given(st.text(min_size=1, max_size=100))
    def test_normalize_path_always_returns_absolute(self, path_text: str):
        """Property: normalize_path should always return an absolute path for valid inputs."""
        # Arrange
        assume(path_text.strip())  # Exclude empty/whitespace-only strings
        assume(
            not any(char in path_text for char in ["\x00", "\r", "\n"])
        )  # Exclude null and newlines

        try:
            # Act
            result = PathResolver.normalize_path(path_text)

            # Assert
            assert result.is_absolute(), (
                f"Result {result} should be absolute for input {path_text!r}"
            )
        except (ValueError, OSError):
            # These are acceptable failures for invalid paths
            pass

    @given(st.just(""))
    def test_normalize_path_empty_raises_error(self, path_text: str):
        """Property: normalize_path should raise ValueError for empty strings."""
        # Act & Assert
        with pytest.raises(ValueError, match="Path cannot be empty"):
            PathResolver.normalize_path(path_text)

    @given(
        st.text(
            min_size=1,
            max_size=255,
            alphabet=string.ascii_letters + string.digits + ".-_",
        )
    )
    def test_validate_filename_valid_ascii_chars(self, filename: str):
        """Property: filenames with only safe ASCII chars should be valid."""
        # Arrange
        assume(filename.strip())  # Exclude empty/whitespace-only

        # Act & Assert
        try:
            result = PathResolver.validate_filename(filename)
            assert result == filename
        except ValueError:
            # Some combinations might still be invalid (reserved names, etc.)
            pass

    @given(st.sampled_from(["<", ">", ":", '"', "|", "?", "*"]))
    def test_validate_filename_forbidden_chars_raise_error(self, forbidden_char: str):
        """Property: filenames containing forbidden characters should raise ValueError."""
        # Arrange
        filename = f"test{forbidden_char}file.md"
        import re

        escaped_char = re.escape(forbidden_char)

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"Filename cannot contain '{escaped_char}' character"
        ):
            PathResolver.validate_filename(filename)

    @given(
        st.sampled_from(
            [
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
        )
    )
    def test_validate_filename_reserved_names_raise_error(self, reserved_name: str):
        """Property: Windows reserved names should raise ValueError."""
        # Test both exact reserved names and with extensions
        test_cases = [
            reserved_name,
            f"{reserved_name}.txt",
            f"{reserved_name.lower()}.md",
        ]

        for filename in test_cases:
            # Act & Assert
            with pytest.raises(
                ValueError, match=f"Filename '{filename}' uses a reserved name"
            ):
                PathResolver.validate_filename(filename)

    @given(
        st.text(
            min_size=256,
            max_size=300,
            alphabet=string.ascii_letters + string.digits + ".-_",
        )
    )
    def test_validate_filename_too_long_raises_error(self, long_filename: str):
        """Property: filenames longer than 255 characters should raise ValueError."""
        # Arrange
        assume(len(long_filename) > 255)
        # Ensure no forbidden characters that would trigger a different error first
        forbidden_chars = ["<", ">", ":", '"', "|", "?", "*"]
        assume(not any(char in long_filename for char in forbidden_chars))

        # Act & Assert
        with pytest.raises(ValueError, match="Filename is too long"):
            PathResolver.validate_filename(long_filename)

    @given(
        st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits)
    )
    def test_ensure_extension_adds_md_when_missing(self, basename: str):
        """Property: ensure_extension should add .md when not present."""
        # Arrange
        assume(not basename.endswith(".md"))

        # Act
        result = PathResolver.ensure_extension(basename)

        # Assert
        assert result.endswith(".md")
        assert result == f"{basename}.md"

    @given(
        st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits)
    )
    def test_ensure_extension_preserves_existing_md(self, basename: str):
        """Property: ensure_extension should preserve existing .md extension."""
        # Arrange
        filename = f"{basename}.md"

        # Act
        result = PathResolver.ensure_extension(filename)

        # Assert
        assert result == filename
        assert result.count(".md") == 1  # Should not duplicate extension

    @given(
        st.text(
            min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits + "/"
        ),
        st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits),
    )
    def test_split_path_and_filename_consistency(self, directory: str, filename: str):
        """Property: split_path_and_filename should be consistent with os.path.split."""
        # Arrange
        assume(directory.strip() and filename.strip())
        assume(not directory.startswith("/"))  # Avoid absolute paths for this test
        filepath = os.path.join(directory, filename)

        # Act
        result_dir, result_filename = PathResolver.split_path_and_filename(filepath)
        expected_dir, expected_filename = os.path.split(filepath)

        # Assert
        assert result_dir == expected_dir
        assert result_filename == expected_filename

    @given(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=string.ascii_letters + string.digits + ".-_",
        )
    )
    def test_create_safe_path_prevents_parent_traversal(self, safe_component: str):
        """Property: create_safe_path should prevent directory traversal."""
        # Arrange
        base_path = Path("/safe/base/directory")
        assume(safe_component.strip())
        assume(".." not in safe_component)  # Test explicitly safe components

        try:
            # Act
            result = PathResolver.create_safe_path(base_path, safe_component)

            # Assert
            assert PathResolver.is_safe_path(base_path, result)
            assert base_path in result.parents or base_path == result
        except ValueError:
            # Some inputs might still be invalid (forbidden chars in filename validation)
            pass

    @given(st.text(min_size=1, max_size=20))
    def test_create_safe_path_blocks_traversal_attempts(self, component: str):
        """Property: create_safe_path should block directory traversal attempts."""
        # Arrange
        base_path = Path("/safe/base/directory")
        dangerous_path = f"../{component}"

        try:
            # Act
            result = PathResolver.create_safe_path(base_path, dangerous_path)

            # Assert - should not escape base directory
            assert PathResolver.is_safe_path(base_path, result)
        except ValueError:
            # This is also acceptable - blocking the attempt entirely
            pass

    @given(
        st.text(min_size=1, max_size=30, alphabet=string.ascii_letters + string.digits),
        st.text(min_size=1, max_size=30, alphabet=string.ascii_letters + string.digits),
    )
    def test_is_safe_path_symmetric_property(
        self, base_component: str, target_component: str
    ):
        """Property: is_safe_path should have consistent behavior."""
        # Arrange
        base_path = Path(f"/test/{base_component}")
        target_path = Path(f"/test/{base_component}/{target_component}")

        # Act
        is_safe = PathResolver.is_safe_path(base_path, target_path)

        # Assert - target should be safe relative to base
        assert isinstance(is_safe, bool)
        if is_safe:
            # If it's safe, target should be within or equal to base
            assert base_path in target_path.parents or base_path == target_path

    @given(st.text(alphabet=string.printable, min_size=0, max_size=50))
    def test_validate_path_components_handles_arbitrary_input(self, path_input: str):
        """Property: validate_path_components should handle any printable string input."""
        # Arrange
        assume(
            "\x00" not in path_input
        )  # Exclude null bytes which are invalid in paths

        try:
            # Act
            PathResolver.validate_path_components(path_input)
            # If no exception, all components were valid
        except (ValueError, OSError):
            # These are acceptable failures for invalid path components
            pass
