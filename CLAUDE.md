# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context
Minerva is a tool that integrates with Claude Desktop to automate tasks such as exporting Markdown documents from chat conversations. It provides MCP (Model Context Protocol) server functionality for Obsidian vault management.

## Build/Test/Lint Commands
- Install dependencies: `uv pip install -e ".[dev]"`
- Run all tests: `uv run pytest`
- Run single test: `uv run pytest tests/path/to/test.py::TestClass::test_method`
- Test with coverage: `uv run pytest --cov=minerva --cov-report=html`
- Run linting: `uv run ruff check`
- Run formatting: `uv run ruff format`
- Type checking: `uv run mypy src tests`
- Run MCP inspector: `uv run mcp dev src/minerva/server.py:mcp`
- Install to Claude Desktop: `uv run mcp install src/minerva/server.py:mcp -f .env --with python-frontmatter`
- Check for trailing whitespace: `python scripts/check_trailing_whitespace.py`
- Fix trailing whitespace (in-place): `find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) -not -path "*/.git/*" -not -path "*/__pycache__/*" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.egg-info/*" -exec sed -i 's/[ \t]*$//' {} \;`

## Architecture Overview
- **MCP Server**: FastMCP-based server (`server.py`) that provides tool endpoints
- **Service Layer**: Core business logic (`service.py`) with dependency injection pattern
  - `MinervaService`: Main service class containing all note operations
  - `MinervaConfig`: Configuration dataclass for dependency injection
  - `create_minerva_service()`: Factory function for service creation
- **Tools**: API wrapper layer (`tools.py`) maintaining backward compatibility
  - Legacy function-based API for existing integrations
  - Service wrapper functions with dependency injection support
- **File Handler**: Low-level file operations (`file_handler.py`)
- **Frontmatter Manager**: Centralized frontmatter processing (`frontmatter_manager.py`)
- **Config**: Environment and configuration management (`config.py`)
- **Tag System**: Comprehensive tag management for Obsidian notes

## Key Features
- Note CRUD operations with frontmatter support
- Full-text search across markdown files
- Tag management (add, remove, rename, search by tag)
- Two-phase deletion process for safety
- Automatic frontmatter generation with metadata
- **Dependency injection architecture** for improved testability and extensibility
- **Backward compatibility** maintained for existing API consumers
- **Service-based architecture** with clear separation of concerns

## Code Style Guidelines
- Python 3.12+ compatibility required
- Follow PEP 8 and AAA (Arrange-Act-Assert) pattern in tests
- Use snake_case for functions/variables, CamelCase for classes
- Line length: 88 characters maximum
- Organize imports: standard lib, third-party, local
- Comprehensive docstrings for all functions (see existing format)
- Type hints required throughout the codebase
- Exception handling should be specific and well-documented
- Use pydantic for data validation and model definition
- **CRITICAL**: Do NOT use f-strings in logging! Use % formatting instead
- **CRITICAL**: Remove all trailing whitespace from files before committing - CI checks will fail otherwise

## Development Workflow
- Always check `.github/instructions/` for custom instructions at the beginning of coding
- After consulting custom instructions, refer to documentation in `docs/` directory and README.md
- Follow a document-first approach: create documentation as part of implementation planning and ask for user review
- Begin coding only after documentation review is complete
- **CRITICAL**: Whenever implementation specs change, you MUST update corresponding documentation
- Update documentation during implementation if discrepancies or improvements are identified
- Before creating a pull request, verify that documentation accurately reflects the implementation
- **PR Preparation Checklist**:
  1. Verify all code follows style guidelines
  2. Run `python scripts/check_trailing_whitespace.py` to detect and fix trailing whitespace
  3. Run local CI checks: `uv run ruff check` and `uv run ruff format`
  4. Ensure all tests pass with `uv run pytest`
  5. **Verify documentation has been updated to match implementation changes**
  6. If you modified any function signatures or behavior, ensure it's documented in appropriate .md files

## Common Pitfalls to Avoid
- Never use f-strings in logging statements (performance issue when log level is disabled)
- Always validate file paths and handle edge cases (empty filenames, absolute paths)
- Use two-phase operations for destructive actions (confirmation → execution)
- Handle binary files appropriately in search operations
- Preserve existing frontmatter when updating notes
- Avoid trailing whitespace in all files (Python, Markdown, YAML) as it will fail CI checks
- Use proper line endings (LF, not CRLF) for all files
- **CRITICAL**: Never delete or modify files in the `.venv` directory, as this can break the virtual environment

## Testing Strategy
- Unit tests for individual functions and service methods
- Integration tests for end-to-end workflows
- Service layer tests with dependency injection
- Mock external dependencies (file system, environment variables)
- Use pytest fixtures for common setup
- Follow AAA pattern: Arrange-Act-Assert with clear section comments
- **Test coverage target**: Maintain 92%+ code coverage
- **Service testing**: Test both service layer and wrapper functions

## Dependency Injection Usage

### Service Layer
The new service layer provides dependency injection for improved testability:

```python
from minerva.service import create_minerva_service, MinervaService
from minerva.config import MinervaConfig
from minerva.frontmatter_manager import FrontmatterManager

# Use factory function for default configuration
service = create_minerva_service()

# Or create custom configuration for testing
config = MinervaConfig(
    vault_path=Path("/custom/vault"),
    default_note_dir="notes",
    default_author="Custom Author"
)
frontmatter_manager = FrontmatterManager("Custom Author")
service = MinervaService(config, frontmatter_manager)
```

### Testing with Dependency Injection
For testing, you can inject mock dependencies:

```python
from minerva.tools import set_service_instance

# Set custom service for testing
mock_service = Mock(spec=MinervaService)
set_service_instance(mock_service)

# Your tests will now use the mock service
# Reset after testing
set_service_instance(None)
```

### Backward Compatibility
Existing function-based API continues to work unchanged:

```python
from minerva.tools import create_note, read_note

# This still works exactly as before
note_path = create_note("content", "filename")
content = read_note(str(note_path))
```

## Environment Setup
Required environment variables in `.env`:
- `OBSIDIAN_VAULT_ROOT`: Path to Obsidian vault root directory
- `DEFAULT_VAULT`: Default vault name to use

## Known Issues
- Import path handling for Claude Desktop vs command line execution
- Binary file detection in search operations
- Frontmatter datetime serialization consistency
