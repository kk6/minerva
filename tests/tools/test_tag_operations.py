import pytest
import frontmatter

from pathlib import Path
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


# --- Basic Tests for _normalize_tag and _validate_tag (can be expanded) ---
def test_normalize_tag():
    assert _normalize_tag("  My Tag  ") == "my tag"
    assert _normalize_tag("UPPERCASE") == "uppercase"
    assert _normalize_tag("NoChange") == "nochange"  # Example of case change


def test_validate_tag():
    assert _validate_tag("validtag")
    assert _validate_tag("valid-tag")
    assert _validate_tag("valid_tag")
    assert _validate_tag(
        "tag with space"
    )  # Spaces are allowed by _validate_tag, normalization handles them for storage
    assert not _validate_tag("")  # Empty string is invalid
    assert not _validate_tag("tag,with,comma")
    assert not _validate_tag("tag<invalid>")
    assert not _validate_tag("tag/slash")
    assert not _validate_tag("tag?question")
    assert not _validate_tag("tag'quote")
    assert not _validate_tag('tag"doublequote')


# --- Tests for get_tags ---


def test_get_tags_with_tags(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    tags = get_tags(filepath=str(note_path))
    assert sorted(tags) == sorted(["TagA", "tagB"])  # Case preserved


def test_get_tags_no_tags_field(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    tags = get_tags(filepath=str(note_path))
    assert tags == []


def test_get_tags_empty_tags_list(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_empty_tags.md"
    tags = get_tags(filepath=str(note_path))
    assert tags == []


def test_get_tags_file_not_exist(mock_vault_path: Path):
    tags = get_tags(
        filepath=str(mock_vault_path / DEFAULT_NOTE_DIR / "non_existent_note.md")
    )
    assert tags == []


def test_get_tags_malformed_frontmatter(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_malformed_frontmatter.md"
    tags = get_tags(filepath=str(note_path))
    assert tags == []  # Should be tolerant and return empty


def test_get_tags_tags_not_a_list(mock_vault_path: Path):
    # This test uses note_malformed_frontmatter.md where tags: not-a-list
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_malformed_frontmatter.md"
    tags = get_tags(filepath=str(note_path))
    assert tags == []


def test_get_tags_by_filename(mock_vault_path: Path):
    """Test retrieving tags using the filename approach."""
    tags = get_tags(filename="note1.md")
    assert sorted(tags) == sorted(["TagA", "tagB"])


def test_get_tags_by_filename_in_subdir(mock_vault_path: Path):
    """Test retrieving tags from a file in a subdirectory."""
    # ファイルのフルパスを渡す方法
    filepath = str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir" / "note_in_subdir.md")
    tags = get_tags(filepath=filepath)
    assert tags == ["SubTag"]


# --- Tests for add_tag ---


def test_add_tag_to_note_without_tags(mock_vault_path: Path):
    """Test adding a tag to a note that doesn't have any tags."""
    # Use fixture to prepare test
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")
    original_author = original_post.metadata.get("author")

    modified_path = add_tag(filename="note_no_tags.md", tag="NewTag")
    assert modified_path == note_path

    post = read_md_file(modified_path)
    assert "tags" in post.metadata
    # Convert list to list before comparison in case it's not a list type
    tags = post.metadata["tags"]
    assert isinstance(tags, list) and tags == ["newtag"]
    assert post.metadata.get("created") == original_created
    assert "updated" in post.metadata
    assert post.metadata.get("author") == original_author


def test_add_tag_to_note_with_existing_tags(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")

    modified_path = add_tag(filepath=str(note_path), tag="TagC")
    post = read_md_file(modified_path)

    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert sorted(str(tag) for tag in tags) == sorted(
        ["taga", "tagb", "tagc"]
    )  # add_tag normalizes existing tags on rewrite
    assert post.metadata.get("created") == original_created
    assert "updated" in post.metadata


def test_add_tag_already_exists(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    modified_path = add_tag(
        filepath=str(note_path), tag="taga"
    )  # Adding "taga" which normalizes to "taga"
    post = read_md_file(modified_path)

    # _generate_note_metadata normalizes all tags and de-duplicates
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert sorted(str(tag) for tag in tags) == sorted(["taga", "tagb"])
    assert (
        "updated" in post.metadata
    )  # File is still re-written and 'updated' timestamp changed


def test_add_tag_needs_normalization(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    modified_path = add_tag(filepath=str(note_path), tag="  Tag D With Spaces  ")
    post = read_md_file(modified_path)
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert "tag d with spaces" in tags


def test_add_tag_invalid_format_value_error(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    with pytest.raises(ValueError, match="Invalid tag"):
        # The validation for tag format happens in add_tag itself, not Pydantic model for AddTagRequest.
        # So we call add_tag.
        # Correction: _validate_tag is called inside add_tag, which should raise the error.
        # The Pydantic model AddTagRequest doesn't validate the tag content itself.
        add_tag(filepath=str(note_path), tag="tag,with,comma")


def test_add_tag_file_not_found_error(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        add_tag(filepath=str(mock_vault_path / "non_existent.md"), tag="ValidTag")


def test_add_tag_preserves_unrelated_metadata(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has custom_field
    original_post = read_md_file(note_path)
    assert "custom_field" in original_post.metadata
    original_custom_field = original_post.metadata["custom_field"]

    modified_path = add_tag(filepath=str(note_path), tag="AnotherNewTag")
    post = read_md_file(modified_path)

    assert post.metadata.get("custom_field") == original_custom_field


# --- Tests for remove_tag ---


def test_remove_existing_tag(mock_vault_path: Path):
    """Test removing an existing tag from a note."""
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")

    modified_path = remove_tag(filename="note1.md", tag="TagA")
    post = read_md_file(modified_path)

    assert "tags" in post.metadata
    # Convert to list before comparison
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert tags == ["tagb"]  # _generate_note_metadata normalizes
    assert post.metadata.get("created") == original_created
    assert "updated" in post.metadata
    assert (
        post.metadata.get("custom_field") == "preserve_me"
    )  # Check unrelated metadata


def test_remove_tag_case_insensitive(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    modified_path = remove_tag(filepath=str(note_path), tag="tAgA")  # Different case
    post = read_md_file(modified_path)
    assert post.metadata["tags"] == ["tagb"]


def test_remove_non_existent_tag(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_tags = read_md_file(note_path).metadata["tags"]
    if not isinstance(original_tags, list):
        original_tags = [original_tags] if original_tags is not None else []

    modified_path = remove_tag(filepath=str(note_path), tag="NonExistentTag")
    post = read_md_file(modified_path)

    # Tags should be normalized by _generate_note_metadata
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert sorted(str(tag) for tag in tags) == sorted(
        [_normalize_tag(str(t)) for t in original_tags]
    )
    assert "updated" in post.metadata  # File is re-written, so updated changes


def test_remove_last_tag(mock_vault_path: Path):
    # Create a note with a single tag for this test
    single_tag_note_content = """---
author: Single Tag Author
tags:
  - OnlyTag
---
Content.
"""
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "single_tag_note.md"
    note_path.write_text(single_tag_note_content)

    modified_path = remove_tag(filepath=str(note_path), tag="OnlyTag")
    post = read_md_file(modified_path)

    assert "tags" not in post.metadata  # Tags field should be removed
    assert "updated" in post.metadata


def test_remove_tag_from_note_with_empty_tags_list(mock_vault_path: Path):
    note_path = (
        mock_vault_path / DEFAULT_NOTE_DIR / "note_empty_tags.md"
    )  # Has tags: []
    modified_path = remove_tag(filepath=str(note_path), tag="AnyTag")
    post = read_md_file(modified_path)

    # _generate_note_metadata removes 'tags' key if list becomes empty
    assert "tags" not in post.metadata
    assert "updated" in post.metadata


def test_remove_tag_from_note_with_no_tags_field(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    modified_path = remove_tag(filepath=str(note_path), tag="AnyTag")
    post = read_md_file(modified_path)

    assert "tags" not in post.metadata
    assert "updated" in post.metadata  # File is re-written


def test_remove_tag_file_not_found(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        remove_tag(filepath=str(mock_vault_path / "non_existent.md"), tag="AnyTag")


def test_remove_tag_needs_normalization_for_match(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"
    modified_path = remove_tag(filepath=str(note_path), tag="whitespace tag")
    post = read_md_file(modified_path)

    # Check that "whitespace tag" (normalized) is removed, others (normalized) remain
    expected_tags = sorted([_normalize_tag("tagB"), _normalize_tag("TagC")])
    tags = post.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert sorted(str(tag) for tag in tags) == expected_tags


# --- Tests for list_all_tags ---


def test_list_all_tags_basic_scenario(mock_vault_path: Path):
    # Covers: multiple files, varied tags, case variations, whitespace, subdir inclusion
    # Files used: note1.md (TagA, tagB), note2.md (tagB, TagC, "  Whitespace Tag  ")
    # subdir/note_in_subdir.md (SubTag)
    # root_note.md (RootTag, tagB)
    all_tags = list_all_tags(directory=str(mock_vault_path))  # Scan whole mock vault

    expected_tags = sorted(
        ["taga", "tagb", "tagc", "whitespace tag", "subtag", "roottag"]
    )
    assert all_tags == expected_tags


def test_list_all_tags_scoped_to_subdir(mock_vault_path: Path):
    subdir_path = mock_vault_path / DEFAULT_NOTE_DIR / "subdir"
    all_tags = list_all_tags(directory=str(subdir_path))
    assert all_tags == ["subtag"]


def test_list_all_tags_scoped_to_default_notes_dir(mock_vault_path: Path):
    # This test ensures that if directory is specified as DEFAULT_NOTE_DIR (within VAULT_PATH),
    # it correctly lists tags from notes_dir but not from vault_dir root.
    notes_dir_path = mock_vault_path / DEFAULT_NOTE_DIR
    all_tags = list_all_tags(directory=str(notes_dir_path))

    # Expected: taga, tagb (note1), tagb, tagc, whitespace tag (note2), subtag (note_in_subdir)
    # Excluded: roottag (from root_note.md at vault_dir level)
    expected_tags = sorted(["taga", "tagb", "tagc", "subtag", "whitespace tag"])
    assert all_tags == expected_tags


def test_list_all_tags_no_markdown_files_or_no_tags(mock_vault_path: Path):
    empty_dir = mock_vault_path / "empty_notes_dir"
    empty_dir.mkdir()
    (empty_dir / "not_a_markdown.txt").write_text("content")

    note_without_any_tags_content = """---
author: Test
---
No tags here."""
    (empty_dir / "no_tags_here.md").write_text(note_without_any_tags_content)

    all_tags = list_all_tags(directory=str(empty_dir))
    assert all_tags == []


def test_list_all_tags_on_empty_directory(mock_vault_path: Path):
    empty_dir = mock_vault_path / "truly_empty_dir"
    empty_dir.mkdir()
    all_tags = list_all_tags(directory=str(empty_dir))
    assert all_tags == []


def test_list_all_tags_non_existent_directory(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        list_all_tags(directory=str(mock_vault_path / "non_existent_dir"))


def test_list_all_tags_handles_malformed_tag_field(mock_vault_path: Path):
    # note_malformed_frontmatter.md has 'tags: not-a-list'
    # This test ensures list_all_tags still processes other files.
    # It will use the main mock_vault_path which includes note_malformed_frontmatter.md
    all_tags = list_all_tags(directory=str(mock_vault_path))

    # Expected tags from other valid files
    expected_tags = sorted(
        ["taga", "tagb", "tagc", "whitespace tag", "subtag", "roottag"]
    )
    assert all_tags == expected_tags  # malformed note's tags are ignored by get_tags


def test_list_all_tags_with_empty_string_tag_in_file(mock_vault_path: Path):
    note_with_empty_tag_str = """---
tags:
  - ""
  - actual_tag
---
Content
"""
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_with_empty_tag_item.md"
    note_path.write_text(note_with_empty_tag_str)

    all_tags = list_all_tags(directory=str(mock_vault_path / DEFAULT_NOTE_DIR))

    # "" after normalization is empty, so it should not be in the list.
    # We expect 'actual_tag' and others from notes in DEFAULT_NOTE_DIR
    # note1: TagA, tagB -> taga, tagb
    # note2: tagB, TagC, "  Whitespace Tag  " -> tagb, tagc, whitespace tag
    # note_in_subdir: SubTag -> subtag
    # note_with_empty_tag_item: actual_tag -> actual_tag
    # note_no_tags, note_empty_tags, note_malformed should not contribute tags.
    expected = sorted(
        ["taga", "tagb", "tagc", "whitespace tag", "subtag", "actual_tag"]
    )
    assert all_tags == expected


# --- Tests for find_notes_with_tag ---


def test_find_notes_with_tag_multiple_files(mock_vault_path: Path):
    # "tagb" is in note1.md, note2.md, and root_note.md (normalized from TagB)
    found_files = find_notes_with_tag(tag="tagb", directory=str(mock_vault_path))

    expected_paths = sorted(
        [
            str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"),
            str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"),
            str(mock_vault_path / "root_note.md"),
        ]
    )
    assert sorted(found_files) == expected_paths


def test_find_notes_with_tag_single_file(mock_vault_path: Path):
    # "taga" is only in note1.md (normalized from TagA)
    found_files = find_notes_with_tag(tag="taga", directory=str(mock_vault_path))
    assert found_files == [str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md")]


def test_find_notes_with_tag_non_existent_tag(mock_vault_path: Path):
    found_files = find_notes_with_tag(
        tag="NonExistentTag", directory=str(mock_vault_path)
    )
    assert found_files == []


def test_find_notes_with_tag_needs_normalization(mock_vault_path: Path):
    # Searching for "  TagA  " should find note1.md which has "TagA"
    found_files = find_notes_with_tag(tag="  TagA  ", directory=str(mock_vault_path))
    assert found_files == [str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md")]

    # Searching for "  WhItEsPaCe tAg  " should find note2.md
    found_files = find_notes_with_tag(
        tag="  WhItEsPaCe tAg  ", directory=str(mock_vault_path)
    )
    assert found_files == [str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md")]


def test_find_notes_with_tag_non_existent_directory(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        find_notes_with_tag(
            tag="anytag", directory=str(mock_vault_path / "non_existent_dir")
        )


def test_find_notes_with_empty_normalized_tag(mock_vault_path: Path):
    found_files = find_notes_with_tag(
        tag="   ", directory=str(mock_vault_path)
    )  # Tag normalizes to empty
    assert found_files == []


def test_find_notes_with_tag_scoped_to_subdir(mock_vault_path: Path):
    subdir_path_str = str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir")
    # "SubTag" is in subdir/note_in_subdir.md
    found_files = find_notes_with_tag(tag="SubTag", directory=subdir_path_str)
    assert found_files == [
        str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir" / "note_in_subdir.md")
    ]

    # "tagb" is not in any note directly under subdir (it's in parent dirs)
    found_files_tagb = find_notes_with_tag(tag="tagb", directory=subdir_path_str)
    assert found_files_tagb == []


def test_find_notes_with_tag_scoped_to_default_dir_excludes_root(mock_vault_path: Path):
    default_dir_str = str(mock_vault_path / DEFAULT_NOTE_DIR)
    # "RootTag" is in root_note.md (at VAULT_PATH level), not in DEFAULT_NOTE_DIR
    found_files = find_notes_with_tag(tag="RootTag", directory=default_dir_str)
    assert found_files == []

    # "tagb" is in note1.md and note2.md within DEFAULT_NOTE_DIR
    found_files_tagb = find_notes_with_tag(tag="tagb", directory=default_dir_str)
    expected_paths_tagb = sorted(
        [
            str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"),
            str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"),
        ]
    )
    assert sorted(found_files_tagb) == expected_paths_tagb


# --- Tests for rename_tag ---


def test_rename_tag_basic(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    note2_path = (
        mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"
    )  # Has tagB, TagC, Whitespace Tag

    original_note1_post = read_md_file(note1_path)
    original_note1_created = original_note1_post.metadata.get("created")
    original_note1_updated = original_note1_post.metadata.get(
        "updated"
    )  # Might not exist initially

    # Specify the directory for the test to use mock_vault_path
    modified_files = rename_tag(
        old_tag="TagA", new_tag="NewTagForA", directory=str(mock_vault_path)
    )

    assert str(note1_path) in [str(p) for p in modified_files]
    assert len(modified_files) == 1

    # Check note1.md
    post1 = read_md_file(note1_path)
    tags = post1.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert sorted(str(tag) for tag in tags) == sorted(["newtagfora", "tagb"])
    assert post1.metadata.get("created") == original_note1_created
    assert (
        post1.metadata.get("updated") != original_note1_updated
    )  # Should have changed

    # Check note2.md (should be unchanged)
    post2 = read_md_file(note2_path)
    tags2 = post2.metadata["tags"]
    if not isinstance(tags2, list):
        tags2 = [tags2] if tags2 is not None else []
    assert sorted(_normalize_tag(str(t)) for t in tags2) == sorted(
        ["tagb", "tagc", "whitespace tag"]
    )


def test_rename_tag_case_insensitive_old_tag(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    # Use the mock_vault_path for the test
    modified_files = rename_tag(
        old_tag="taga", new_tag="StillNewTagA", directory=str(mock_vault_path)
    )  # old_tag is lowercase

    assert str(note1_path) in [str(p) for p in modified_files]
    post1 = read_md_file(note1_path)
    tags = post1.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert "stillnewtaga" in tags


def test_rename_tag_new_tag_casing_preserved_on_write_normalized_on_logic(
    mock_vault_path: Path,
):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    # The function _generate_note_metadata normalizes tags before writing.
    # So, the actual stored tag will be lowercase.
    # The test should reflect this behavior of _generate_note_metadata.
    rename_tag(
        old_tag="TagA", new_tag="BrandNewTagWithCase", directory=str(mock_vault_path)
    )
    post1 = read_md_file(note1_path)
    tags = post1.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert "brandnewtagwithcase" in tags  # It will be normalized


def test_rename_tag_to_existing_tag_merges(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    modified_files = rename_tag(
        old_tag="TagA", new_tag="tagB", directory=str(mock_vault_path)
    )  # Rename TagA to tagB

    assert str(note1_path) in [str(p) for p in modified_files]
    post1 = read_md_file(note1_path)
    # _generate_note_metadata de-duplicates normalized tags
    tags = post1.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert sorted(str(tag) for tag in tags) == [
        "tagb"
    ]  # Only "tagb" should remain (normalized)


def test_rename_tag_non_existent_old_tag(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    original_content = note1_path.read_text()

    modified_files = rename_tag(old_tag="NonExistentTag", new_tag="AnyNewTag")

    assert len(modified_files) == 0
    assert (
        note1_path.read_text() == original_content
    )  # File should not have been re-written


def test_rename_tag_old_and_new_are_same_normalized(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA
    original_post = read_md_file(note1_path)
    original_updated = original_post.metadata.get("updated")

    modified_files = rename_tag(old_tag="TagA", new_tag="taga")  # Normalize to the same
    assert len(modified_files) == 0

    current_post = read_md_file(note1_path)
    # If the file wasn't rewritten, updated time should be same or None if it wasn't there.
    # The rename_tag function has a check to avoid rewriting if tags list effectively doesn't change.
    assert current_post.metadata.get("updated") == original_updated


def test_rename_tag_invalid_new_tag_format(mock_vault_path: Path):
    with pytest.raises(ValueError, match="Invalid new_tag"):
        rename_tag(old_tag="TagA", new_tag="new,tag")  # Pydantic model is fine
        rename_tag(old_tag="TagA", new_tag="new,tag")


def test_rename_tag_non_existent_directory(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        rename_tag(
            old_tag="TagA",
            new_tag="NewTag",
            directory=str(mock_vault_path / "non_existent_dir"),
        )


def test_rename_tag_preserves_unrelated_metadata(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has custom_field
    original_post = read_md_file(note1_path)
    original_custom_field = original_post.metadata["custom_field"]
    original_author = original_post.metadata["author"]
    original_created = original_post.metadata["created"]

    rename_tag(old_tag="TagA", new_tag="TagADifferent")

    post = read_md_file(note1_path)
    assert post.metadata["custom_field"] == original_custom_field
    assert post.metadata["author"] == original_author
    assert post.metadata["created"] == original_created


def test_rename_tag_across_multiple_files(mock_vault_path: Path):
    # tagB is in note1.md, note2.md, root_note.md
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    note2_path = mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"
    root_note_path = mock_vault_path / "root_note.md"  # Has RootTag, tagB

    modified_files = rename_tag(
        old_tag="tagB", new_tag="UniversalTagB", directory=str(mock_vault_path)
    )

    assert len(modified_files) == 3
    paths_modified = [str(p) for p in modified_files]
    assert str(note1_path) in paths_modified
    assert str(note2_path) in paths_modified
    assert str(root_note_path) in paths_modified

    # Check note1
    post1 = read_md_file(note1_path)
    tags1 = post1.metadata["tags"]
    if not isinstance(tags1, list):
        tags1 = [tags1] if tags1 is not None else []
    assert sorted(str(tag) for tag in tags1) == sorted(
        [_normalize_tag("TagA"), "universaltagb"]
    )
    # Check note2
    post2 = read_md_file(note2_path)
    tags2 = post2.metadata["tags"]
    if not isinstance(tags2, list):
        tags2 = [tags2] if tags2 is not None else []
    assert sorted(str(tag) for tag in tags2) == sorted(
        [_normalize_tag("TagC"), _normalize_tag("Whitespace Tag"), "universaltagb"]
    )
    # Check root_note
    post_root = read_md_file(root_note_path)
    tags_root = post_root.metadata["tags"]
    if not isinstance(tags_root, list):
        tags_root = [tags_root] if tags_root is not None else []
    assert sorted(str(tag) for tag in tags_root) == sorted(
        [_normalize_tag("RootTag"), "universaltagb"]
    )


def test_rename_tag_scoped_to_directory(mock_vault_path: Path):
    # root_note.md has "RootTag", "tagB"
    # subdir/note_in_subdir.md has "SubTag"
    # We'll rename "tagB" to "NewTagB" but only scope to DEFAULT_NOTE_DIR
    # So root_note.md should NOT be affected.

    notes_dir_path_str = str(mock_vault_path / DEFAULT_NOTE_DIR)
    root_note_path = mock_vault_path / "root_note.md"
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB

    original_root_note_tags = read_md_file(root_note_path).metadata["tags"]

    modified_files = rename_tag(
        old_tag="tagB", new_tag="NewTagBInNotesDir", directory=notes_dir_path_str
    )

    paths_modified = [str(p) for p in modified_files]

    # note1.md and note2.md in DEFAULT_NOTE_DIR had "tagB"
    assert str(note1_path) in paths_modified
    assert str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md") in paths_modified
    assert str(root_note_path) not in paths_modified  # Crucial check

    # Verify root_note.md is unchanged
    current_root_note_tags = read_md_file(root_note_path).metadata["tags"]

    # Ensure both are lists before sorting for comparison
    def ensure_list(val):
        if isinstance(val, list):
            return val
        elif val is None:
            return []
        else:
            return [val]

    assert sorted(str(t) for t in ensure_list(current_root_note_tags)) == sorted(
        str(t) for t in ensure_list(original_root_note_tags)
    )

    # Verify a modified note
    post_note1 = read_md_file(note1_path)
    tags = post_note1.metadata["tags"]
    if not isinstance(tags, list):
        tags = [tags] if tags is not None else []
    assert "newtagbinnotesdir" in tags
    tags_list = post_note1.metadata["tags"]
    if not isinstance(tags_list, list):
        tags_list = [tags_list] if tags_list is not None else []
    assert "taga" in tags_list
    assert "tagb" not in tags_list


def test_rename_tag_empty_new_tag_after_normalization_is_invalid(mock_vault_path: Path):
    # This relies on _validate_tag disallowing empty normalized tags,
    # which rename_tag calls for the new_tag.
    with pytest.raises(ValueError, match="Invalid new_tag"):
        rename_tag(old_tag="TagA", new_tag="   ")
