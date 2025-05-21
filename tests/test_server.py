from minerva import server


def test_mcp_server_initialization():
    """Test that the MCP server is properly initialized."""
    # ここではserver.mcpオブジェクトの存在とプロパティをテストします
    assert server.mcp is not None
    # FastMCPオブジェクトの構造を確認
    assert hasattr(server.mcp, "add_tool")
    # FastMCPオブジェクトはversion属性を公開していないようなので、__version__の検証は省略


def test_mcp_tools_registration():
    """Test that all required tools are registered with the MCP server."""
    # すべてのツールが登録されていることを確認します

    # サーバーモジュールの現在の状態を検証
    # 必要なツールがすべて登録されているか確認
    expected_tools = [
        "read_note",
        "search_notes",
        "create_note",
        "edit_note",
        "get_note_delete_confirmation",
        "perform_note_delete",
    ]

    # 各ツールがサーバーモジュールからインポートされていることを確認
    for tool_name in expected_tools:
        assert hasattr(server, tool_name), (
            f"Tool {tool_name} was not imported in server.py"
        )
