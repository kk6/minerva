import logging

from mcp.server.fastmcp import FastMCP

from minerva.tools import (
    write_note,
    read_note,
    search_notes,
)

# Set up logging
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("minerva", "0.1.0")

mcp.add_tool(write_note)
mcp.add_tool(read_note)
mcp.add_tool(search_notes)
#     try:

if __name__ == "__main__":
    # Run the server
    mcp.run(transport="stdio")
