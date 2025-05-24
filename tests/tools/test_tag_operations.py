from pathlib import Path
import pytest
import frontmatter
from unittest import mock

from minerva.tools import (
    add_tag,
    remove_tag,
    get_tags,
    list_all_tags,
    find_notes_with_tag,
    rename_tag,
    _normalize_tag,
    _validate_tag,
)
from minerva.config import DEFAULT_NOTE_DIR

# Test Data
NOTE1_CONTENT = """---
author: Test Author
created: 2023-01-01T12:00:00
tags:
  - TagA
  - tagB
custom_field: preserve_me
---
Content of note1.
"""

NOTE2_CONTENT = """---
author: Another Author
created: 2023-01-02T12:00:00
tags:
  - tagB
  - TagC
  - "  Whitespace Tag  "
---
Content of note2.
"""

NOTE_NO_TAGS_CONTENT = """---
author: No Tags Author
created: 2023-01-03T12:00:00
---
Content of note with no tags.
"""

NOTE_EMPTY_TAGS_CONTENT = """---
author: Empty Tags Author
created: 2023-01-04T12:00:00
tags: []
---
Content of note with empty tags.
"""

NOTE_MALFORMED_FRONTMATTER_CONTENT = """---
author: Malformed Author
created: 2023-01-05T12:00:00
tags: not-a-list
---
Content of note with malformed tags.
"""

NOTE_IN_SUBDIR_CONTENT = """---
author: Subdir Author
created: 2023-01-06T12:00:00
tags:
  - SubTag
---
Content of note in subdirectory.
"""

# --- Pytest Fixtures ---


@pytest.fixture
def mock_vault_path(tmp_path_factory):
    # Create a unique base temporary directory for the vault
    base_vault_path = tmp_path_factory.mktemp("mock_vault_base")

    # Create the main vault directory (e.g., equivalent to VAULT_PATH)
    # This is what VAULT_PATH will be patched to.
    vault_dir = base_vault_path / "actual_vault"
    vault_dir.mkdir()

    # Create the default notes directory within the vault
    # Assuming DEFAULT_NOTE_DIR is relative to vault_dir
    notes_dir = vault_dir / DEFAULT_NOTE_DIR
    notes_dir.mkdir(parents=True, exist_ok=True)

    # Create sample files in the default notes directory
    (notes_dir / "note1.md").write_text(NOTE1_CONTENT)
    (notes_dir / "note2.md").write_text(NOTE2_CONTENT)
    (notes_dir / "note_no_tags.md").write_text(NOTE_NO_TAGS_CONTENT)
    (notes_dir / "note_empty_tags.md").write_text(NOTE_EMPTY_TAGS_CONTENT)
    (notes_dir / "note_malformed_frontmatter.md").write_text(
        NOTE_MALFORMED_FRONTMATTER_CONTENT
    )

    # Create a subdirectory and a note within it
    subdir = notes_dir / "subdir"
    subdir.mkdir()
    (subdir / "note_in_subdir.md").write_text(NOTE_IN_SUBDIR_CONTENT)

    # Create a file at the root of the vault_dir for testing directory scope
    (vault_dir / "root_note.md").write_text(NOTE1_CONTENT.replace("TagA", "RootTag"))

    with mock.patch("minerva.tools.VAULT_PATH", vault_dir):
        yield vault_dir


# --- Helper Functions for Tests ---
def read_md_file(file_path: Path) -> frontmatter.Post:
    return frontmatter.load(str(file_path))


# --- Basic Tests for _normalize_tag ---
def test_normalize_tag():
    # Arrange
    tags = ["  My Tag  ", "UPPERCASE", "NoChange"]
    expected_results = ["my tag", "uppercase", "nochange"]

    # Act & Assert
    for tag, expected in zip(tags, expected_results):
        result = _normalize_tag(tag)
        assert result == expected


# --- Tests for _validate_tag ---


def test_validate_tag_with_simple_text():
    # Arrange
    tag = "validtag"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is True


