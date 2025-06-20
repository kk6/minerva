# ベクター検索 API リファレンス

Minervaのベクター検索（セマンティック検索）機能の完全なAPIリファレンスです。この機能では、AI埋め込みベクターを使用して、キーワード検索では見つけられない意味的に関連するコンテンツを発見できます。

## 目次

1. [概要](#概要)
2. [セットアップと設定](#セットアップと設定)
3. [検索機能](#検索機能)
4. [インデックス管理](#インデックス管理)
5. [バッチ処理](#バッチ処理)
6. [デバッグとメンテナンス](#デバッグとメンテナンス)
7. [エラーハンドリング](#エラーハンドリング)
8. [使用例とワークフロー](#使用例とワークフロー)

## 概要

ベクター検索は以下の技術を使用して実装されています：

- **埋め込みモデル**: `all-MiniLM-L6-v2` (384次元)
- **ベクターデータベース**: DuckDB with VSS (Vector Similarity Search)
- **類似度計算**: コサイン類似度
- **インデックス方式**: HNSW (Hierarchical Navigable Small World)

### 利用可能なMCPツール

| ツール名 | カテゴリ | 目的 |
|---------|----------|------|
| `semantic_search` | 検索 | 自然言語クエリでセマンティック検索 |
| `find_similar_notes` | 検索 | 指定ノートに類似するノートを検索 |
| `find_duplicate_notes` | 検索 | セマンティック類似度による重複ノート検出 |
| `build_vector_index` | インデックス | 全ファイルのベクターインデックス作成 |
| `build_vector_index_batch` | インデックス | 小規模バッチでのインデックス作成 |
| `get_vector_index_status` | 状態確認 | インデックス状況の確認 |
| `process_batch_index` | バッチ処理 | 保留中のバッチタスク処理 |
| `get_batch_index_status` | バッチ処理 | バッチ処理システムの状態確認 |
| `debug_vector_schema` | デバッグ | ベクターデータベースの詳細診断 |
| `reset_vector_database` | メンテナンス | ベクターデータベースの完全リセット |

## セットアップと設定

### 必要な依存関係

```bash
# オプション依存関係のインストール
pip install "minerva[vector]"

# または個別インストール
pip install duckdb sentence-transformers numpy
```

### 環境変数の設定

`.env` ファイルに以下を追加：

```bash
# 基本設定（必須）
VECTOR_SEARCH_ENABLED=true

# 詳細設定（オプション）
VECTOR_DB_PATH=/custom/path/vectors.db  # デフォルト: {vault}/.minerva/vectors.db
EMBEDDING_MODEL=all-MiniLM-L6-v2        # デフォルト: all-MiniLM-L6-v2

# 自動インデックス設定（オプション）
AUTO_INDEX_ENABLED=true                 # デフォルト: true
AUTO_INDEX_STRATEGY=batch               # immediate/batch/background（デフォルト: immediate）

# バッチ処理設定（将来実装予定）
BATCH_SIZE=10                           # バッチサイズ（デフォルト: 10）
BATCH_TIMEOUT=30.0                      # バッチタイムアウト秒数（デフォルト: 30.0）
```

#### 設定オプション詳細

| 設定項目 | デフォルト値 | 説明 | 実装状況 |
|---------|-------------|------|----------|
| `VECTOR_SEARCH_ENABLED` | `false` | ベクター検索機能の有効/無効 | ✅ 実装済み |
| `VECTOR_DB_PATH` | `{vault}/.minerva/vectors.db` | ベクターデータベースファイルパス | ✅ 実装済み |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | 使用する埋め込みモデル名 | ✅ 実装済み |
| `AUTO_INDEX_ENABLED` | `true` | 自動インデックス更新の有効/無効 | ✅ 実装済み |
| `AUTO_INDEX_STRATEGY` | `immediate` | 自動インデックス戦略 | ✅ 実装済み |
| `BATCH_SIZE` | `10` | バッチ処理時のファイル数 | 🚧 内部実装済み、設定公開待ち |
| `BATCH_TIMEOUT` | `30.0` | バッチタイムアウト（秒） | 🚧 内部実装済み、設定公開待ち |

#### 自動インデックス戦略の詳細

- **`immediate`**: ファイル作成/更新時に即座にインデックス化
  - **利点**: 常に最新のインデックス状態を維持
  - **欠点**: ファイル操作のたびに処理負荷
  - **適用場面**: 小規模vault、リアルタイム性重視

- **`batch`**: ファイル変更をバッチ化して定期処理
  - **利点**: 処理効率が良い、システム負荷を分散
  - **欠点**: インデックス更新に遅延
  - **適用場面**: 中規模vault、効率重視

- **`background`**: バックグラウンドでの継続的処理
  - **利点**: ユーザー操作をブロックしない
  - **欠点**: 複雑な実装、デバッグが困難
  - **適用場面**: 大規模vault、パフォーマンス重視

#### 埋め込みモデルオプション

| モデル名 | 次元数 | 言語サポート | パフォーマンス | 推奨用途 |
|----------|--------|-------------|---------------|----------|
| `all-MiniLM-L6-v2` | 384 | 多言語 | 高速 | 一般用途（デフォルト） |
| `all-mpnet-base-v2` | 768 | 英語メイン | 中速 | 高精度英語検索 |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 多言語強化 | 中速 | 日本語コンテンツ重視 |

**注意**: 埋め込みモデルを変更する場合は、既存のベクターインデックスをリセットする必要があります。

### 初期セットアップ手順

```python
# 1. 設定確認
get_vector_index_status()

# 2. 小規模テスト
build_vector_index_batch(max_files=5, force_rebuild=True)

# 3. 動作確認
semantic_search("テストクエリ", limit=3)

# 4. 全体インデックス化
build_vector_index()
```

## 検索機能

### semantic_search

**概要**: 自然言語クエリを使用してセマンティック検索を実行

```python
semantic_search(
    query: str,
    limit: int = 10,
    threshold: float | None = None,
    directory: str | None = None
) -> list[SemanticSearchResult]
```

**パラメータ**:
- `query`: 検索したい内容の自然言語記述
- `limit`: 返す結果の最大数（デフォルト: 10）
- `threshold`: 最小類似度スコア 0.0-1.0（オプション）
- `directory`: 検索対象ディレクトリ（オプション、デフォルト: vault全体）

**返り値**: `SemanticSearchResult`のリスト
- `file_path`: ファイルパス
- `similarity_score`: 類似度スコア（0.0-1.0）
- `content_preview`: コンテンツプレビュー
- `metadata`: ファイルメタデータ

**使用例**:
```python
# 基本的な検索
results = semantic_search("機械学習の概念")

# 閾値を設定した高精度検索
results = semantic_search("プロジェクト計画", limit=5, threshold=0.7)

# 特定ディレクトリ内での検索
results = semantic_search("データ分析", directory="research")
```

**エラー条件**:
- `RuntimeError`: ベクター検索が無効化されている
- `ImportError`: 必要な依存関係がインストールされていない
- `ValueError`: 無効なパラメータ値

### find_similar_notes

**概要**: 指定されたノートに類似するノートを検索

```python
find_similar_notes(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str | None = None,
    limit: int = 5,
    exclude_self: bool = True
) -> list[SemanticSearchResult]
```

**パラメータ**:
- `filename`: 参照ファイル名（`filepath`と排他的）
- `filepath`: 参照ファイルの完全パス（`filename`と排他的）
- `default_path`: ファイル検索時のサブフォルダ（オプション）
- `limit`: 返す結果の最大数（デフォルト: 5）
- `exclude_self`: 参照ファイル自体を結果から除外（デフォルト: true）

**使用例**:
```python
# ファイル名で指定
similar = find_similar_notes(filename="project-analysis.md")

# 完全パスで指定
similar = find_similar_notes(filepath="/vault/research/paper.md", limit=3)

# サブフォルダ内のファイルを参照
similar = find_similar_notes(
    filename="meeting.md",
    default_path="work",
    exclude_self=False
)
```

**エラー条件**:
- `FileNotFoundError`: 指定されたファイルが存在しない
- `RuntimeError`: ファイルがベクターインデックスに登録されていない
- `ValueError`: `filename`と`filepath`の両方または両方とも未指定

### find_duplicate_notes

**概要**: セマンティック類似度を使用して重複の可能性があるノートを検出

```python
find_duplicate_notes(
    similarity_threshold: float = 0.85,
    directory: str | None = None,
    min_content_length: int = 100,
    exclude_frontmatter: bool = True
) -> dict
```

**パラメータ**:
- `similarity_threshold`: 重複判定の類似度閾値 0.0-1.0（デフォルト: 0.85）
- `directory`: 検索対象ディレクトリ（Noneの場合vault全体）
- `min_content_length`: 検討対象の最小コンテンツ長（デフォルト: 100バイト）
- `exclude_frontmatter`: 分析時にフロントマターを除外（デフォルト: True）

**返り値**:
```python
{
    "duplicate_groups": [
        {
            "group_id": int,                    # グループID
            "files": [
                {
                    "file_path": str,           # ファイルパス
                    "similarity_score": float,  # 類似度スコア
                    "content_length": int,      # コンテンツ長
                    "preview": str              # コンテンツプレビュー
                }
            ],
            "average_similarity": float,        # グループ内平均類似度
            "max_similarity": float,           # グループ内最大類似度
            "recommendation": str              # 統合推奨事項
        }
    ],
    "statistics": {
        "total_files_analyzed": int,        # 分析対象ファイル数
        "duplicate_groups_found": int,      # 検出された重複グループ数
        "total_duplicates": int,            # 重複ファイル総数
        "potential_space_savings": int,     # 統合による推定削減サイズ
        "analysis_time_seconds": float     # 分析時間（秒）
    },
    "analysis_time": str                    # 分析時間（人間が読める形式）
}
```

**使用例**:
```python
# デフォルト設定での重複検出
result = find_duplicate_notes()

# 高精度での重複検出（厳しい閾値）
result = find_duplicate_notes(similarity_threshold=0.9)

# 特定ディレクトリでの重複検出
result = find_duplicate_notes(
    similarity_threshold=0.8,
    directory="meeting-notes"
)

# 短いコンテンツも含めた重複検出
result = find_duplicate_notes(
    similarity_threshold=0.75,
    min_content_length=50
)

# 結果の活用
for group in result["duplicate_groups"]:
    print(f"重複グループ {group['group_id']} (類似度: {group['max_similarity']:.2f})")
    for file_info in group["files"]:
        print(f"  - {file_info['file_path']} ({file_info['content_length']} bytes)")
    print(f"  推奨: {group['recommendation']}")
```

**活用ワークフロー**:
```python
# 1. 重複検出の実行
duplicates = find_duplicate_notes(similarity_threshold=0.85)

# 2. 統計情報の確認
stats = duplicates["statistics"]
print(f"分析ファイル数: {stats['total_files_analyzed']}")
print(f"重複グループ: {stats['duplicate_groups_found']}")
print(f"削減可能サイズ: {stats['potential_space_savings']} bytes")

# 3. 各グループの詳細確認
for group in duplicates["duplicate_groups"]:
    print(f"\n=== グループ {group['group_id']} ===")
    print(f"平均類似度: {group['average_similarity']:.2f}")

    # ファイル詳細の表示
    for file_info in group["files"]:
        print(f"ファイル: {file_info['file_path']}")
        print(f"プレビュー: {file_info['preview'][:100]}...")
```

**類似度閾値ガイドライン**:
- **0.95-1.0**: ほぼ同一コンテンツ（誤字修正程度の差異）
- **0.85-0.95**: 高い類似性（構造やトピックが同じ）
- **0.70-0.85**: 中程度の類似性（関連するが異なる内容）
- **0.50-0.70**: 低い類似性（部分的な重複）

**エラー条件**:
- `RuntimeError`: ベクター検索が無効化されている
- `ImportError`: 必要な依存関係がインストールされていない
- `ValueError`: 無効なパラメータ値（閾値範囲外等）

**注意事項**:
- 大規模なvaultでは処理時間が長くなる可能性があります
- `exclude_frontmatter=True`では作成日等のメタデータは比較に含まれません
- 非常に短いファイル（`min_content_length`未満）は分析対象外です
- 重複判定は内容の意味的類似性に基づき、ファイル名は考慮されません

## インデックス管理

### build_vector_index

**概要**: Markdownファイルの完全なベクターインデックスを作成

```python
build_vector_index(
    directory: str | None = None,
    file_pattern: str = "*.md",
    force_rebuild: bool = False
) -> dict[str, int | list[str]]
```

**パラメータ**:
- `directory`: インデックス対象ディレクトリ（デフォルト: vault全体）
- `file_pattern`: ファイルパターン（デフォルト: "*.md"）
- `force_rebuild`: 既存のインデックスを強制再構築（デフォルト: false）

**返り値**:
```python
{
    "processed": int,    # 処理されたファイル数
    "skipped": int,      # スキップされたファイル数
    "errors": list[str]  # エラーメッセージのリスト
}
```

**使用例**:
```python
# 全ファイルのインデックス作成
result = build_vector_index()

# 特定ディレクトリの強制再構築
result = build_vector_index(directory="research", force_rebuild=True)

# テキストファイルのインデックス作成
result = build_vector_index(file_pattern="*.txt")
```

### build_vector_index_batch

**概要**: 小規模バッチでのベクターインデックス作成（MCP Inspector安全）

```python
build_vector_index_batch(
    directory: str | None = None,
    file_pattern: str = "*.md",
    max_files: int = 5,
    force_rebuild: bool = False
) -> dict[str, int | list[str]]
```

**パラメータ**:
- `directory`: インデックス対象ディレクトリ（デフォルト: vault全体）
- `file_pattern`: ファイルパターン（デフォルト: "*.md"）
- `max_files`: 1回の処理で扱う最大ファイル数（デフォルト: 5、上限: 100）
- `force_rebuild`: 既存のインデックスを強制再構築（デフォルト: false）

**返り値**:
```python
{
    "processed": int,         # 処理されたファイル数
    "skipped": int,           # スキップされたファイル数
    "errors": list[str],      # エラーメッセージのリスト
    "total_files_found": int  # 発見された総ファイル数
}
```

**使用例**:
```python
# MCP Inspectorでの安全なテスト
result = build_vector_index_batch(max_files=1, force_rebuild=True)

# 中規模バッチ処理
result = build_vector_index_batch(max_files=20)

# 特定ディレクトリの段階的処理
result = build_vector_index_batch(directory="drafts", max_files=10)
```

**セーフティ機能**:
- `max_files`の上限制限（100ファイル）
- ファイルパターンの検証
- ディレクトリパスの検証（vault外アクセス防止）

### get_vector_index_status

**概要**: ベクターインデックスの現在の状態を取得

```python
get_vector_index_status() -> dict[str, int | bool | str]
```

**返り値**:
```python
{
    "vector_search_enabled": bool,     # ベクター検索の有効/無効
    "database_exists": bool,           # データベースファイルの存在
    "indexed_files": int,              # インデックス済みファイル数
    "total_files": int,                # 総ファイル数
    "index_completeness": float,       # インデックス完成度（0.0-1.0）
    "database_size": int,              # データベースサイズ（バイト）
    "last_updated": str,               # 最終更新日時
    "embedding_model": str             # 使用中の埋め込みモデル
}
```

**使用例**:
```python
# 現在の状態確認
status = get_vector_index_status()
print(f"インデックス完成度: {status['index_completeness']:.1%}")
print(f"インデックス済み: {status['indexed_files']}/{status['total_files']} ファイル")
```

## バッチ処理

### process_batch_index

**概要**: 保留中のバッチインデックスタスクを処理

```python
process_batch_index() -> dict[str, Any]
```

**返り値**:
```python
{
    "tasks_processed": int,      # 処理されたタスク数
    "queue_size_before": int,    # 処理前のキューサイズ
    "queue_size_after": int,     # 処理後のキューサイズ
    "message": str               # 処理結果メッセージ
}
```

**使用例**:
```python
# 保留中のタスクを処理
result = process_batch_index()
print(f"処理済みタスク: {result['tasks_processed']}")
```

**注意**: `immediate`戦略では機能しません。`batch`または`background`戦略でのみ有効。

### get_batch_index_status

**概要**: バッチインデックスシステムの状態を取得

```python
get_batch_index_status() -> dict[str, Any]
```

**返り値**:
```python
{
    "auto_index_enabled": bool,      # 自動インデックスの有効/無効
    "auto_index_strategy": str,      # インデックス戦略
    "vector_search_enabled": bool,   # ベクター検索の有効/無効
    "queue_size": int,               # 現在のキューサイズ
    "tasks_queued": int,             # キューされたタスク数
    "tasks_processed": int,          # 処理済みタスク数
    "batches_processed": int,        # 処理済みバッチ数
    "errors": int                    # エラー数
}
```

**使用例**:
```python
# バッチシステムの状態確認
status = get_batch_index_status()
if status["queue_size"] > 0:
    print(f"待機中のタスク: {status['queue_size']}")
    process_batch_index()
```

## デバッグとメンテナンス

### debug_vector_schema

**概要**: ベクターデータベースの詳細診断情報を取得

```python
debug_vector_schema() -> dict
```

**返り値**:
```python
{
    "embedding_model": str,              # 埋め込みモデル名
    "test_embedding_dimension": int,     # テスト埋め込みの次元数
    "test_embedding_type": str,          # 埋め込みのデータ型
    "database_path": str,                # データベースファイルパス
    "database_exists": bool,             # データベースファイルの存在
    "existing_tables": list[str],        # 既存テーブルのリスト
    "vectors_table_schema": dict,        # ベクターテーブルのスキーマ
    "database_error": str                # データベースエラー（存在する場合）
}
```

**使用例**:
```python
# 詳細診断の実行
debug_info = debug_vector_schema()
print(f"埋め込み次元: {debug_info['test_embedding_dimension']}")
print(f"既存テーブル: {debug_info['existing_tables']}")

# 次元ミスマッチの診断
if debug_info['test_embedding_dimension'] != 384:
    print("警告: 予期しない埋め込み次元")
```

**診断項目**:
- 埋め込みモデルの動作確認
- データベースファイルの存在確認
- テーブルスキーマの検証
- 次元整合性のチェック

### reset_vector_database

**概要**: ベクターデータベースを完全にリセット

```python
reset_vector_database() -> dict[str, str]
```

**返り値**:
```python
{
    "status": str  # 操作の結果メッセージ
}
```

**使用例**:
```python
# 次元ミスマッチエラーの修復
reset_result = reset_vector_database()
print(reset_result["status"])

# リセット後の再構築
build_vector_index()
```

**注意**: この操作は不可逆的です。既存のベクターインデックスは完全に削除されます。

**使用場面**:
- 次元ミスマッチエラーの解決
- データベース破損の修復
- 埋め込みモデル変更時のクリーンアップ
- 開発/テスト環境のリセット

## エラーハンドリング

### 一般的なエラーと対処法

#### ImportError: 依存関係不足
```python
# エラー: sentence-transformers is required
# 解決: 依存関係のインストール
pip install "minerva[vector]"
```

#### RuntimeError: ベクター検索無効
```python
# エラー: Vector search is not enabled
# 解決: 環境変数の設定
VECTOR_SEARCH_ENABLED=true
```

#### 次元ミスマッチエラー
```python
# エラー: Array arguments must be of the same size
# 解決: データベースリセット
reset_vector_database()
build_vector_index()
```

#### FileNotFoundError: ファイル不存在
```python
# エラー: Specified file does not exist
# 解決: ファイルパスの確認
get_vector_index_status()  # インデックス済みファイルの確認
```

### エラー処理のベストプラクティス

1. **段階的診断**: `get_vector_index_status` → `debug_vector_schema`
2. **小規模テスト**: `build_vector_index_batch`でテスト後、全体処理
3. **データバックアップ**: 重要なデータは事前にバックアップ
4. **ログ確認**: エラーメッセージの詳細な記録

## 使用例とワークフロー

### 初回セットアップワークフロー

```python
# ステップ1: 環境確認
status = get_vector_index_status()
if not status["vector_search_enabled"]:
    print("ベクター検索を有効化してください")
    exit()

# ステップ2: 小規模テスト
print("小規模テストを実行中...")
test_result = build_vector_index_batch(max_files=5, force_rebuild=True)
print(f"テスト結果: {test_result['processed']} ファイル処理")

# ステップ3: 動作確認
print("動作確認を実行中...")
search_results = semantic_search("テスト", limit=3)
print(f"検索結果: {len(search_results)} 件")

# ステップ4: 全体インデックス化
print("全体インデックス化を実行中...")
full_result = build_vector_index()
print(f"完了: {full_result['processed']} ファイル処理")
```

### 定期メンテナンスワークフロー

```python
# ステップ1: 現状確認
status = get_vector_index_status()
print(f"完成度: {status['index_completeness']:.1%}")

# ステップ2: 新規ファイルの追加
if status["index_completeness"] < 1.0:
    print("新規ファイルを追加中...")
    result = build_vector_index(force_rebuild=False)
    print(f"追加: {result['processed']} ファイル")

# ステップ3: バッチ処理確認
batch_status = get_batch_index_status()
if batch_status["queue_size"] > 0:
    print("バッチ処理を実行中...")
    process_batch_index()
```

### 類似ノート発見ワークフロー

```python
# ステップ1: 参照ノートの類似ノート検索
reference_file = "important-project.md"
similar_notes = find_similar_notes(filename=reference_file, limit=10)

print(f"{reference_file} に類似するノート:")
for note in similar_notes:
    print(f"- {note.file_path} (類似度: {note.similarity_score:.2f})")

# ステップ2: セマンティック検索で関連コンテンツ発見
related_content = semantic_search("プロジェクト計画", threshold=0.6)
print(f"\n関連コンテンツ ({len(related_content)} 件):")
for content in related_content:
    print(f"- {content.file_path}: {content.content_preview[:100]}...")
```

### 重複ノート検出ワークフロー

```python
# ステップ1: 基本的な重複検出
print("=== 重複ノート検出 ===")
duplicates = find_duplicate_notes(similarity_threshold=0.85)

# ステップ2: 統計情報の表示
stats = duplicates["statistics"]
print(f"分析対象: {stats['total_files_analyzed']} ファイル")
print(f"重複グループ: {stats['duplicate_groups_found']} 個")
print(f"重複ファイル: {stats['total_duplicates']} 件")
print(f"削減可能サイズ: {stats['potential_space_savings']:,} bytes")
print(f"分析時間: {duplicates['analysis_time']}")

# ステップ3: 重複グループの詳細確認
if duplicates["duplicate_groups"]:
    print("\n=== 重複グループ詳細 ===")
    for i, group in enumerate(duplicates["duplicate_groups"], 1):
        print(f"\nグループ {i} (ID: {group['group_id']})")
        print(f"平均類似度: {group['average_similarity']:.2f}")
        print(f"最大類似度: {group['max_similarity']:.2f}")
        print(f"推奨事項: {group['recommendation']}")

        # ファイル一覧
        print("含まれるファイル:")
        for file_info in group["files"]:
            print(f"  - {file_info['file_path']}")
            print(f"    類似度: {file_info['similarity_score']:.2f}")
            print(f"    サイズ: {file_info['content_length']:,} bytes")
            print(f"    プレビュー: {file_info['preview'][:80]}...")
else:
    print("\n重複ノートは検出されませんでした。")

# ステップ4: 特定ディレクトリでの詳細検索（必要に応じて）
print("\n=== 会議ノートの重複検出 ===")
meeting_duplicates = find_duplicate_notes(
    similarity_threshold=0.8,
    directory="meetings",
    min_content_length=200
)
if meeting_duplicates["duplicate_groups"]:
    print(f"会議ノートで {len(meeting_duplicates['duplicate_groups'])} 個の重複グループを検出")
```

### トラブル診断ワークフロー

```python
# ステップ1: 基本診断
print("=== 基本診断 ===")
status = get_vector_index_status()
print(f"ベクター検索: {'有効' if status['vector_search_enabled'] else '無効'}")
print(f"データベース: {'存在' if status['database_exists'] else '不存在'}")

# ステップ2: 詳細診断
print("\n=== 詳細診断 ===")
debug_info = debug_vector_schema()
print(f"埋め込み次元: {debug_info.get('test_embedding_dimension', 'N/A')}")
print(f"既存テーブル: {debug_info.get('existing_tables', [])}")

# ステップ3: 問題があれば修復
if debug_info.get('database_error') or debug_info.get('test_embedding_dimension') != 384:
    print("\n=== 修復実行 ===")
    reset_result = reset_vector_database()
    print(reset_result["status"])

    # 再構築
    build_result = build_vector_index()
    print(f"再構築完了: {build_result['processed']} ファイル")
```

## 関連ドキュメント

- [vector_search_troubleshooting.md](vector_search_troubleshooting.md) - トラブルシューティング詳細ガイド
- [technical_spec.md](technical_spec.md) - 技術仕様とアーキテクチャ
- [optional_dependencies.md](optional_dependencies.md) - オプション依存関係の実装パターン
- [CLAUDE.md](../CLAUDE.md) - 開発者向け詳細情報

## サポート

問題が発生した場合:

1. [GitHub Issues](https://github.com/kk6/minerva/issues) で報告
2. `debug_vector_schema()`の出力結果を添付
3. エラーメッセージの全文を記載
4. 使用環境（OS、Python バージョン、vault サイズ）を明記
