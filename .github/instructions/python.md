---
applyTo: '**/*.py'
---

# Python Coding Standards for Minerva

## General Guidelines
- Python code must comply with PEP 8 style guide
- Limit line length to 88 characters (Ruff compliant)
- Use 4 spaces for indentation
- Use CamelCase for class names, snake_case for function and method names
- Use ALL_CAPS for constants
- Remove all trailing whitespace from files
- Use Unix line endings (LF, not CRLF)

## Code Quality Tools
- Run `make lint` to check code style with Ruff
- Run `make format` to auto-format code
- Run `make type-check` to verify type annotations with mypy
- Run `make check-all` for comprehensive quality checks
- Use `make fix-whitespace` to remove trailing whitespace safely

## Logging Guidelines
- Do NOT use f-strings when logging!
  - Correct example: `logger.info("Found %s files matching the query: %s", len(matching_files), query)`
  - Incorrect example: `logger.info(f"Found {len(matching_files)} files matching the query: {query}")`
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log all exceptions with `logger.error()` or `logger.exception()`

## Imports
Group imports in the following order:
1. Standard library (os, pathlib, etc)
2. Third-party libraries (pydantic, frontmatter, etc)
3. Local modules (minerva.*)

## Error Handling
- Catch specific exceptions (concrete exception classes rather than Exception)
- Provide clear error messages to users
- Use Pydantic models for input validation

## Testing
- Create unit tests for all functions and methods
- Structure tests following the AAA pattern (Arrange-Act-Assert)
- Include appropriate docstrings in test functions
- Update corresponding tests when the code being tested changes
- Run tests using `make test` (recommended) or `uv run pytest`
- Check test coverage with `make test-cov`

## Docstrings
- Docstrings should be written in English
- Use Google-style docstrings for all functions and methods
- Include parameters, return values, exceptions, and examples in docstrings
- Use `:param` for parameters, `:return` for return values, and `:raises` for exceptions
- Use `:example` for usage examples
- Use `:note` for additional notes
- Use `:warning` for warnings
- Use `:see_also` for related functions or classes
- Use `:todo` for future improvements or features
- Use `:deprecated` for deprecated functions or classes
- Use `:type` for parameter types
- Use `:rtype` for return types

## Docstring Example
```python
def example_function(param1: str, param2: int) -> bool:
    """
    Example function that does something.

    :param param1: Description of the first parameter.
    :param param2: Description of the second parameter.
    :return: True if successful, False otherwise.
    :raises ValueError: If param2 is negative.
    :note: This is an example note.
    :warning: This is an example warning.
    :see_also: `another_function`
    """
    ...


def another_function():
    """
    Another function that does something else.
    """
    ...
```

## Comments
- Comments should be in English
- Use inline comments sparingly