def test_validate_tag_with_hyphen():
    # Arrange
    tag = "valid-tag"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is True


def test_validate_tag_with_underscore():
    # Arrange
    tag = "valid_tag"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is True


def test_validate_tag_with_space():
    # Arrange
    tag = "tag with space"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is True, (
        "Spaces are allowed by _validate_tag, normalization handles them for storage"
    )


def test_validate_tag_with_empty_string():
    # Arrange
    tag = ""

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Empty string should be invalid"


def test_validate_tag_with_comma():
    # Arrange
    tag = "tag,with,comma"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Tag with comma should be invalid"


def test_validate_tag_with_angle_brackets():
    # Arrange
    tag = "tag<invalid>"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Tag with angle brackets should be invalid"


def test_validate_tag_with_slash():
    # Arrange
    tag = "tag/slash"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Tag with slash should be invalid"


def test_validate_tag_with_question_mark():
    # Arrange
    tag = "tag?question"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Tag with question mark should be invalid"


def test_validate_tag_with_single_quote():
    # Arrange
    tag = "tag'quote"

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Tag with single quote should be invalid"


def test_validate_tag_with_double_quote():
    # Arrange
    tag = 'tag"doublequote'

    # Act
    result = _validate_tag(tag)

    # Assert
    assert result is False, "Tag with double quote should be invalid"


# --- Tests for get_tags ---


def test_get_tags_with_tags(mock_vault_path: Path):
    """Tests that tags can be retrieved from a file (when tags exist)"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    expected_tags = ["TagA", "tagB"]

    # Act
    actual_tags = get_tags(filepath=str(note_path))

    # Assert
    assert sorted(actual_tags) == sorted(expected_tags), (
        "Case should be preserved in tags"
    )


def test_get_tags_no_tags_field(mock_vault_path: Path):
    """Tests that tags can be retrieved from a file (when the tags field doesn't exist)"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    expected_tags: list[str] = []

    # Act
    actual_tags = get_tags(filepath=str(note_path))

    # Assert
    assert actual_tags == expected_tags, (
        "Should return empty list when note has no tags field"
    )


def test_get_tags_empty_tags_list(mock_vault_path: Path):
    """Tests that tags can be retrieved from a file (when the tags list is empty)"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_empty_tags.md"
    expected_tags: list[str] = []

    # Act
    actual_tags = get_tags(filepath=str(note_path))

    # Assert
    assert actual_tags == expected_tags, (
        "Should return empty list when tags field is empty"
    )


def test_get_tags_file_not_exist(mock_vault_path: Path):
    """Tests that tags cannot be retrieved when the file doesn't exist"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "non_existent_note.md"
    expected_tags: list[str] = []

    # Act
    actual_tags = get_tags(filepath=str(note_path))

    # Assert
    assert actual_tags == expected_tags, (
        "Should return empty list when file does not exist"
    )


def test_get_tags_malformed_frontmatter(mock_vault_path: Path):
    """Tests that tags cannot be retrieved from a file with malformed frontmatter"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_malformed_frontmatter.md"
    expected_tags: list[str] = []

    # Act
    actual_tags = get_tags(filepath=str(note_path))

    # Assert
    assert actual_tags == expected_tags, (
        "Should return empty list when frontmatter is malformed"
    )


def test_get_tags_tags_not_a_list(mock_vault_path: Path):
    """Tests that tags cannot be retrieved when the tags field is not a list"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_malformed_frontmatter.md"
    expected_tags: list[str] = []

    # Act
    actual_tags = get_tags(filepath=str(note_path))

    # Assert
    assert actual_tags == expected_tags, (
        "Should return empty list when tags field is not a list"
    )


def test_get_tags_by_filename(mock_vault_path: Path):
    """Tests that tags can be retrieved using a filename"""
    # Arrange
    filename = "note1.md"
    expected_tags = ["TagA", "tagB"]

    # Act
    actual_tags = get_tags(filename=filename)

    # Assert
    assert sorted(actual_tags) == sorted(expected_tags), (
        "Case should be preserved in tags"
    )


def test_get_tags_by_filename_in_subdir(mock_vault_path: Path):
    """Tests that tags can be retrieved from a file in a subdirectory"""
    # Arrange
    filepath = str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir" / "note_in_subdir.md")
    expected_tags = ["SubTag"]

    # Act
    actual_tags = get_tags(filepath=filepath)

    # Assert
    assert actual_tags == expected_tags, (
        "Should correctly get tags from file in subdirectory"
    )


# --- Tests for add_tag ---


def test_add_tag_to_note_without_tags(mock_vault_path: Path):
    """Tests that a tag can be added to a note without existing tags"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")
    original_author = original_post.metadata.get("author")
    tag_to_add = "NewTag"

    # Act
    modified_path = add_tag(filename="note_no_tags.md", tag=tag_to_add)

    # Assert
    assert modified_path == note_path, "Should return the path to the modified file"

    post = read_md_file(modified_path)
    assert "tags" in post.metadata, "Tags field should be created"
    tags = post.metadata["tags"]
    assert isinstance(tags, list), "Tags should be a list"
    assert tags == ["newtag"], "Tag should be added and normalized"
    assert post.metadata.get("created") == original_created, (
        "Created timestamp should be preserved"
    )
    assert "updated" in post.metadata, "Updated timestamp should be added"
    assert post.metadata.get("author") == original_author, "Author should be preserved"


def test_add_tag_to_note_with_existing_tags(mock_vault_path: Path):
    """Tests that a new tag can be added to a note with existing tags"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")
    tag_to_add = "TagC"

    # Act
    modified_path = add_tag(filepath=str(note_path), tag=tag_to_add)

    # Assert
    post = read_md_file(modified_path)
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []

    assert sorted(str(tag) for tag in tags) == sorted(["taga", "tagb", "tagc"]), (
        "Tag should be added and all tags normalized"
    )
    assert post.metadata.get("created") == original_created, (
        "Created timestamp should be preserved"
    )
    assert "updated" in post.metadata, "Updated timestamp should be added"


