# Error Handling Patterns for Minerva

## Basic Principles

The Minerva project follows these principles for error handling:

1. **Exception Propagation and Transformation**: Convert low-level exceptions into more meaningful high-level exceptions
2. **Appropriate Logging**: Log all exceptions at appropriate log levels
3. **Clear Error Messages**: Provide user-friendly error messages for end users
4. **Detailed Context**: Include helpful information for debugging in errors

## Exception Types

### 1. Input Validation Errors

Example of input validation using Pydantic:

```python
class FileOperationRequest(BaseModel):
    """Base request model for file operations."""

    directory: str = Field(description="Directory for the file operation")
    filename: str = Field(description="Name of the file")

    @field_validator("filename")
    def validate_filename(cls, v):
        """Validate the filename."""
        if not v:
            raise ValueError("Filename cannot be empty")
        if os.path.isabs(v):
            raise ValueError("Filename cannot be an absolute path")
        if any(char in v for char in FORBIDDEN_CHARS):
            raise ValueError(
                f"Filename contains forbidden characters: {FORBIDDEN_CHARS}"
            )
        return v
```

### 2. File Operation Errors

Error handling related to file operations:

```python
def write_file(request: FileWriteRequest) -> Path:
    """Write the content to a file in the specified directory."""
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Ensure the directory exists
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists() and not request.overwrite:
        raise FileExistsError(
            f"File {file_path} already exists and overwrite is set to False"
        )

    # Write the content to the file
    try:
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write(request.content)
        return file_path
    except IOError as e:
        logger.error("Error writing to file %s: %s", file_path, e)
        raise IOError(f"Failed to write to file {file_path}: {e}") from e
```

## try-except Patterns

### 1. Basic Pattern

```python
try:
    # Potentially exception-raising operation
    result = potentially_failing_operation()
except SpecificException as e:
    # Handle the exception appropriately
    logger.error("Operation failed: %s", e)
    # Raise a more specific exception if needed
    raise CustomException("Failed to perform operation") from e
```

### 2. Using finally Blocks

When resource cleanup is needed:

```python
resource = None
try:
    resource = acquire_resource()
    result = use_resource(resource)
    return result
except Exception as e:
    logger.error("Resource operation failed: %s", e)
    raise
finally:
    # Resource cleanup (executed even if an exception occurs)
    if resource:
        release_resource(resource)
```

### 3. Using else Blocks

Processing that only executes if no exception occurs:

```python
try:
    data = parse_input(user_input)
except ValueError as e:
    logger.error("Invalid input: %s", e)
    raise InvalidInputError("Input could not be parsed") from e
else:
    # Only executes if no exception occurred
    process_valid_data(data)
```

## Error Handling Best Practices

1. **Catch Specific Exceptions**: Catch specific exception classes rather than `Exception`

2. **Provide Error Context**: Include information in error messages that clearly explains what happened

3. **Preserve the Cause of Exceptions**: Use the `raise ... from e` syntax to preserve the original exception

4. **Appropriate Error Abstraction**: At API boundaries, return errors at an appropriate level of abstraction that doesn't leak internal implementation details

5. **Consistent Error Responses**: Keep error messages returned to users in a consistent format

6. **Early Input Validation**: Validate inputs early in the process to detect invalid inputs as soon as possible
