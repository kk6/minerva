# オプション依存関係実装ガイド

このドキュメントでは、Minervaで採用されているオプション依存関係の実装パターンと戦略について説明します。特に、`numpy`、`duckdb`、`sentence-transformers`などの外部ライブラリを必要とするベクトル検索機能を例に、オプション依存関係の適切な管理方法を解説します。

## 概要

Minervaでは以下を可能にする条件付きテスト・依存関係戦略を実装しています：
- オプション依存関係なしでのコア機能動作
- 依存関係インストール時のベクトル検索機能利用
- CI/CDパイプラインでの明確な分離
- 依存関係の有無に関わらず適切な型チェック

## 実装パターン

### 1. モジュールレベルでの条件付きインポート

```python
# ベクトルモジュールの先頭で
try:
    import numpy as np
except ImportError:
    np = None

try:
    import duckdb
except ImportError:
    duckdb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
```

**利点:**
- モジュールレベルでのインポート失敗を明確に処理
- 複雑なインポートパッチなしでテストでのモックが可能
- モジュールキャッシュがテスト分離に干渉しない

### 2. 依存関係チェック関数

```python
def _check_numpy_available() -> None:
    """numpyが利用可能かチェックし、なければエラーを発生させる。"""
    if np is None:
        raise ImportError(
            "ベクトル操作にはnumpyが必要です。"
            "次のコマンドでインストールしてください: pip install 'minerva[vector]'"
        )
```

**使用法:**
- 依存関係を必要とする関数の開始時に呼び出し
- インストール手順を含む明確なエラーメッセージを提供
- 依存関係チェックロジックを一元化

### 3. オプション依存関係に対する型アノテーション

```python
# 依存関係が不足する可能性がある場合は具体的な型を避ける
def embed(self, text: Union[str, List[str]]) -> Any:  # np.ndarrayではなく
    _check_numpy_available()
    # ... 実装
```

**MyPy設定:**
```toml
# pyproject.toml内
[[tool.mypy.overrides]]
module = [
    "numpy.*",
    "sentence_transformers.*", 
    "duckdb.*",
]
ignore_missing_imports = true
```

### 4. 依存関係ベースのテスト用pytestマーカー

```python
# 個別テスト
@pytest.mark.vector
def test_vector_functionality():
    import numpy as np  # ここで安全にインポート
    # ... テスト実装

# モジュール全体にマーカー
pytestmark = pytest.mark.vector  # モジュールレベルで記述
```

**設定:**
```toml
# pyproject.toml内
[tool.pytest.ini_options]
markers = [
    "vector: ベクトル検索依存関係が必要なテスト",
]
```

## CI/CD戦略

### 分離されたテストジョブ

```yaml
# .github/workflows/ci.yml
test-core:
  name: コアテスト（ベクトル依存関係なし）
  steps:
    - run: uv sync --dev  # 基本依存関係のみ
    - run: uv run pytest -m "not vector"

test-vector:
  name: ベクトルテスト（全依存関係あり）  
  steps:
    - run: uv sync --dev --extra vector  # 全依存関係
    - run: uv run pytest -m "vector"
```

**利点:**
- コア機能のより迅速なフィードバック
- 並列実行による総CI時間の短縮
- 関心事の明確な分離
- 適切な依存関係分離

### 依存関係ありでの品質チェック

```yaml
quality-checks:
  steps:
    - run: uv sync --dev --extra vector  # 型チェック用に全依存関係をインストール
    - run: make check-all  # MyPy型チェックを含む
```

**理由:**
- 型チェックには全依存関係が必要
- リンティングとフォーマットは依存関係に関係なく動作
- 品質チェックは全依存関係のコンテキストで実行

## 開発ワークフロー

### Makefileターゲット

```makefile
install: ## 基本依存関係のみ
    uv pip install -e .
    uv sync --group dev

install-vector: ## ベクトル検索依存関係あり
    uv pip install -e ".[vector]"
    uv sync --group dev --extra vector

test-core: ## コアテストのみ（高速）
    uv run pytest -m "not vector"

test-vector: ## ベクトルテストのみ（依存関係必要）
    uv run pytest -m "vector"

check-all-core: ## ベクトル依存関係なしでの品質チェック
    lint type-check test-core
```

### 開発コマンド

```bash
# 日常開発（高速）
make install
make test-core      # ~2-3秒
make check-all-core # コア品質チェック

# ベクトル機能開発  
make install-vector
make test-vector    # ~17秒
make check-all      # 全品質チェック

# コミット前の全テスト
make test           # 全テスト（~20秒）
```

## テストパターン

### 1. インポートエラーテスト

```python
def test_optional_dependency_handling():
    """依存関係が利用できない場合の適切な処理をテスト。"""
    from minerva.vector import indexer
    original_duckdb = indexer.duckdb
    indexer.duckdb = None

    try:
        vector_indexer = VectorIndexer(Path("/test.db"))
        with pytest.raises(ImportError, match="duckdb is required"):
            vector_indexer._get_connection()
    finally:
        indexer.duckdb = original_duckdb
```

### 2. モジュールキャッシュクリア

```python
def test_with_environment_patch():
    with patch.dict(os.environ, {"VAR": "new_value"}):
        # 新しいインポートのため関連モジュールをキャッシュからクリア
        sys.modules.pop("minerva.vector.module", None)
        
        from minerva.vector import module  # 新しい環境での新しいインポート
```