def test_add_tag_already_exists(mock_vault_path: Path):
    """Tests the behavior when attempting to add a tag that already exists in a note"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    tag_to_add = "taga"  # Already exists (case-insensitive)

    # Act
    modified_path = add_tag(filepath=str(note_path), tag=tag_to_add)

    # Assert
    post = read_md_file(modified_path)
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []

    assert sorted(str(tag) for tag in tags) == sorted(["taga", "tagb"]), (
        "Duplicate tag should not be added"
    )
    assert "updated" in post.metadata, "Updated timestamp should still be added"


def test_add_tag_needs_normalization(mock_vault_path: Path):
    """Tests that a tag needing normalization can be added to a note"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    tag_to_add = "  Tag D With Spaces  "

    # Act
    modified_path = add_tag(filepath=str(note_path), tag=tag_to_add)

    # Assert
    post = read_md_file(modified_path)
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []

    assert "tag d with spaces" in [str(tag).lower() for tag in tags], (
        "Tag should be normalized and added"
    )


def test_add_tag_invalid_format_value_error(mock_vault_path: Path):
    """Tests the behavior when attempting to add a tag with an invalid format"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    invalid_tag = "tag,with,comma"

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid tag"):
        add_tag(filepath=str(note_path), tag=invalid_tag)


def test_add_tag_file_not_found_error(mock_vault_path: Path):
    """Tests the behavior when attempting to add a tag to a non-existent file"""
    # Arrange
    non_existent_path = str(mock_vault_path / "non_existent.md")
    tag_to_add = "ValidTag"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        add_tag(filepath=non_existent_path, tag=tag_to_add)


def test_add_tag_preserves_unrelated_metadata(mock_vault_path: Path):
    """Tests that adding a tag preserves unrelated metadata"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has custom_field
    original_post = read_md_file(note_path)
    original_custom_field = original_post.metadata["custom_field"]
    tag_to_add = "AnotherNewTag"

    # Act
    modified_path = add_tag(filepath=str(note_path), tag=tag_to_add)

    # Assert
    post = read_md_file(modified_path)
    assert post.metadata.get("custom_field") == original_custom_field, (
        "Unrelated metadata should be preserved"
    )


