# Frontmatter Processing Patterns for Minerva

## Basic Concepts

The Minerva project uses the `python-frontmatter` library to process frontmatter (YAML format metadata) in Obsidian notes. The following basic principles are observed for frontmatter processing:

1. **Consistency**: Use a consistent frontmatter format for all notes
2. **Metadata Preservation**: Respect and preserve existing frontmatter data
3. **Automatic Addition**: Automatically add or update necessary metadata
4. **Separation**: Separate frontmatter processing from file operations

## Frontmatter Generation

Pattern for generating or updating frontmatter for new or existing notes:

```python
def _generate_note_metadata(
    text: str,
    author: str | None = None,
    is_new_note: bool = True,
    existing_frontmatter: dict | None = None,
) -> frontmatter.Post:
    """
    Generate or update YAML frontmatter metadata for a note.

    Args:
        text: The text content of the note (with or without existing frontmatter)
        author: The author name to include in the metadata
        is_new_note: Whether this is a new note (True) or an update to existing note (False)
        existing_frontmatter: Existing frontmatter data from the file (if any)

    Returns:
        frontmatter.Post: Post object with properly processed frontmatter
    """
    # Get current time in ISO format
    now = datetime.now().isoformat()

    # Check and load frontmatter
    has_frontmatter = text.startswith("---\n")
    if has_frontmatter:
        # Load existing frontmatter
        post = frontmatter.loads(text)
    else:
        # Create new frontmatter object
        post = frontmatter.Post(text)

    # Add author information
    post.metadata["author"] = author or DEFAULT_NOTE_AUTHOR

    # Preserve created field from existing frontmatter
    if existing_frontmatter and "created" in existing_frontmatter:
        post.metadata["created"] = existing_frontmatter["created"]

    # Add created field for new notes (don't overwrite if exists)
    if is_new_note and "created" not in post.metadata:
        post.metadata["created"] = now

    # Add updated field for note updates (always update with current time)
    if not is_new_note:
        post.metadata["updated"] = now

    return post
```

## Reading Existing Frontmatter

Pattern for reading frontmatter from existing files:

```python
def _read_existing_frontmatter(file_path: Path) -> dict | None:
    """
    Read and extract frontmatter metadata from an existing file.

    Args:
        file_path: Path to the file to read

    Returns:
        dict | None: Existing frontmatter metadata as a dictionary, or:
            - Empty dict ({}) if the file exists but has no frontmatter
            - None if the file doesn't exist or can't be read as text
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r") as f:
            content = f.read()
            if content.startswith("---\n"):  # If frontmatter exists
                post = frontmatter.loads(content)
                metadata = dict(post.metadata)
                # 日付型の値が文字列として一貫して処理されるようにする
                for key, value in metadata.items():
                    if isinstance(value, datetime):
                        metadata[key] = value.isoformat()
                return metadata
            # No frontmatter found in file
            return {}
    except PermissionError as e:
        logger.error("Permission denied when reading file %s: %s", file_path, e)
        raise
    except UnicodeDecodeError as e:
        logger.warning(
            "File %s cannot be decoded as text (possibly binary): %s", file_path, e
        )
        return None
    except (IOError, OSError) as e:
        logger.warning(
            "I/O or OS error reading existing file %s for metadata: %s", file_path, e
        )
        return None
    except Exception as e:
        logger.warning("Failed to read existing file %s for metadata: %s", file_path, e)
        return None
```

## Note Assembly

Pattern for assembling a note by combining frontmatter and content:

```python
def _assemble_complete_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
    is_new_note: bool = True,
) -> tuple[Path, str, str]:
    """
    Assemble a complete note by combining file path resolution, metadata generation, and content preparation.

    Args:
        text: The content to write to the file
        filename: The name of the file to write
        author: The author name to add to the frontmatter
        default_path: The default directory to save the file
        is_new_note: Whether this is a new note (True) or an update to an existing note (False)

    Returns:
        tuple: (full_dir_path, base_filename, prepared_content)
    """
    # Build file path
    full_dir_path, base_filename = _build_file_path(filename, default_path)

    # Check existing frontmatter
    file_path = full_dir_path / base_filename
    existing_frontmatter = _read_existing_frontmatter(file_path)

    # Generate metadata
    post = _generate_note_metadata(
        text=text,
        author=author,
        is_new_note=is_new_note,
        existing_frontmatter=existing_frontmatter,
    )

    # Convert Post object to string with frontmatter
    content = frontmatter.dumps(post)

    return full_dir_path, base_filename, content
```

## Parsing and Manipulating Frontmatter

Pattern for parsing and manipulating frontmatter:

```python
# Extract frontmatter and content from a note
content = read_note(str(file_path))
post = frontmatter.loads(content)

# Get and manipulate metadata
created_date = post.metadata.get('created')
tags = post.metadata.get('tags', [])
tags.append('new-tag')
post.metadata['tags'] = tags

# Add metadata
post.metadata['status'] = 'completed'

# Convert to string with frontmatter and content
updated_content = frontmatter.dumps(post)
```

## Date Time Format

Minerva standardizes date and time information in frontmatter using ISO 8601 format:

```python
# Get current date time in ISO 8601 format
now = datetime.now().isoformat()  # Example: '2025-05-02T12:34:56.789012'

# Add to frontmatter
post.metadata["created"] = now
```

## Processing Tags and Attributes

Pattern for processing list-format metadata such as tags or attributes:

```python
# Get tags (using empty list as default value)
tags = post.metadata.get('tags', [])

# Convert to list if not already a list (e.g., if it's a string)
if not isinstance(tags, list):
    tags = [tags]

# Add a tag
if 'new-tag' not in tags:
    tags.append('new-tag')

# Set updated tags in metadata
post.metadata['tags'] = tags
```

## Best Practices

1. **Separate Functions**: Perform frontmatter processing in separate functions, isolated from file operations
2. **Respect Existing Data**: Preserve existing frontmatter data whenever possible
3. **Appropriate Default Values**: Provide appropriate default values for required fields
4. **Consistent Schema**: Maintain a consistent schema (field names and types) for frontmatter
5. **Error Handling**: Properly handle and log errors during frontmatter processing
