"""Common test fixtures and setup."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests.helpers import MinervaTestHelper


@pytest.fixture
def minerva_test_helper():
    """Provides an instance of MinervaTestHelper.

    Returns:
        Instance of MinervaTestHelper
    """
    return MinervaTestHelper()


@pytest.fixture
def test_vault(tmp_path):
    """Create a test Vault directory.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path to the initialized Vault directory
    """
    return MinervaTestHelper.setup_test_vault(tmp_path)


@pytest.fixture
def sample_notes(test_vault, minerva_test_helper):
    """Create sample notes for testing.

    Args:
        test_vault: Test Vault fixture
        minerva_test_helper: MinervaTestHelper fixture

    Returns:
        List of paths to created note files
    """
    return minerva_test_helper.create_sample_notes(test_vault)


# Legacy fixture for backward compatibility
@pytest.fixture
def temp_dir():
    """Fixture that provides a temporary directory for file operations.

    Yields:
        str: Path to a temporary directory that is automatically cleaned up.
    """
    with TemporaryDirectory() as tempdir:
        yield tempdir


@pytest.fixture
def create_test_file(temp_dir):
    """Helper fixture for creating test files with specified content.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        function: Helper function that creates a file with specified name and content
    """

    def _create_file(filename, content):
        file_path = Path(temp_dir) / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    return _create_file


@pytest.fixture
def mock_write_setup(tmp_path):
    """Fixture providing common mock setup for write tests."""
    with (
        mock.patch("minerva.tools.write_file") as mock_write_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}
