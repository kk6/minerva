import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
OBSIDIAN_VAULT_ROOT = os.environ["OBSIDIAN_VAULT_ROOT"]
DEFAULT_VAULT = os.environ["DEFAULT_VAULT"]
VAULT_PATH = Path(OBSIDIAN_VAULT_ROOT) / DEFAULT_VAULT
DEFAULT_NOTE_DIR = os.getenv("DEFAULT_NOTE_DIR", "default_notes")
DEFAULT_NOTE_AUTHOR = os.getenv("DEFAULT_NOTE_AUTHOR", "Minerva")
