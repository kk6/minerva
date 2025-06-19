"""
Merge strategy processors for note merging operations.

This module contains the implementation of different merging strategies
that can be applied when combining multiple notes into a single note.
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

from minerva.frontmatter_manager import FrontmatterManager

logger = logging.getLogger(__name__)


class MergeProcessor(ABC):
    """
    Abstract base class for merge strategy processors.

    Each merge processor implements a specific strategy for combining
    multiple note contents into a single consolidated note.
    """

    def __init__(self, frontmatter_manager: FrontmatterManager):
        """
        Initialize merge processor.

        Args:
            frontmatter_manager: Manager for frontmatter operations
        """
        self.frontmatter_manager = frontmatter_manager

    @abstractmethod
    def process_merge(
        self,
        note_contents: list[tuple[str, str]],  # (file_path, content)
        target_filename: str,
        **options: Any,
    ) -> tuple[str, dict[str, Any], list[str]]:
        """
        Process the merge operation according to the strategy.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target merged file
            **options: Strategy-specific options

        Returns:
            tuple: (merged_content, merge_history, warnings)
        """
        pass

    def _consolidate_frontmatter(
        self,
        note_contents: list[tuple[str, str]],
        target_filename: str,
        preserve_frontmatter: bool = True,
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Consolidate frontmatter from all source notes.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            preserve_frontmatter: Whether to consolidate frontmatter from source files

        Returns:
            tuple: (consolidated_frontmatter, warnings)
        """
        if not preserve_frontmatter:
            # Create minimal frontmatter without source metadata
            return {
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "author": self.frontmatter_manager.default_author,
            }, []

        # Extract metadata from all notes
        metadata_collection, warnings = self._extract_metadata_from_notes(note_contents)

        # Build consolidated frontmatter
        consolidated_metadata = self._build_consolidated_metadata(metadata_collection)
        return consolidated_metadata, warnings

    def _parse_date_robustly(
        self, date_value: Any
    ) -> tuple[datetime | None, str | None]:
        """
        Robustly parse various date formats into datetime objects.

        Args:
            date_value: Date value from frontmatter (str, datetime, or other)

        Returns:
            tuple: (parsed_datetime, warning_message)
        """
        if date_value is None:
            return None, None

        # If already a datetime object, return as-is
        if isinstance(date_value, datetime):
            return date_value, None

        # If not a string, try to convert
        if not isinstance(date_value, str):
            try:
                date_value = str(date_value)
            except Exception:
                return (
                    None,
                    f"Could not convert date value to string: {type(date_value)}",
                )

        # List of common date formats to try
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds and Z
            "%Y-%m-%dT%H:%M:%SZ",  # ISO format with Z
            "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format with microseconds and timezone
            "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
            "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%S",  # ISO format
            "%Y-%m-%d %H:%M:%S",  # Standard datetime
            "%Y-%m-%d",  # Date only
            "%Y/%m/%d %H:%M:%S",  # Alternative format
            "%Y/%m/%d",  # Alternative date only
            "%d-%m-%Y %H:%M:%S",  # European format
            "%d-%m-%Y",  # European date only
            "%d/%m/%Y %H:%M:%S",  # European with slashes
            "%d/%m/%Y",  # European date with slashes
        ]

        # Handle Z timezone manually for fromisoformat
        if date_value.endswith("Z"):
            try:
                return datetime.fromisoformat(date_value.replace("Z", "+00:00")), None
            except ValueError:
                pass

        # Try fromisoformat first (handles most ISO formats)
        try:
            return datetime.fromisoformat(date_value), None
        except ValueError:
            pass

        # Try each format
        for fmt in date_formats:
            try:
                return datetime.strptime(date_value, fmt), None
            except ValueError:
                continue

        # If all fails, return None with warning
        return None, f"Could not parse date format: {date_value}"

    def _extract_metadata_from_notes(
        self, note_contents: list[tuple[str, str]]
    ) -> tuple[dict[str, Any], list[str]]:
        """Extract and collect metadata from all source notes."""
        all_tags: set[str] = set()
        all_aliases: set[str] = set()
        creation_dates: list[Any] = []
        modification_dates: list[Any] = []
        authors: set[str] = set()
        source_files: list[str] = []
        warnings: list[str] = []

        for file_path, content in note_contents:
            file_warnings = self._process_single_note_metadata(
                file_path,
                content,
                all_tags,
                all_aliases,
                creation_dates,
                modification_dates,
                authors,
                source_files,
            )
            warnings.extend(file_warnings)

        metadata_collection = {
            "tags": all_tags,
            "aliases": all_aliases,
            "creation_dates": creation_dates,
            "modification_dates": modification_dates,
            "authors": authors,
            "source_files": source_files,
        }

        return metadata_collection, warnings

    def _process_single_note_metadata(
        self,
        file_path: str,
        content: str,
        all_tags: set[str],
        all_aliases: set[str],
        creation_dates: list[Any],
        modification_dates: list[Any],
        authors: set[str],
        source_files: list[str],
    ) -> list[str]:
        """Process metadata from a single note file."""
        warnings: list[str] = []

        try:
            post = frontmatter.loads(content)
            metadata = post.metadata

            # Collect tags and aliases
            self._collect_tags(metadata, all_tags)
            self._collect_aliases(metadata, all_aliases)

            # Collect dates with robust parsing
            date_warnings = self._process_note_dates(
                metadata, file_path, creation_dates, modification_dates
            )
            warnings.extend(date_warnings)

            # Collect authors
            if "author" in metadata:
                authors.add(metadata["author"])
            else:
                warnings.append(f"No author found in {file_path}")

            source_files.append(str(file_path))

        except Exception as e:
            warning_msg = f"Failed to parse frontmatter from {file_path}: {e}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)

        return warnings

    def _process_note_dates(
        self,
        metadata: dict[str, Any],
        file_path: str,
        creation_dates: list[Any],
        modification_dates: list[Any],
    ) -> list[str]:
        """Process creation and modification dates from note metadata."""
        warnings: list[str] = []
        created_parsed = False

        if "created" in metadata:
            parsed_date, warning = self._parse_date_robustly(metadata["created"])
            if parsed_date:
                creation_dates.append(parsed_date)
                created_parsed = True
            elif warning:
                warnings.append(
                    f"Failed to parse created date in {file_path}: {warning}"
                )

        if "modified" in metadata:
            parsed_date, warning = self._parse_date_robustly(metadata["modified"])
            if parsed_date:
                modification_dates.append(parsed_date)
            elif warning:
                warnings.append(
                    f"Failed to parse modified date in {file_path}: {warning}"
                )
        elif not created_parsed:
            warnings.append(f"No creation or modification date found in {file_path}")

        return warnings

    def _collect_tags(self, metadata: dict, all_tags: set) -> None:
        """Collect tags from metadata into the provided set."""
        if "tags" in metadata:
            if isinstance(metadata["tags"], list):
                all_tags.update(metadata["tags"])
            elif isinstance(metadata["tags"], str):
                all_tags.add(metadata["tags"])

    def _collect_aliases(self, metadata: dict, all_aliases: set) -> None:
        """Collect aliases from metadata into the provided set."""
        if "aliases" in metadata:
            if isinstance(metadata["aliases"], list):
                all_aliases.update(metadata["aliases"])
            elif isinstance(metadata["aliases"], str):
                all_aliases.add(metadata["aliases"])

    def _build_consolidated_metadata(
        self, metadata_collection: dict[str, Any]
    ) -> dict[str, Any]:
        """Build the final consolidated metadata dictionary."""
        consolidated: dict[str, Any] = {
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "author": self.frontmatter_manager.default_author,
        }

        # Add collected metadata if present
        if metadata_collection["tags"]:
            consolidated["tags"] = sorted(list(metadata_collection["tags"]))

        if metadata_collection["aliases"]:
            consolidated["aliases"] = sorted(list(metadata_collection["aliases"]))

        if metadata_collection["creation_dates"]:
            # Filter to only valid datetime objects before finding min
            valid_creation_dates = [
                dt
                for dt in metadata_collection["creation_dates"]
                if isinstance(dt, datetime)
            ]
            if valid_creation_dates:
                consolidated["original_created"] = min(valid_creation_dates)

        if metadata_collection["modification_dates"]:
            # Filter to only valid datetime objects before finding max
            valid_modification_dates = [
                dt
                for dt in metadata_collection["modification_dates"]
                if isinstance(dt, datetime)
            ]
            if valid_modification_dates:
                consolidated["original_modified"] = max(valid_modification_dates)

        if metadata_collection["authors"]:
            consolidated["original_authors"] = sorted(
                list(metadata_collection["authors"])
            )

        # Add merge metadata
        consolidated["merged_from"] = metadata_collection["source_files"]
        consolidated["merge_date"] = datetime.now().isoformat()

        return consolidated


