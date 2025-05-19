from unittest import mock

import pytest

from minerva import tools


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

        result = tools.search_notes(
            query=search_note_request.query,
            case_sensitive=search_note_request.case_sensitive,
        )

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
            tools.search_notes(
                query=search_note_request.query,
                case_sensitive=search_note_request.case_sensitive,
            )

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
            tools.search_notes(
                query=search_note_request.query,
                case_sensitive=search_note_request.case_sensitive,
            )

        mock_search.assert_called_once()
