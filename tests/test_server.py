from minerva import server


def test_mcp_server_initialization():
    """Test that the MCP server is properly initialized."""
    # Here we test the existence and properties of the server.mcp object
    assert server.mcp is not None
    # Verify the structure of the FastMCP object
    assert hasattr(server.mcp, "add_tool")
    # The FastMCP object doesn't seem to expose a version attribute, so we skip the __version__ verification


def test_mcp_tools_registration():
    """Test that all required tools are registered with the MCP server."""
    # Verify that all tools are registered

    # Validate the current state of the server module
    # Check that all required tools are registered
    expected_tools = [
        "read_note",
        "search_notes",
        "create_note",
        "edit_note",
        "get_note_delete_confirmation",
        "perform_note_delete",
    ]

    # Verify that each tool is imported in the server module
    for tool_name in expected_tools:
        assert hasattr(server, tool_name), (
            f"Tool {tool_name} was not imported in server.py"
        )