class AppendMergeProcessor(MergeProcessor):
    """
    Simple append merge strategy.

    Concatenates all notes with separators and source file headers.
    """

    def process_merge(
        self,
        note_contents: list[tuple[str, str]],
        target_filename: str,
        separator: str = "\n\n---\n\n",
        create_toc: bool = True,
        **options: Any,
    ) -> tuple[str, dict[str, Any], list[str]]:
        """
        Process merge by appending all notes with separators.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            separator: Separator between merged sections
            create_toc: Whether to create a table of contents
            **options: Additional options (ignored)

        Returns:
            tuple: (merged_content, merge_history, warnings)
        """
        sections: list[str] = []
        merge_history: dict[str, Any] = {"sections": []}
        content_warnings: list[str] = []

        for file_path, content in note_contents:
            # Extract content without frontmatter
            try:
                post = frontmatter.loads(content)
                note_content = post.content
            except Exception as e:
                note_content = content
                content_warnings.append(
                    f"Failed to parse frontmatter from {file_path}, using raw content: {e}"
                )

            # Create section header
            file_name = Path(file_path).stem
            section_header = f"## {file_name}"

            # Build section
            section = f"{section_header}\n\n{note_content.strip()}"
            sections.append(section)

            # Track merge history
            merge_history["sections"].append(
                {
                    "source_file": str(file_path),
                    "section_title": file_name,
                    "content_length": len(note_content),
                }
            )

        # Build final content
        title = f"# {Path(target_filename).stem}"
        content_parts = [title]

        # Add TOC if requested
        if create_toc:
            toc_content = self._generate_toc(merge_history["sections"])
            content_parts.extend(toc_content)

        content_parts.append(separator.join(sections))

        # Consolidate frontmatter
        preserve_frontmatter = options.get("preserve_frontmatter", True)
        consolidated_frontmatter, frontmatter_warnings = self._consolidate_frontmatter(
            note_contents, target_filename, preserve_frontmatter
        )

        # Combine all warnings
        all_warnings = content_warnings + frontmatter_warnings

        # Create final content with frontmatter
        final_content = frontmatter.dumps(
            frontmatter.Post("\n".join(content_parts), **consolidated_frontmatter)
        )

        return final_content, merge_history, all_warnings

    def _generate_toc(self, sections_info: list[dict[str, Any]]) -> list[str]:
        """
        Generate table of contents from sections information.

        Args:
            sections_info: List of section dictionaries with section_title and other info

        Returns:
            List of TOC content lines ready to be added to content
        """
        if not sections_info:
            return []

        toc_lines = ["", "## 目次", ""]

        for section in sections_info:
            section_title = section["section_title"]
            anchor = section_title.lower().replace(" ", "-")
            toc_lines.append(f"- [{section_title}](#{anchor})")

        toc_lines.append("")  # Empty line after TOC
        return toc_lines


