"""Common test fixtures and setup."""

import pytest
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
