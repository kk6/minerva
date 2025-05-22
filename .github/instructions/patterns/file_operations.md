---
applyTo: 'src/**/*.py'
---

# File Operation Patterns for Minerva

## Basic Principles

The Minerva project follows these principles for file operations:

1. **Path Validation**: All file paths are validated before use
2. **Encoding Consistency**: A consistent encoding (UTF-8) is used for all text file operations
3. **Directory Existence Check**: Directory existence is verified before writing files, and created if necessary
4. **Atomic Operations**: Atomic operations are used when possible to ensure file operation reliability

## File Path Validation

Use the following pattern for file path validation:

```python
def _get_validated_file_path(directory: str, filename: str) -> Path:
    """Validate and return the full file path."""
    dirpath = Path(directory)
    # Check if the directory is absolute
    if not dirpath.is_absolute():
        raise ValueError("Directory must be an absolute path")

    return dirpath / filename
```

## File Writing

Use the following pattern for file writing operations:

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
    with open(file_path, "w", encoding=ENCODING) as f:
        f.write(request.content)
    return file_path
```

## File Reading

Use the following pattern for file reading operations:

```python
def read_file(request: FileReadRequest) -> str:
    """Read the content from a file in the specified directory."""
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Check if the file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Read the content from the file
    with open(file_path, "r", encoding=ENCODING) as f:
        content = f.read()
    return content
```

## Binary File Detection

Pattern for detecting binary files to avoid accidentally processing them as text files:

```python
def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except (IOError, PermissionError) as e:
        logger.warning("Error checking if file is binary: %s", e)
        return False
```

## Subdirectory Processing

Use the following pattern for handling subdirectories in Obsidian notes:

```python
def _build_file_path(filename: str, default_path: str = DEFAULT_NOTE_DIR) -> tuple[Path, str]:
    """
    Resolve and build the complete file path from a filename.

    Args:
        filename: The filename (may include subdirectories)
        default_path: The default path to use if no subdirectory is specified

    Returns:
        tuple: (directory_path, base_filename)
    """
    # Check if filename is empty before processing
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Parse path components
    path_parts = Path(filename)
    subdirs = path_parts.parent
    base_filename = path_parts.name

    if not base_filename:
        raise ValueError("Filename cannot be empty")

    # Create final directory path
    full_dir_path = VAULT_PATH
    if str(subdirs) != ".":  # If subdirectory is specified
        full_dir_path = full_dir_path / subdirs
    elif isinstance(default_path, str) and default_path.strip() != "":
        full_dir_path = full_dir_path / default_path

    return full_dir_path, base_filename
```

## File Searching

Use the following pattern for file search operations:

```python
def search_keyword_in_files(config: SearchConfig) -> list[SearchResult]:
    """
    Search for a keyword in files within a directory.
    """
    matching_files = []

    # Create a regex pattern if case sensitivity is disabled
    if not config.case_sensitive:
        pattern = re.compile(re.escape(config.keyword), re.IGNORECASE)

    try:
        # Recursively search the directory
        for root, _, files in os.walk(config.directory):
            for file_name in files:
                # Check if the file matches the specified extensions
                if config.file_extensions is not None:
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext not in config.file_extensions:
                        continue

                file_path = Path(root) / file_name

                # Skip binary files
                if is_binary_file(file_path):
                    continue

                try:
                    # Open the file and search for the keyword
                    with open(file_path, "r", encoding=ENCODING) as file:
                        for line_num, line in enumerate(file, 1):
                            if config.case_sensitive:
                                found = config.keyword in line
                            else:
                                found = pattern.search(line) is not None

                            if found:
                                result = SearchResult(
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    context=line.strip(),
                                )
                                matching_files.append(result)
                                break  # Stop after finding first match in this file
                except (UnicodeDecodeError, PermissionError):
                    # Ignore read errors and continue
                    sanitized_path = str(file_path).replace('\n', '_').replace('\r', '_')
                    logger.warning("Could not read file %s. Skipping.", sanitized_path)

    except OSError as e:
        logger.error(
            "OS error during search for keyword '%s' in directory '%s': %s",
            config.keyword,
            config.directory,
            e,
        )
        raise
    except Exception as e:  # Keep for truly unexpected
        logger.error(
            "Unexpected error during search for keyword '%s' in directory '%s': %s",
            config.keyword,
            config.directory,
            e,
        )
        raise

    return matching_files
```
