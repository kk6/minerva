from unittest import mock

import pytest

from minerva import tools


class TestWriteNote:
    @pytest.fixture
    def write_note_request(self):
        return tools.WriteNoteRequest(
            text="Sample text",
            filename="sample_note",
            is_overwrite=False,
        )

    @pytest.fixture
    def mock_write_setup(self, tmp_path):
        """Fixture providing common mock setup for write tests."""
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}

    @pytest.mark.parametrize(
        "is_overwrite,old_content,should_raise,expected_exception",
        [
            (False, None, False, None),
            (True, "old content", False, None),
            (False, "old content", True, FileExistsError),
        ],
        ids=["create-new", "overwrite", "no-overwrite"],
    )
    def test_write_note_file_cases(
        self,
        mock_write_setup,
        write_note_request,
        is_overwrite,
        old_content,
        should_raise,
        expected_exception,
    ):
        """Test writing a note for create, overwrite, and no-overwrite cases."""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        test_file = tmp_path / f"{write_note_request.filename}.md"
        if old_content is not None:
            test_file.write_text(old_content)
        write_note_request.is_overwrite = is_overwrite
        if should_raise:
            mock_write_file.side_effect = FileExistsError(
                "File exists and overwrite is False"
            )
            with pytest.raises(
                FileExistsError, match="File exists and overwrite is False"
            ):
                tools.write_note(write_note_request)
            mock_write_file.assert_called_once()
        else:
            mock_write_file.return_value = test_file
            result = tools.write_note(write_note_request)
            assert result == test_file
            mock_write_file.assert_called_once()

    def test_write_note_creates_file_params(self, mock_write_setup, write_note_request):
        """Verify that correct parameters are passed to write_file."""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]
        expected_path = tmp_path / f"{write_note_request.filename}.md"
        mock_write_file.return_value = expected_path
        result = tools.write_note(write_note_request)
        assert result == expected_path
        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == f"{write_note_request.filename}.md"
        assert called_request.content == write_note_request.text
        assert called_request.overwrite == write_note_request.is_overwrite

    def test_write_note_raises_exception(self, mock_write_setup, write_note_request):
        """Verify that exceptions from write_file are propagated."""
        mock_write_file = mock_write_setup["mock_write_file"]
        mock_write_file.side_effect = Exception("File write error")
        with pytest.raises(Exception, match="File write error"):
            tools.write_note(write_note_request)
        mock_write_file.assert_called_once()

    @pytest.mark.parametrize(
        "filename,expected_message,expected_exception",
        [
            ("invalid|filename", "forbidden characters", "pydantic.ValidationError"),
            ("", "cannot be empty", "ValueError"),
        ],
    )
    def test_write_note_invalid_filename(
        self,
        mock_write_setup,
        write_note_request,
        filename,
        expected_message,
        expected_exception,
    ):
        """If the filename is invalid, ValidationError or ValueError is raised and write_file is not called."""
        import pydantic

        mock_write_file = mock_write_setup["mock_write_file"]
        write_note_request.filename = filename
        if expected_exception == "pydantic.ValidationError":
            with pytest.raises(pydantic.ValidationError, match=expected_message):
                tools.write_note(write_note_request)
        else:
            with pytest.raises(ValueError, match=expected_message):
                tools.write_note(write_note_request)
        mock_write_file.assert_not_called()

    def test_write_note_with_subdirectory_path(self, mock_write_setup, write_note_request):
        """Test to verify that paths with subdirectories are processed correctly"""
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        # Update filename to include subdirectory
        write_note_request.filename = "subdir/note_in_subdir"
        expected_dir_path = tmp_path / "subdir"
        expected_file_path = expected_dir_path / "note_in_subdir.md"

        mock_write_file.return_value = expected_file_path

        result = tools.write_note(write_note_request)
        assert result == expected_file_path

        mock_write_file.assert_called_once()
        called_request = mock_write_file.call_args[0][0]

        # Verify that subdirectory is properly separated and directory path and filename are set correctly
        assert called_request.directory == str(expected_dir_path)
        assert called_request.filename == "note_in_subdir.md"
        assert called_request.content == write_note_request.text
        assert called_request.overwrite == write_note_request.is_overwrite


