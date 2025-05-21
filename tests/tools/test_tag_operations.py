import pytest
import frontmatter

from pathlib import Path
from unittest import mock

from minerva.tools import (
    add_tag,
    AddTagRequest,
    remove_tag,
    RemoveTagRequest,
    get_tags,
    GetTagsRequest,
    list_all_tags,
    ListAllTagsRequest,
    find_notes_with_tag,
    FindNotesWithTagRequest,
    rename_tag,
    RenameTagRequest,
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


@pytest.fixture
def get_tags_request_factory(mock_vault_path: Path):
    """GetTagsRequest オブジェクトを作成するファクトリフィクスチャ"""

    def _make_request(filename: str, subdir: str = ""):
        path = mock_vault_path / DEFAULT_NOTE_DIR
        if subdir:
            path = path / subdir
        note_path = path / filename
        return GetTagsRequest(filepath=str(note_path))

    return _make_request


@pytest.fixture
def add_tag_request_factory(mock_vault_path: Path):
    """AddTagRequest オブジェクトを作成するファクトリフィクスチャ"""

    def _make_request(filename: str, tag: str, subdir: str = ""):
        path = mock_vault_path / DEFAULT_NOTE_DIR
        if subdir:
            path = path / subdir
        note_path = path / filename
        return AddTagRequest(filepath=str(note_path), tag=tag)

    return _make_request


@pytest.fixture
def remove_tag_request_factory(mock_vault_path: Path):
    """RemoveTagRequest オブジェクトを作成するファクトリフィクスチャ"""

    def _make_request(filename: str, tag: str, subdir: str = ""):
        path = mock_vault_path / DEFAULT_NOTE_DIR
        if subdir:
            path = path / subdir
        note_path = path / filename
        return RemoveTagRequest(filepath=str(note_path), tag=tag)

    return _make_request


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
    request = GetTagsRequest(filepath=str(note_path))
    tags = get_tags(request)
    assert sorted(tags) == sorted(["TagA", "tagB"])  # Case preserved


def test_get_tags_no_tags_field(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    request = GetTagsRequest(filepath=str(note_path))
    tags = get_tags(request)
    assert tags == []


def test_get_tags_empty_tags_list(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_empty_tags.md"
    request = GetTagsRequest(filepath=str(note_path))
    tags = get_tags(request)
    assert tags == []


def test_get_tags_file_not_exist(mock_vault_path: Path):
    request = GetTagsRequest(
        filepath=str(mock_vault_path / DEFAULT_NOTE_DIR / "non_existent_note.md")
    )
    tags = get_tags(request)
    assert tags == []


def test_get_tags_malformed_frontmatter(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_malformed_frontmatter.md"
    request = GetTagsRequest(filepath=str(note_path))
    tags = get_tags(request)
    assert tags == []  # Should be tolerant and return empty


def test_get_tags_tags_not_a_list(mock_vault_path: Path):
    # This test uses note_malformed_frontmatter.md where tags: not-a-list
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_malformed_frontmatter.md"
    request = GetTagsRequest(filepath=str(note_path))
    tags = get_tags(request)
    assert tags == []


def test_get_tags_by_filename(get_tags_request_factory):
    """Test retrieving tags using the filename approach."""
    # Use the factory to create a properly configured request
    request = get_tags_request_factory(filename="note1.md")
    tags = get_tags(request)
    assert sorted(tags) == sorted(["TagA", "tagB"])


def test_get_tags_by_filename_in_subdir(get_tags_request_factory):
    """Test retrieving tags from a file in a subdirectory."""
    # Use the factory to create a properly configured request for a file in a subdirectory
    request = get_tags_request_factory(filename="note_in_subdir.md", subdir="subdir")
    tags = get_tags(request)
    assert tags == ["SubTag"]


# --- Tests for add_tag ---


def test_add_tag_to_note_without_tags(mock_vault_path: Path, add_tag_request_factory):
    """Test adding a tag to a note that doesn't have any tags."""
    # Use fixture to prepare test
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")
    original_author = original_post.metadata.get("author")

    # Use the factory to create the request
    request = add_tag_request_factory(filename="note_no_tags.md", tag="NewTag")
    modified_path = add_tag(request)
    assert modified_path == note_path

    post = read_md_file(modified_path)
    assert "tags" in post.metadata
    # Convert list to list before comparison in case it's not a list type
    assert list(post.metadata["tags"]) == ["newtag"]
    assert post.metadata.get("created") == original_created
    assert "updated" in post.metadata
    assert post.metadata.get("author") == original_author


def test_add_tag_to_note_with_existing_tags(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")

    request = AddTagRequest(filepath=str(note_path), tag="TagC")
    modified_path = add_tag(request)
    post = read_md_file(modified_path)

    assert sorted(post.metadata["tags"]) == sorted(
        ["taga", "tagb", "tagc"]
    )  # add_tag normalizes existing tags on rewrite
    assert post.metadata.get("created") == original_created
    assert "updated" in post.metadata


def test_add_tag_already_exists(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    request = AddTagRequest(
        filepath=str(note_path), tag="taga"
    )  # Adding "taga" which normalizes to "taga"
    modified_path = add_tag(request)
    post = read_md_file(modified_path)

    # _generate_note_metadata normalizes all tags and de-duplicates
    assert sorted(post.metadata["tags"]) == sorted(["taga", "tagb"])
    assert (
        "updated" in post.metadata
    )  # File is still re-written and 'updated' timestamp changed


def test_add_tag_needs_normalization(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    request = AddTagRequest(filepath=str(note_path), tag="  Tag D With Spaces  ")
    modified_path = add_tag(request)
    post = read_md_file(modified_path)
    assert "tag d with spaces" in post.metadata["tags"]


def test_add_tag_invalid_format_value_error(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    with pytest.raises(ValueError, match="Invalid tag"):
        AddTagRequest(filepath=str(note_path), tag="tag,with,comma")
        # The validation for tag format happens in add_tag itself, not Pydantic model for AddTagRequest.
        # So we call add_tag.
        # Correction: _validate_tag is called inside add_tag, which should raise the error.
        # The Pydantic model AddTagRequest doesn't validate the tag content itself.
        request = AddTagRequest(filepath=str(note_path), tag="tag,with,comma")
        add_tag(request)


def test_add_tag_file_not_found_error(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        request = AddTagRequest(
            filepath=str(mock_vault_path / "non_existent.md"), tag="ValidTag"
        )
        add_tag(request)


def test_add_tag_preserves_unrelated_metadata(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has custom_field
    original_post = read_md_file(note_path)
    assert "custom_field" in original_post.metadata
    original_custom_field = original_post.metadata["custom_field"]

    request = AddTagRequest(filepath=str(note_path), tag="AnotherNewTag")
    modified_path = add_tag(request)
    post = read_md_file(modified_path)

    assert post.metadata.get("custom_field") == original_custom_field


# --- Tests for remove_tag ---


def test_remove_existing_tag(mock_vault_path: Path, remove_tag_request_factory):
    """Test removing an existing tag from a note."""
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_post = read_md_file(note_path)
    original_created = original_post.metadata.get("created")

    # Use the factory to create the request
    request = remove_tag_request_factory(filename="note1.md", tag="TagA")
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)

    assert "tags" in post.metadata
    # Convert to list before comparison
    assert list(post.metadata["tags"]) == ["tagb"]  # _generate_note_metadata normalizes
    assert post.metadata.get("created") == original_created
    assert "updated" in post.metadata
    assert (
        post.metadata.get("custom_field") == "preserve_me"
    )  # Check unrelated metadata


def test_remove_tag_case_insensitive(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    request = RemoveTagRequest(filepath=str(note_path), tag="tAgA")  # Different case
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)
    assert post.metadata["tags"] == ["tagb"]


def test_remove_non_existent_tag(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    original_tags = read_md_file(note_path).metadata["tags"]

    request = RemoveTagRequest(filepath=str(note_path), tag="NonExistentTag")
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)

    # Tags should be normalized by _generate_note_metadata
    assert sorted(post.metadata["tags"]) == sorted(
        [_normalize_tag(t) for t in original_tags]
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

    request = RemoveTagRequest(filepath=str(note_path), tag="OnlyTag")
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)

    assert "tags" not in post.metadata  # Tags field should be removed
    assert "updated" in post.metadata


def test_remove_tag_from_note_with_empty_tags_list(mock_vault_path: Path):
    note_path = (
        mock_vault_path / DEFAULT_NOTE_DIR / "note_empty_tags.md"
    )  # Has tags: []
    request = RemoveTagRequest(filepath=str(note_path), tag="AnyTag")
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)

    # _generate_note_metadata removes 'tags' key if list becomes empty
    assert "tags" not in post.metadata
    assert "updated" in post.metadata


def test_remove_tag_from_note_with_no_tags_field(mock_vault_path: Path):
    note_path = mock_vault_path / DEFAULT_NOTE_DIR / "note_no_tags.md"
    request = RemoveTagRequest(filepath=str(note_path), tag="AnyTag")
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)

    assert "tags" not in post.metadata
    assert "updated" in post.metadata  # File is re-written


def test_remove_tag_file_not_found(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        request = RemoveTagRequest(
            filepath=str(mock_vault_path / "non_existent.md"), tag="AnyTag"
        )
        remove_tag(request)


def test_remove_tag_needs_normalization_for_match(mock_vault_path: Path):
    note_path = (
        mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"
    )  # Has "  Whitespace Tag  "
    request = RemoveTagRequest(
        filepath=str(note_path), tag="whitespace tag"
    )  # Normalized form
    modified_path = remove_tag(request)
    post = read_md_file(modified_path)

    # Check that "whitespace tag" (normalized) is removed, others (normalized) remain
    expected_tags = sorted([_normalize_tag("tagB"), _normalize_tag("TagC")])
    assert sorted(post.metadata["tags"]) == expected_tags


# --- Tests for list_all_tags ---


def test_list_all_tags_basic_scenario(mock_vault_path: Path):
    # Covers: multiple files, varied tags, case variations, whitespace, subdir inclusion
    # Files used: note1.md (TagA, tagB), note2.md (tagB, TagC, "  Whitespace Tag  ")
    # subdir/note_in_subdir.md (SubTag)
    # root_note.md (RootTag, tagB)
    request = ListAllTagsRequest(
        directory=str(mock_vault_path)
    )  # Scan whole mock vault
    all_tags = list_all_tags(request)

    expected_tags = sorted(
        ["taga", "tagb", "tagc", "whitespace tag", "subtag", "roottag"]
    )
    assert all_tags == expected_tags


def test_list_all_tags_scoped_to_subdir(mock_vault_path: Path):
    subdir_path = mock_vault_path / DEFAULT_NOTE_DIR / "subdir"
    request = ListAllTagsRequest(directory=str(subdir_path))
    all_tags = list_all_tags(request)
    assert all_tags == ["subtag"]


def test_list_all_tags_scoped_to_default_notes_dir(mock_vault_path: Path):
    # This test ensures that if directory is specified as DEFAULT_NOTE_DIR (within VAULT_PATH),
    # it correctly lists tags from notes_dir but not from vault_dir root.
    notes_dir_path = mock_vault_path / DEFAULT_NOTE_DIR
    request = ListAllTagsRequest(directory=str(notes_dir_path))
    all_tags = list_all_tags(request)

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

    request = ListAllTagsRequest(directory=str(empty_dir))
    all_tags = list_all_tags(request)
    assert all_tags == []


def test_list_all_tags_on_empty_directory(mock_vault_path: Path):
    empty_dir = mock_vault_path / "truly_empty_dir"
    empty_dir.mkdir()
    request = ListAllTagsRequest(directory=str(empty_dir))
    all_tags = list_all_tags(request)
    assert all_tags == []


def test_list_all_tags_non_existent_directory(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        request = ListAllTagsRequest(
            directory=str(mock_vault_path / "non_existent_dir")
        )
        list_all_tags(request)


def test_list_all_tags_handles_malformed_tag_field(mock_vault_path: Path):
    # note_malformed_frontmatter.md has 'tags: not-a-list'
    # This test ensures list_all_tags still processes other files.
    # It will use the main mock_vault_path which includes note_malformed_frontmatter.md
    request = ListAllTagsRequest(directory=str(mock_vault_path))
    all_tags = list_all_tags(request)

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

    request = ListAllTagsRequest(directory=str(mock_vault_path / DEFAULT_NOTE_DIR))
    all_tags = list_all_tags(request)

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
    request = FindNotesWithTagRequest(tag="tagb", directory=str(mock_vault_path))
    found_files = find_notes_with_tag(request)

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
    request = FindNotesWithTagRequest(tag="taga", directory=str(mock_vault_path))
    found_files = find_notes_with_tag(request)
    assert found_files == [str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md")]


def test_find_notes_with_tag_non_existent_tag(mock_vault_path: Path):
    request = FindNotesWithTagRequest(
        tag="NonExistentTag", directory=str(mock_vault_path)
    )
    found_files = find_notes_with_tag(request)
    assert found_files == []


def test_find_notes_with_tag_needs_normalization(mock_vault_path: Path):
    # Searching for "  TagA  " should find note1.md which has "TagA"
    request = FindNotesWithTagRequest(tag="  TagA  ", directory=str(mock_vault_path))
    found_files = find_notes_with_tag(request)
    assert found_files == [str(mock_vault_path / DEFAULT_NOTE_DIR / "note1.md")]

    # Searching for "  WhItEsPaCe tAg  " should find note2.md
    request = FindNotesWithTagRequest(
        tag="  WhItEsPaCe tAg  ", directory=str(mock_vault_path)
    )
    found_files = find_notes_with_tag(request)
    assert found_files == [str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md")]


def test_find_notes_with_tag_non_existent_directory(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        request = FindNotesWithTagRequest(
            tag="anytag", directory=str(mock_vault_path / "non_existent_dir")
        )
        find_notes_with_tag(request)


def test_find_notes_with_empty_normalized_tag(mock_vault_path: Path):
    request = FindNotesWithTagRequest(
        tag="   ", directory=str(mock_vault_path)
    )  # Tag normalizes to empty
    found_files = find_notes_with_tag(request)
    assert found_files == []


def test_find_notes_with_tag_scoped_to_subdir(mock_vault_path: Path):
    subdir_path_str = str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir")
    # "SubTag" is in subdir/note_in_subdir.md
    request = FindNotesWithTagRequest(tag="SubTag", directory=subdir_path_str)
    found_files = find_notes_with_tag(request)
    assert found_files == [
        str(mock_vault_path / DEFAULT_NOTE_DIR / "subdir" / "note_in_subdir.md")
    ]

    # "tagb" is not in any note directly under subdir (it's in parent dirs)
    request_tagb = FindNotesWithTagRequest(tag="tagb", directory=subdir_path_str)
    found_files_tagb = find_notes_with_tag(request_tagb)
    assert found_files_tagb == []


def test_find_notes_with_tag_scoped_to_default_dir_excludes_root(mock_vault_path: Path):
    default_dir_str = str(mock_vault_path / DEFAULT_NOTE_DIR)
    # "RootTag" is in root_note.md (at VAULT_PATH level), not in DEFAULT_NOTE_DIR
    request = FindNotesWithTagRequest(tag="RootTag", directory=default_dir_str)
    found_files = find_notes_with_tag(request)
    assert found_files == []

    # "tagb" is in note1.md and note2.md within DEFAULT_NOTE_DIR
    request_tagb = FindNotesWithTagRequest(tag="tagb", directory=default_dir_str)
    found_files_tagb = find_notes_with_tag(request_tagb)
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
    request = RenameTagRequest(
        old_tag="TagA", new_tag="NewTagForA", directory=str(mock_vault_path)
    )
    modified_files = rename_tag(request)

    assert str(note1_path) in [str(p) for p in modified_files]
    assert len(modified_files) == 1

    # Check note1.md
    post1 = read_md_file(note1_path)
    assert sorted(post1.metadata["tags"]) == sorted(["newtagfora", "tagb"])
    assert post1.metadata.get("created") == original_note1_created
    assert (
        post1.metadata.get("updated") != original_note1_updated
    )  # Should have changed

    # Check note2.md (should be unchanged)
    post2 = read_md_file(note2_path)
    assert sorted(_normalize_tag(t) for t in post2.metadata["tags"]) == sorted(
        ["tagb", "tagc", "whitespace tag"]
    )


def test_rename_tag_case_insensitive_old_tag(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    # Use the mock_vault_path for the test
    request = RenameTagRequest(
        old_tag="taga", new_tag="StillNewTagA", directory=str(mock_vault_path)
    )  # old_tag is lowercase
    modified_files = rename_tag(request)

    assert str(note1_path) in [str(p) for p in modified_files]
    post1 = read_md_file(note1_path)
    assert "stillnewtaga" in post1.metadata["tags"]


def test_rename_tag_new_tag_casing_preserved_on_write_normalized_on_logic(
    mock_vault_path: Path,
):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    # The function _generate_note_metadata normalizes tags before writing.
    # So, the actual stored tag will be lowercase.
    # The test should reflect this behavior of _generate_note_metadata.
    request = RenameTagRequest(
        old_tag="TagA", new_tag="BrandNewTagWithCase", directory=str(mock_vault_path)
    )
    rename_tag(request)
    post1 = read_md_file(note1_path)
    assert "brandnewtagwithcase" in post1.metadata["tags"]  # It will be normalized


def test_rename_tag_to_existing_tag_merges(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA, tagB
    request = RenameTagRequest(
        old_tag="TagA", new_tag="tagB", directory=str(mock_vault_path)
    )  # Rename TagA to tagB
    modified_files = rename_tag(request)

    assert str(note1_path) in [str(p) for p in modified_files]
    post1 = read_md_file(note1_path)
    # _generate_note_metadata de-duplicates normalized tags
    assert sorted(post1.metadata["tags"]) == [
        "tagb"
    ]  # Only "tagb" should remain (normalized)


def test_rename_tag_non_existent_old_tag(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    original_content = note1_path.read_text()

    request = RenameTagRequest(old_tag="NonExistentTag", new_tag="AnyNewTag")
    modified_files = rename_tag(request)

    assert len(modified_files) == 0
    assert (
        note1_path.read_text() == original_content
    )  # File should not have been re-written


def test_rename_tag_old_and_new_are_same_normalized(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has TagA
    original_post = read_md_file(note1_path)
    original_updated = original_post.metadata.get("updated")

    request = RenameTagRequest(old_tag="TagA", new_tag="taga")  # Normalize to the same
    modified_files = rename_tag(request)
    assert len(modified_files) == 0

    current_post = read_md_file(note1_path)
    # If the file wasn't rewritten, updated time should be same or None if it wasn't there.
    # The rename_tag function has a check to avoid rewriting if tags list effectively doesn't change.
    assert current_post.metadata.get("updated") == original_updated


def test_rename_tag_invalid_new_tag_format(mock_vault_path: Path):
    with pytest.raises(ValueError, match="Invalid new_tag"):
        RenameTagRequest(old_tag="TagA", new_tag="new,tag")  # Pydantic model is fine
        request = RenameTagRequest(old_tag="TagA", new_tag="new,tag")
        rename_tag(request)  # rename_tag itself validates normalized new_tag


def test_rename_tag_non_existent_directory(mock_vault_path: Path):
    with pytest.raises(FileNotFoundError):
        request = RenameTagRequest(
            old_tag="TagA",
            new_tag="NewTag",
            directory=str(mock_vault_path / "non_existent_dir"),
        )
        rename_tag(request)


def test_rename_tag_preserves_unrelated_metadata(mock_vault_path: Path):
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"  # Has custom_field
    original_post = read_md_file(note1_path)
    original_custom_field = original_post.metadata["custom_field"]
    original_author = original_post.metadata["author"]
    original_created = original_post.metadata["created"]

    request = RenameTagRequest(old_tag="TagA", new_tag="TagADifferent")
    rename_tag(request)

    post = read_md_file(note1_path)
    assert post.metadata["custom_field"] == original_custom_field
    assert post.metadata["author"] == original_author
    assert post.metadata["created"] == original_created


def test_rename_tag_across_multiple_files(mock_vault_path: Path):
    # tagB is in note1.md, note2.md, root_note.md
    note1_path = mock_vault_path / DEFAULT_NOTE_DIR / "note1.md"
    note2_path = mock_vault_path / DEFAULT_NOTE_DIR / "note2.md"
    root_note_path = mock_vault_path / "root_note.md"  # Has RootTag, tagB

    request = RenameTagRequest(
        old_tag="tagB", new_tag="UniversalTagB", directory=str(mock_vault_path)
    )
    modified_files = rename_tag(request)

    assert len(modified_files) == 3
    paths_modified = [str(p) for p in modified_files]
    assert str(note1_path) in paths_modified
    assert str(note2_path) in paths_modified
    assert str(root_note_path) in paths_modified

    # Check note1
    post1 = read_md_file(note1_path)
    assert sorted(post1.metadata["tags"]) == sorted(
        [_normalize_tag("TagA"), "universaltagb"]
    )
    # Check note2
    post2 = read_md_file(note2_path)
    assert sorted(post2.metadata["tags"]) == sorted(
        [_normalize_tag("TagC"), _normalize_tag("Whitespace Tag"), "universaltagb"]
    )
    # Check root_note
    post_root = read_md_file(root_note_path)
    assert sorted(post_root.metadata["tags"]) == sorted(
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

    request = RenameTagRequest(
        old_tag="tagB", new_tag="NewTagBInNotesDir", directory=notes_dir_path_str
    )
    modified_files = rename_tag(request)

    paths_modified = [str(p) for p in modified_files]

    # note1.md and note2.md in DEFAULT_NOTE_DIR had "tagB"
    assert str(note1_path) in paths_modified
    assert str(mock_vault_path / DEFAULT_NOTE_DIR / "note2.md") in paths_modified
    assert str(root_note_path) not in paths_modified  # Crucial check

    # Verify root_note.md is unchanged
    current_root_note_tags = read_md_file(root_note_path).metadata["tags"]
    assert sorted(current_root_note_tags) == sorted(original_root_note_tags)

    # Verify a modified note
    post_note1 = read_md_file(note1_path)
    assert "newtagbinnotesdir" in post_note1.metadata["tags"]
    assert "taga" in post_note1.metadata["tags"]
    assert "tagb" not in post_note1.metadata["tags"]


def test_rename_tag_empty_new_tag_after_normalization_is_invalid(mock_vault_path: Path):
    # This relies on _validate_tag disallowing empty normalized tags,
    # which rename_tag calls for the new_tag.
    with pytest.raises(ValueError, match="Invalid new_tag"):
        request = RenameTagRequest(old_tag="TagA", new_tag="   ")
        rename_tag(request)
