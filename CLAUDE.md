# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context
Minerva is a tool that integrates with Claude Desktop to automate tasks such as exporting Markdown documents from chat conversations. It provides MCP (Model Context Protocol) server functionality for Obsidian vault management.

## Build/Test/Lint Commands

### Using Makefile (Recommended)
For a unified development experience, use the Makefile commands:

- **Development Environment**:
  - Install dependencies: `make install`
  - Set up development environment: `make setup-dev`
  - Clean build artifacts: `make clean`

- **Testing**:
  - Run all tests: `make test`
  - Run fast tests only (excludes slow integration tests): `make test-fast`
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

- Install dependencies: `uv pip install -e .` then `uv sync --group dev`
- Run all tests: `uv run pytest`
- Run single test: `uv run pytest tests/path/to/test.py::TestClass::test_method`
- Run property-based tests: `uv run pytest tests/*_properties.py`
- Reduce property test examples (for faster CI): `uv run pytest --hypothesis-max-examples=20`
- Test with coverage: `uv run pytest --cov=minerva --cov-report=html`
- Run linting: `uv run ruff check`
- Run formatting: `uv run ruff format`
- Type checking: `uv run mypy src tests`
- Run MCP inspector: `uv run mcp dev src/minerva/server.py:mcp`
- Install to Claude Desktop: `uv run mcp install src/minerva/server.py:mcp -f .env --with-editable .`
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
- **Vector Search Module**: Optional semantic search infrastructure (`vector/`) - **Phase 1 Implemented**
  - `EmbeddingProvider`: Abstract base class for text embedding systems
  - `SentenceTransformerProvider`: Concrete implementation using all-MiniLM-L6-v2 model
  - `VectorIndexer`: DuckDB VSS integration with HNSW indexing for similarity search
  - `VectorSearcher`: Placeholder for Phase 2 search functionality integration
- **Tag System**: Comprehensive tag management for Obsidian notes

## Key Features
- Note CRUD operations with frontmatter support
- Full-text search across markdown files
- Tag management (add, remove, rename, search by tag)
- Two-phase deletion process for safety
- Automatic frontmatter generation with metadata
- **Vector search infrastructure** (Phase 1 complete) - Optional semantic search capabilities with DuckDB VSS and sentence transformers
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
# or
git checkout -b fix/issue-123-handle-encoding-error
# or
git checkout -b refactor/issue-456-simplify-service-layer
# or
git checkout -b docs/issue-789-update-test-guidelines
```

**If you are already on main branch and have made changes:**
1. Stash changes: `git stash`
2. Create topic branch: `git checkout -b feature/issue-NUMBER-short-description`
3. Apply changes: `git stash pop`

### Hierarchical Branch Strategy for Multi-Phase Features (December 2024)

For complex features implemented across multiple phases (like vector search infrastructure), use a hierarchical branch strategy:

**Structure Pattern:**
```
main
 └── feature/issue-88-vector-search-main (parent issue branch)
      ├── feature/issue-89-vector-search-infrastructure (Phase 1)
      ├── feature/issue-90-vector-search-integration (Phase 2)
      └── feature/issue-91-vector-search-ui (Phase 3)
