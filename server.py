import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from minerva.file_handler import FileWriteRequest, write_file, FileReadRequest, read_file

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

OBSIDIAN_VAULT_ROOT = os.environ["OBSIDIAN_VAULT_ROOT"]
DEFAULT_VAULT = os.environ["DEFAULT_VAULT"]
VAULT_PATH = Path(OBSIDIAN_VAULT_ROOT) / DEFAULT_VAULT

# Create an MCP server
mcp = FastMCP("minerva", "0.1.0")


@mcp.tool()
def write_note(text: str, filename: str, is_overwrite: bool = False) -> Path | None:
    """
    Write a note to a file in the Obsidian vault.

    Args:
        text (str): The content to write to the file.
        filename (str): The name of the file to write.
        is_overwrite (bool): Whether to overwrite the file if it exists. Defaults to False.
    Returns:
        file_path (Path): The path to the written file.
    """
    file_path = None
    try:
        request = FileWriteRequest(
            directory=str(VAULT_PATH),
            filename=f"{filename}.md",
            content=text,
            overwrite=is_overwrite,
        )
        file_path = write_file(request)
        logger.info(f"File written to {file_path}")
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        raise

    # Return the file path
    return file_path


@mcp.tool()
def read_note(filename: str) -> str | None:
    """
    Read a note from a file in the Obsidian vault.

    Args:
        filename (str): The name of the file to read.
    Returns:
        content (str): The content of the file.
    """
    content = None
    try:
        request = FileReadRequest(
            directory=str(VAULT_PATH),
            filename=f"{filename}.md",
        )
        content = read_file(request)
        logger.info(f"File read from {filename}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

    # Return the content
    return content


if __name__ == "__main__":
    # Run the server
    mcp.run(transport="stdio")