class HeadingMergeProcessor(MergeProcessor):
    """
    Heading-based merge strategy.

    Groups content by markdown headings across all notes.
    """

    def process_merge(
        self, note_contents: list[tuple[str, str]], target_filename: str, **options: Any
    ) -> tuple[str, dict[str, Any], list[str]]:
        """
        Process merge by grouping content under headings.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            **options: Additional options (ignored)

        Returns:
            tuple: (merged_content, merge_history, warnings)
        """
        heading_groups: dict[str, list[str]] = {}
        merge_history: dict[str, Any] = {"heading_groups": {}}
        content_warnings: list[str] = []

        for file_path, content in note_contents:
            # Extract content without frontmatter
            try:
                post = frontmatter.loads(content)
                note_content = post.content
            except Exception as e:
                note_content = content
                content_warnings.append(
                    f"Failed to parse frontmatter from {file_path}, using raw content: {e}"
                )

            # Parse headings and content
            sections = self._parse_sections(note_content)

            for heading, section_content in sections:
                if heading not in heading_groups:
                    heading_groups[heading] = []
                    merge_history["heading_groups"][heading] = []

                heading_groups[heading].append(section_content)
                merge_history["heading_groups"][heading].append(
                    {
                        "source_file": str(file_path),
                        "content_length": len(section_content),
                    }
                )

        # Build merged content
        title = f"# {Path(target_filename).stem}"
        content_parts = [title, ""]

        # Sort headings and build content
        for heading in sorted(heading_groups.keys()):
            if heading != "# " + Path(target_filename).stem:  # Avoid duplicate title
                content_parts.append(f"## {heading.lstrip('# ')}")
                content_parts.append("")

                # Combine all content under this heading
                combined_content = "\n\n".join(heading_groups[heading])
                content_parts.append(combined_content)
                content_parts.append("")

        # Consolidate frontmatter
        preserve_frontmatter = options.get("preserve_frontmatter", True)
        consolidated_frontmatter, frontmatter_warnings = self._consolidate_frontmatter(
            note_contents, target_filename, preserve_frontmatter
        )

        # Combine all warnings
        all_warnings = content_warnings + frontmatter_warnings

        # Create final content with frontmatter
        final_content = frontmatter.dumps(
            frontmatter.Post("\n".join(content_parts), **consolidated_frontmatter)
        )

        return final_content, merge_history, all_warnings

    def _parse_sections(self, content: str) -> list[tuple[str, str]]:
        """
        Parse content into sections based on headings.

        Args:
            content: Markdown content to parse

        Returns:
            list: List of (heading, content) tuples
        """
        lines = content.split("\n")
        sections: list[tuple[str, str]] = []
        current_heading = "その他"
        current_content: list[str] = []

        for line in lines:
            if re.match(r"^#+\s+", line):  # Heading line
                # Save previous section
                if current_content:
                    sections.append(
                        (current_heading, "\n".join(current_content).strip())
                    )

                # Start new section
                current_heading = line.strip()
                current_content = []
            else:
                current_content.append(line)

        # Save final section
        if current_content:
            sections.append((current_heading, "\n".join(current_content).strip()))

        return sections


