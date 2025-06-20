"""
Data models for Minerva application.

This module contains dataclasses and enums used throughout the application
for structured data representation and type safety.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class MergeStrategy(Enum):
    """
    Enumeration of available note merging strategies.

    Each strategy defines a different approach to combining multiple notes
    into a single consolidated note.
    """

    APPEND = "append"
    """Simple concatenation with separators between notes."""

    BY_HEADING = "by_heading"
    """Group content by markdown headings across all notes."""

    BY_DATE = "by_date"
    """Sort notes by creation/modification dates."""

    SMART = "smart"
    """Intelligent content analysis and optimal grouping."""


@dataclass
class MergeOptions:
    """
    Configuration options for note merging operations.

    This dataclass groups related merge parameters to reduce complexity
    in function signatures and improve maintainability.
    """

    merge_strategy: str = "append"
    """Strategy to use for merging ("append", "by_heading", "by_date", "smart")."""

    separator: str = "\n\n---\n\n"
    """Separator between merged sections (for append strategy)."""

    preserve_frontmatter: bool = True
    """Whether to consolidate frontmatter from source files."""

    delete_sources: bool = False
    """Whether to delete source files after successful merge."""

    create_toc: bool = True
    """Whether to create a table of contents (for applicable strategies)."""

    author: str | None = None
    """Author name for the merged note."""

    default_path: str | None = None
    """Subfolder within vault to save the merged note."""

    group_by: str = "heading"
    """Hint for grouping preference ("heading", "tag", "date") for smart merge."""


@dataclass
class MergeResult:
    """
    Result of a note merging operation.

    Contains information about the merge process including success status,
    file locations, and any issues encountered during the operation.
    """

    source_files: list[str]
    """List of source file paths that were merged."""

    target_file: Path
    """Path to the created merged file."""

    merge_strategy: MergeStrategy
    """Strategy used for merging the notes."""

    files_processed: int
    """Number of files successfully processed and merged."""

    warnings: list[str]
    """List of non-fatal warnings encountered during merge."""

    merge_history: dict[str, Any]
    """Record of which content sections came from which source files."""

    def to_dict(self) -> dict:
        """
        Convert MergeResult to dictionary for serialization.

        Returns:
            dict: Dictionary representation suitable for JSON serialization
        """
        return {
            "source_files": self.source_files,
            "target_file": str(self.target_file),
            "merge_strategy": self.merge_strategy.value,
            "files_processed": self.files_processed,
            "warnings": self.warnings,
            "merge_history": self.merge_history,
        }


@dataclass
class DuplicateFile:
    """
    Represents a single file in a duplicate detection result.

    Contains information about a file that is similar to other files
    in the same duplicate group.
    """

    file_path: str
    """Path to the file relative to vault root."""

    title: str | None = None
    """Title of the note (from frontmatter or filename)."""

    similarity_score: float = 0.0
    """Similarity score with other files in the group (0.0-1.0)."""

    content_preview: str = ""
    """Preview of the file content (first few lines)."""

    file_size: int = 0
    """Size of the file in bytes."""

    modified_date: str | None = None
    """Last modification date of the file."""

    def to_dict(self) -> dict:
        """
        Convert DuplicateFile to dictionary for serialization.

        Returns:
            dict: Dictionary representation suitable for JSON serialization
        """
        return {
            "file_path": self.file_path,
            "title": self.title,
            "similarity_score": self.similarity_score,
            "content_preview": self.content_preview,
            "file_size": self.file_size,
            "modified_date": self.modified_date,
        }


@dataclass
class DuplicateGroup:
    """
    Represents a group of similar files detected as potential duplicates.

    Groups files that have similarity scores above the specified threshold
    and provides aggregate information about the group.
    """

    group_id: int
    """Unique identifier for this duplicate group."""

    files: list[DuplicateFile]
    """List of files in this duplicate group."""

    average_similarity: float
    """Average similarity score between all files in the group."""

    max_similarity: float
    """Maximum similarity score found within the group."""

    min_similarity: float
    """Minimum similarity score found within the group."""

    file_count: int
    """Number of files in this group."""

    total_size: int
    """Total size of all files in the group (bytes)."""

    def to_dict(self) -> dict:
        """
        Convert DuplicateGroup to dictionary for serialization.

        Returns:
            dict: Dictionary representation suitable for JSON serialization
        """
        return {
            "group_id": self.group_id,
            "file_count": self.file_count,
            "average_similarity": self.average_similarity,
            "max_similarity": self.max_similarity,
            "min_similarity": self.min_similarity,
            "total_size": self.total_size,
            "files": [file.to_dict() for file in self.files],
        }


@dataclass
class DuplicateDetectionResult:
    """
    Result of a duplicate detection operation.

    Contains all duplicate groups found and summary information
    about the detection process.
    """

    duplicate_groups: list[DuplicateGroup]
    """List of duplicate groups found."""

    total_files_analyzed: int
    """Total number of files that were analyzed."""

    total_groups_found: int
    """Number of duplicate groups identified."""

    similarity_threshold: float
    """Similarity threshold used for detection."""

    directory_searched: str | None = None
    """Directory that was searched (None for entire vault)."""

    min_content_length: int = 100
    """Minimum content length used for filtering."""

    analysis_time_seconds: float = 0.0
    """Time taken to complete the analysis."""

    def to_dict(self) -> dict:
        """
        Convert DuplicateDetectionResult to dictionary for serialization.

        Returns:
            dict: Dictionary representation suitable for JSON serialization
        """
        return {
            "total_files_analyzed": self.total_files_analyzed,
            "total_groups_found": self.total_groups_found,
            "similarity_threshold": self.similarity_threshold,
            "directory_searched": self.directory_searched,
            "min_content_length": self.min_content_length,
            "analysis_time_seconds": self.analysis_time_seconds,
            "duplicate_groups": [group.to_dict() for group in self.duplicate_groups],
        }
