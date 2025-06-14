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
            "VECTOR_SEARCH_ENABLED": "false",
            "MINERVA_SKIP_DOTENV": "1",
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
        # Vector search defaults
        self.assertEqual(config.vector_search_enabled, False)
        self.assertEqual(config.vector_db_path, None)
        self.assertEqual(config.embedding_model, "all-MiniLM-L6-v2")

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

    @mock.patch.dict(
        os.environ,
        {
            "OBSIDIAN_VAULT_ROOT": "/test/vault",
            "DEFAULT_VAULT": "test_vault",
            "VECTOR_SEARCH_ENABLED": "true",
            "VECTOR_DB_PATH": "/custom/vector.db",
            "EMBEDDING_MODEL": "custom-model",
            "MINERVA_SKIP_DOTENV": "1",
        },
        clear=True,
    )
    def test_config_vector_search_enabled(self):
        """Test configuration with vector search enabled and custom settings."""
        config = MinervaConfig.from_env()

        # Verify vector search configuration
        self.assertEqual(config.vector_search_enabled, True)
        self.assertEqual(config.vector_db_path, Path("/custom/vector.db"))
        self.assertEqual(config.embedding_model, "custom-model")

    @mock.patch.dict(
        os.environ,
        {
            "OBSIDIAN_VAULT_ROOT": "/test/vault",
            "DEFAULT_VAULT": "test_vault",
            "VECTOR_SEARCH_ENABLED": "true",
            "MINERVA_SKIP_DOTENV": "1",
        },
        clear=True,
    )
    def test_config_vector_search_default_db_path(self):
        """Test that default vector DB path is set when enabled but not specified."""
        config = MinervaConfig.from_env()

        # Verify default vector DB path
        self.assertEqual(config.vector_search_enabled, True)
        expected_path = Path("/test/vault/test_vault/.minerva/vectors.db")
        self.assertEqual(config.vector_db_path, expected_path)

    def test_config_direct_initialization_with_vector_search(self):
        """Test direct initialization with vector search parameters."""
        config = MinervaConfig(
            vault_path=Path("/custom/vault"),
            default_note_dir="custom_notes",
            default_author="Custom Author",
            vector_search_enabled=True,
            vector_db_path=Path("/custom/vectors.db"),
            embedding_model="custom-embedding-model",
        )

        self.assertEqual(config.vector_search_enabled, True)
        self.assertEqual(config.vector_db_path, Path("/custom/vectors.db"))
        self.assertEqual(config.embedding_model, "custom-embedding-model")


if __name__ == "__main__":
    unittest.main()
