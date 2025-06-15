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
    # Vector search configuration
    vector_search_enabled: bool = False
    vector_db_path: Path | None = None
    embedding_model: str = "all-MiniLM-L6-v2"
    # Automatic index updates configuration
    auto_index_enabled: bool = True
    auto_index_strategy: str = "immediate"  # immediate, batch, background

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
                f"Required environment variables not set: {', '.join(missing_vars)}. "
                "These must be provided"
            )

        # At this point, we know vault_root and default_vault are not None
        assert vault_root is not None
        assert default_vault is not None

        # Vector search configuration from environment
        def _str_to_bool(value: str) -> bool:
            """Convert string to boolean, similar to distutils.util.strtobool."""
            return value.lower() in ("true", "1", "yes", "on")

        vector_search_enabled = _str_to_bool(
            os.getenv("VECTOR_SEARCH_ENABLED", "false")
        )
        vector_db_path = None
        if vector_search_enabled:
            db_path_str = os.getenv("VECTOR_DB_PATH")
            if db_path_str:
                vector_db_path = Path(db_path_str)
            else:
                # Default to vault directory if not specified
                vector_db_path = (
                    Path(vault_root) / default_vault / ".minerva" / "vectors.db"
                )

        # Auto index configuration
        auto_index_enabled = _str_to_bool(os.getenv("AUTO_INDEX_ENABLED", "true"))
        auto_index_strategy = os.getenv("AUTO_INDEX_STRATEGY", "immediate")

        return cls(
            vault_path=Path(vault_root) / default_vault,
            default_note_dir=os.getenv("DEFAULT_NOTE_DIR", "default_notes"),
            default_author=os.getenv("DEFAULT_NOTE_AUTHOR", "Minerva"),
            vector_search_enabled=vector_search_enabled,
            vector_db_path=vector_db_path,
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            auto_index_enabled=auto_index_enabled,
            auto_index_strategy=auto_index_strategy,
        )