# --- Tests for remove_tag ---


def test_remove_existing_tag(mock_vault_path: Path):
    """Tests that an existing tag can be removed from a note"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")
    tag_to_remove = "TagA"

    # Act
    modified_path = remove_tag(filename="note1.md", tag=tag_to_remove)

    # Assert
    assert modified_path == note_path, "Should return the path to the modified file"

    post = read_md_file(modified_path)
    assert "tags" in post.metadata, "Tags field should still exist"
    tags = post.metadata["tags"]
    assert isinstance(tags, list), "Tags should be a list"
    assert tags == ["tagb"], (
        "Specified tag should be removed and remaining tags normalized"
    )
    assert post.metadata.get("created") == original_created, (
        "Created timestamp should be preserved"
    )
    assert "updated" in post.metadata, "Updated timestamp should be added"
    assert post.metadata.get("custom_field") == "preserve_me", (
        "Unrelated metadata should be preserved"
    )


def test_remove_tag_case_insensitive(mock_vault_path: Path):
    """Tests that tags can be removed regardless of case sensitivity"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    tag_to_remove = "tAgA"  # Different case

    # Act
    modified_path = remove_tag(filepath=str(note_path), tag=tag_to_remove)

    # Assert
    post = read_md_file(modified_path)
    tags = post.metadata["tags"]
    assert isinstance(tags, list), "Tags should be a list"
    assert "taga" not in [tag.lower() for tag in tags], (
        "Tag should be removed regardless of case"
    )
    assert "tagb" in [tag.lower() for tag in tags], "Other tags should remain"


def test_remove_non_existent_tag(mock_vault_path: Path):
    """Tests the behavior when attempting to remove a non-existent tag"""
    # Arrange
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_tags = original_post.metadata["tags"]
    non_existent_tag = "NonExistentTag"

    # Act
    modified_path = remove_tag(filepath=str(note_path), tag=non_existent_tag)

    # Assert
    post = read_md_file(modified_path)
    tags = post.metadata["tags"]
    assert sorted([tag.lower() for tag in tags]) == sorted(
        [tag.lower() for tag in original_tags]
    ), "Tags should remain unchanged"
    assert "updated" in post.metadata, "File should still be updated with timestamp"


def test_remove_last_tag(mock_vault_path: Path):
    """Tests the behavior when removing the last tag from a note"""
    # Arrange
    # Create a temp note with just one tag
    temp_note_path = mock_vault_path / DEFAULT_NOTE_DIR / "temp_single_tag.md"
    temp_content = """---
author: Temp Author
created: 2023-01-07T12:00:00
tags:
  - SingleTag
---
Content of temporary note.
"""
    temp_note_path.write_text(temp_content)
    tag_to_remove = "SingleTag"

    # Act
    modified_path = remove_tag(filepath=str(temp_note_path), tag=tag_to_remove)

    # Assert
    post = read_md_file(modified_path)
    # In the implementation, when the last tag is removed, the tags field itself is removed
    assert "tags" not in post.metadata, (
        "Tags field should be removed when last tag is deleted"
    )
    assert "updated" in post.metadata, "Updated timestamp should be added"


# --- Tests for list_all_tags ---


def test_list_all_tags_in_vault(mock_vault_path: Path):
    """Tests that all tags in the vault can be listed"""
    # Arrange
    expected_tags = sorted(
        ["taga", "tagb", "tagc", "whitespace tag", "subtag", "roottag"]
    )

    # Act
    actual_tags = list_all_tags(directory=None)

    # Assert
    assert sorted(actual_tags) == expected_tags, (
        "Should list all normalized tags in the vault"
    )


