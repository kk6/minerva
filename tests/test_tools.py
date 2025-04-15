from unittest import mock

import pytest

from minerva import tools


class TestWriteNote:
    def test_write_note_creates_file(self, tmp_path):
        test_text = "hello world"
        test_filename = "testnote"
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_write_file.return_value = tmp_path / f"{test_filename}.md"
            result = tools.write_note(test_text, test_filename)
            assert result == tmp_path / f"{test_filename}.md"
            mock_write_file.assert_called_once()

    def test_write_note_overwrites_file(self, tmp_path):
        test_text = "hello world"
        test_filename = "testnote"
        test_file = tmp_path / f"{test_filename}.md"
        test_file.write_text("old content")
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_write_file.return_value = test_file
            result = tools.write_note(test_text, test_filename, is_overwrite=True)
            assert result == test_file
            mock_write_file.assert_called_once()

    def test_write_note_does_not_overwrite_file(self, tmp_path):
        test_text = "hello world"
        test_filename = "testnote"
        test_file = tmp_path / f"{test_filename}.md"
        test_file.write_text("old content")
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_write_file.return_value = test_file
            result = tools.write_note(test_text, test_filename, is_overwrite=False)
            assert result == test_file
            mock_write_file.assert_called_once()

    def test_write_note_raises_exception(self, tmp_path):
        test_text = "hello world"
        test_filename = "testnote"
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_write_file.side_effect = Exception("File write error")
            with pytest.raises(Exception):
                tools.write_note(test_text, test_filename)
            mock_write_file.assert_called_once()

    def test_write_note_invalid_filename(self, tmp_path):
        test_text = "hello world"
        test_filename = "invalid|filename"
        with (
            mock.patch("minerva.tools.write_file") as mock_write_file,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_write_file.side_effect = Exception("Invalid filename")
            with pytest.raises(Exception):
                tools.write_note(test_text, test_filename)
            mock_write_file.assert_not_called()


class TestReadNote:
    def test_read_note_returns_content(self, tmp_path):
        test_content = "sample content"
        test_file = tmp_path / "note.md"
        test_file.write_text(test_content)
        with mock.patch("minerva.tools.read_file") as mock_read_file:
            mock_read_file.return_value = test_content
            result = tools.read_note(str(test_file))
            assert result == test_content
            mock_read_file.assert_called_once()

    def test_read_note_raises_exception(self, tmp_path):
        test_file = tmp_path / "note.md"
        with mock.patch("minerva.tools.read_file") as mock_read_file:
            mock_read_file.side_effect = Exception("File read error")
            with pytest.raises(Exception):
                tools.read_note(str(test_file))
            mock_read_file.assert_called_once()


class TestSearchNotes:
    def test_search_notes_returns_results(self, tmp_path):
        test_query = "keyword"
        fake_result = [mock.Mock()]
        with (
            mock.patch("minerva.tools.search_keyword_in_files") as mock_search,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_search.return_value = fake_result
            result = tools.search_notes(test_query)
            assert result == fake_result
            mock_search.assert_called_once()

    def test_search_notes_empty_query(self):
        with pytest.raises(ValueError, match="Query cannot be empty"):
            tools.search_notes("")

    def test_search_notes_raises_exception(self, tmp_path):
        test_query = "keyword"
        with (
            mock.patch("minerva.tools.search_keyword_in_files") as mock_search,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_search.side_effect = Exception("Search error")
            with pytest.raises(Exception):
                tools.search_notes(test_query)
            mock_search.assert_called_once()

    def test_search_notes_case_insensitive(self, tmp_path):
        test_query = "keyword"
        fake_result = [mock.Mock()]
        with (
            mock.patch("minerva.tools.search_keyword_in_files") as mock_search,
            mock.patch("minerva.tools.VAULT_PATH", tmp_path),
        ):
            mock_search.return_value = fake_result
            result = tools.search_notes(test_query, case_sensitive=False)
            assert result == fake_result
            mock_search.assert_called_once()
