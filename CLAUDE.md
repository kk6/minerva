# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context
Minerva is a tool that integrates with Claude Desktop to automate tasks such as exporting Markdown documents from chat conversations. It provides MCP (Model Context Protocol) server functionality for Obsidian vault management.

## Build/Test/Lint Commands

### Using Makefile (Recommended)
For a unified development experience, use the Makefile commands:

- **Development Environment**:
  - Install basic dependencies: `make install`
  - Install with vector search: `make install-vector`
  - Set up development environment: `make setup-dev` (includes vector search)
  - Clean build artifacts: `make clean`

- **Testing**:
  - Run all tests: `make test`
  - Run fast tests only (excludes slow integration tests): `make test-fast`
  - Run core tests only (excludes vector dependency tests): `make test-core`
  - Run vector tests only (requires vector dependencies): `make test-vector`
  - Run slow integration tests only: `make test-slow`
  - Run tests with coverage: `make test-cov`
  - Run only property-based tests: `uv run pytest tests/*_properties.py`

- **Code Quality**:
  - Run linting: `make lint`
  - Run type checking: `make type-check`
  - Format code: `make format`
  - Fix trailing whitespace: `make fix-whitespace`
  - Run pre-commit hooks: `make pre-commit`

- **Development Tools**:
  - Start MCP inspector: `make dev`
  - Show all available commands: `make help`

### Direct uv Commands (Alternative)
If you prefer to use uv commands directly:

- Install basic dependencies: `uv pip install -e .` then `uv sync --group dev`
- Install with vector search: `uv pip install -e ".[vector]"` then `uv sync --group dev --extra vector`
- Run all tests: `uv run pytest`
- Run core tests only: `uv run pytest -m "not vector"`
- Run vector tests only: `uv run pytest -m "vector"`
- Run single test: `uv run pytest tests/path/to/test.py::TestClass::test_method`
- Run property-based tests: `uv run pytest tests/*_properties.py`
- Reduce property test examples (for faster CI): `uv run pytest --hypothesis-max-examples=20`
- Test with coverage: `uv run pytest --cov=minerva --cov-report=html`
- Run linting: `uv run ruff check`
- Run formatting: `uv run ruff format`
- Type checking: `uv run mypy src tests`
- Run MCP inspector: `uv run mcp dev src/minerva/server.py:mcp`
- Install to Claude Desktop: `uv run mcp install src/minerva/server.py:mcp -f .env`
- Check for trailing whitespace: Use the find command below or run pre-commit hooks
- Fix trailing whitespace (in-place): `uv run ruff format src/ tests/` (RECOMMENDED - safest method)
- Alternative manual fix: `find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) -not -path "*/.git/*" -not -path "*/__pycache__/*" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.egg-info/*" -exec sed -i 's/[[:space:]]*$//' {} \;`


## GitHub Labels
**IMPORTANT**: Only use predefined labels listed in `docs/github_workflow.md`. Do NOT create new labels without explicit approval.

Predefined label categories include:
- **Type**: `type:feature`, `type:bug`, `type:docs`, `type:refactor`, `type:test`, `type:chore`, `type:ci`
- **Feature**: `feature:obsidian`, `feature:claude`, `feature:markdown`, `feature:create`, `feature:edit`, `feature:read`, `feature:search`, `feature:tags`, `feature:delete`, `feature:config`
- **Area**: `area:backend`, `area:ci`, `area:docs`
- **Priority**: `priority:high`, `priority:medium`, `priority:low`
- **Status**: `status:wip`, `status:review`, `status:blocked`, `status:ready`
- **Scope**: `scope:core`, `scope:ui`, `scope:performance`, `scope:security`
- **PR**: `pr:ready`, `pr:wip`, `pr:needs-rebase`, `pr:needs-tests`

If you need a label that doesn't exist, ask for permission before creating it.

- **MCP Server**: FastMCP-based server (`server.py`) that provides tool endpoints
  - Uses `@mcp.tool()` decorators for direct service integration
  - Tool functions directly call service methods without wrapper layer
- **Service Layer**: Modular service architecture (`services/`) with dependency injection pattern
  - `ServiceManager`: Central facade coordinating all service operations
  - `NoteOperations`: Note CRUD operations and content management
  - `TagOperations`: Comprehensive tag management functionality
  - `AliasOperations`: Alias management and conflict detection
  - `SearchOperations`: Full-text search across markdown files
  - `create_minerva_service()`: Factory function for ServiceManager creation
