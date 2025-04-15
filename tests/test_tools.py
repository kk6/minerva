from unittest import mock
from minerva import tools


def test_write_note_creates_file(tmp_path):
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


def test_read_note_reads_content(tmp_path):
    test_content = "sample content"
    test_file = tmp_path / "note.md"
    test_file.write_text(test_content)
    with mock.patch("minerva.tools.read_file") as mock_read_file:
        mock_read_file.return_value = test_content
        result = tools.read_note(str(test_file))
        assert result == test_content
        mock_read_file.assert_called_once()


def test_search_notes_returns_results(tmp_path):
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
