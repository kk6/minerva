"""Unified test helper utilities for Minerva project."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import frontmatter


class MinervaTestHelper:
    """Test helper class for the Minerva project."""

    @staticmethod
    def create_temp_note(
        temp_dir: Path,
        filename: str,
        content: str,
        frontmatter_data: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Create a test note.

        Args:
            temp_dir: Path to the temporary directory
            filename: File name
            content: Note content
            frontmatter_data: Frontmatter data (optional)

        Returns:
            Path to the created file
        """
        if frontmatter_data:
            post = frontmatter.Post(content)
            post.metadata.update(frontmatter_data)
            content_with_frontmatter = frontmatter.dumps(post)
        else:
            content_with_frontmatter = content

        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_with_frontmatter, encoding="utf-8")
        return file_path

    @staticmethod
    def assert_note_content(
        file_path: Path,
        expected_content: str,
        expected_frontmatter: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Verify the content of a note.

        Args:
            file_path: Path to the file to check
            expected_content: Expected content
            expected_frontmatter: Expected frontmatter (optional)
        """
        assert file_path.exists(), f"File {file_path} does not exist"

        content = file_path.read_text(encoding="utf-8")

        if expected_frontmatter:
            post = frontmatter.loads(content)
            assert post.content.strip() == expected_content.strip()
            for key, value in expected_frontmatter.items():
                assert key in post.metadata
                assert post.metadata[key] == value
        else:
            assert content.strip() == expected_content.strip()

    @staticmethod
    def assert_frontmatter_fields(
        file_path: Path, expected_fields: Dict[str, Union[Any, type]]
    ) -> None:
        """Verify frontmatter fields.

        Args:
            file_path: Path to the file to check
            expected_fields: Expected fields (value or type)
        """
        content = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(content)

        for key, expected_value in expected_fields.items():
            assert key in post.metadata, f"Field '{key}' not found in frontmatter"
            actual_value = post.metadata[key]

            if isinstance(expected_value, type):
                assert isinstance(actual_value, expected_value), (
                    f"Field '{key}' expected type {expected_value}, got {type(actual_value)}"
                )
            else:
                assert actual_value == expected_value, (
                    f"Field '{key}' expected {expected_value}, got {actual_value}"
                )

    @staticmethod
    def create_test_config(temp_dir: Path) -> Dict[str, Any]:
        """Create a test configuration.

        Args:
            temp_dir: Path to the temporary directory

        Returns:
            Dictionary for test configuration
        """
        return {
            "vault_path": temp_dir,
            "default_note_dir": "test_notes",
            "default_author": "Test Author",
            "encoding": "utf-8",
        }

    @staticmethod
    def setup_test_vault(temp_dir: Path) -> Path:
        """Initialize a test Vault.

        Args:
            temp_dir: Path to the temporary directory

        Returns:
            Path to the initialized Vault directory
        """
        vault_dir = temp_dir / "test_vault"
        vault_dir.mkdir(exist_ok=True)

        # Create subdirectories for testing
        (vault_dir / "test_notes").mkdir(exist_ok=True)
        (vault_dir / "archive").mkdir(exist_ok=True)

        return vault_dir

    @staticmethod
    def create_sample_notes(vault_dir: Path) -> List[Path]:
        """Create sample notes.

        Args:
            vault_dir: Path to the Vault directory

        Returns:
            List of paths to created note files
        """
        notes = []
        notes_dir = vault_dir / "test_notes"

        # Basic note
        note1 = MinervaTestHelper.create_temp_note(
            notes_dir,
            "sample1.md",
            "This is a sample note",
            {"tags": ["sample", "test"]},
        )
        notes.append(note1)

        # Note with complex frontmatter
        note2 = MinervaTestHelper.create_temp_note(
            notes_dir,
            "sample2.md",
            "Another sample note with more content",
            {
                "tags": ["example", "documentation"],
                "created": "2025-01-01T00:00:00",
                "author": "Test Author",
            },
        )
        notes.append(note2)

        return notes

    @staticmethod
    def assert_file_exists(file_path: Path) -> None:
        """Check that a file exists.

        Args:
            file_path: Path to the file to check
        """
        assert file_path.exists(), f"File {file_path} does not exist"

    @staticmethod
    def assert_file_not_exists(file_path: Path) -> None:
        """Check that a file does not exist.

        Args:
            file_path: Path to the file to check
        """
        assert not file_path.exists(), f"File {file_path} should not exist"

    @staticmethod
    def create_test_file_with_content(
        temp_dir: Path, filename: str, content: str
    ) -> Path:
        """Create a test file (without frontmatter).

        Args:
            temp_dir: Path to the temporary directory
            filename: File name
            content: File content

        Returns:
            Path to the created file
        """
        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path