- **File Handler**: Low-level file operations (`file_handler.py`)
- **Frontmatter Manager**: Centralized frontmatter processing (`frontmatter_manager.py`)
- **Config**: Environment and configuration management (`config.py`) with optional feature support
- **Vector Search Module**: Complete semantic search functionality (`vector/`) - **Phase 2 Implemented**
  - `EmbeddingProvider`: Abstract base class for text embedding systems
  - `SentenceTransformerProvider`: Concrete implementation using all-MiniLM-L6-v2 model (384-dimensional embeddings)
  - `VectorIndexer`: DuckDB VSS integration with HNSW indexing for similarity search
  - `VectorSearcher`: Full vector similarity search with cosine similarity and threshold filtering
- **Tag System**: Comprehensive tag management for Obsidian notes

## Key Features
- Note CRUD operations with frontmatter support
- Full-text search across markdown files
- Tag management (add, remove, rename, search by tag)
- Two-phase deletion process for safety
- Automatic frontmatter generation with metadata
- **Semantic search functionality** (Phase 2 complete) - Full vector search implementation with DuckDB VSS and sentence transformers
- **Modular service architecture** with dependency injection for improved testability and extensibility
- **ServiceManager facade pattern** providing unified access to specialized service modules
- **Simplified MCP server architecture** with direct service integration using FastMCP decorators

## Language Usage Rules

Follow the language conventions defined in `.github/instructions/language_rules.md`:

### Code and Technical Content
- **Source code comments and docstrings**: English only
  - All inline comments, function/class docstrings, module docstrings
  - Type hints and annotations
- **Log messages**: English only
- **System-level error messages**: English only
- **Variable and function names**: English only (snake_case for Python)

### AI and Development Documentation
- **CLAUDE.md**: English only
- **All files in `.github/instructions/`**: English only
  - These files are AI-specific guidelines and must remain in English for consistency

### User-Facing Documentation
- **Documentation in `docs/` directory**: Japanese (with English technical terms)
- **README.md and user guides**: Japanese (with English technical terms)
- **User-facing error messages**: Japanese

### File Format Requirements
- **No trailing whitespace** in any file (Python, Markdown, YAML, etc.)
- **Unix line endings (LF)** for all files
- **Files must end with a newline character**
- **UTF-8 encoding** for all text files

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

### Code Complexity Management (Updated December 2024)

