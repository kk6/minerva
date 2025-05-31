"""MinervaTestHelperの使用例とデモンストレーション."""

import pytest
from pathlib import Path

from tests.helpers import MinervaTestHelper


class TestMinervaTestHelperExample:
    """MinervaTestHelperの使用例を示すテストクラス."""
    
    def test_basic_note_creation(self, tmp_path, minerva_test_helper):
        """基本的なノート作成の例.
        
        新しいヘルパーを使った基本的なテストパターンのデモ。
        """
        # ==================== Arrange ====================
        content = "This is a test note"
        filename = "test_note.md"
        
        # ==================== Act ====================
        note_path = minerva_test_helper.create_temp_note(
            tmp_path,
            filename,
            content
        )
        
        # ==================== Assert ====================
        minerva_test_helper.assert_file_exists(note_path)
        minerva_test_helper.assert_note_content(note_path, content)
    
    def test_note_with_frontmatter(self, tmp_path, minerva_test_helper):
        """フロントマター付きノートの作成例."""
        # ==================== Arrange ====================
        content = "Note with metadata"
        frontmatter_data = {
            "title": "Test Note",
            "tags": ["test", "example"],
            "author": "Test Author"
        }
        
        # ==================== Act ====================
        note_path = minerva_test_helper.create_temp_note(
            tmp_path,
            "metadata_note.md",
            content,
            frontmatter_data
        )
        
        # ==================== Assert ====================
        minerva_test_helper.assert_note_content(
            note_path,
            content,
            frontmatter_data
        )
        
        # フロントマターフィールドの型チェック
        minerva_test_helper.assert_frontmatter_fields(
            note_path,
            {
                "title": str,
                "tags": list,
                "author": "Test Author"
            }
        )
    
    def test_vault_setup_with_sample_notes(self, tmp_path, minerva_test_helper):
        """Vault環境のセットアップとサンプルノート作成の例."""
        # ==================== Arrange & Act ====================
        vault_dir = minerva_test_helper.setup_test_vault(tmp_path)
        sample_notes = minerva_test_helper.create_sample_notes(vault_dir)
        
        # ==================== Assert ====================
        # Vaultディレクトリの構造確認
        assert vault_dir.exists()
        assert (vault_dir / "test_notes").exists()
        assert (vault_dir / "archive").exists()
        
        # サンプルノートの確認
        assert len(sample_notes) == 2
        for note_path in sample_notes:
            minerva_test_helper.assert_file_exists(note_path)
    
    def test_migration_from_old_pattern(self, tmp_path):
        """従来のテストパターンからの移行例."""
        # ==================== 従来のパターン ====================
        # file_path = Path(tmp_path) / "old_style.md"
        # with open(file_path, "w", encoding="utf-8") as f:
        #     f.write("Old style content")
        # assert file_path.exists()
        
        # ==================== 新しいパターン ====================
        helper = MinervaTestHelper()
        
        note_path = helper.create_temp_note(
            tmp_path,
            "new_style.md",
            "New style content"
        )
        
        helper.assert_file_exists(note_path)
        helper.assert_note_content(note_path, "New style content")
    
    def test_with_fixture_integration(self, test_vault, sample_notes, minerva_test_helper):
        """共通フィクスチャとの統合例."""
        # ==================== Assert ====================
        # test_vaultフィクスチャによるVault構造の確認
        assert test_vault.exists()
        assert (test_vault / "test_notes").exists()
        
        # sample_notesフィクスチャによるサンプルノートの確認
        assert len(sample_notes) == 2
        
        # 各ノートの内容確認
        for note_path in sample_notes:
            minerva_test_helper.assert_file_exists(note_path)
            
        # 最初のノートのフロントマター確認
        minerva_test_helper.assert_frontmatter_fields(
            sample_notes[0],
            {"tags": list}
        )