```

**Implementation Workflow:**

1. **Create Parent Branch for Main Issue:**
```bash
# Create parent branch from main
git checkout main
git checkout -b feature/issue-88-vector-search-main
```

2. **Create Phase Branches from Parent:**
```bash
# Create phase branch from parent branch
git checkout feature/issue-88-vector-search-main
git checkout -b feature/issue-89-vector-search-infrastructure
```

3. **Merge Phases into Parent Branch:**
```bash
# After completing Phase 1, merge to parent
git checkout feature/issue-88-vector-search-main
git merge feature/issue-89-vector-search-infrastructure --no-ff
```

4. **Final Merge to Main:**
```bash
# After all phases complete, merge parent to main
git checkout main
git merge feature/issue-88-vector-search-main --no-ff
```

**Benefits:**
- **Clear feature organization**: All related phases grouped under parent issue
- **Incremental integration**: Each phase can be reviewed and merged separately
- **Risk mitigation**: Problems in later phases don't affect earlier completed work
- **Better code review**: Reviewers can focus on individual phases
- **Flexible development**: Phases can be developed in parallel or adjusted based on feedback

**Branch Naming Convention:**
- **Parent branch**: `feature/issue-{PARENT_NUMBER}-{feature-name}-main`
- **Phase branches**: `feature/issue-{PHASE_NUMBER}-{phase-description}`
- Always use the actual GitHub issue numbers for traceability

**Example from Vector Search Implementation:**
- Parent issue #88: Complete vector search functionality
- Phase 1 issue #89: Infrastructure setup (embeddings, indexing, configuration)
- Future phase issues will be created for integration, search implementation, etc.

### **MANDATORY: Check Documentation Impact IMMEDIATELY**
**BEFORE starting implementation**: You MUST check if documentation needs updates:

1. **Identify affected documentation**: Search docs/ for related content
2. **Plan documentation updates**: What files need changes?
3. **Update documentation DURING implementation**, not after
4. **Ask user to verify documentation changes** before finalizing

### Development Process
- Always check `.github/instructions/` for custom instructions at the beginning of coding
- After consulting custom instructions, refer to documentation in `docs/` directory and README.md
- Follow a document-first approach: create documentation as part of implementation planning and ask for user review
- Begin coding only after documentation review is complete
- **CRITICAL**: Whenever implementation specs change, you MUST update corresponding documentation
- Update documentation during implementation if discrepancies or improvements are identified
- Before creating a pull request, verify that documentation accurately reflects the implementation

### **PR Preparation Checklist**
1. **Confirm you are on a topic branch** (not main)
2. Verify all code follows style guidelines
3. Run `python scripts/check_trailing_whitespace.py` to detect and fix trailing whitespace
4. Run local CI checks: `uv run ruff check` and `uv run ruff format`
5. Ensure all tests pass with `uv run pytest`
6. **Verify documentation has been updated to match implementation changes**
7. If you modified any function signatures or behavior, ensure it's documented in appropriate .md files
8. **Ask user to review documentation changes before creating PR**

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
- **Mock external dependencies**: File system, environment variables, API calls

### Test Organization Best Practices

#### Project Structure
```
tests/
├── unit/              # Fast, isolated tests for individual functions
│   ├── models/
│   ├── services/
│   └── utils/
├── integration/       # Tests for component interactions
│   ├── test_api_endpoints.py
│   └── test_service_integration.py
├── e2e/              # End-to-end workflow tests
│   └── test_full_workflows.py
├── fixtures/         # Shared fixtures (optional)
│   ├── fixtures_db.py
│   └── fixtures_mock.py
├── conftest.py       # Shared fixtures and pytest configuration
└── pytest.ini        # Pytest configuration
```

#### Test Discovery Configuration
In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = [
    "--import-mode=importlib",  # Recommended for new projects
    "--strict-markers",         # Enforce marker registration
]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Fixture Management

#### Fixture Scopes and When to Use Them
- **function** (default): New instance for each test function
- **class**: Shared across all methods in a test class
- **module**: Shared across all tests in a module
- **session**: Shared across the entire test session

#### Fixture Best Practices
```python
# Use yield fixtures for setup/teardown
@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

# Factory fixtures for multiple instances
@pytest.fixture
def make_user():
    def _make_user(name, age=None):
        return User(name=name, age=age or 25)
    return _make_user

# Fixture composition
@pytest.fixture
def authenticated_client(client, user):
    client.login(user)
    return client
```

#### conftest.py Organization
- Place common fixtures in `tests/conftest.py`
- Use local `conftest.py` files for directory-specific fixtures
- Consider a hybrid approach for large projects:
  - Global fixtures in root `conftest.py`
  - Specialized fixtures in `fixtures/` directory
  - Local fixtures in subdirectory `conftest.py` files

### Parametrization Best Practices

```python
# Basic parametrization
@pytest.mark.parametrize("input,expected", [
    ("", True),
    ("a", True),
    ("Bob", True),
    ("Never odd or even", True),
    ("abc", False),
])
def test_is_palindrome(input, expected):
    assert is_palindrome(input) == expected

# Multiple parameters with IDs
@pytest.mark.parametrize(
    "a,b,expected",
    [
        (2, 3, 5),
        (-10, 5, -5),
        (0, 0, 0),
    ],
    ids=["positive", "negative", "zero"]
)
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### Markers and Test Categories

```python
# Register markers in pytest.ini
[pytest]
markers =
    slow: marks tests as slow
    unit: unit tests
    integration: integration tests
    e2e: end-to-end tests
    db: tests requiring database

# Use markers in tests
@pytest.mark.slow
@pytest.mark.integration
def test_complex_workflow():
    pass

# Run specific markers
# pytest -m "unit and not slow"
# pytest -m integration
```

