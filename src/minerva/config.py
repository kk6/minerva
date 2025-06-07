import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Legacy global variables for backward compatibility
OBSIDIAN_VAULT_ROOT = os.environ["OBSIDIAN_VAULT_ROOT"]
DEFAULT_VAULT = os.environ["DEFAULT_VAULT"]
VAULT_PATH = Path(OBSIDIAN_VAULT_ROOT) / DEFAULT_VAULT
DEFAULT_NOTE_DIR = os.getenv("DEFAULT_NOTE_DIR", "default_notes")
DEFAULT_NOTE_AUTHOR = os.getenv("DEFAULT_NOTE_AUTHOR", "Minerva")


@dataclass
class MinervaConfig:
    """
    Configuration class for Minerva application.

    This class encapsulates all configuration parameters needed for
    Minerva's operation, providing a clean interface for dependency injection
    and testing while maintaining backward compatibility.
    """

    vault_path: Path
    default_note_dir: str
    default_author: str
    encoding: str = "utf-8"

    @classmethod
    def from_env(cls) -> "MinervaConfig":
        """
        Create configuration from environment variables.

        Returns:
            MinervaConfig: Configuration instance populated from environment

        Raises:
            ValueError: If required environment variables are not set
        """
        vault_root = os.getenv("OBSIDIAN_VAULT_ROOT")
        default_vault = os.getenv("DEFAULT_VAULT")

        missing_vars = []
        if not vault_root:
            missing_vars.append("OBSIDIAN_VAULT_ROOT")
        if not default_vault:
            missing_vars.append("DEFAULT_VAULT")

        if missing_vars:
            raise ValueError(
                f"Required environment variables not set: {', '.join(missing_vars)} must be provided"
            )

        # At this point, we know vault_root and default_vault are not None
        assert vault_root is not None
        assert default_vault is not None

        return cls(
            vault_path=Path(vault_root) / default_vault,
            default_note_dir=os.getenv("DEFAULT_NOTE_DIR", "default_notes"),
            default_author=os.getenv("DEFAULT_NOTE_AUTHOR", "Minerva"),
        )

    @classmethod
    def from_legacy_globals(cls) -> "MinervaConfig":
        """
        Create configuration from legacy global variables.

        This method provides backward compatibility for existing code
        that relies on global variables.

        Returns:
            MinervaConfig: Configuration instance using legacy globals
        """
        return cls(
            vault_path=VAULT_PATH,
            default_note_dir=DEFAULT_NOTE_DIR,
            default_author=DEFAULT_NOTE_AUTHOR,
        )
