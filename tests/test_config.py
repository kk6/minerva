"""
Test module for config.py functionality.
"""

import os
import unittest
from unittest import mock
from pathlib import Path

from minerva import config


class TestConfig(unittest.TestCase):
    """Test suite for config module."""

    @mock.patch.dict(
        os.environ,
        {
            "OBSIDIAN_VAULT_ROOT": "/test/vault",
            "DEFAULT_VAULT": "test_vault",
            "DEFAULT_NOTE_DIR": "test_notes",
            "DEFAULT_NOTE_AUTHOR": "Test Author",
        },
        clear=True,
    )
    def test_config_with_all_env_variables(self):
        """Test loading configuration with all environment variables set."""
        # We need to reload the module to apply the patched environment variables
        import importlib

        importlib.reload(config)

        # Verify the config values reflect environment variables
        self.assertEqual(config.OBSIDIAN_VAULT_ROOT, "/test/vault")
        self.assertEqual(config.DEFAULT_VAULT, "test_vault")
        self.assertEqual(config.VAULT_PATH, Path("/test/vault/test_vault"))
        self.assertEqual(config.DEFAULT_NOTE_DIR, "test_notes")
        self.assertEqual(config.DEFAULT_NOTE_AUTHOR, "Test Author")

    @mock.patch.dict(
        os.environ,
        {
            "OBSIDIAN_VAULT_ROOT": "/test/vault",
            "DEFAULT_VAULT": "test_vault",
        },
        clear=True,
    )
    def test_config_with_minimal_env_variables(self):
        """Test loading configuration with only required environment variables."""
        # We need to reload the module to apply the patched environment variables
        import importlib

        importlib.reload(config)

        # Verify required values are set
        self.assertEqual(config.OBSIDIAN_VAULT_ROOT, "/test/vault")
        self.assertEqual(config.DEFAULT_VAULT, "test_vault")
        self.assertEqual(config.VAULT_PATH, Path("/test/vault/test_vault"))

        # Verify default values are used for optional values (not checking specific values)
        self.assertIsInstance(config.DEFAULT_NOTE_DIR, str)
        self.assertIsInstance(config.DEFAULT_NOTE_AUTHOR, str)