class TestReadNote:
    @pytest.fixture
    def read_note_request(self, tmp_path):
        return tools.ReadNoteRequest(
            filepath=str(tmp_path / "note.md"),
        )

    @pytest.fixture
    def mock_read_setup(self):
        """Fixture providing common mock setup for read tests."""
        with mock.patch("minerva.tools.read_file") as mock_read_file:
            yield {"mock_read_file": mock_read_file}

    def test_read_note_returns_content(self, mock_read_setup, read_note_request):
        """Test reading a note returns the content.

        Expects:
            - read_file is called with correct parameters
            - The function returns the expected content
            - The file path is properly extracted from the request
        """
        mock_read_file = mock_read_setup["mock_read_file"]
        expected_content = "sample content"

        mock_read_file.return_value = expected_content

        result = tools.read_note(read_note_request)

        assert result == expected_content
        mock_read_file.assert_called_once()

        # Enhanced verification: Check that read_file is called with the correct parameters
        import os

        directory, filename = os.path.split(read_note_request.filepath)
        called_request = mock_read_file.call_args[0][0]
        assert called_request.directory == directory
        assert called_request.filename == filename

    def test_read_note_raises_exception(self, mock_read_setup, read_note_request):
        """Test reading a note raises an exception.

        Expects:
            - When read_file raises an exception, it's propagated to the caller
            - The read_file function is still called once
        """
        mock_read_file = mock_read_setup["mock_read_file"]

        mock_read_file.side_effect = Exception("File read error")

        with pytest.raises(Exception, match="File read error"):
            tools.read_note(read_note_request)

        mock_read_file.assert_called_once()


