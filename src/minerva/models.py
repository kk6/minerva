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
