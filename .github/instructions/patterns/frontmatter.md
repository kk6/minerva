---
applyTo: 'src/**/*.py'
---

# Frontmatter Processing Patterns for Minerva

## Basic Concepts

The Minerva project uses the `python-frontmatter` library to process frontmatter (YAML format metadata) in Obsidian notes. The following basic principles are observed for frontmatter processing:

1. **Consistency**: Use a consistent frontmatter format for all notes
2. **Metadata Preservation**: Respect and preserve existing frontmatter data
3. **Automatic Addition**: Automatically add or update necessary metadata
4. **Separation**: Separate frontmatter processing from file operations
5. **Centralization**: Use FrontmatterManager class for all frontmatter operations

## FrontmatterManager Class

The `FrontmatterManager` class centralizes all frontmatter-related operations, providing a clean interface for metadata management:

```python
from minerva.frontmatter_manager import FrontmatterManager

# Initialize with default author
manager = FrontmatterManager(default_author="Claude 3.7 Sonnet")

# Generate metadata for a new note
post = manager.generate_metadata(
    text="Content of the note",
    author="Custom Author",
    is_new_note=True,
    tags=["project", "documentation"]
)

# Read existing metadata from a file
existing_metadata = manager.read_existing_metadata(file_path)

# Add a tag to an existing note
manager.add_tag(file_path, "new-tag")

# Remove a tag from an existing note
manager.remove_tag(file_path, "old-tag")

# Update all tags for a note
manager.update_tags(file_path, ["tag1", "tag2", "tag3"])
```

## Legacy Function Support (Backward Compatibility)

For backward compatibility, the following functions are still available as wrappers:

```python
def _generate_note_metadata(
    text: str,
    author: str | None = None,
    is_new_note: bool = True,
    existing_frontmatter: dict | None = None,
    tags: list[str] | None = None,
) -> frontmatter.Post:
    """
    Legacy wrapper for FrontmatterManager.generate_metadata().

    DEPRECATED: Use FrontmatterManager directly for new code.
    """
    manager = FrontmatterManager()
    return manager.generate_metadata(
        text=text,
        author=author,
        is_new_note=is_new_note,
        existing_frontmatter=existing_frontmatter,
        tags=tags
    )

def _read_existing_frontmatter(file_path: Path) -> dict | None:
    """
    Legacy wrapper for FrontmatterManager.read_existing_metadata().

    DEPRECATED: Use FrontmatterManager directly for new code.
    """
    manager = FrontmatterManager()
    return manager.read_existing_metadata(file_path)
```

## Frontmatter Generation

Pattern for generating or updating frontmatter for new or existing notes:

```python
def generate_metadata_example():
    """Example of using FrontmatterManager for metadata generation."""
    manager = FrontmatterManager(default_author="AI Assistant")

    # For a new note
    post = manager.generate_metadata(
        text="This is a new note content",
        author="Custom Author",
        is_new_note=True,
        tags=["example", "documentation"]
    )

    # For updating an existing note
    existing_metadata = manager.read_existing_metadata(file_path)
    post = manager.generate_metadata(
        text="Updated content",
        is_new_note=False,
        existing_frontmatter=existing_metadata,
        tags=["updated", "example"]
    )

    return post
```

## Tag Management

Pattern for managing tags in frontmatter:

```python
def tag_management_example(file_path: Path):
    """Example of tag management using FrontmatterManager."""
    manager = FrontmatterManager()

    # Add a single tag
    manager.add_tag(file_path, "new-tag")

    # Remove a single tag
    manager.remove_tag(file_path, "old-tag")

    # Update all tags (replaces existing tags)
    manager.update_tags(file_path, ["tag1", "tag2", "tag3"])

    # Get current tags
    current_tags = manager.get_tags(file_path)

    return current_tags
```

## Date Time Format

Minerva standardizes date and time information in frontmatter using ISO 8601 format:

```python
# Get current date time in ISO 8601 format
now = datetime.now().isoformat()  # Example: '2025-05-02T12:34:56.789012'

# Add to frontmatter
post.metadata["created"] = now
```

## Error Handling

Pattern for error handling in frontmatter operations:

```python
def safe_frontmatter_operation(file_path: Path):
    """Example of safe frontmatter operations with error handling."""
    manager = FrontmatterManager()

    try:
        # Attempt to read existing metadata
        metadata = manager.read_existing_metadata(file_path)
        if metadata is None:
            logger.warning("File %s does not exist or cannot be read", file_path)
            return None

        # Perform operations
        manager.add_tag(file_path, "processed")
        return metadata

    except PermissionError as e:
        logger.error("Permission denied accessing file %s: %s", file_path, e)
        raise
    except Exception as e:
        logger.error("Unexpected error processing frontmatter for %s: %s", file_path, e)
        raise
```

## Best Practices

1. **Use FrontmatterManager**: Always use the FrontmatterManager class for new code
2. **Handle Errors Gracefully**: Implement proper error handling for file operations
3. **Preserve Existing Data**: Respect and preserve existing frontmatter data
4. **Consistent Schema**: Maintain a consistent schema (field names and types) for frontmatter
5. **Tag Normalization**: Always normalize tags before processing
6. **Backward Compatibility**: Use legacy wrapper functions only when necessary for compatibility

## Migration Guide

When migrating from legacy functions to FrontmatterManager:

### Before (Legacy)
```python
# Old way using private functions
existing_metadata = _read_existing_frontmatter(file_path)
post = _generate_note_metadata(
    text=content,
    author=author,
    is_new_note=False,
    existing_frontmatter=existing_metadata,
    tags=["new", "tags"]
)
```

### After (New Approach)
```python
# New way using FrontmatterManager
manager = FrontmatterManager(default_author=author)
existing_metadata = manager.read_existing_metadata(file_path)
post = manager.generate_metadata(
    text=content,
    is_new_note=False,
    existing_frontmatter=existing_metadata,
    tags=["new", "tags"]
)
```
