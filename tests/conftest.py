"""共通テストフィクスチャとセットアップ."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests.helpers import MinervaTestHelper


@pytest.fixture
def minerva_test_helper():
    """MinervaTestHelperインスタンスを提供.
    
    Returns:
        MinervaTestHelperのインスタンス
    """
    return MinervaTestHelper()


@pytest.fixture
def test_vault(tmp_path):
    """テスト用Vaultの作成.
    
    Args:
        tmp_path: pytestの一時ディレクトリフィクスチャ
        
    Returns:
        初期化されたVaultディレクトリのパス
    """
    return MinervaTestHelper.setup_test_vault(tmp_path)


@pytest.fixture
def sample_notes(test_vault, minerva_test_helper):
    """サンプルノートの作成.
    
    Args:
        test_vault: テスト用Vaultフィクスチャ
        minerva_test_helper: MinervaTestHelperフィクスチャ
        
    Returns:
        作成されたノートファイルのパスリスト
    """
    return minerva_test_helper.create_sample_notes(test_vault)


# 後方互換性のための既存フィクスチャ
@pytest.fixture
def temp_dir():
    """Fixture that provides a temporary directory for file operations.

    Yields:
        str: Path to a temporary directory that is automatically cleaned up.
    """
    with TemporaryDirectory() as tempdir:
        yield tempdir


@pytest.fixture
def create_test_file(temp_dir):
    """Helper fixture for creating test files with specified content.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        function: Helper function that creates a file with specified name and content
    """
    def _create_file(filename, content):
        file_path = Path(temp_dir) / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    return _create_file


@pytest.fixture
def mock_write_setup(tmp_path):
    """Fixture providing common mock setup for write tests."""
    with (
        mock.patch("minerva.tools.write_file") as mock_write_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}