class TestSearchNotes:
    @pytest.fixture
    def search_note_request(self):
        return tools.SearchNoteRequest(
            query="keyword",
            case_sensitive=False,
        )

    @pytest.fixture
    def mock_search_setup(self, tmp_path):
        """Fixture providing common mock setup for search tests."""
        with (
            mock.patch("minerva.tools.search_keyword_in_files") as mock_search,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            yield {"mock_search": mock_search, "tmp_path": tmp_path}

    def test_search_notes_returns_results(self, mock_search_setup, search_note_request):
        """Test searching notes returns results.

        Expects:
            - search_keyword_in_files is called with correct configuration
            - The function returns the search results unmodified
            - The search directory is set to VAULT_PATH
        """
        mock_search = mock_search_setup["mock_search"]
        tmp_path = mock_search_setup["tmp_path"]
        fake_result = [mock.Mock()]

        mock_search.return_value = fake_result

        result = tools.search_notes(search_note_request)

        assert result == fake_result
        mock_search.assert_called_once()

        # Enhanced verification: Check that search_keyword_in_files is called with the correct parameters
        search_config = mock_search.call_args[0][0]
        assert search_config.directory == str(tmp_path)
        assert search_config.keyword == search_note_request.query
        assert search_config.file_extensions == [".md"]
        assert search_config.case_sensitive == search_note_request.case_sensitive

    def test_search_notes_empty_query(self, search_note_request):
        """Test searching notes with an empty query raises an exception.

        Expects:
            - When an empty query is provided, a ValueError is raised with specific message
            - The search function is never called with empty queries
        """
        search_note_request.query = ""

        with pytest.raises(ValueError, match="Query cannot be empty"):
            tools.search_notes(search_note_request)

    def test_search_notes_raises_exception(
        self, mock_search_setup, search_note_request
    ):
        """Test searching notes raises an exception.

        Expects:
            - When search_keyword_in_files raises an exception, it's propagated to the caller
            - The search_keyword_in_files function is still called once
        """
        mock_search = mock_search_setup["mock_search"]

        mock_search.side_effect = Exception("Search error")

        with pytest.raises(Exception, match="Search error"):
            tools.search_notes(search_note_request)

        mock_search.assert_called_once()

    @pytest.mark.parametrize(
        "case_sensitive,expected_config",
        [
            (True, True),
            (False, False),
        ],
        ids=["case-sensitive", "case-insensitive"],
    )
    def test_search_notes_case_sensitivity(
        self, mock_search_setup, search_note_request, case_sensitive, expected_config
    ):
        """Test searching notes with different case sensitivity settings.

        Expects:
            - search_keyword_in_files is called with the correct case_sensitive setting
            - The search configuration properly reflects the case sensitivity setting
        """
        mock_search = mock_search_setup["mock_search"]
        fake_result = [mock.Mock()]

        search_note_request.case_sensitive = case_sensitive
        mock_search.return_value = fake_result

        result = tools.search_notes(search_note_request)

        assert result == fake_result
        search_config = mock_search.call_args[0][0]
        assert search_config.case_sensitive == expected_config


class TestIntegrationTests:
    """Integration tests that test the actual file operations."""

    @pytest.fixture
    def setup_vault(self, tmp_path):
        """Set up a temporary vault directory."""
        with mock.patch("minerva.tools.VAULT_PATH", tmp_path):
            # Create some test files in the vault
            (tmp_path / "note1.md").write_text("This is note 1 with keyword apple")
            (tmp_path / "note2.md").write_text("This is note 2 with keyword banana")
            (tmp_path / "note3.md").write_text("This is note 3 with keyword APPLE")
            yield tmp_path

    def test_integration_write_and_read_note(self, setup_vault):
        """Test writing and then reading a note."""

        # Create a note
        write_request = tools.WriteNoteRequest(
            text="This is a test note", filename="integration_test", is_overwrite=False
        )

        file_path = tools.write_note(write_request)
        assert file_path.exists()

        # Read the note back
        read_request = tools.ReadNoteRequest(filepath=str(file_path))

        content = tools.read_note(read_request)
        assert content == "This is a test note"

    def test_integration_search_notes(self, setup_vault):
        """Test searching notes in the vault."""
        # Search case sensitive
        search_request1 = tools.SearchNoteRequest(query="apple", case_sensitive=True)

        results1 = tools.search_notes(search_request1)
        assert len(results1) == 1
        assert "note1.md" in results1[0].file_path

        # Search case insensitive
        search_request2 = tools.SearchNoteRequest(query="apple", case_sensitive=False)

        results2 = tools.search_notes(search_request2)
        assert len(results2) == 2

        # Verify both files are found (note1 and note3)
        found_files = [result.file_path for result in results2]
        assert any("note1.md" in path for path in found_files)
        assert any("note3.md" in path for path in found_files)

    def test_integration_write_with_overwrite(self, setup_vault):
        """Test overwriting an existing note."""

        # Create initial note
        initial_request = tools.WriteNoteRequest(
            text="Initial content", filename="overwrite_test", is_overwrite=False
        )

        file_path = tools.write_note(initial_request)
        assert file_path.exists()

        # Try to overwrite with is_overwrite=False (should fail)
        with pytest.raises(Exception):
            tools.write_note(
                tools.WriteNoteRequest(
                    text="New content", filename="overwrite_test", is_overwrite=False
                )
            )

        # Verify content is still the original
        read_request = tools.ReadNoteRequest(filepath=str(file_path))
        content = tools.read_note(read_request)
        assert content == "Initial content"

        # Overwrite with is_overwrite=True (should succeed)
        tools.write_note(
            tools.WriteNoteRequest(
                text="New content", filename="overwrite_test", is_overwrite=True
            )
        )

        # Verify content is updated
        content = tools.read_note(read_request)
        assert content == "New content"

    def test_edge_case_empty_file(self, setup_vault):
        """Test reading and searching an empty file."""
        vault_path = setup_vault

        # Create an empty file
        empty_file = vault_path / "empty.md"
        empty_file.touch()

        # Read empty file
        read_request = tools.ReadNoteRequest(filepath=str(empty_file))
        content = tools.read_note(read_request)
        assert content == ""

        # Search in empty files
        search_request = tools.SearchNoteRequest(query="anything", case_sensitive=True)

        results = tools.search_notes(search_request)
        # Empty file should not match any keyword
        assert not any(result.file_path == str(empty_file) for result in results)

    def test_integration_write_to_subdirectory(self, setup_vault):
        """Test for creating a file in a subdirectory"""
        vault_path = setup_vault

        # Create a note with a path that includes a subdirectory
        write_request = tools.WriteNoteRequest(
            text="This is a note in a subdirectory",
            filename="subdir/note_in_subdir",
            is_overwrite=False
        )

        file_path = tools.write_note(write_request)

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "subdir" / "note_in_subdir.md"
        assert file_path == expected_path

        # Verify the content of the created file
        read_request = tools.ReadNoteRequest(filepath=str(file_path))
        content = tools.read_note(read_request)
        assert content == "This is a note in a subdirectory"

    def test_integration_write_to_nested_subdirectory(self, setup_vault):
        """Test for creating a file in multiple levels of nested subdirectories"""
        vault_path = setup_vault

        # Create a note with a path that includes multiple levels of subdirectories
        write_request = tools.WriteNoteRequest(
            text="This is a note in a nested subdirectory",
            filename="level1/level2/level3/deep_note",
            is_overwrite=False
        )

        file_path = tools.write_note(write_request)

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = vault_path / "level1" / "level2" / "level3" / "deep_note.md"
        assert file_path == expected_path

        # Verify the content of the created file
        read_request = tools.ReadNoteRequest(filepath=str(file_path))
        content = tools.read_note(read_request)
        assert content == "This is a note in a nested subdirectory"

    def test_integration_subdirectory_creation(self, setup_vault):
        """Test to verify that non-existent subdirectories are automatically created"""
        vault_path = setup_vault

        # Subdirectory path
        subdir_path = vault_path / "auto_created_dir"

        # Verify that the subdirectory does not exist
        assert not subdir_path.exists()

        # Create a note in a non-existent subdirectory
        write_request = tools.WriteNoteRequest(
            text="Testing automatic directory creation",
            filename="auto_created_dir/auto_note",
            is_overwrite=False
        )

        file_path = tools.write_note(write_request)

        # Verify that the subdirectory was automatically created
        assert subdir_path.exists()
        assert subdir_path.is_dir()

        # Verify that the file was created
        assert file_path.exists()

        # Verify that the file was created at the correct path
        expected_path = subdir_path / "auto_note.md"
        assert file_path == expected_path
