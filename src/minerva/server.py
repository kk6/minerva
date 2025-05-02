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

from minerva.tools import (
    read_note,
    search_notes,
    create_note,
    edit_note,
)

# Set up logging
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("minerva", "0.2.0")

mcp.add_tool(read_note)
mcp.add_tool(search_notes)
mcp.add_tool(create_note)
mcp.add_tool(edit_note)
