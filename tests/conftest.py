"""Pytest configuration and shared fixtures for Minerva tests."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pytest

from tests.helpers import MinervaTestHelper


@pytest.fixture
def minerva_test_helper():
    """Provide a MinervaTestHelper instance for tests.
    
    Returns:
        MinervaTestHelper: Instance of the test helper class
    """
    return MinervaTestHelper()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for file operations.
    
    This fixture is maintained for backward compatibility with existing tests.
    
    Yields:
        str: Path to a temporary directory that is automatically cleaned up
    """
    with TemporaryDirectory() as tempdir:
        yield tempdir


@pytest.fixture
def test_vault(tmp_path, minerva_test_helper):
    """Create a test vault with standard directory structure.
    
    Args:
        tmp_path: pytest temporary path fixture
        minerva_test_helper: MinervaTestHelper instance
        
    Returns:
        Path: Path to the created test vault
    """
    return minerva_test_helper.setup_test_vault(tmp_path)


@pytest.fixture
def sample_notes(test_vault, minerva_test_helper):
    """Create sample notes for testing.
    
    Creates a variety of notes with different frontmatter configurations
    to support comprehensive testing scenarios.
    
    Args:
        test_vault: Test vault fixture
        minerva_test_helper: MinervaTestHelper instance
        
    Returns:
        list[Path]: List of paths to created sample notes
    """
    return minerva_test_helper.create_sample_notes(test_vault)


@pytest.fixture
def mock_vault_path(tmp_path):
    """Mock the VAULT_PATH for tools tests.
    
    This fixture provides backward compatibility for existing tests
    that use VAULT_PATH mocking.
    
    Args:
        tmp_path: pytest temporary path fixture
        
    Yields:
        dict: Dictionary containing mock object and tmp_path
    """
    with mock.patch("minerva.tools.VAULT_PATH", tmp_path) as mock_vault:
        yield {"mock_vault": mock_vault, "tmp_path": tmp_path}


@pytest.fixture
def mock_write_setup(tmp_path):
    """Common mock setup for write operation tests.
    
    Provides mocking for both write_file function and VAULT_PATH.
    This fixture maintains compatibility with existing test patterns.
    
    Args:
        tmp_path: pytest temporary path fixture
        
    Yields:
        dict: Dictionary containing mock objects and tmp_path
    """
    with (
        mock.patch("minerva.tools.write_file") as mock_write_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {
            "mock_write_file": mock_write_file,
            "tmp_path": tmp_path,
        }


@pytest.fixture
def mock_read_setup(tmp_path):
    """Common mock setup for read operation tests.
    
    Provides mocking for both read_file function and VAULT_PATH.
    
    Args:
        tmp_path: pytest temporary path fixture
        
    Yields:
        dict: Dictionary containing mock objects and tmp_path
    """
    with (
        mock.patch("minerva.tools.read_file") as mock_read_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {
            "mock_read_file": mock_read_file,
            "tmp_path": tmp_path,
        }


@pytest.fixture
def mock_delete_setup(tmp_path):
    """Common mock setup for delete operation tests.
    
    Provides mocking for both delete_file function and VAULT_PATH.
    
    Args:
        tmp_path: pytest temporary path fixture
        
    Yields:
        dict: Dictionary containing mock objects and tmp_path
    """
    with (
        mock.patch("minerva.tools.delete_file") as mock_delete_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {
            "mock_delete_file": mock_delete_file,
            "tmp_path": tmp_path,
        }


@pytest.fixture
def sample_frontmatter_note(tmp_path, minerva_test_helper):
    """Create a single note with comprehensive frontmatter for testing.
    
    Args:
        tmp_path: pytest temporary path fixture
        minerva_test_helper: MinervaTestHelper instance
        
    Returns:
        Path: Path to the created note
    """
    return minerva_test_helper.create_temp_note(
        tmp_path,
        "frontmatter_test.md",
        "This is a test note with comprehensive frontmatter.",
        {
            "tags": ["test", "frontmatter", "sample"],
            "created": "2025-01-01T12:00:00",
            "updated": "2025-01-02T12:00:00",
            "author": "Test Author",
            "description": "A comprehensive test note",
            "status": "active",
        },
    )


@pytest.fixture
def plain_note(tmp_path, minerva_test_helper):
    """Create a plain note without frontmatter for testing.
    
    Args:
        tmp_path: pytest temporary path fixture
        minerva_test_helper: MinervaTestHelper instance
        
    Returns:
        Path: Path to the created note
    """
    return minerva_test_helper.create_temp_note(
        tmp_path,
        "plain_test.md",
        "This is a plain test note without frontmatter.",
        None,
    )