### 3. モック重視 vs 実依存関係テスト

```python
# モックでの高速テスト
def test_vector_logic_with_mocks():
    mock_provider = Mock()
    mock_provider.embed.return_value = Mock()  # 実際のnumpyは不要
    # 実依存関係なしでロジックをテスト

# 実依存関係での統合テスト  
@pytest.mark.vector
def test_vector_integration_real():
    import numpy as np
    provider = SentenceTransformerProvider()
    result = provider.embed("test")
    assert isinstance(result, np.ndarray)
```

## 設定パターン

### 環境ベースの機能切り替え

```python
@dataclass
class MinervaConfig:
    # コア必須フィールド
    vault_path: Path
    
    # 安全なデフォルトを持つオプション機能フィールド
    vector_search_enabled: bool = False
    vector_db_path: Path | None = None

    @classmethod  
    def from_env(cls) -> "MinervaConfig":
        vector_enabled = os.getenv("VECTOR_SEARCH_ENABLED", "false").lower() == "true"
        
        # 機能が有効な場合のみスマートデフォルト
        vector_db_path = None
        if vector_enabled:
            vector_db_path = Path(os.getenv("VECTOR_DB_PATH", f"{vault}/.minerva/vectors.db"))
            
        return cls(
            vector_search_enabled=vector_enabled,
            vector_db_path=vector_db_path,
        )
```

### サービス層統合

```python
class ServiceManager:
    def __init__(self, config: MinervaConfig):
        self.config = config
        
    def semantic_search(self, query: str) -> List[SearchResult]:
        if not self.config.vector_search_enabled:
            raise RuntimeError("ベクトル検索が有効になっていません")
            
        # 依存関係チェックはベクトルモジュール内で発生
        return self._vector_search_impl(query)
```

## パフォーマンス考察

### テストパフォーマンス結果

- **変更前**: 全テストで14.32秒（遅いフィードバックループ）
- **変更後（コアのみ）**: 575テストで2.19秒（85%改善）
- **変更後（ベクトルのみ）**: 73テストで16.88秒（重いテストを分離）

### 開発への影響

- **日常開発**: 85%高速なテスト実行
- **CI効率**: 並列実行により総パイプライン時間短縮
- **デバッグ**: コア機能とオプション機能の問題を明確に分離

## よくある落とし穴と解決策

### 1. モジュールキャッシュ問題

**問題:** 環境変数をパッチするテストが、キャッシュされたモジュールインポートのため失敗する可能性がある。

**解決策:** グローバル状態を変更するテストでは、インポート前にモジュールキャッシュをクリアする。

### 2. テストでのインポート順序

**問題:** 条件付きインポートを使用する際の `E402 Module level import not at top of file`。

**解決策:** 条件付きインポートを標準インポートの後、pytestマーカーの前に配置する。

```python
import pytest
from pathlib import Path

from minerva.core import CoreModule  # 標準インポートを先に

# 条件付きインポートを次に
try:
    import numpy as np
except ImportError:
    np = None

# pytestマーカーを最後に
pytestmark = pytest.mark.vector
```

### 3. 型チェック vs ランタイム動作

**問題:** 依存関係が不足している場合、MyPyがランタイムと異なる型を認識する。

**解決策:** オプション依存関係の戻り値には`Any`型を使用し、不足インポートを無視するようMyPyを設定する。

### 4. CI依存関係インストール

**問題:** 型チェックに依存関係が不足している場合の品質チェック失敗。

**解決策:** 品質チェックジョブでは全依存関係をインストールするが、テスト実行は依存関係要件で分離する。

## ベストプラクティス

1. **ハード依存関係よりも機能フラグ**: インポート成功/失敗に依存するより、設定による機能有効/無効を使用。

2. **明確なエラーメッセージ**: インポートエラーメッセージには常にインストール手順を含める。

3. **粒度の細かいテスト**: 異なる依存関係要件用に分離されたテストカテゴリを作成。

4. **ドキュメント優先**: 機能のオプション性とその依存関係を明確に文書化。

5. **適切な劣化**: オプション依存関係なしでもコア機能は完璧に動作する。

6. **CI並列化**: 依存関係要件でCIジョブを分離して最適なパフォーマンスを実現。

## 将来の検討事項

### 新しいオプション依存関係の追加

新しいオプション機能を追加する際は：

1. **pyproject.toml更新**: `[project.optional-dependencies]`に追加
2. **pytestマーカー作成**: 機能用の新しいマーカーを追加
3. **CI更新**: 必要に応じて分離されたテストジョブを追加
4. **インストール文書化**: READMEとドキュメントを更新
5. **MyPy設定**: 新しい依存関係の無視ルールを追加

### 依存関係管理の進化

プロジェクトが成長した場合の、より洗練された依存関係管理への移行を検討：
- 複数のオプション依存関係グループ
- 機能固有のCIマトリックス
- 条件付きドキュメントビルド
- オプション機能のプラグインアーキテクチャ

## 関連ドキュメント

- [テストガイドライン](test_guidelines.md) - 一般的なテストパターン
- [CI/CDワークフロー](../github_workflow.md) - CI設定詳細
- [Property-Basedテスト](property_based_testing.md) - 高度なテストパターン