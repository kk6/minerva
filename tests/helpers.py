"""Test helper utilities for Minerva project.

This module provides a unified testing interface for common operations
such as creating test notes, validating content, and setting up test environments.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

import frontmatter
import pytest


class MinervaTestHelper:
    """Minerva project test helper class.
    
    Provides unified utilities for test file creation, content validation,
    and common test setup operations.
    """

    @staticmethod
    def create_temp_note(
        temp_dir: Path,
        filename: str,
        content: str,
        frontmatter_data: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8",
    ) -> Path:
        """Create a test note with optional frontmatter.
        
        Args:
            temp_dir: Directory to create the note in
            filename: Name of the file (should include .md extension)
            content: Body content of the note
            frontmatter_data: Optional metadata to include in frontmatter
            encoding: File encoding (default: utf-8)
            
        Returns:
            Path to the created file
            
        Example:
            >>> helper = MinervaTestHelper()
            >>> note_path = helper.create_temp_note(
            ...     temp_dir=Path("/tmp/test"),
            ...     filename="test.md",
            ...     content="Test content",
            ...     frontmatter_data={"tags": ["test"], "author": "Test Author"}
            ... )
        """
        if frontmatter_data:
            post = frontmatter.Post(content)
            post.metadata.update(frontmatter_data)
            content_with_frontmatter = frontmatter.dumps(post)
        else:
            content_with_frontmatter = content

        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_with_frontmatter, encoding=encoding)
        return file_path

    @staticmethod
    def assert_note_content(
        file_path: Path,
        expected_content: str,
        expected_frontmatter: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8",
    ) -> None:
        """Validate note content and frontmatter.
        
        Args:
            file_path: Path to the note file
            expected_content: Expected body content
            expected_frontmatter: Expected frontmatter fields
            encoding: File encoding (default: utf-8)
            
        Raises:
            AssertionError: If content or frontmatter doesn't match expectations
        """
        assert file_path.exists(), f"File {file_path} does not exist"

        content = file_path.read_text(encoding=encoding)

        if expected_frontmatter:
            post = frontmatter.loads(content)
            assert post.content.strip() == expected_content.strip(), (
                f"Content mismatch. Expected: {expected_content.strip()!r}, "
                f"Got: {post.content.strip()!r}"
            )
            for key, value in expected_frontmatter.items():
                assert key in post.metadata, f"Field '{key}' not found in frontmatter"
                assert post.metadata[key] == value, (
                    f"Field '{key}' expected {value!r}, got {post.metadata[key]!r}"
                )
        else:
            assert content.strip() == expected_content.strip(), (
                f"Content mismatch. Expected: {expected_content.strip()!r}, "
                f"Got: {content.strip()!r}"
            )

    @staticmethod
    def assert_frontmatter_fields(
        file_path: Path,
        expected_fields: Dict[str, Any],
        encoding: str = "utf-8",
    ) -> None:
        """Validate specific frontmatter fields.
        
        Args:
            file_path: Path to the note file
            expected_fields: Dict mapping field names to expected values or types
            encoding: File encoding (default: utf-8)
            
        Note:
            If the expected value is a type (e.g., `str`, `datetime`),
            this method will check the type. Otherwise, it checks for equality.
            
        Example:
            >>> helper.assert_frontmatter_fields(
            ...     note_path,
            ...     {
            ...         "author": "Test Author",  # Exact match
            ...         "created": datetime,      # Type check
            ...         "tags": ["test", "demo"]  # Exact match
            ...     }
            ... )
        """
        assert file_path.exists(), f"File {file_path} does not exist"
        
        content = file_path.read_text(encoding=encoding)
        post = frontmatter.loads(content)

        for key, expected_value in expected_fields.items():
            assert key in post.metadata, f"Field '{key}' not found in frontmatter"
            actual_value = post.metadata[key]

            if isinstance(expected_value, type):
                assert isinstance(actual_value, expected_value), (
                    f"Field '{key}' expected type {expected_value.__name__}, "
                    f"got {type(actual_value).__name__}"
                )
            else:
                assert actual_value == expected_value, (
                    f"Field '{key}' expected {expected_value!r}, "
                    f"got {actual_value!r}"
                )

    @staticmethod
    def create_test_config(
        temp_dir: Path,
        default_note_dir: str = "notes",
        default_author: str = "Test Author",
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """Create a test configuration dictionary.
        
        Args:
            temp_dir: Base directory for the vault
            default_note_dir: Default subdirectory for notes
            default_author: Default author name
            encoding: File encoding
            
        Returns:
            Configuration dictionary suitable for testing
        """
        return {
            "vault_path": temp_dir,
            "default_note_dir": default_note_dir,
            "default_author": default_author,
            "encoding": encoding,
        }

    @staticmethod
    def setup_test_vault(temp_dir: Path) -> Path:
        """Initialize a test vault directory structure.
        
        Creates a standard vault structure with common subdirectories.
        
        Args:
            temp_dir: Base temporary directory
            
        Returns:
            Path to the created vault directory
        """
        vault_dir = temp_dir / "test_vault"
        vault_dir.mkdir(exist_ok=True)

        # Create common subdirectories
        (vault_dir / "notes").mkdir(exist_ok=True)
        (vault_dir / "archive").mkdir(exist_ok=True)
        (vault_dir / "templates").mkdir(exist_ok=True)

        return vault_dir

    @staticmethod
    def create_sample_notes(
        vault_dir: Path,
        encoding: str = "utf-8",
    ) -> list[Path]:
        """Create a set of sample notes for testing.
        
        Args:
            vault_dir: Vault directory to create notes in
            encoding: File encoding
            
        Returns:
            List of paths to created notes
        """
        notes = []

        # Basic note with minimal frontmatter
        note1 = MinervaTestHelper.create_temp_note(
            vault_dir / "notes",
            "basic_note.md",
            "This is a basic test note.",
            {"tags": ["basic", "test"]},
            encoding,
        )
        notes.append(note1)

        # Note with full metadata
        note2 = MinervaTestHelper.create_temp_note(
            vault_dir / "notes",
            "detailed_note.md",
            "This is a detailed test note with full metadata.",
            {
                "tags": ["detailed", "metadata", "test"],
                "created": "2025-01-01T12:00:00",
                "updated": "2025-01-02T12:00:00",
                "author": "Test Author",
                "description": "A test note with comprehensive metadata",
            },
            encoding,
        )
        notes.append(note2)

        # Note without tags
        note3 = MinervaTestHelper.create_temp_note(
            vault_dir / "notes",
            "untagged_note.md",
            "This note has no tags.",
            {"author": "Test Author"},
            encoding,
        )
        notes.append(note3)

        # Note in subdirectory
        note4 = MinervaTestHelper.create_temp_note(
            vault_dir / "archive",
            "archived_note.md",
            "This is an archived note.",
            {"tags": ["archive"], "status": "archived"},
            encoding,
        )
        notes.append(note4)

        # Note without frontmatter
        note5 = MinervaTestHelper.create_temp_note(
            vault_dir / "notes",
            "plain_note.md",
            "This is a plain note without frontmatter.",
            None,
            encoding,
        )
        notes.append(note5)

        return notes

    @staticmethod
    def assert_file_exists(file_path: Path, message: Optional[str] = None) -> None:
        """Assert that a file exists.
        
        Args:
            file_path: Path to check
            message: Optional custom error message
        """
        default_message = f"File {file_path} does not exist"
        assert file_path.exists(), message or default_message

    @staticmethod
    def assert_file_not_exists(file_path: Path, message: Optional[str] = None) -> None:
        """Assert that a file does not exist.
        
        Args:
            file_path: Path to check
            message: Optional custom error message
        """
        default_message = f"File {file_path} should not exist"
        assert not file_path.exists(), message or default_message

    @staticmethod
    def get_frontmatter_metadata(file_path: Path, encoding: str = "utf-8") -> Dict[str, Any]:
        """Extract frontmatter metadata from a file.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            Dictionary containing frontmatter metadata
            
        Raises:
            AssertionError: If file doesn't exist
        """
        assert file_path.exists(), f"File {file_path} does not exist"
        
        content = file_path.read_text(encoding=encoding)
        post = frontmatter.loads(content)
        return post.metadata

    @staticmethod
    def get_note_content(file_path: Path, encoding: str = "utf-8") -> str:
        """Extract body content from a note (excluding frontmatter).
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            Note body content
            
        Raises:
            AssertionError: If file doesn't exist
        """
        assert file_path.exists(), f"File {file_path} does not exist"
        
        content = file_path.read_text(encoding=encoding)
        post = frontmatter.loads(content)
        return post.content