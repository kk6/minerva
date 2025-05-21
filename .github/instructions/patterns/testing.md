# Testing Patterns for Minerva

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
