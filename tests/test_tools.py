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
        mock_write_file = mock.patch("minerva.tools.write_file").start()
        mock.patch("minerva.tools.VAULT_PATH", tmp_path).start()

        yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}

        mock.patch.stopall()

    def test_write_note_creates_file(self, mock_write_setup, write_note_request):
        """Test writing a note creates a new file.

        Expects:
            - write_file is called with correct parameters
            - The function returns the expected file path
            - The filename has .md extension appended
        """
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        expected_path = tmp_path / f"{write_note_request.filename}.md"
        mock_write_file.return_value = expected_path

        result = tools.write_note(write_note_request)

        assert result == expected_path
        mock_write_file.assert_called_once()

        # 検証を強化：正しいパラメータで呼ばれていることを確認
        called_request = mock_write_file.call_args[0][0]
        assert called_request.directory == str(tmp_path)
        assert called_request.filename == f"{write_note_request.filename}.md"
        assert called_request.content == write_note_request.text
        assert called_request.overwrite == write_note_request.is_overwrite

    def test_write_note_overwrites_file(self, mock_write_setup, write_note_request):
        """Test writing a note overwrites an existing file.

        Expects:
            - write_file is called with is_overwrite=True
            - The function returns the expected file path
            - The existing file content would be overwritten
        """
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        test_file = tmp_path / f"{write_note_request.filename}.md"
        test_file.write_text("old content")
        write_note_request.is_overwrite = True

        mock_write_file.return_value = test_file

        result = tools.write_note(write_note_request)

        assert result == test_file
        mock_write_file.assert_called_once()

    def test_write_note_does_not_overwrite_file(
        self, mock_write_setup, write_note_request
    ):
        """Test writing a note does not overwrite an existing file.

        Expects:
            - write_file is called with is_overwrite=False
            - The original file content remains unchanged
            - The function returns the expected file path
        """
        mock_write_file = mock_write_setup["mock_write_file"]
        tmp_path = mock_write_setup["tmp_path"]

        old_content = "old content"
        test_file = tmp_path / f"{write_note_request.filename}.md"
        test_file.write_text(old_content)
        write_note_request.is_overwrite = False

        mock_write_file.return_value = test_file

        result = tools.write_note(write_note_request)

        assert result == test_file
        assert test_file.read_text() == old_content
        mock_write_file.assert_called_once()

    def test_write_note_raises_exception(self, mock_write_setup, write_note_request):
        """Test writing a note raises an exception.

        Expects:
            - When write_file raises an exception, it's propagated to the caller
            - The write_file function is still called once
        """
        mock_write_file = mock_write_setup["mock_write_file"]

        mock_write_file.side_effect = Exception("File write error")

        with pytest.raises(Exception):
            tools.write_note(write_note_request)

        mock_write_file.assert_called_once()

    def test_write_note_invalid_filename(self, mock_write_setup, write_note_request):
        """Test writing a note with an invalid filename.

        Expects:
            - When an invalid filename is provided, an exception is raised
            - write_file is never called due to filename validation
        """
        mock_write_file = mock_write_setup["mock_write_file"]

        write_note_request.filename = "invalid|filename"

        mock_write_file.side_effect = Exception("Invalid filename")

        with pytest.raises(Exception):
            tools.write_note(write_note_request)

        mock_write_file.assert_not_called()


class TestReadNote:
    @pytest.fixture
    def read_note_request(self, tmp_path):
        return tools.ReadNoteRequest(
            filepath=str(tmp_path / "note.md"),
        )

    @pytest.fixture
    def mock_read_setup(self):
        """Fixture providing common mock setup for read tests."""
        mock_read_file = mock.patch("minerva.tools.read_file").start()

        yield {"mock_read_file": mock_read_file}

        mock.patch.stopall()

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

        # 検証を強化：正しいパラメータで呼ばれていることを確認
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

        with pytest.raises(Exception):
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
        mock_search = mock.patch("minerva.tools.search_keyword_in_files").start()
        mock.patch("minerva.tools.VAULT_PATH", tmp_path).start()

        yield {"mock_search": mock_search, "tmp_path": tmp_path}

        mock.patch.stopall()

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

        # 検証を強化：search_keyword_in_filesが正しいパラメータで呼ばれていることを確認
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

        with pytest.raises(Exception):
            tools.search_notes(search_note_request)

        mock_search.assert_called_once()

    def test_search_notes_case_insensitive(
        self, mock_search_setup, search_note_request
    ):
        """Test searching notes with case insensitive option.

        Expects:
            - search_keyword_in_files is called with case_sensitive=False
            - The search configuration properly reflects the case insensitivity
            - The function returns the expected search results
        """
        mock_search = mock_search_setup["mock_search"]
        fake_result = [mock.Mock()]

        search_note_request.case_sensitive = False
        mock_search.return_value = fake_result

        result = tools.search_notes(search_note_request)

        assert result == fake_result
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
