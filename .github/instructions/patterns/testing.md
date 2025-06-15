---
applyTo: 'tests/**/*.py'
---

# Testing Patterns for Minerva

## Testing Strategy

Minerva uses a multi-layered testing approach with performance optimization:

1. **Unit Tests**: Fast, isolated tests for individual functions
2. **Integration Tests**: Component interaction tests 
3. **Property-based Tests**: Edge case discovery with Hypothesis
4. **Performance-optimized Test Execution**: pytest markers for efficient development

### Pytest Markers for Performance Optimization

Minerva uses pytest markers to categorize tests by execution speed:

- **`@pytest.mark.slow`**: Tests taking >3 seconds (ML models, heavy processing)
- **`@pytest.mark.unit`**: Fast unit tests (<1 second)
- **`@pytest.mark.integration`**: Integration tests (1-3 seconds)

```python
@pytest.mark.slow
def test_ml_model_loading():
    """Test that requires ML model loading (slow)."""
    provider = SentenceTransformerProvider()
    result = provider.embed("test text")
    assert isinstance(result, np.ndarray)

@pytest.mark.unit  
def test_config_validation():
    """Fast unit test for configuration validation."""
    config = MinervaConfig(vault_path=Path("/test"))
    assert config.vault_path == Path("/test")
```

### Test Execution Commands

- **Daily development**: `pytest -m "not slow"` (487 tests in ~5 seconds)
- **Complete testing**: `pytest` (492 tests in ~22 seconds)
- **Slow tests only**: `pytest -m "slow"` (5 tests in ~17 seconds)
- **Using Makefile**: `make test-fast`, `make test`, `make test-slow`

## Arrange-Act-Assert (AAA) Pattern

The Minerva project uses the AAA (Arrange-Act-Assert) pattern for all tests. This pattern structures tests clearly and makes code behavior easy to understand.

### 1. Arrange
Set up the system under test in an appropriate initial state.
- Prepare test data
- Set up mock objects
- Build prerequisites

```python
# ==================== Arrange ====================
request = FileWriteRequest(
    directory=temp_dir,
    filename="test.txt",
    content="Hello, World!",
    overwrite=True,
)
```

### 2. Act
Execute the code being tested. This is typically a single function or method call.

```python
# ==================== Act ====================
file_path = write_file(request)
```

### 3. Assert
Verify that the results are as expected.

```python
# ==================== Assert ====================
assert file_path == Path(temp_dir) / "test.txt"
assert file_path.exists()
with open(file_path, "r", encoding=ENCODING) as f:
    content = f.read()
    assert content == "Hello, World!"
```

## Test Docstrings

Include a docstring with the following structure for each test method:

```python
def test_write_file_success(self, temp_dir):
    """Test writing a file successfully.

    Arrange:
        - Create a file write request with test content
    Act:
        - Call write_file with the request
    Assert:
        - File is created at the expected path
        - File exists in the filesystem
        - File content matches the input
    """
    # Test implementation
```

## Fixtures

Extract common setup code into pytest fixtures for reuse:

```python
@pytest.fixture
def temp_dir():
    """Fixture that provides a temporary directory for file operations."""
    with TemporaryDirectory() as tempdir:
        yield tempdir
```

## Mocking

Properly mock external dependencies to isolate your tests:

```python
@pytest.fixture
def mock_write_setup(self, tmp_path):
    """Fixture providing common mock setup for write tests."""
    with (
        mock.patch("minerva.tools.write_file") as mock_write_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}
```

## Parameterized Tests

Use parameterized tests to efficiently test multiple test cases:

```python
@pytest.mark.parametrize(
    "filename,expected_message",
    [
        ("", "Filename cannot be empty"),
        ("/absolute/path/to/file.txt", "Filename cannot be an absolute path"),
    ],
)
def test_invalid_filename_validation(self, temp_dir, filename, expected_message):
    # Test implementation
```

## Edge Cases

Test not only basic functionality but also edge cases such as:
- Empty inputs
- Invalid inputs
- Boundary values
- Resource constraints (large files, many files, etc.)

## Test Independence

Each test should be able to run independently without relying on other tests. Avoid sharing state between tests.

### Module Caching Issues ⚠️

Python's module caching can cause test isolation problems when using environment variable patching:

```python
# Problem: Cached modules retain old environment
def test_with_env_patch():
    with patch.dict(os.environ, {"VAR": "new_value"}):
        from minerva import module  # May use cached module with old env

# Solution: Clear module cache before importing  
def test_with_env_patch():
    with patch.dict(os.environ, {"VAR": "new_value"}):
        # Clear relevant modules from cache
        sys.modules.pop("minerva.module", None)
        sys.modules.pop("minerva.config", None)
        
        from minerva import module  # Fresh import with new env
```

## Performance Guidelines

### When to Use `@pytest.mark.slow`

Mark tests as slow if they:
- Load ML models (sentence-transformers, etc.)
- Process large datasets
- Make external service calls
- Take >3 seconds to execute

### Fast Test Design

- Mock external dependencies (ML models, APIs, databases)
- Use minimal test data
- Design single-responsibility tests
- Prefer unit tests over integration tests when possible

```python
# Fast test: Mock ML model loading
def test_embedding_provider_init():
    """Test provider initialization without loading models."""
    provider = SentenceTransformerProvider("test-model")
    assert provider.model_name == "test-model"
    assert provider._model is None  # Model not loaded yet
```
