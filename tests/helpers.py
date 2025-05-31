"""Unified test helper utilities for Minerva project."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import frontmatter


class MinervaTestHelper:
    """Minervaプロジェクト用のテストヘルパークラス."""
    
    @staticmethod
    def create_temp_note(
        temp_dir: Path, 
        filename: str, 
        content: str,
        frontmatter_data: Optional[Dict[str, Any]] = None
    ) -> Path:
        """テスト用ノートの作成.
        
        Args:
            temp_dir: 一時ディレクトリのパス
            filename: ファイル名
            content: ノートの内容
            frontmatter_data: フロントマターデータ（省略可能）
            
        Returns:
            作成されたファイルのパス
        """
        if frontmatter_data:
            post = frontmatter.Post(content)
            post.metadata.update(frontmatter_data)
            content_with_frontmatter = frontmatter.dumps(post)
        else:
            content_with_frontmatter = content
            
        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_with_frontmatter, encoding="utf-8")
        return file_path
    
    @staticmethod
    def assert_note_content(
        file_path: Path, 
        expected_content: str,
        expected_frontmatter: Optional[Dict[str, Any]] = None
    ) -> None:
        """ノート内容の検証.
        
        Args:
            file_path: 検証対象のファイルパス
            expected_content: 期待されるコンテンツ
            expected_frontmatter: 期待されるフロントマター（省略可能）
        """
        assert file_path.exists(), f"File {file_path} does not exist"
        
        content = file_path.read_text(encoding="utf-8")
        
        if expected_frontmatter:
            post = frontmatter.loads(content)
            assert post.content.strip() == expected_content.strip()
            for key, value in expected_frontmatter.items():
                assert key in post.metadata
                assert post.metadata[key] == value
        else:
            assert content.strip() == expected_content.strip()
    
    @staticmethod
    def assert_frontmatter_fields(
        file_path: Path, 
        expected_fields: Dict[str, Union[Any, type]]
    ) -> None:
        """フロントマターフィールドの検証.
        
        Args:
            file_path: 検証対象のファイルパス
            expected_fields: 期待されるフィールド（値または型）
        """
        content = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(content)
        
        for key, expected_value in expected_fields.items():
            assert key in post.metadata, f"Field '{key}' not found in frontmatter"
            actual_value = post.metadata[key]
            
            if isinstance(expected_value, type):
                assert isinstance(actual_value, expected_value), \
                    f"Field '{key}' expected type {expected_value}, got {type(actual_value)}"
            else:
                assert actual_value == expected_value, \
                    f"Field '{key}' expected {expected_value}, got {actual_value}"
    
    @staticmethod
    def create_test_config(temp_dir: Path) -> Dict[str, Any]:
        """テスト用設定の作成.
        
        Args:
            temp_dir: 一時ディレクトリのパス
            
        Returns:
            テスト用設定辞書
        """
        return {
            "vault_path": temp_dir,
            "default_note_dir": "test_notes",
            "default_author": "Test Author",
            "encoding": "utf-8"
        }
    
    @staticmethod
    def setup_test_vault(temp_dir: Path) -> Path:
        """テスト用Vaultの初期化.
        
        Args:
            temp_dir: 一時ディレクトリのパス
            
        Returns:
            初期化されたVaultディレクトリのパス
        """
        vault_dir = temp_dir / "test_vault"
        vault_dir.mkdir(exist_ok=True)
        
        # テスト用サブディレクトリの作成
        (vault_dir / "test_notes").mkdir(exist_ok=True)
        (vault_dir / "archive").mkdir(exist_ok=True)
        
        return vault_dir
    
    @staticmethod
    def create_sample_notes(vault_dir: Path) -> List[Path]:
        """サンプルノートの作成.
        
        Args:
            vault_dir: Vaultディレクトリのパス
            
        Returns:
            作成されたノートファイルのパスリスト
        """
        notes = []
        notes_dir = vault_dir / "test_notes"
        
        # 基本ノート
        note1 = MinervaTestHelper.create_temp_note(
            notes_dir,
            "sample1.md",
            "This is a sample note",
            {"tags": ["sample", "test"]}
        )
        notes.append(note1)
        
        # 複雑なフロントマター付きノート
        note2 = MinervaTestHelper.create_temp_note(
            notes_dir,
            "sample2.md",
            "Another sample note with more content",
            {
                "tags": ["example", "documentation"],
                "created": "2025-01-01T00:00:00",
                "author": "Test Author"
            }
        )
        notes.append(note2)
        
        return notes
    
    @staticmethod
    def assert_file_exists(file_path: Path) -> None:
        """ファイルの存在確認.
        
        Args:
            file_path: 確認対象のファイルパス
        """
        assert file_path.exists(), f"File {file_path} does not exist"
    
    @staticmethod
    def assert_file_not_exists(file_path: Path) -> None:
        """ファイルの非存在確認.
        
        Args:
            file_path: 確認対象のファイルパス
        """
        assert not file_path.exists(), f"File {file_path} should not exist"
    
    @staticmethod
    def create_test_file_with_content(
        temp_dir: Path,
        filename: str,
        content: str
    ) -> Path:
        """テスト用ファイルの作成（フロントマターなし）.
        
        Args:
            temp_dir: 一時ディレクトリのパス
            filename: ファイル名
            content: ファイル内容
            
        Returns:
            作成されたファイルのパス
        """
        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path