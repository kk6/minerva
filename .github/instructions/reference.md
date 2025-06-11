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
- MCP Server (server.py) with FastMCP and @mcp.tool() decorators
  - Direct service integration without wrapper functions
  - Tool functions: create_note, edit_note, read_note, search_notes, etc.
  - Simplified architecture with ~5% code reduction
- Modular service layer architecture (services/)
  - ServiceManager facade providing unified interface
  - Specialized service modules (NoteOperations, TagOperations, AliasOperations, SearchOperations)
  - Dependency injection pattern maintained across all service modules
  - Factory function `create_minerva_service()` for default ServiceManager configuration
- Configuration management (config.py)
  - MinervaConfig dataclass for dependency injection
  - Legacy global variables for backward compatibility
- File operation module (file_handler.py)
- Frontmatter management (frontmatter_manager.py)

## Development Environment
- Python 3.12+
- uv package manager
- Makefile for unified development commands (recommended)

## Common Development Commands

### Using Makefile (Recommended)
- `make help` - Show all available commands
- `make install` - Install project dependencies
- `make setup-dev` - Set up complete development environment
- `make clean` - Clean build artifacts and cache
- `make test` - Run all tests
- `make test-cov` - Run tests with coverage
- `make lint` - Run linting
- `make type-check` - Run type checking
- `make format` - Format code
- `make fix-whitespace` - Fix trailing whitespace in source files
- `make check-all` - Run comprehensive quality checks
- `make pre-commit` - Run pre-commit hooks
- `make dev` - Start MCP inspector for development

### Direct uv Commands (Alternative)
- `uv run pytest` - Run tests
- `uv run ruff check` - Run linting
- `uv run mypy src tests` - Run type checking

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
