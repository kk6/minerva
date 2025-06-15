# Optional Dependencies Implementation Guide

This document outlines the patterns and strategies used in Minerva for implementing optional dependencies, specifically for the vector search feature that requires external libraries like `numpy`, `duckdb`, and `sentence-transformers`.

## Overview

Minerva implements a conditional testing and dependency strategy that allows:
- Core functionality to work without optional dependencies
- Vector search features to be available when dependencies are installed
- Clean separation in CI/CD pipelines
- Proper type checking regardless of dependency availability

## Implementation Patterns

### 1. Module-Level Conditional Imports

```python
# At the top of vector modules
try:
    import numpy as np
except ImportError:
    np = None

try:
    import duckdb
except ImportError:
    duckdb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
```

**Benefits:**
- Clean import failures at module level
- Allows mocking in tests without complex import patching
- Module caching doesn't interfere with test isolation

### 2. Dependency Check Functions

```python
def _check_numpy_available() -> None:
    """Check if numpy is available and raise error if not."""
    if np is None:
        raise ImportError(
            "numpy is required for vector operations. "
            "Install it with: pip install 'minerva[vector]'"
        )
```

**Usage:**
- Call at the beginning of functions that require the dependency
- Provides clear error messages with installation instructions
- Centralizes dependency checking logic

### 3. Type Annotations for Optional Dependencies

```python
# Instead of specific types when dependencies might be missing
def embed(self, text: Union[str, List[str]]) -> Any:  # Not np.ndarray
    _check_numpy_available()
    # ... implementation
```

**MyPy Configuration:**
```toml
# In pyproject.toml
[[tool.mypy.overrides]]
module = [
    "numpy.*",
    "sentence_transformers.*", 
    "duckdb.*",
]
ignore_missing_imports = true
```

### 4. Pytest Markers for Dependency-Based Tests

```python
# Mark individual tests
@pytest.mark.vector
def test_vector_functionality():
    import numpy as np  # Safe to import here
    # ... test implementation

# Mark entire test modules
pytestmark = pytest.mark.vector  # At module level
```

**Configuration:**
```toml
# In pyproject.toml
[tool.pytest.ini_options]
markers = [
    "vector: tests that require vector search dependencies",
]
```

## CI/CD Strategy

### Separate Test Jobs

```yaml
# .github/workflows/ci.yml
test-core:
  name: Core Tests (without vector dependencies)
  steps:
    - run: uv sync --dev  # Basic dependencies only
    - run: uv run pytest -m "not vector"

test-vector:
  name: Vector Tests (with full dependencies)  
  steps:
    - run: uv sync --dev --extra vector  # Full dependencies
    - run: uv run pytest -m "vector"
```

**Benefits:**
- Faster feedback for core functionality
- Parallel execution reduces total CI time
- Clear separation of concerns
- Proper dependency isolation

### Quality Checks with Dependencies

```yaml
quality-checks:
  steps:
    - run: uv sync --dev --extra vector  # Install all deps for type checking
    - run: make check-all  # Includes MyPy type checking
```

**Rationale:**
- Type checking requires all dependencies to be available
- Linting and formatting work regardless of dependencies
- Quality checks run with full dependency context

## Development Workflow

### Makefile Targets

```makefile
install: ## Basic dependencies only
    uv pip install -e .
    uv sync --group dev

install-vector: ## With vector search dependencies
    uv pip install -e ".[vector]"
    uv sync --group dev --extra vector

test-core: ## Core tests only (fast)
    uv run pytest -m "not vector"

test-vector: ## Vector tests only (requires deps)
    uv run pytest -m "vector"

check-all-core: ## Quality checks without vector deps
    lint type-check test-core
```

### Development Commands

```bash
# Daily development (fast)
make install
make test-core      # ~2-3 seconds
make check-all-core # Core quality checks

# Vector feature development  
make install-vector
make test-vector    # ~17 seconds
make check-all      # Full quality checks

# Full testing before commits
make test           # All tests (~20 seconds)
```

## Testing Patterns

### 1. Import Error Testing

```python
def test_optional_dependency_handling():
    """Test graceful handling when dependencies unavailable."""
    from minerva.vector import indexer
    original_duckdb = indexer.duckdb
    indexer.duckdb = None

    try:
        vector_indexer = VectorIndexer(Path("/test.db"))
        with pytest.raises(ImportError, match="duckdb is required"):
            vector_indexer._get_connection()
    finally:
        indexer.duckdb = original_duckdb
```

### 2. Module Cache Clearing