def test_list_all_tags_in_directory(mock_vault_path: Path):
    """Tests that tags in a specified directory can be listed"""
    # Arrange
    directory = str(mock_vault_path / DEFAULT_NOTE_DIR)
    expected_tags = sorted(["taga", "tagb", "tagc", "whitespace tag", "subtag"])

    # Act
    actual_tags = list_all_tags(directory=directory)

    # Assert
    assert sorted(actual_tags) == expected_tags, (
        "Should list all normalized tags in the specified directory"
    )


def test_list_all_tags_in_subdirectory(mock_vault_path: Path):
    """Tests that tags in a subdirectory can be listed"""
    # Arrange
    directory = str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir")
    expected_tags = ["subtag"]

    # Act
    actual_tags = list_all_tags(directory=directory)

    # Assert
    assert actual_tags == expected_tags, (
        "Should list all normalized tags in the subdirectory"
    )


def test_list_all_tags_nonexistent_directory(mock_vault_path: Path):
    """Tests that a FileNotFoundError occurs for a non-existent directory"""
    # Arrange
    non_existent_dir = str(mock_vault_path / "does_not_exist")

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        list_all_tags(directory=non_existent_dir)


# --- Tests for find_notes_with_tag ---


def test_find_notes_with_tag(mock_vault_path: Path):
    """Tests that notes containing a specific tag can be found"""
    # Arrange
    tag = "taga"
    expected_paths = [
        str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"),
    ]

    # Act
    actual_paths = find_notes_with_tag(tag=tag, directory=None)

    # Assert
    assert sorted(actual_paths) == sorted(expected_paths), (
        "Should find all notes with the specified tag"
    )


def test_find_notes_with_tag_case_insensitive(mock_vault_path: Path):
    """Tests that notes can be found using case-insensitive tag matching"""
    # Arrange
    tag = "TagA"  # Different case
    expected_paths = [
        str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"),
    ]

    # Act
    actual_paths = find_notes_with_tag(tag=tag, directory=None)

    # Assert
    assert sorted(actual_paths) == sorted(expected_paths), (
        "Search should be case-insensitive"
    )


def test_find_notes_with_tag_in_directory(mock_vault_path: Path):
    """Tests that notes with a specific tag can be found within a specified directory"""
    # Arrange
    tag = "tagb"
    directory = str(mock_vault_path / DEFAULT_NOTE_DIR)
    expected_paths = [
        str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"),
        str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"),
    ]

    # Act
    actual_paths = find_notes_with_tag(tag=tag, directory=directory)

    # Assert
    assert sorted(actual_paths) == sorted(expected_paths), (
        "Should find notes with the tag in the specified directory"
    )


def test_find_notes_with_nonexistent_tag(mock_vault_path: Path):
    """Tests that searching for a non-existent tag returns an empty list"""
    # Arrange
    tag = "nonexistenttag"

    # Act
    actual_paths = find_notes_with_tag(tag=tag, directory=None)

    # Assert
    assert actual_paths == [], "Should return empty list for nonexistent tag"


def test_find_notes_with_tag_nonexistent_directory(mock_vault_path: Path):
    """Tests that a FileNotFoundError occurs when searching in a non-existent directory"""
    # Arrange
    tag = "taga"
    non_existent_dir = str(mock_vault_path / "does_not_exist")

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        find_notes_with_tag(tag=tag, directory=non_existent_dir)


def test_find_notes_with_roottag(mock_vault_path: Path):
    """Tests that root_note tags can be found"""
    # Arrange
    tag = "roottag"
    expected_paths = [str(mock_vault_path / "root_note.md")]

    # Act
    actual_paths = find_notes_with_tag(tag=tag, directory=None)

    # Assert
    assert sorted(actual_paths) == sorted(expected_paths), (
        "Should find root_note.md with roottag"
    )


# --- Tests for rename_tag ---