### Property-Based Testing with Hypothesis
Minerva uses property-based testing to discover edge cases automatically:

- **Target areas**: Path validation, filename validation, tag operations, search functionality
- **Test files**: `tests/*_properties.py` (separate from traditional unit tests)
- **Performance**: ~5-6x slower than unit tests but provides much broader input coverage
- **Edge cases discovered**: Unicode handling, regex escaping, validation order dependencies
- **Documentation**: See `docs/property_based_testing.md` for comprehensive guidelines

**Commands**:
- Run property-based tests: `uv run pytest tests/*_properties.py`
- Reduce examples for CI: `uv run pytest --hypothesis-max-examples=20`
- Debug with seed: `uv run pytest --hypothesis-seed=12345`

### Testing Gotchas and Solutions ⚠️

#### Module Caching Issues
Python's module caching can cause test isolation problems when patching environment variables:

```python
# Problem: Cached modules retain old environment
def test_with_env_patch():
    with patch.dict(os.environ, {"VAR": "new_value"}):
        # If module was already imported, it uses old env
        from myproject import module  # May fail!

# Solution: Clear module cache before importing
def test_with_env_patch():
    with patch.dict(os.environ, {"VAR": "new_value"}):
        # Clear relevant modules from cache
        sys.modules.pop("myproject.module", None)
        sys.modules.pop("myproject.config", None)

        from myproject import module  # Fresh import with new env
```

#### Exception Testing Issues
`pytest.raises` may fail with custom exceptions due to module reloading:

```python
# Unreliable with custom exceptions
with pytest.raises(CustomError):
    some_function()

# More reliable approach
try:
    some_function()
    assert False, "Expected exception but none was raised"
except Exception as e:
    from myproject.exceptions import CustomError
    assert isinstance(e, (BuiltinError, CustomError)), f"Unexpected: {type(e)}"
```

#### Other Common Pitfalls
- **Hypothesis filtering**: Avoid over-filtering strategies; use specific alphabets instead of `assume()` calls
- **Mutable default arguments**: Never use mutable defaults in function signatures
- **Global state pollution**: Always reset global variables/singletons between tests
- **Async testing**: Use `pytest-asyncio` with proper event loop isolation
- **Temporary files**: Use `tempfile.TemporaryDirectory()` for automatic cleanup

### Optional Dependency Testing Patterns
When implementing optional features with external dependencies (like vector search with DuckDB), use these testing patterns:

#### Module-Level Import Mocking
```python
# Import at module level for proper testing/mocking
try:
    import duckdb
except ImportError:
    duckdb = None

class VectorIndexer:
    def _get_connection(self):
        if duckdb is None:
            raise ImportError("duckdb is required for VectorIndexer")
        return duckdb.connect(self.db_path)
```

#### Test Import Error Handling
```python
def test_import_error_handling(self):
    indexer = VectorIndexer(Path("/test/path.db"))

    # Mock the global variable, not the import
    with patch('minerva.vector.indexer.duckdb', None):
        with pytest.raises(ImportError, match="duckdb is required"):
            indexer._get_connection()
```

#### Lazy Loading with Dependency Injection
```python
def _ensure_model_loaded(self):
    if self._model is None:
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required")
        self._model = SentenceTransformer(self._model_name)
```

**Key Benefits:**
- Tests can mock dependencies without complex import patching
- Clear error messages for missing dependencies
- Proper separation between availability and usage of optional dependencies
- Module caching doesn't interfere with test isolation

### Performance Optimization

#### Identifying Slow Tests
```bash
# Show slowest 10 tests
pytest --durations=10

# Show all test durations (including setup/teardown)
pytest --durations=0 -vv
```

#### Speed Optimization Strategies
1. **Use pytest-xdist for parallel execution**: `pytest -n auto`
2. **Group slow tests with markers**: Mark and run separately
3. **Optimize fixture scope**: Use broader scopes for expensive setups
4. **Mock external dependencies**: Avoid real network/database calls
5. **Use pytest-randomly**: Detect order-dependent tests

### Recommended Pytest Plugins

#### Essential Plugins
- **pytest-cov**: Coverage reporting (`pytest --cov=minerva`)
- **pytest-xdist**: Parallel test execution (`pytest -n auto`)
- **pytest-randomly**: Randomize test order to detect dependencies
- **pytest-clarity**: Better assertion failure messages