```python
def test_with_environment_patch():
    with patch.dict(os.environ, {"VAR": "new_value"}):
        # Clear relevant modules from cache for fresh imports
        sys.modules.pop("minerva.vector.module", None)
        
        from minerva.vector import module  # Fresh import with new env
```

### 3. Mock-Heavy vs Real Dependency Tests

```python
# Fast tests with mocks
def test_vector_logic_with_mocks():
    mock_provider = Mock()
    mock_provider.embed.return_value = Mock()  # Don't need real numpy
    # Test logic without real dependencies

# Integration tests with real dependencies  
@pytest.mark.vector
def test_vector_integration_real():
    import numpy as np
    provider = SentenceTransformerProvider()
    result = provider.embed("test")
    assert isinstance(result, np.ndarray)
```

## Configuration Patterns

### Environment-Based Feature Toggles

```python
@dataclass
class MinervaConfig:
    # Core required fields
    vault_path: Path
    
    # Optional feature fields with safe defaults
    vector_search_enabled: bool = False
    vector_db_path: Path | None = None

    @classmethod  
    def from_env(cls) -> "MinervaConfig":
        vector_enabled = os.getenv("VECTOR_SEARCH_ENABLED", "false").lower() == "true"
        
        # Smart defaults only when feature is enabled
        vector_db_path = None
        if vector_enabled:
            vector_db_path = Path(os.getenv("VECTOR_DB_PATH", f"{vault}/.minerva/vectors.db"))
            
        return cls(
            vector_search_enabled=vector_enabled,
            vector_db_path=vector_db_path,
        )
```

### Service Layer Integration

```python
class ServiceManager:
    def __init__(self, config: MinervaConfig):
        self.config = config
        
    def semantic_search(self, query: str) -> List[SearchResult]:
        if not self.config.vector_search_enabled:
            raise RuntimeError("Vector search is not enabled")
            
        # Dependency check happens inside vector modules
        return self._vector_search_impl(query)
```

## Performance Considerations

### Test Performance Results

- **Before**: 14.32s for all tests (slow feedback loop)
- **After (core only)**: 2.19s for 575 tests (85% improvement)
- **After (vector only)**: 16.88s for 73 tests (isolated heavy tests)

### Development Impact

- **Daily development**: 85% faster test execution
- **CI efficiency**: Parallel execution reduces total pipeline time
- **Debugging**: Clear separation between core and optional feature issues

## Common Pitfalls and Solutions

### 1. Module Caching Issues

**Problem:** Tests that patch environment variables may fail due to cached module imports.

**Solution:** Clear module cache before importing in tests that change global state.

### 2. Import Order in Tests

**Problem:** `E402 Module level import not at top of file` when using conditional imports.

**Solution:** Place conditional imports after standard imports but before pytest markers.

```python
import pytest
from pathlib import Path

from minerva.core import CoreModule  # Standard imports first

# Conditional imports second
try:
    import numpy as np
except ImportError:
    np = None

# Pytest markers last
pytestmark = pytest.mark.vector
```

### 3. Type Checking vs Runtime Behavior

**Problem:** MyPy sees different types than runtime when dependencies are missing.

**Solution:** Use `Any` types for optional dependency returns and configure MyPy to ignore missing imports.

### 4. CI Dependency Installation

**Problem:** Quality checks fail when dependencies are missing for type checking.

**Solution:** Install full dependencies for quality check jobs, but separate test execution by dependency requirements.

## Best Practices

1. **Feature Flags Over Hard Dependencies**: Use configuration to enable/disable features rather than relying on import success/failure.

2. **Clear Error Messages**: Always provide installation instructions in import error messages.

3. **Granular Testing**: Create separate test categories for different dependency requirements.

4. **Documentation First**: Document the optional nature of features and their dependencies clearly.

5. **Graceful Degradation**: Core functionality should work perfectly without optional dependencies.

6. **CI Parallelization**: Separate CI jobs by dependency requirements for optimal performance.

## Future Considerations

### Adding New Optional Dependencies

When adding new optional features:

1. **Update pyproject.toml**: Add to `[project.optional-dependencies]`
2. **Create pytest markers**: Add new markers for the feature
3. **Update CI**: Add separate test jobs if needed
4. **Document installation**: Update README and docs
5. **Configure MyPy**: Add ignore rules for new dependencies

### Dependency Management Evolution

Consider migrating to more sophisticated dependency management if the project grows:
- Multiple optional dependency groups
- Feature-specific CI matrices
- Conditional documentation building
- Plugin architecture for optional features

## Related Documentation

- [Testing Guidelines](test_guidelines.md) - General testing patterns
- [CI/CD Workflow](../github_workflow.md) - CI configuration details
- [Property-Based Testing](property_based_testing.md) - Advanced testing patterns