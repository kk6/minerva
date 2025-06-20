"""Common test fixtures and setup."""

import os
import pytest
import time_machine
from datetime import datetime
from tests.helpers import MinervaTestHelper


@pytest.fixture(scope="session", autouse=True)
def skip_dotenv_in_tests():
    """Automatically skip .env loading during all tests."""
    os.environ["MINERVA_SKIP_DOTENV"] = "1"
    yield
    # Cleanup after tests
    os.environ.pop("MINERVA_SKIP_DOTENV", None)


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


# Datetime testing fixtures using time-machine


@pytest.fixture
def fixed_datetime():
    """Fixed datetime for consistent test results across all tests.

    Uses a fixed datetime of 2023-06-15 12:00:00 UTC to ensure
    all timestamp-related tests produce consistent results.

    Returns:
        datetime: Fixed datetime object (2023-06-15 12:00:00)
    """
    return datetime(2023, 6, 15, 12, 0, 0)


@pytest.fixture
def mock_time(fixed_datetime):
    """Mock current time using time-machine for consistent datetime behavior.

    This fixture freezes time to the fixed_datetime value, ensuring
    all datetime.now() calls within the test return the same value.

    Args:
        fixed_datetime: The datetime to freeze time to

    Yields:
        time_machine.travel context that freezes time
    """
    with time_machine.travel(fixed_datetime) as traveler:
        yield traveler


@pytest.fixture
def frontmatter_test_time():
    """Specific time for frontmatter timestamp generation testing.

    Uses a memorable datetime for frontmatter-related tests:
    2023-01-01 00:00:00 UTC

    Returns:
        datetime: Test datetime for frontmatter operations
    """
    return datetime(2023, 1, 1, 0, 0, 0)


@pytest.fixture
def mock_frontmatter_time(frontmatter_test_time):
    """Mock time specifically for frontmatter timestamp generation.

    Freezes time to 2023-01-01 00:00:00 for consistent frontmatter
    timestamp testing across all related test cases.

    Args:
        frontmatter_test_time: The datetime to use for frontmatter tests

    Yields:
        time_machine.travel context that freezes time for frontmatter tests
    """
    with time_machine.travel(frontmatter_test_time) as traveler:
        yield traveler


@pytest.fixture
def incremental_test_time():
    """Base time for incremental indexing tests.

    Uses a specific datetime for file modification time testing:
    2023-12-01 10:30:00 UTC

    Returns:
        datetime: Base datetime for incremental indexing tests
    """
    return datetime(2023, 12, 1, 10, 30, 0)


@pytest.fixture
def mock_incremental_time(incremental_test_time):
    """Mock time for incremental indexing and file tracking tests.

    Freezes time to a specific datetime for testing file modification
    time tracking and incremental indexing functionality.

    Args:
        incremental_test_time: The datetime to use for indexing tests

    Yields:
        time_machine.travel context for incremental indexing tests
    """
    with time_machine.travel(incremental_test_time) as traveler:
        yield traveler
