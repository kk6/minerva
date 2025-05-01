import logging

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

if __name__ == "__main__":
    # Run the server
    mcp.run(transport="stdio")