**Complexity Threshold**: `max-complexity = 10` (Ruff's default level)
- This is a **strict setting** compared to industry standards (12-20)
- Appropriate for Minerva's high-quality requirements and small team size
- Enforces better code organization and testability

**Industry Comparison**:
- Ruff/Flake8 default: 10 (Minerva's setting)
- SonarQube: 15
- ESLint: 20
- Large enterprise projects: 12-15

**When C901 "too complex" errors occur**:
1. **Extract helper functions**: Break complex validation, configuration checks, or processing logic into focused functions
2. **Use early returns**: Reduce nesting with guard clauses and early exits
3. **Separate concerns**: Split functions that handle multiple responsibilities
4. **Create private methods**: Extract reusable logic within classes

**Example refactoring pattern**:
```python
# Before: Complex function (complexity > 10)
@mcp.tool()
def complex_function(param1, param2, param3):
    # Validation logic (5 conditions)
    if not param1:
        raise ValueError("...")
    if param2 < 0:
        raise ValueError("...")
    # ... more validation

    # Configuration checks (3 conditions)
    if not config.enabled:
        raise RuntimeError("...")
    # ... more config checks

    # Main processing logic
    # ... complex implementation

# After: Refactored with helper functions (complexity < 10)
def _validate_parameters(param1, param2, param3):
    """Extract validation logic."""
    if not param1:
        raise ValueError("...")
    if param2 < 0:
        raise ValueError("...")

def _check_configuration(config):
    """Extract configuration validation."""
    if not config.enabled:
        raise RuntimeError("...")

@mcp.tool()
def complex_function(param1, param2, param3):
    _validate_parameters(param1, param2, param3)
    _check_configuration(get_config())

    # Simplified main logic
    return process_main_logic()
```

**Benefits of strict complexity limits**:
- **Improved testability**: Smaller functions are easier to unit test
- **Better maintainability**: Easier to understand and modify
- **Reduced bugs**: Less complex control flow reduces error potential
- **Enhanced readability**: Functions have clear, single responsibilities

## Development Workflow

### **MANDATORY FIRST STEP: Create Topic Branch**
**BEFORE ANY CODE CHANGES**: You MUST create a topic branch. Do NOT work on main branch.

**Branch Naming Convention** (from `docs/github_workflow.md`):
- Feature addition: `feature/issue-NUMBER-short-description`
- Bug fix: `fix/issue-NUMBER-short-description`
- Refactoring: `refactor/issue-NUMBER-short-description`
- Documentation: `docs/issue-NUMBER-short-description`

```bash
# Check current branch first
git branch --show-current

# If on main, create topic branch immediately with proper naming
git checkout -b feature/issue-64-remove-legacy-fixtures
```

**If you are already on main branch and have made changes:**
1. Stash changes: `git stash`
2. Create topic branch: `git checkout -b feature/issue-NUMBER-short-description`
3. Apply changes: `git stash pop`

### **MANDATORY: Check Documentation Impact IMMEDIATELY**
**BEFORE starting implementation**: You MUST check if documentation needs updates:

1. **Identify affected documentation**: Search docs/ for related content
2. **Plan documentation updates**: What files need changes?
3. **Update documentation DURING implementation**, not after
4. **Ask user to verify documentation changes** before finalizing

### Development Process
- Always check `.github/instructions/` for custom instructions at the beginning of coding
- Follow a document-first approach: create documentation as part of implementation planning and ask for user review
- Begin coding only after documentation review is complete
- **CRITICAL**: Whenever implementation specs change, you MUST update corresponding documentation

### **PR Preparation Checklist**
1. **Confirm you are on a topic branch** (not main)
2. Verify all code follows style guidelines
3. Run local CI checks: `uv run ruff check` and `uv run ruff format`
4. Ensure all tests pass with `uv run pytest`
5. **Verify documentation has been updated to match implementation changes**
6. **Ask user to review documentation changes before creating PR**

### See Also
- `docs/development_workflow.md` for comprehensive development guidelines
- `docs/github_workflow.md` for branching strategies and Git best practices

## Common Pitfalls to Avoid
- Never use f-strings in logging statements (performance issue when log level is disabled)
- Always validate file paths and handle edge cases (empty filenames, absolute paths)
- Use two-phase operations for destructive actions (confirmation → execution)
- Handle binary files appropriately in search operations
- Preserve existing frontmatter when updating notes
- Avoid trailing whitespace in all files (Python, Markdown, YAML) as it will fail CI checks
- Use proper line endings (LF, not CRLF) for all files
- **CRITICAL**: Never delete or modify files in the `.venv` directory, as this can break the virtual environment

### sed Command Pitfalls ⚠️
**CRITICAL WARNING**: The `sed` command with certain regex patterns can corrupt files by unintentionally deleting characters:

**Problematic patterns**:
```bash
# DANGEROUS - can delete 't' characters from words like "pytest" → "pytes"
sed -i '' 's/[ \t]*$//' file.py

# DANGEROUS - inconsistent behavior across different sed implementations
rg -l ".*" src/ tests/ | xargs sed -i '' 's/[ \t]*$//'
```

**Root causes**:
1. **Character class interpretation**: `[ \t]` may not parse `\t` correctly in all sed versions
2. **Greedy matching**: Pattern can match more than intended
3. **Encoding issues**: Unicode/UTF-8 handling differences between macOS sed and GNU sed
4. **Implementation differences**: macOS BSD sed vs GNU sed behavioral differences

**Safe alternatives** (December 2024):
```bash
# RECOMMENDED: Use ruff for Python files (safest)
uv run ruff format src/ tests/

# Alternative: More explicit regex patterns
sed -i '' 's/[[:space:]]*$//' file.py
sed -i '' 's/[[:blank:]]*$//' file.py  # spaces and tabs only

# For broader file types, use Python script:
python -c "
import os, glob
for file in glob.glob('**/*.py', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(line.rstrip() for line in content.splitlines()) + '\n')
"
```

**Always verify** after using sed:
- Check `git diff` for unintended changes
- Run tests to ensure functionality wasn't broken
- Use `ruff check` to verify Python syntax is still valid

## Testing Strategy

### Core Testing Principles
- **Test isolation**: Each test should be independent and not rely on other tests
- **Single responsibility**: One test should test one behavior
- **Clear test names**: Use descriptive names that explain what is being tested
- **AAA pattern**: Follow Arrange-Act-Assert with clear section comments
- **Test coverage target**: Maintain 92%+ code coverage
- **Property-based testing**: Use Hypothesis for edge case discovery

### Key Testing Commands
```bash
# Fast tests for development (85% speed improvement)
make test-fast          # Exclude slow tests
pytest -m "not slow"    # Direct execution

# Full test suite
make test              # All tests including slow/integration tests
pytest                 # Direct execution

# Coverage reporting
make test-cov          # Generate coverage reports
pytest --cov=minerva   # Direct coverage

# Dependency-specific testing
make test-core         # Core functionality only (no vector dependencies)
make test-vector       # Vector search tests only (requires dependencies)
```

### Testing Gotchas ⚠️
- **Module caching issues**: Tests that patch environment variables may need to clear `sys.modules` to ensure fresh imports
- **Exception testing**: `pytest.raises` may fail with custom exceptions; use explicit `try/except` with `isinstance` checks
- **Hypothesis filtering**: Avoid over-filtering strategies; use specific alphabets instead of `assume()` calls

### See Also
- `docs/test_guidelines.md` for comprehensive testing patterns and best practices
- `docs/property_based_testing.md` for Hypothesis testing guide
- `.github/workflows/` for CI configuration examples

## Service-Based Architecture

### Service Layer Usage
The modular service layer provides clean dependency injection through ServiceManager:

```python
from minerva.services.service_manager import ServiceManager, create_minerva_service
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
service = ServiceManager(config, frontmatter_manager)

# Access specialized services through the manager
service.note_operations.create_note(text, filename)
service.tag_operations.add_tag(tag, filename)
service.search_operations.search_notes(query)
```

### MCP Server Integration
The server.py uses `@mcp.tool()` decorators for direct service integration:

```python
# In server.py - tools directly call service methods
@mcp.tool()
def read_note(filepath: str) -> str:
    """Read the content of a markdown note from your Obsidian vault."""
    return service.read_note(filepath)

@mcp.tool()
def create_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str | None = None,
) -> Path:
    """Create a new markdown note in your Obsidian vault."""
    return service.create_note(text, filename, author, default_path)
```

### Testing with Dependency Injection
For testing, create mock ServiceManager instances:

```python
from unittest.mock import Mock
from minerva.services.service_manager import ServiceManager

# Create mock service for testing
mock_service = Mock(spec=ServiceManager)
mock_service.create_note.return_value = Path("/fake/path")

# Use mock service in tests (test server functions directly)
from minerva import server
result = server.create_note("test", "filename")
```

### Key Improvements
- **Modular architecture**: Specialized service modules for different concerns
- **ServiceManager facade**: Unified access to all service operations
- **Simplified MCP integration**: Direct service calls via `@mcp.tool()` decorators
- **Reduced code duplication**: Eliminated redundant wrapper functions
- **Clean dependency injection**: ServiceManager instances for better testability
- **FastMCP integration**: Native decorator-based tool registration

## MyPy Type Checking Solutions

### Common MyPy Issues and Resolutions

#### Issue 1: Module-Level Import Type Assignments
**Problem**: MyPy errors when assigning `None` to module-level imports for optional dependencies.

**Solution**: Use type ignore comments:
```python
try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment,misc]
```

#### Issue 2: Return Type Annotations for External Dependencies
**Solution**: Use `Any` type for dynamic objects:
```python
from typing import Any

def _get_connection(self) -> Any:
    """Get DuckDB connection - type varies by library version."""
    return duckdb.connect(str(self.db_path))
```

#### Issue 3: "Statement is unreachable" False Positives
**Solution**: Test actual behavior rather than the type:
```python
# Instead of testing type (redundant with annotation)
assert isinstance(result, np.ndarray)

# Test actual behavior/properties
assert len(result) > 0
assert result.shape[0] == 1
```

#### MyPy Best Practices for Optional Dependencies
1. **Separate import checks from usage**: Define helper methods that check availability
2. **Use `Any` for external library types**: Avoid complex type inference issues
3. **Prefer behavior testing over type testing**: Test what the code does, not what type it returns
4. **Handle module-level imports explicitly**: Use type ignore comments for unavoidable import patterns

### See Also
- Official MyPy documentation for comprehensive type checking guidance

## Optional Feature Implementation Patterns

### Architecture for Optional Dependencies
When implementing features with external dependencies:

#### 1. Safe Import Pattern
```python
# At module level - allows mocking in tests
try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment]
```

#### 2. Lazy Loading with Clear Error Messages
```python
def _ensure_dependencies_loaded(self):
    if SentenceTransformer is None:
        raise ImportError(
            "sentence-transformers is required for this feature. "
            "Install it with: pip install 'minerva[vector]'"
        )
```

#### 3. Configuration Integration
- Add optional fields to existing config dataclass with sensible defaults
- Use environment variables with feature-specific prefixes
- Implement smart defaults that activate only when feature is enabled
- Maintain backward compatibility by defaulting to disabled state

#### 4. Phased Implementation Strategy
- **Phase 1**: Infrastructure and configuration
- **Phase 2**: Basic functionality implementation
- **Phase 3**: Integration with existing features
- **Phase 4**: Advanced features and optimizations

**Benefits of this approach:**
- No impact on core functionality when feature is disabled
- Clear separation of concerns
- Easy to test both enabled and disabled states
- Gradual rollout reduces implementation risk
- Dependencies only loaded when feature is actively used

### Critical Vector Search Debugging Insights

#### Embedding Dimension Mismatch
**Problem**: "Cannot cast list with length 384 to array with length 1" errors during vector indexing.

**Root Cause**: Using `len(embedding_array)` instead of `embedding_array.shape[1]` for 2D arrays.

**Critical Fix**:
```python
# WRONG - causes dimension mismatch
dimension = len(sample_embedding)  # Returns 1 for shape (1, 384)

# CORRECT - gets actual embedding dimension
dimension = sample_embedding.shape[1] if sample_embedding.ndim == 2 else len(sample_embedding)
```

#### Vector Search Troubleshooting Commands
```bash
# Check current vector state
debug_vector_schema()

# Reset if dimension mismatch detected
reset_vector_database()

# Test with single file first
build_vector_index_batch({"max_files": 1, "force_rebuild": true})

# Verify semantic search works
semantic_search({"query": "test query", "limit": 3})
```

### See Also
- `docs/optional_dependencies.md` for complete implementation patterns
- `docs/vector_search_troubleshooting.md` for comprehensive troubleshooting guides

## Environment Setup
Required environment variables in `.env`:
- `OBSIDIAN_VAULT_ROOT`: Path to Obsidian vault root directory
- `DEFAULT_VAULT`: Default vault name to use

### Optional Feature Configuration
For features with optional dependencies (e.g., vector search):
- `VECTOR_SEARCH_ENABLED`: Set to "true" to enable vector search functionality
- `VECTOR_DB_PATH`: Custom path for vector database (defaults to `{vault}/.minerva/vectors.db`)
- `EMBEDDING_MODEL`: Model name for text embeddings (defaults to `all-MiniLM-L6-v2`)

**Configuration Pattern for Optional Features:**
```python
@dataclass
class MinervaConfig:
    # Core required fields
    vault_path: Path
    default_note_dir: str
    default_author: str

    # Optional feature fields with defaults
    vector_search_enabled: bool = False
    vector_db_path: Path | None = None
    embedding_model: str = "all-MiniLM-L6-v2"

    @classmethod
    def from_env(cls) -> "MinervaConfig":
        # Load optional feature configuration
        vector_search_enabled = os.getenv("VECTOR_SEARCH_ENABLED", "false").lower() == "true"

        # Set smart defaults for dependent configuration
        vector_db_path = None
        if vector_search_enabled:
            db_path_str = os.getenv("VECTOR_DB_PATH")
            if db_path_str:
                vector_db_path = Path(db_path_str)
            else:
                # Default to vault directory if not specified
                vector_db_path = Path(vault_root) / default_vault / ".minerva" / "vectors.db"
```

**Testing Optional Configuration:**
- Test default values when feature is disabled
- Test custom configuration when feature is enabled
- Test smart defaults for dependent configuration values
- Verify backward compatibility when optional features are added

## Known Issues
- Import path handling for Claude Desktop vs command line execution
- Binary file detection in search operations
- Frontmatter datetime serialization consistency

## GitHub Management Guidelines

### Label Management
**CRITICAL**: Minerva uses a well-defined label system for issue and PR management. AI agents MUST follow these rules:

1. **Use existing labels only**: Only use labels that already exist in the repository
2. **Never create new labels**: Do not create new labels without explicit approval
3. **Required confirmation**: If you believe a new label is necessary, ask the user for permission first
4. **Reference documentation**: See `docs/label_management.md` for the complete label system

**Existing label categories**:
- `type:` (required) - feature, bug, docs, refactor, test, chore, ci
- `feature:` (recommended) - obsidian, claude, markdown, create, edit, read, search, tags, delete, config
- `area:` (optional) - backend, ci, docs
- `priority:` (recommended) - high, medium, low
- `status:` (optional) - wip, review, blocked, ready
- `scope:` (optional) - core, ui, performance, security
- `pr:` (PR only) - ready, wip, needs-rebase, needs-tests

**Example of proper label usage**:
```bash
# Correct - using existing labels
gh issue edit 123 --add-label "type:feature,feature:create,priority:medium"

# Incorrect - do not create new labels
gh label create "new-category" --description "..." --color "..."
```

### Pull Request Creation
When creating PRs, ensure:
1. Use appropriate existing labels only
2. Follow the established naming conventions
3. Include proper documentation updates if needed
4. Reference related issues using "Closes #123" syntax

## MCP Development and Debugging Patterns

### MCP Inspector Debugging Workflow

#### 1. Start MCP Inspector
```bash
make dev  # or uv run mcp dev src/minerva/server.py:mcp
```

**Common Issues**:
- **Port conflicts**: Use `lsof -ti:6277 | xargs kill` to free ports
- **Process hanging**: Kill processes with specific port numbers

#### 2. Systematic Testing Approach
Start with basic functionality and work up to complex operations:

```json
// 1. Check configuration and status
{"name": "get_vector_index_status", "arguments": {}}

// 2. Test minimal operations
{"name": "build_vector_index_batch", "arguments": {"max_files": 1, "force_rebuild": true}}

// 3. Test full functionality
{"name": "semantic_search", "arguments": {"query": "test", "limit": 3}}
```

#### 3. Common Error Resolution

**Timeout Issues**:
- Start with smallest possible batch sizes (`max_files: 1`)
- Use batch processing tools for large operations
- Add yield control in processing loops (`time.sleep(0.1)`)

**Import/Dependency Errors**:
- Test dependency availability in isolation
- Verify error messages guide users to installation commands
- Test both enabled and disabled states of optional features

### Vector Search Usage Patterns

**For complete vector search documentation, see [docs/vector_search_api.md](docs/vector_search_api.md)**

#### Quick Configuration Setup
```env
# Enable vector search
VECTOR_SEARCH_ENABLED=true

# Optional: Custom database path (defaults to vault/.minerva/vectors.db)
VECTOR_DB_PATH=/custom/path/vectors.db

# Optional: Custom embedding model (defaults to all-MiniLM-L6-v2)
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### Essential Vector Search Tools
- `semantic_search()` - Natural language semantic search
- `find_similar_notes()` - Find notes similar to reference note
- `build_vector_index()` - Full vault indexing
- `build_vector_index_batch()` - Batch processing (5-100 files, MCP inspector safe)
- `get_vector_index_status()` - Index statistics
- `debug_vector_schema()` - Database debugging
- `reset_vector_database()` - Database reset
- `process_batch_index()` - Batch queue processing
- `get_batch_index_status()` - Batch system status

#### Typical Workflow in Claude Desktop
1. **Initial Setup**: `build_vector_index()` - Index all markdown files
2. **Check Status**: `get_vector_index_status()` - Verify indexing progress
3. **Semantic Search**: `semantic_search("concept query", limit=10)` - Find related content
4. **Incremental Updates**: `build_vector_index(force_rebuild=false)` - Add new files only

#### Common Semantic Search Patterns
```python
# Find conceptually similar content
semantic_search("machine learning techniques", limit=5)

# Search with similarity threshold
semantic_search("project planning", limit=10, threshold=0.7)

# Search within specific directory
semantic_search("meeting notes", directory="work/meetings")
```

### See Also
- **[docs/vector_search_api.md](docs/vector_search_api.md)** - Complete API reference for all vector search tools
- `docs/vector_search_troubleshooting.md` for comprehensive troubleshooting guides
- `docs/claude_code_commands.md` for MCP tool development patterns
