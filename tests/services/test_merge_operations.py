"""
Tests for note merging operations.

This module tests the note merging functionality including different merge strategies
and integration with the service layer.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager
from minerva.models import MergeResult, MergeStrategy
from minerva.services.merge_processors import (
    AppendMergeProcessor,
    HeadingMergeProcessor,
    DateMergeProcessor,
    SmartMergeProcessor,
)
from minerva.services.note_operations import NoteOperations


class TestMergeProcessors:
    """Test the merge processor implementations."""

    @pytest.fixture
    def frontmatter_manager(self):
        """Create a FrontmatterManager for testing."""
        return FrontmatterManager("Test Author")

    @pytest.fixture
    def sample_notes(self):
        """Sample note contents for testing."""
        return [
            ("/path/note1.md", "---\ntags: [meeting]\n---\n# Meeting 1\nContent 1"),
            ("/path/note2.md", "---\ntags: [meeting]\n---\n# Meeting 2\nContent 2"),
        ]

    def test_append_merge_processor(self, frontmatter_manager, sample_notes):
        """Test the append merge processor."""
        processor = AppendMergeProcessor(frontmatter_manager)

        merged_content, merge_history, warnings = processor.process_merge(
            sample_notes, "merged.md"
        )

        assert "# merged" in merged_content.lower()
        assert "## note1" in merged_content
        assert "## note2" in merged_content
        assert "Content 1" in merged_content
        assert "Content 2" in merged_content
        assert "sections" in merge_history
        assert isinstance(warnings, list)

    def test_heading_merge_processor(self, frontmatter_manager, sample_notes):
        """Test the heading merge processor."""
        processor = HeadingMergeProcessor(frontmatter_manager)

        merged_content, merge_history, warnings = processor.process_merge(
            sample_notes, "merged.md"
        )

        assert "# merged" in merged_content.lower()
        assert "heading_groups" in merge_history
        assert merged_content  # Should produce some content
        assert isinstance(warnings, list)

    def test_smart_merge_processor_analysis(self, frontmatter_manager, sample_notes):
        """Test the smart merge processor content analysis."""
        processor = SmartMergeProcessor(frontmatter_manager)

        # Test strategy analysis
        strategy = processor._analyze_best_strategy(sample_notes)
        assert strategy in ["append", "by_heading", "by_date"]

    def test_consolidate_frontmatter(self, frontmatter_manager, sample_notes):
        """Test frontmatter consolidation."""
        processor = AppendMergeProcessor(frontmatter_manager)
        consolidated, warnings = processor._consolidate_frontmatter(
            sample_notes, "merged.md"
        )

        assert "created" in consolidated
        assert "modified" in consolidated
        assert "author" in consolidated
        assert "tags" in consolidated
        assert "merged_from" in consolidated
        assert consolidated["author"] == "Test Author"
        assert isinstance(warnings, list)


class TestNoteOperationsMerge:
    """Test the note operations merge functionality."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            yield vault_path

    @pytest.fixture
    def config(self, temp_vault):
        """Create a test configuration."""
        return MinervaConfig(
            vault_path=temp_vault,
            default_note_dir="notes",
            default_author="Test Author",
        )

    @pytest.fixture
    def note_operations(self, config):
        """Create NoteOperations instance for testing."""
        frontmatter_manager = FrontmatterManager(config.default_author)
        return NoteOperations(config, frontmatter_manager)

    def test_validate_merge_inputs_valid(self, note_operations):
        """Test merge input validation with valid inputs."""
        source_files = ["file1.md", "file2.md"]
        strategy = note_operations._validate_merge_inputs(source_files, "append")

        assert strategy == MergeStrategy.APPEND

    def test_validate_merge_inputs_invalid_strategy(self, note_operations):
        """Test merge input validation with invalid strategy."""
        source_files = ["file1.md", "file2.md"]

        with pytest.raises(ValueError, match="Invalid merge strategy"):
            note_operations._validate_merge_inputs(source_files, "invalid")

    def test_validate_merge_inputs_insufficient_files(self, note_operations):
        """Test merge input validation with insufficient files."""
        with pytest.raises(ValueError, match="At least two source files"):
            note_operations._validate_merge_inputs(["file1.md"], "append")

    def test_get_merge_processor(self, note_operations):
        """Test merge processor selection."""
        append_processor = note_operations._get_merge_processor(MergeStrategy.APPEND)
        assert isinstance(append_processor, AppendMergeProcessor)

        heading_processor = note_operations._get_merge_processor(
            MergeStrategy.BY_HEADING
        )
        assert isinstance(heading_processor, HeadingMergeProcessor)

        date_processor = note_operations._get_merge_processor(MergeStrategy.BY_DATE)
        assert isinstance(date_processor, DateMergeProcessor)

        smart_processor = note_operations._get_merge_processor(MergeStrategy.SMART)
        assert isinstance(smart_processor, SmartMergeProcessor)

    @patch("minerva.services.note_operations.resolve_note_file")
    @patch.object(NoteOperations, "read_note")
    def test_read_and_validate_source_files(
        self, mock_read_note, mock_resolve_note_file, note_operations, temp_vault
    ):
        """Test reading and validating source files."""
        # Mock file resolution and reading
        file1_path = temp_vault / "file1.md"
        file2_path = temp_vault / "file2.md"

        mock_resolve_note_file.side_effect = [file1_path, file2_path]
        mock_read_note.side_effect = ["content1", "content2"]

        # Create mock files
        file1_path.touch()
        file2_path.touch()

        source_files = ["file1.md", "file2.md"]
        result = note_operations._read_and_validate_source_files(source_files, None)

        assert len(result) == 2
        assert result[0] == (str(file1_path), "content1")
        assert result[1] == (str(file2_path), "content2")


class TestMergeModels:
    """Test the merge data models."""

    def test_merge_strategy_enum(self):
        """Test MergeStrategy enum values."""
        assert MergeStrategy.APPEND.value == "append"
        assert MergeStrategy.BY_HEADING.value == "by_heading"
        assert MergeStrategy.BY_DATE.value == "by_date"
        assert MergeStrategy.SMART.value == "smart"

    def test_merge_result_to_dict(self):
        """Test MergeResult serialization."""
        result = MergeResult(
            source_files=["file1.md", "file2.md"],
            target_file=Path("/vault/merged.md"),
            merge_strategy=MergeStrategy.APPEND,
            files_processed=2,
            warnings=[],
            merge_history={"sections": []},
        )

        result_dict = result.to_dict()

        assert result_dict["source_files"] == ["file1.md", "file2.md"]
        assert result_dict["target_file"] == "/vault/merged.md"
        assert result_dict["merge_strategy"] == "append"
        assert result_dict["files_processed"] == 2
        assert result_dict["warnings"] == []
        assert result_dict["merge_history"] == {"sections": []}