#### Development Productivity
- **pytest-watch**: Auto-run tests on file changes
- **pytest-sugar**: Progress bar and better formatting
- **pytest-picked**: Run tests related to unstaged changes
- **pytest-testmon**: Run only tests affected by code changes

#### Specialized Plugins
- **pytest-mock**: Enhanced mock functionality
- **pytest-freezegun**: Mock datetime for time-based tests
- **pytest-benchmark**: Performance benchmarking
- **pytest-timeout**: Prevent hanging tests

### Service Testing with Dependency Injection

```python
# Testing with real ServiceManager
def test_note_creation():
    # Arrange
    service = create_minerva_service()

    # Act
    result = service.note_operations.create_note("content", "test.md")

    # Assert
    assert result.exists()

# Testing with mocked dependencies
def test_note_creation_with_mock():
    # Arrange
    mock_file_handler = Mock(spec=FileHandler)
    mock_file_handler.write_file.return_value = Path("/test/path.md")

    service = ServiceManager(config, frontmatter_manager)
    service.note_operations.file_handler = mock_file_handler

    # Act
    result = service.note_operations.create_note("content", "test.md")

    # Assert
    mock_file_handler.write_file.assert_called_once()
    assert result == Path("/test/path.md")
```

### CI/CD Testing Best Practices

1. **Fast feedback loop**: Run unit tests first, then integration, then e2e
2. **Fail fast**: Use `--exitfirst` to stop on first failure during development
3. **Parallel execution**: Use `pytest-xdist` in CI for faster runs
4. **Coverage gates**: Enforce minimum coverage thresholds
5. **Marker-based stages**: Run different test types in different CI stages

### Test Performance Optimization Strategies (December 2024)

#### Problem: Slow Tests with Real Dependencies
When implementing features with heavy external dependencies (like ML models), tests can become significantly slow:

**Example issue**: `test_embeddings.py` took 14+ seconds due to:
- Real sentence-transformers model loading (~2-3 seconds per test)
- Actual AI inference processing for embeddings
- Model initialization happening in multiple tests

**Solution: Test Categorization with Pytest Markers**

1. **Add markers to pyproject.toml**:
```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "unit: fast unit tests",
    "integration: integration tests",
]
```

2. **Categorize tests by speed**:
```python
# Fast tests (mocked dependencies)
def test_initialization_with_default_model(self):
    provider = SentenceTransformerProvider()
    assert provider.model_name == "all-MiniLM-L6-v2"

# Slow tests (real dependencies)
@pytest.mark.slow
def test_embed_single_text_real(self):
    provider = SentenceTransformerProvider()
    result = provider.embed("single text")
    assert isinstance(result, np.ndarray)
```

3. **Usage commands for different scenarios**:
```bash
# Development: Fast tests only (85% time reduction)
uv run pytest tests/vector/test_embeddings.py -m "not slow"  # 2.19s vs 14.32s

# CI/Integration: All tests
uv run pytest tests/vector/test_embeddings.py

# Troubleshooting: Slow tests only
uv run pytest tests/vector/test_embeddings.py -m "slow"

# Project-wide: Exclude slow tests from regular development
uv run pytest -m "not slow"
```

**Performance Results:**
- **Before**: 14.32 seconds for all 9 tests
- **After**: 2.19 seconds for 4 fast tests (85% improvement for daily development)
- **Slow tests**: Still available when needed for integration testing

**Key Benefits:**
- Fast feedback loop during development
- Full coverage available for CI/CD
- Clear separation between unit and integration tests
- Maintainable test organization pattern

#### Makefile Integration for Performance Optimization (December 2024)
Enhanced the Makefile with performance-optimized test commands for better developer experience:

```makefile
# Performance-optimized test commands
test-fast: ## Run fast tests only (excludes slow integration tests)
    @echo "$(BLUE)Running fast tests (excluding slow tests)...$(RESET)"
    PYTHONPATH=src uv run pytest -m "not slow"
    @echo "$(GREEN)Fast tests completed! Use 'make test' for full test suite.$(RESET)"

test-slow: ## Run slow integration tests only
    @echo "$(BLUE)Running slow integration tests...$(RESET)"
    PYTHONPATH=src uv run pytest -m "slow"
    @echo "$(GREEN)Slow tests completed!$(RESET)"

check-fast: lint type-check test-fast ## Run fast quality checks (excludes slow tests)
    @echo "$(GREEN)Fast quality checks passed!$(RESET)"
```

