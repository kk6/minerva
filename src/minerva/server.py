# NOTE:
# When running this file from the command line (e.g. `uv run mcp dev src/minerva/server.py:mcp`),
# the parent directory is automatically added to sys.path, so absolute imports like `from minerva.tools import ...` work fine.
# However, when launched from Claude Desktop (see `claude_desktop_config.json`), the sys.path may not include the parent directory.
# In that case, adding the following lines ensures the minerva package can always be imported:
#
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
# This guarantees the minerva package is importable regardless of the execution context.

import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP

from minerva.__version__ import __version__
from minerva.service import create_minerva_service

from minerva.tools import (
    read_note,
    search_notes,
    create_note,
    edit_note,
    get_note_delete_confirmation,
    perform_note_delete,
    add_tag,
    remove_tag,
    rename_tag,
    get_tags,
    list_all_tags,
    find_notes_with_tag,
    set_service_instance,
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize service layer with dependency injection
try:
    service = create_minerva_service()
    set_service_instance(service)
    logger.info("MCP server initialized with dependency injection")
except Exception as e:
    logger.warning(
        "Failed to initialize service layer, falling back to legacy mode: %s", e
    )

# Create an MCP server
mcp = FastMCP("minerva", __version__)

mcp.add_tool(read_note)
mcp.add_tool(search_notes)
mcp.add_tool(create_note)
mcp.add_tool(edit_note)
mcp.add_tool(get_note_delete_confirmation)
mcp.add_tool(perform_note_delete)
mcp.add_tool(add_tag)
mcp.add_tool(remove_tag)
mcp.add_tool(rename_tag)
mcp.add_tool(get_tags)
mcp.add_tool(list_all_tags)
mcp.add_tool(find_notes_with_tag)
