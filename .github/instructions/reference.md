---
applyTo: '**'
---

# Minerva Project Reference

## Project Overview
Minerva is a tool that integrates with Claude Desktop to automate tasks such as exporting Markdown documents from chat conversations.

## Development Philosophy
The Minerva project adopts a "Document-First" approach. Always update relevant documentation before implementing new features or fixing bugs. For details, refer to `.github/instructions/patterns/document_first.md`.

## Important References
- Always refer to `README.md` before starting development
- Project detailed specifications are in documents within the `docs/` directory
  - Specifically, `docs/requirements.md` contains project requirements
  - `docs/technical_spec.md` contains technical specifications
  - `docs/note_operations.md` contains specifications for note operation features

## Architecture
- MCP Server (FastMCP) with dependency injection initialization
- Service layer architecture (service.py)
  - MinervaService class encapsulating all business logic
  - Dependency injection pattern for improved testability and extensibility
  - Factory function `create_minerva_service()` for default configuration
- Tool implementation layer (tools.py)
  - Backward-compatible function-based API wrapping service layer
  - Functions such as create_note, edit_note, read_note, search_notes, etc.
  - Service instance management with lazy initialization
- Configuration management (config.py)
  - MinervaConfig dataclass for dependency injection
  - Legacy global variables for backward compatibility
- File operation module (file_handler.py)
- Frontmatter management (frontmatter_manager.py)

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

## AI Assistant Guidelines

### Issue Creation
- Always identify your AI model name when creating issues
- Follow the document-first approach before proposing new features
- Use appropriate issue templates and fill out all required fields
- Provide specific, actionable descriptions with proper context
