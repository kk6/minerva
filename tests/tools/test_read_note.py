from unittest import mock

import pytest

from minerva import tools


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

        result = tools.read_note(read_note_request.filepath)

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
            tools.read_note(read_note_request.filepath)

        mock_read_file.assert_called_once()