**Usage in Daily Development Workflow:**
```bash
# Quick development cycle (recommended for daily work)
make test-fast     # ~5 seconds instead of ~17 seconds
make check-fast    # Fast complete quality checks

# Full testing before commits/PRs
make test          # All tests including slow ones
make check-all     # Complete quality checks with all tests
```

**Benefits:**
- **85% time reduction** for routine development testing
- **Encourages frequent testing** due to faster feedback
- **Maintains full coverage** available when needed
- **Improves developer productivity** for quick iteration cycles

### See Also
- `docs/test_guidelines.md` for detailed testing patterns and solutions
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

## MyPy Type Checking Solutions (December 2024)

### Common MyPy Issues and Resolutions

#### Issue 1: Module-Level Import Type Assignments
**Problem**: MyPy errors when assigning `None` to module-level imports for optional dependencies:
```python
try:
    import duckdb
except ImportError:
    duckdb = None  # error: Incompatible types in assignment
```

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
**Problem**: MyPy cannot infer return types for external library objects.

**Solution**: Use `Any` type for dynamic objects:
```python
from typing import Any

def _get_connection(self) -> Any:
    """Get DuckDB connection - type varies by library version."""
    return duckdb.connect(str(self.db_path))
```

#### Issue 3: "Statement is unreachable" False Positives
**Problem**: MyPy thinks code is unreachable due to aggressive type inference:
```python
result = provider.embed("test text")  # Returns np.ndarray per annotation
assert isinstance(result, np.ndarray)  # MyPy: "Statement is unreachable"
```

**Root cause**: Function return type annotation tells MyPy the result will always be `np.ndarray`, making the isinstance check redundant.

**Solutions**:
1. **Remove redundant assertions** that conflict with return type annotations
2. **Test the actual behavior** rather than the type:
```python
# Instead of testing type (redundant with annotation)
assert isinstance(result, np.ndarray)

# Test actual behavior/properties
assert len(result) > 0
assert result.shape[0] == 1
```

3. **Simplify test logic** to avoid complex type inference paths:
```python
# Problematic: MyPy gets confused about control flow
provider.embed("test text")
result = get_some_result()
assert result.shape[0] == 1  # MyPy: unreachable

# Better: Direct testing
provider.embed("test text")
assert provider._model is not None  # Test the side effect
```

#### Issue 4: Auto-increment Database Schema
**Problem**: DuckDB schema with `INTEGER PRIMARY KEY` requires explicit ID values, causing constraint violations.

**Solution**: Use sequence-based auto-increment:
```sql
-- Instead of:
CREATE TABLE vectors (
    id INTEGER PRIMARY KEY,  -- Requires manual ID assignment
    ...
)

-- Use:
CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
CREATE TABLE vectors (
    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
    ...
)
```

**Alternative for DuckDB**:
```sql
CREATE TABLE vectors (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    ...
)
```

#### MyPy Best Practices for Optional Dependencies
1. **Separate import checks from usage**: Define helper methods that check availability
2. **Use `Any` for external library types**: Avoid complex type inference issues
3. **Prefer behavior testing over type testing**: Test what the code does, not what type it returns
4. **Handle module-level imports explicitly**: Use type ignore comments for unavoidable import patterns
5. **Validate type annotations match implementation**: Ensure return types accurately reflect what the function can return

**Example Pattern**:
```python
from typing import Any, Union

# Safe import pattern
try:
    from external_lib import ExternalClass
except ImportError:
    ExternalClass = None  # type: ignore[assignment]

class MyClass:
    def __init__(self):
        self._external_obj: Any = None

    def _ensure_dependency_available(self) -> None:
        """Check if optional dependency is available."""
        if ExternalClass is None:
            raise ImportError("external_lib is required")

    def use_external_feature(self) -> Any:
        """Use external feature with proper error handling."""
        self._ensure_dependency_available()
        if self._external_obj is None:
            self._external_obj = ExternalClass()
        return self._external_obj.do_something()
```

## Optional Feature Implementation Patterns

### Architecture for Optional Dependencies
When adding features with external dependencies (implemented December 2024 for vector search):

#### 1. Module Structure Pattern
```
src/minerva/
├── vector/                    # Optional feature module
│   ├── __init__.py           # Clean public API exports
│   ├── embeddings.py         # Abstract + concrete implementations
│   ├── indexer.py            # Core functionality with dependency checks
│   └── searcher.py           # Stub implementation for future phases
```

#### 2. Safe Import Pattern
```python
# At module level - allows mocking in tests
try:
    import duckdb
except ImportError:
    duckdb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
```