def test_rename_tag_across_vault(mock_vault_path: Path):
    """Tests that a tag can be renamed across the entire vault"""
    # Arrange
    old_tag = "taga"
    new_tag = "newtag"
    expected_modified_paths = [
        mock_vault_path / DEFAULT_NOTE_DIR / "note1.md",
    ]

    # Act
    modified_paths = rename_tag(old_tag=old_tag, new_tag=new_tag)

    # Assert
    assert sorted(str(p) for p in modified_paths) == sorted(
        str(p) for p in expected_modified_paths
    ), "Should rename tag in all files"

    # Verify tag was actually renamed in the files
    for path in modified_paths:
        tags = get_tags(filepath=str(path))
        assert "newtag" in [t.lower() for t in tags], (
            f"File {path} should contain the new tag"
        )
        assert "taga" not in [t.lower() for t in tags], (
            f"File {path} should not contain the old tag"
        )


def test_rename_tag_in_directory(mock_vault_path: Path):
    """Tests that a tag can be renamed within a specific directory"""
    # Arrange
    old_tag = "tagb"
    new_tag = "updatedb"
    directory = str(mock_vault_path / DEFAULT_NOTE_DIR)
    expected_modified_paths = [
        mock_vault_path / DEFAULT_NOTE_DIR / "note1.md",
        mock_vault_path / DEFAULT_NOTE_DIR / "note2.md",
    ]

    # Act
    modified_paths = rename_tag(old_tag=old_tag, new_tag=new_tag, directory=directory)

    # Assert
    assert sorted(str(p) for p in modified_paths) == sorted(
        str(p) for p in expected_modified_paths
    ), "Should rename tag in the directory"

    # Verify tag was actually renamed in the files
    for path in modified_paths:
        tags = get_tags(filepath=str(path))
        assert "updatedb" in [t.lower() for t in tags], (
            f"File {path} should contain the new tag"
        )
        assert "tagb" not in [t.lower() for t in tags], (
            f"File {path} should not contain the old tag"
        )


def test_rename_tag_to_invalid_format(mock_vault_path: Path):
    """Tests that a ValueError occurs when attempting to rename to an invalid tag format"""
    # Arrange
    old_tag = "taga"
    invalid_new_tag = "tag,with,comma"

    # Act & Assert
    with pytest.raises(ValueError):
        rename_tag(old_tag=old_tag, new_tag=invalid_new_tag)


def test_rename_tag_nonexistent_directory(mock_vault_path: Path):
    """Tests that a FileNotFoundError occurs when renaming tags in a non-existent directory"""
    # Arrange
    old_tag = "taga"
    new_tag = "newtag"
    non_existent_dir = str(mock_vault_path / "does_not_exist")

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        rename_tag(old_tag=old_tag, new_tag=new_tag, directory=non_existent_dir)


def test_rename_tag_to_existing_tag(mock_vault_path: Path):
    """Tests that renaming to an existing tag is handled properly"""
    # Arrange
    old_tag = "taga"
    new_tag = "tagb"  # Already exists in note1.md
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"

    # Act
    modified_paths = rename_tag(old_tag=old_tag, new_tag=new_tag)

    # Assert
    assert note_path in modified_paths, "File should be modified"
    tags = get_tags(filepath=str(note_path))
    assert len(tags) == 1, "Should have one tag after merging duplicates"
    assert "tagb" in [t.lower() for t in tags], "Should keep the existing tag"


def test_rename_roottag(mock_vault_path: Path):
    """Tests that tags in root_note can be renamed"""
    # Arrange
    old_tag = "roottag"
    new_tag = "newroottag"
    expected_modified_paths = [mock_vault_path / "root_note.md"]

    # Act
    modified_paths = rename_tag(old_tag=old_tag, new_tag=new_tag)

    # Assert
    assert sorted(str(p) for p in modified_paths) == sorted(
        str(p) for p in expected_modified_paths
    ), "Should rename tag in root_note.md"

    # Verify tag was actually renamed in the files
    for path in modified_paths:
        tags = get_tags(filepath=str(path))
        assert "newroottag" in [t.lower() for t in tags], (
            f"File {path} should contain the new tag"
        )
        assert "roottag" not in [t.lower() for t in tags], (
            f"File {path} should not contain the old tag"
        )