class DateMergeProcessor(MergeProcessor):
    """
    Date-based merge strategy.

    Sorts notes by creation or modification dates.
    """

    def process_merge(
        self,
        note_contents: list[tuple[str, str]],
        target_filename: str,
        sort_by: str = "created",
        separator: str = "\n\n---\n\n",
        create_toc: bool = True,
        **options: Any,
    ) -> tuple[str, dict[str, Any], list[str]]:
        """
        Process merge by sorting notes by date.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            sort_by: Sort by "created" or "modified" date
            separator: Separator between sections
            create_toc: Whether to create table of contents
            **options: Additional options (ignored)

        Returns:
            tuple: (merged_content, merge_history, warnings)
        """
        # Extract dates and sort
        dated_contents = []

        for file_path, content in note_contents:
            try:
                post = frontmatter.loads(content)
                metadata = post.metadata

                # Get date for sorting with robust parsing
                date_value = metadata.get(sort_by)
                if date_value:
                    parsed_date, warning = self._parse_date_robustly(date_value)
                    if parsed_date:
                        sort_date = parsed_date
                    else:
                        # Use file modification time as fallback
                        sort_date = datetime.fromtimestamp(
                            Path(file_path).stat().st_mtime
                        )
                        logger.warning(
                            "Failed to parse %s date for %s (%s), using file mtime",
                            sort_by,
                            file_path,
                            warning or "unknown format",
                        )
                else:
                    # Fallback to file modification time
                    sort_date = datetime.fromtimestamp(Path(file_path).stat().st_mtime)

                dated_contents.append((sort_date, file_path, content))

            except Exception as e:
                logger.warning("Failed to extract date from %s: %s", file_path, e)
                # Use file modification time as fallback
                sort_date = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
                dated_contents.append((sort_date, file_path, content))

        # Sort by date
        dated_contents.sort(key=lambda x: x[0])

        # Use AppendMergeProcessor for actual merging with sorted content
        sorted_note_contents = [
            (file_path, content) for _, file_path, content in dated_contents
        ]

        append_processor = AppendMergeProcessor(self.frontmatter_manager)
        merged_content, merge_history, warnings = append_processor.process_merge(
            sorted_note_contents,
            target_filename,
            separator=separator,
            create_toc=create_toc,
            **options,
        )

        # Add date sorting information to merge history
        merge_history["sort_strategy"] = sort_by
        merge_history["date_order"] = [
            {"file": str(file_path), "date": date.isoformat()}
            for date, file_path, _ in dated_contents
        ]

        return merged_content, merge_history, warnings


