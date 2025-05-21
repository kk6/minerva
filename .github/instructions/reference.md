# Minerva Project Reference

## Project Overview
Minerva is a tool that integrates with Claude Desktop to automate tasks such as exporting Markdown documents from chat conversations.

## Important References
- Always refer to `README.md` before starting development
- Project detailed specifications are in documents within the `docs/` directory
  - Specifically, `docs/requirements.md` contains project requirements
  - `docs/technical_spec.md` contains technical specifications
  - `docs/note_operations.md` contains specifications for note operation features

## Architecture
- MCP Server (FastMCP)
- Tool implementation (tools.py)
  - Functions such as write_note, read_note, search_notes, etc.
- File operation module (file_handler.py)
- Configuration management (config.py)

## Development Environment
- Python 3.12+
- uv package manager

## Dependencies
Main dependencies:
- mcp[cli]
- pydantic
- python-dotenv
- python-frontmatter

Development dependencies:
- mypy
- pytest
- pytest-cov
- pytest-mock
