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
    ) -> tuple[str, dict[str, Any]]:
        """
        Process the merge operation according to the strategy.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target merged file
            **options: Strategy-specific options

        Returns:
            tuple: (merged_content, merge_history)
        """
        pass

    def _consolidate_frontmatter(
        self, note_contents: list[tuple[str, str]], target_filename: str
    ) -> dict[str, Any]:
        """
        Consolidate frontmatter from all source notes.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file

        Returns:
            dict: Consolidated frontmatter
        """
        # Extract metadata from all notes
        metadata_collection = self._extract_metadata_from_notes(note_contents)

        # Build consolidated frontmatter
        return self._build_consolidated_metadata(metadata_collection)

    def _extract_metadata_from_notes(
        self, note_contents: list[tuple[str, str]]
    ) -> dict[str, Any]:
        """Extract and collect metadata from all source notes."""
        all_tags: set[str] = set()
        all_aliases: set[str] = set()
        creation_dates: list[Any] = []
        modification_dates: list[Any] = []
        authors: set[str] = set()
        source_files: list[str] = []

        for file_path, content in note_contents:
            try:
                post = frontmatter.loads(content)
                metadata = post.metadata

                # Collect tags
                self._collect_tags(metadata, all_tags)

                # Collect aliases
                self._collect_aliases(metadata, all_aliases)

                # Collect dates
                if "created" in metadata:
                    creation_dates.append(metadata["created"])
                if "modified" in metadata:
                    modification_dates.append(metadata["modified"])

                # Collect authors
                if "author" in metadata:
                    authors.add(metadata["author"])

                source_files.append(str(file_path))

            except Exception as e:
                logger.warning("Failed to parse frontmatter from %s: %s", file_path, e)

        return {
            "tags": all_tags,
            "aliases": all_aliases,
            "creation_dates": creation_dates,
            "modification_dates": modification_dates,
            "authors": authors,
            "source_files": source_files,
        }

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
            consolidated["original_created"] = min(
                metadata_collection["creation_dates"]
            )

        if metadata_collection["modification_dates"]:
            consolidated["original_modified"] = max(
                metadata_collection["modification_dates"]
            )

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
    ) -> tuple[str, dict[str, Any]]:
        """
        Process merge by appending all notes with separators.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            separator: Separator between merged sections
            create_toc: Whether to create a table of contents
            **options: Additional options (ignored)

        Returns:
            tuple: (merged_content, merge_history)
        """
        sections: list[str] = []
        merge_history: dict[str, Any] = {"sections": []}
        toc_entries: list[str] = []

        for file_path, content in note_contents:
            # Extract content without frontmatter
            try:
                post = frontmatter.loads(content)
                note_content = post.content
            except Exception:
                note_content = content

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

            # Add to TOC
            if create_toc:
                toc_entries.append(
                    f"- [{file_name}](#{file_name.lower().replace(' ', '-')})"
                )

        # Build final content
        title = f"# {Path(target_filename).stem}"
        content_parts = [title]

        if create_toc and toc_entries:
            content_parts.extend(["", "## 目次", "", "\n".join(toc_entries), ""])

        content_parts.append(separator.join(sections))

        # Consolidate frontmatter
        consolidated_frontmatter = self._consolidate_frontmatter(
            note_contents, target_filename
        )

        # Create final content with frontmatter
        final_content = frontmatter.dumps(
            frontmatter.Post("\n".join(content_parts), **consolidated_frontmatter)
        )

        return final_content, merge_history


class HeadingMergeProcessor(MergeProcessor):
    """
    Heading-based merge strategy.

    Groups content by markdown headings across all notes.
    """

    def process_merge(
        self, note_contents: list[tuple[str, str]], target_filename: str, **options: Any
    ) -> tuple[str, dict[str, Any]]:
        """
        Process merge by grouping content under headings.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            **options: Additional options (ignored)

        Returns:
            tuple: (merged_content, merge_history)
        """
        heading_groups: dict[str, list[str]] = {}
        merge_history: dict[str, Any] = {"heading_groups": {}}

        for file_path, content in note_contents:
            # Extract content without frontmatter
            try:
                post = frontmatter.loads(content)
                note_content = post.content
            except Exception:
                note_content = content

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
        consolidated_frontmatter = self._consolidate_frontmatter(
            note_contents, target_filename
        )

        # Create final content with frontmatter
        final_content = frontmatter.dumps(
            frontmatter.Post("\n".join(content_parts), **consolidated_frontmatter)
        )

        return final_content, merge_history

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
    ) -> tuple[str, dict[str, Any]]:
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
            tuple: (merged_content, merge_history)
        """
        # Extract dates and sort
        dated_contents = []

        for file_path, content in note_contents:
            try:
                post = frontmatter.loads(content)
                metadata = post.metadata

                # Get date for sorting
                date_str = metadata.get(sort_by)
                if date_str:
                    if isinstance(date_str, str):
                        try:
                            sort_date = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except ValueError:
                            sort_date = datetime.min
                    else:
                        sort_date = date_str
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
        merged_content, merge_history = append_processor.process_merge(
            sorted_note_contents,
            target_filename,
            separator=separator,
            create_toc=create_toc,
        )

        # Add date sorting information to merge history
        merge_history["sort_strategy"] = sort_by
        merge_history["date_order"] = [
            {"file": str(file_path), "date": date.isoformat()}
            for date, file_path, _ in dated_contents
        ]

        return merged_content, merge_history


class SmartMergeProcessor(MergeProcessor):
    """
    Smart merge strategy.

    Analyzes content and chooses the best merging approach.
    """

    def process_merge(
        self, note_contents: list[tuple[str, str]], target_filename: str, **options: Any
    ) -> tuple[str, dict[str, Any]]:
        """
        Process merge using intelligent content analysis.

        Args:
            note_contents: List of tuples containing (file_path, content)
            target_filename: Name of the target file
            **options: Additional options

        Returns:
            tuple: (merged_content, merge_history)
        """
        # Analyze content to determine best strategy
        strategy = self._analyze_best_strategy(note_contents)

        # Delegate to appropriate processor
        processor: MergeProcessor
        if strategy == "by_heading":
            processor = HeadingMergeProcessor(self.frontmatter_manager)
        elif strategy == "by_date":
            processor = DateMergeProcessor(self.frontmatter_manager)
        else:
            processor = AppendMergeProcessor(self.frontmatter_manager)

        merged_content, merge_history = processor.process_merge(
            note_contents, target_filename, **options
        )

        # Add strategy selection info to merge history
        merge_history["smart_strategy_selected"] = strategy

        return merged_content, merge_history

    def _analyze_best_strategy(self, note_contents: list[tuple[str, str]]) -> str:
        """
        Analyze content to determine the best merging strategy.

        Args:
            note_contents: List of tuples containing (file_path, content)

        Returns:
            str: Best strategy ("append", "by_heading", or "by_date")
        """
        has_consistent_headings = 0
        has_dates = 0
        total_notes = len(note_contents)

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

        # Decision logic
        if has_consistent_headings >= total_notes * 0.6:  # 60% have common headings
            return "by_heading"
        elif has_dates >= total_notes * 0.8:  # 80% have dates
            return "by_date"
        else:
            return "append"
