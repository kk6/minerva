# Python Coding Standards for Minerva

## General Guidelines
- Python code must comply with PEP 8 style guide
- Limit line length to 88 characters (Ruff compliant)
- Use 4 spaces for indentation
- Use CamelCase for class names, snake_case for function and method names
- Use ALL_CAPS for constants

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
