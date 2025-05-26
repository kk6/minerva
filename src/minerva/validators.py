"""
Unified validation logic for the Minerva application.

This module provides centralized validation classes to ensure consistency
across all request models and reduce code duplication.
"""

import os
import re
from pathlib import Path


class FilenameValidator:
    """
    Validator for filename operations.
    
    Provides unified validation for filenames used across the application,
    ensuring they meet security and filesystem requirements.
    """
    
    FORBIDDEN_CHARS = set('<>:"/\\|?*')
    
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """
        Validate filename for security and filesystem compatibility.
        
        Args:
            filename: The filename to validate
            
        Returns:
            str: The validated filename
            
        Raises:
            ValueError: If filename is invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        if os.path.isabs(filename):
            raise ValueError("Filename cannot be an absolute path")
        if any(char in filename for char in cls.FORBIDDEN_CHARS):
            raise ValueError(f"Filename contains forbidden characters: {cls.FORBIDDEN_CHARS}")
        return filename
    
    @classmethod
    def validate_filename_with_subdirs(cls, filename: str) -> str:
        """
        Validate a filename that may contain subdirectories.
        
        Only validates the final filename component, allowing subdirectories
        in the path as long as they use forward slashes and don't contain
        forbidden characters other than forward slashes.
        
        Args:
            filename: The filename (may include subdirectories)
            
        Returns:
            str: The validated filename
            
        Raises:
            ValueError: If filename is invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        if os.path.isabs(filename):
            raise ValueError("Filename cannot be an absolute path")
            
        # Split into path components
        path = Path(filename)
        
        # Validate each path component for forbidden chars (excluding forward slash)
        forbidden_chars_no_slash = cls.FORBIDDEN_CHARS - {'/'}
        for part in path.parts:
            if any(char in part for char in forbidden_chars_no_slash):
                raise ValueError(f"Filename contains forbidden characters: {cls.FORBIDDEN_CHARS}")
        
        # Validate the final filename component isn't empty
        if not path.name:
            raise ValueError("Filename cannot be empty")
            
        return filename


class TagValidator:
    """
    Validator for tag operations.
    
    Provides unified validation and normalization for tags used in notes,
    ensuring consistency across tag operations.
    """
    
    FORBIDDEN_CHARS = set(',<>/?\'"`')
    _FORBIDDEN_TAG_CHARS_PATTERN = re.compile(r"[,<>/?'\"]")
    
    @classmethod
    def validate_tag(cls, tag: str) -> str:
        """
        Validate a tag for forbidden characters and emptiness.
        
        Args:
            tag: The tag string to validate
            
        Returns:
            str: The validated tag
            
        Raises:
            ValueError: If tag is invalid
        """
        if not tag or not tag.strip():
            raise ValueError("Tag cannot be empty")
        if any(char in tag for char in cls.FORBIDDEN_CHARS):
            raise ValueError(f"Tag contains forbidden characters: {cls.FORBIDDEN_CHARS}")
        return tag
    
    @classmethod
    def normalize_tag(cls, tag: str) -> str:
        """
        Normalize a tag to its standard form.
        
        Converts tag to lowercase and strips leading/trailing whitespace.
        
        Args:
            tag: The tag string to normalize
            
        Returns:
            str: The normalized tag
        """
        return tag.strip().lower()
    
    @classmethod
    def validate_normalized_tag(cls, tag: str) -> bool:
        """
        Check if a normalized tag is valid.
        
        Args:
            tag: The normalized tag string to validate
            
        Returns:
            bool: True if the tag is valid, False otherwise
        """
        if not tag:  # Empty tags (e.g., after normalization of "   ") are not allowed
            return False
        return not bool(cls._FORBIDDEN_TAG_CHARS_PATTERN.search(tag))


class PathValidator:
    """
    Validator for directory and file path operations.
    
    Provides unified validation for paths used across the application.
    """
    
    @classmethod
    def validate_directory_path(cls, path: str) -> str:
        """
        Validate that a directory path is absolute.
        
        Args:
            path: The directory path to validate
            
        Returns:
            str: The validated directory path
            
        Raises:
            ValueError: If path is not absolute
        """
        if not os.path.isabs(path):
            raise ValueError("Directory must be an absolute path")
        return path
    
    @classmethod
    def validate_directory_exists(cls, path: str) -> str:
        """
        Validate that a directory exists.
        
        Args:
            path: The directory path to validate
            
        Returns:
            str: The validated directory path
            
        Raises:
            ValueError: If directory does not exist
        """
        path_obj = Path(path)
        if not path_obj.is_dir():
            raise ValueError(f"Directory {path} does not exist")
        return path