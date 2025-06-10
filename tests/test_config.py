"""
Test module for config.py functionality.
"""

import os
import unittest
from unittest import mock
from pathlib import Path

from minerva.config import MinervaConfig


class TestMinervaConfig(unittest.TestCase):
    """Test suite for MinervaConfig class."""

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
    def test_config_from_env_with_all_variables(self):
        """Test loading configuration with all environment variables set."""
        config = MinervaConfig.from_env()

        # Verify the config values reflect environment variables
        self.assertEqual(config.vault_path, Path("/test/vault/test_vault"))
        self.assertEqual(config.default_note_dir, "test_notes")
        self.assertEqual(config.default_author, "Test Author")
        self.assertEqual(config.encoding, "utf-8")

    @mock.patch.dict(
        os.environ,
        {
            "OBSIDIAN_VAULT_ROOT": "/test/vault",
            "DEFAULT_VAULT": "test_vault",
            "MINERVA_SKIP_DOTENV": "1",
        },
        clear=True,
    )
    def test_config_from_env_with_minimal_variables(self):
        """Test loading configuration with minimal environment variables set."""
        config = MinervaConfig.from_env()

        # Verify the config values with defaults
        self.assertEqual(config.vault_path, Path("/test/vault/test_vault"))
        self.assertEqual(config.default_note_dir, "default_notes")  # default value
        self.assertEqual(config.default_author, "Minerva")  # default value
        self.assertEqual(config.encoding, "utf-8")

    def test_config_from_env_missing_required_variables(self):
        """Test that missing required environment variables raise ValueError."""
        with mock.patch.dict(os.environ, {"MINERVA_SKIP_DOTENV": "1"}, clear=True):
            with self.assertRaises(ValueError) as context:
                MinervaConfig.from_env()

            error_message = str(context.exception)
            self.assertIn("OBSIDIAN_VAULT_ROOT", error_message)
            self.assertIn("DEFAULT_VAULT", error_message)

    def test_config_direct_initialization(self):
        """Test direct initialization of MinervaConfig."""
        config = MinervaConfig(
            vault_path=Path("/custom/vault"),
            default_note_dir="custom_notes",
            default_author="Custom Author",
        )

        self.assertEqual(config.vault_path, Path("/custom/vault"))
        self.assertEqual(config.default_note_dir, "custom_notes")
        self.assertEqual(config.default_author, "Custom Author")
        self.assertEqual(config.encoding, "utf-8")  # default value


if __name__ == "__main__":
    unittest.main()