#### 3. Lazy Loading with Clear Error Messages
```python
def _ensure_dependencies_loaded(self):
    if SentenceTransformer is None:
        raise ImportError(
            "sentence-transformers is required for this feature. "
            "Install it with: pip install sentence-transformers"
        )
```

#### 4. Configuration Integration
- Add optional fields to existing config dataclass with sensible defaults
- Use environment variables with feature-specific prefixes
- Implement smart defaults that activate only when feature is enabled
- Maintain backward compatibility by defaulting to disabled state

#### 5. Phased Implementation Strategy
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

### Vector Search Implementation Insights (December 2024)

#### DuckDB VSS Extension Considerations

**HNSW Index Requirements**:
- HNSW indexes only work in **in-memory databases** by default
- For persistent databases, requires setting `hnsw_enable_experimental_persistence = true`
- Solution for testing: Use `:memory:` databases for HNSW index tests

```python
# For persistent database tests
indexer = VectorIndexer(Path("/path/to/file.db"))

# For HNSW index tests (in-memory required)
indexer = VectorIndexer(Path(":memory:"))
```

**Vector Dimension Matching**:
- Database schema must exactly match embedding dimensions
- Mismatched dimensions cause `ConversionException` at insert time
- Example: Schema with `FLOAT[384]` but inserting `FLOAT[3]` arrays

```python
# Ensure dimension consistency
embedding_dim = 384  # or get from actual embeddings
indexer.initialize_schema(embedding_dim)

# Match test data to schema
embeddings = np.array([[0.1, 0.2, 0.3]])  # 3 dimensions
indexer.initialize_schema(3)  # Match the schema to test data
```

**Auto-increment ID Handling**:
DuckDB requires explicit sequence setup for auto-incrementing primary keys:

```sql
-- Working pattern for DuckDB
CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
CREATE TABLE vectors (
    id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding FLOAT[{embedding_dim}] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Testing Patterns for External Database Dependencies

**File-based Database Testing**:
```python
# Avoid NamedTemporaryFile - creates invalid DB files
# Use TemporaryDirectory instead
def test_with_real_database():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        indexer = VectorIndexer(db_path)
        # Database will be created fresh
        indexer.initialize_schema(3)
        # ... test operations
        indexer.close()
    # Automatic cleanup when context exits
```

**Mixed Testing Strategy**:
- **Fast tests**: Mock the database operations for unit testing
- **Integration tests**: Use real in-memory databases (`:memory:`)
- **E2E tests**: Use temporary file databases for full workflow testing

**VSS Extension Loading**:
- Extension loading happens automatically on connection
- No explicit testing needed - connection failure indicates extension issues
- Log level can be adjusted to see extension loading messages

#### Embedding Provider Patterns

**Lazy Loading with Model Caching**:
```python
class SentenceTransformerProvider:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model: Any = None  # Lazy loaded
        self._embedding_dim: int | None = None

    def _ensure_model_loaded(self) -> None:
        if self._model is None:
            # Check dependency availability
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is required")

            # Load model once
            self._model = SentenceTransformer(self._model_name)

            # Cache dimension from sample embedding
            dummy_embedding = self._model.encode("test")
            self._embedding_dim = len(dummy_embedding)
```

**Benefits of this pattern**:
- Model only loaded when actually needed
- Dimension determined dynamically from model
- Clear error messages for missing dependencies
- Model reused across multiple embed() calls
- Memory efficient for testing scenarios

#### Configuration Patterns for Optional Features

**Smart Defaults with Environment Integration**:
```python
@classmethod
def from_env(cls) -> "MinervaConfig":
    # Feature toggle
    vector_search_enabled = os.getenv("VECTOR_SEARCH_ENABLED", "false").lower() == "true"

    # Conditional configuration loading
    vector_db_path = None
    if vector_search_enabled:
        db_path_str = os.getenv("VECTOR_DB_PATH")
        if db_path_str:
            vector_db_path = Path(db_path_str)
        else:
            # Smart default: inside vault directory
            vector_db_path = Path(vault_root) / default_vault / ".minerva" / "vectors.db"

    return cls(
        # ... core config
        vector_search_enabled=vector_search_enabled,
        vector_db_path=vector_db_path,
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
    )
```

**Key principles**:
- Feature disabled by default (safe rollout)
- Smart defaults only activate when feature is enabled
- Environment variables provide customization points
- Configuration validates dependencies are available when enabled

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
