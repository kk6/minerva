import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class MinervaConfig:
    """
    Configuration class for Minerva application.

    This class encapsulates all configuration parameters needed for
    Minerva's operation, providing a clean interface for dependency injection
    and testing.
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
        # Load .env file unless explicitly disabled (e.g., in test environments)
        if not os.getenv("MINERVA_SKIP_DOTENV"):
            load_dotenv(override=False)  # Don't override existing env vars

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
