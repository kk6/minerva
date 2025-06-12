# Property-Based Testing with Hypothesis

## Overview

Property-based testing has been introduced to Minerva to discover edge cases and improve test coverage beyond what traditional unit tests can achieve. This document provides guidelines for writing and maintaining property-based tests in the project.

## What is Property-Based Testing?

Property-based testing generates many test cases automatically and verifies that certain properties hold for all inputs. Instead of testing specific examples, you define the properties that should always be true, and Hypothesis generates hundreds of test cases to verify those properties.

## Benefits Observed in Minerva

### Edge Cases Discovered
During implementation, property-based tests have already found several edge cases:

1. **Path validation edge cases**: Characters like `\r` not being properly handled as whitespace
2. **Regex special characters**: Issues with `?` and other regex metacharacters in error messages
3. **Validation order dependencies**: Long filenames with forbidden characters failing on character validation before length validation

### Improved Confidence
Property-based tests provide confidence that our validation functions work correctly across a much wider range of inputs than manual test cases.

## Performance Considerations

### Performance Comparison
- **Traditional tests**: ~40 tests in 0.07s
- **Property-based tests**: ~13 tests in 0.40s
- **Performance impact**: ~5-6x slower execution

### Best Practices for Performance
1. **Use property-based tests selectively** - Focus on critical validation and edge-case-prone functions
2. **Limit test scope** - Use `min_size` and `max_size` parameters to constrain input generation
3. **Run in CI selectively** - Consider running property-based tests only on specific branches or schedules

## Writing Property-Based Tests

### Target Areas for Property-Based Testing

#### High-Value Areas (Implemented)
1. **Path validation** (`PathResolver`, `FilenameValidator`)
   - Complex validation rules (forbidden chars, length limits, reserved names)
   - Unicode handling edge cases
   - Security-critical path traversal prevention

2. **Tag validation and normalization** (`TagValidator`, `FrontmatterManager`)
   - Case-insensitive operations
   - Character validation and normalization
   - Duplicate handling

3. **Search functionality** (`SearchOperations`)
   - Query validation and escaping
   - Configuration parameter handling
   - Case sensitivity behaviors

#### General Guidelines
- Use property-based tests for functions with complex validation rules
- Focus on functions that handle user input or external data
- Target areas where edge cases could cause security issues

### Test Structure

```python
import string
from hypothesis import given, assume, strategies as st

@given(st.text(min_size=1, max_size=100, alphabet=string.ascii_letters))
def test_property_example(self, input_text: str):
    """Property: describe what should always be true."""
    # Arrange
    assume(input_text.strip())  # Filter out cases we don't want to test

    # Act
    result = function_under_test(input_text)

    # Assert
    assert some_property_holds(result)
```

### Key Patterns

#### 1. Input Validation Properties
```python
import string
from hypothesis import given, strategies as st

# Define safe characters
safe_characters = string.ascii_letters + string.digits + ".-_"

@given(st.text(min_size=1, max_size=50, alphabet=safe_characters))
def test_valid_input_always_succeeds(self, valid_input: str):
    """Property: valid inputs should never raise exceptions."""
    result = validator.validate(valid_input)
    assert result == valid_input
```

#### 2. Error Condition Properties
```python
from hypothesis import given, strategies as st

# Define forbidden characters
forbidden_characters = ["<", ">", ":", '"', "|", "?", "*"]

@given(st.sampled_from(forbidden_characters))
def test_invalid_input_always_fails(self, forbidden_char: str):
    """Property: inputs with forbidden characters should always fail."""
    invalid_input = f"test{forbidden_char}input"
    with pytest.raises(ValueError):
        validator.validate(invalid_input)
```

#### 3. Consistency Properties
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=30))
def test_normalization_is_idempotent(self, input_text: str):
    """Property: normalizing twice should give same result as normalizing once."""
    once = normalizer.normalize(input_text)
    twice = normalizer.normalize(once)
    assert once == twice
```

## Common Pitfalls and Solutions

### 1. Strategy Filtering Issues
**Problem**: Hypothesis generates many inputs that are filtered out, causing slow tests.

```python
import string
from hypothesis import given, assume, strategies as st

# ❌ Bad: Filters out too many examples
@given(st.text(min_size=0, max_size=100))
def test_non_empty_strings(self, text: str):
    assume(text.strip())  # Filters out most generated strings
```

```python
# ✅ Good: Generate only what you need
@given(st.text(min_size=1, max_size=100, alphabet=string.ascii_letters))
def test_non_empty_strings(self, text: str):
    # No filtering needed
```

### 2. Regex Escape Issues
**Problem**: Special regex characters in error message matching.

```python
# ❌ Bad: ? is a regex metacharacter
with pytest.raises(ValueError, match=f"contains '{char}' character"):

# ✅ Good: Escape special characters
import re
escaped_char = re.escape(char)
with pytest.raises(ValueError, match=f"contains '{escaped_char}' character"):
```

### 3. Validation Order Dependencies
**Problem**: Testing one type of validation when multiple validations occur.

```python
# ❌ Bad: May fail on other validation first
@given(st.text(min_size=300))  # Any characters
def test_too_long_filename(self, long_name: str):
    with pytest.raises(ValueError, match="too long"):
        validate_filename(long_name)

# ✅ Good: Use only safe characters to isolate the validation
@given(st.text(min_size=300, alphabet=string.ascii_letters))
def test_too_long_filename(self, long_name: str):
    with pytest.raises(ValueError, match="too long"):
        validate_filename(long_name)
```

## Integration with Existing Tests

### Complementary Approach
Property-based tests should complement, not replace, traditional unit tests:

- **Unit tests**: Verify specific known edge cases and examples
- **Property-based tests**: Verify general properties across wide input ranges

### File Organization
Property-based tests are organized in separate files with `_properties` suffix:
- `test_path_resolver.py` - Traditional unit tests
- `test_path_resolver_properties.py` - Property-based tests

## Running Property-Based Tests

### Local Development
```bash
# Run all property-based tests
uv run pytest tests/*_properties.py

# Run specific property-based test file
uv run pytest tests/test_validators_properties.py

# Control Hypothesis example count (default is 100)
uv run pytest tests/test_validators_properties.py --hypothesis-max-examples=50
```

### CI/CD Considerations
Given the performance impact, consider:
1. Running property-based tests on PR validation
2. Using reduced example counts in CI (`--hypothesis-max-examples=20`)
3. Running full property-based test suites nightly

## Example Output

When property-based tests find issues, Hypothesis provides helpful debugging:

```
Falsifying example: test_validate_filename_forbidden_chars(
    self=<TestClass object>,
    forbidden_char='?',
)
```

This shows the minimal failing case that triggered the property violation.

## Further Reading

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Patterns](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Testing strategies and tactics](https://hypothesis.readthedocs.io/en/latest/data.html)

## Implementation Status

### ✅ Completed
- Path validation and normalization (PathResolver)
- Filename validation (FilenameValidator, TagValidator, PathValidator)
- Frontmatter processing and tag operations (FrontmatterManager)
- Search operations and configuration (SearchOperations)
- Basic performance analysis and documentation

### 🔄 Future Enhancements
- Error handling edge cases in file operations
- Configuration validation and edge cases
- Integration test properties for end-to-end workflows
- Performance optimization for CI environments