class SmartMergeProcessor(MergeProcessor):
    """
    Smart merge strategy.

    Analyzes content and chooses the best merging approach.
    """

    def process_merge(
        self, note_contents: list[tuple[str, str]], target_filename: str, **options: Any
    ) -> tuple[str, dict[str, Any], list[str]]:
        """
        Process merge using intelligent content analysis.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            **options: Additional options

        Returns:
            tuple: (merged_content, merge_history, warnings)
        """
        # Analyze content to determine best strategy
        group_by_hint = options.get("group_by", "heading")
        strategy = self._analyze_best_strategy(note_contents, group_by_hint)

        # Delegate to appropriate processor
        processor: MergeProcessor
        if strategy == "by_heading":
            processor = HeadingMergeProcessor(self.frontmatter_manager)
        elif strategy == "by_date":
            processor = DateMergeProcessor(self.frontmatter_manager)
        else:
            processor = AppendMergeProcessor(self.frontmatter_manager)

        merged_content, merge_history, warnings = processor.process_merge(
            note_contents, target_filename, **options
        )

        # Add strategy selection info to merge history
        merge_history["smart_strategy_selected"] = strategy

        return merged_content, merge_history, warnings

    def _analyze_best_strategy(
        self, note_contents: list[tuple[str, str]], group_by_hint: str = "heading"
    ) -> str:
        """
        Analyze content to determine the best merging strategy.

        Args:
            note_contents: List of tuples containing (file_path, content)
            group_by_hint: Hint for grouping preference ("heading", "tag", "date")

        Returns:
            str: Best strategy ("append", "by_heading", or "by_date")
        """
        has_consistent_headings, has_dates = self._analyze_content_patterns(
            note_contents
        )
        return self._select_strategy_with_hint(
            has_consistent_headings, has_dates, len(note_contents), group_by_hint
        )

    def _analyze_content_patterns(
        self, note_contents: list[tuple[str, str]]
    ) -> tuple[int, int]:
        """Analyze content patterns in notes to determine structure."""
        has_consistent_headings = 0
        has_dates = 0
        common_headings = set()
        first_note = True

        for file_path, content in note_contents:
            try:
                post = frontmatter.loads(content)
                note_content = post.content
                metadata = post.metadata

                # Check for dates
                if "created" in metadata or "modified" in metadata:
                    has_dates += 1

                # Check for headings
                headings = re.findall(r"^#+\s+(.+)$", note_content, re.MULTILINE)
                if headings:
                    if first_note:
                        common_headings.update(headings)
                        first_note = False
                    else:
                        common_headings.intersection_update(headings)

                    if len(common_headings) > 0:
                        has_consistent_headings += 1

            except Exception:
                continue

        return has_consistent_headings, has_dates

    def _select_strategy_with_hint(
        self,
        has_consistent_headings: int,
        has_dates: int,
        total_notes: int,
        group_by_hint: str,
    ) -> str:
        """Select the best strategy based on analysis and hint."""
        # If specific hint provided, bias toward that strategy if viable
        if group_by_hint == "date" and has_dates >= total_notes * 0.5:
            return "by_date"
        if group_by_hint == "heading" and has_consistent_headings >= total_notes * 0.4:
            return "by_heading"

        # Default analysis (higher thresholds without specific hint)
        if has_consistent_headings >= total_notes * 0.6:
            return "by_heading"
        if has_dates >= total_notes * 0.8:
            return "by_date"

        return "append"
