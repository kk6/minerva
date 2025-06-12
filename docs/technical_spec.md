# Minerva 技術仕様書

この技術仕様書はMinervaプロジェクトの内部実装の詳細と設計思想について説明します。

## 1. アーキテクチャ概要

Minervaは依存性注入パターンを採用した階層化アーキテクチャです：

1. **サービス層** (`services/`) - **モジュール化済み**
   - **ServiceManager**: 全サービス操作の統一インターフェース（ファサードパターン）
   - **専門化されたサービスモジュール**: 機能別に分離されたサービスクラス群
     - **NoteOperations**: ノート作成・編集・削除・読み込み操作
     - **TagOperations**: タグ追加・削除・一括変更・検索機能
     - **AliasOperations**: エイリアス管理と競合検出
     - **SearchOperations**: 全文検索とフィルタリング機能
   - **MinervaConfig**: 依存性注入用の設定データクラス
   - **create_minerva_service()**: デフォルト設定でのServiceManagerファクトリー関数

2. **MCPサーバー層** (`server.py`) - **MCP 1.9対応済み**
   - **FastMCPサーバー**: MCP 1.9.3準拠、リソースとツールの適切な分離
   - **ダイレクトサービス統合**: ラッパー関数を排除し、サービスメソッドを直接呼び出し
   - **リソース機能** (`@mcp.resource`):
     - `read_note()` - `note://{filepath}`: ノート内容の読み取り専用リソース
     - `search_notes()` - `search://{query}/{case_sensitive}`: 検索結果の読み取り専用リソース
   - **ツール機能** (`@mcp.tool`):
     - `create_note()`, `edit_note()` 関数（状態変更操作）
     - `get_note_delete_confirmation()`, `perform_note_delete()` 関数（2段階削除プロセス）
     - `add_tag()`, `remove_tag()`, `rename_tag()`, `get_tags()`, `list_all_tags()`, `find_notes_with_tag()` 関数

3. **設定管理層** (`config.py`) - **拡張済み**
   - **MinervaConfig**: 新しい設定データクラス
   - **レガシーグローバル変数**: 既存の設定（後方互換性維持）

4. **フロントマター管理層** (`frontmatter_manager.py`)
   - **FrontmatterManager**: 専用のフロントマター処理クラス

5. **ファイル操作層** (`file_handler.py`)
   - `FileWriteRequest`, `FileReadRequest`, `FileDeleteRequest`, `SearchConfig` クラス
   - `write_file()`, `read_file()`, `delete_file()`, `search_keyword_in_files()` 関数

## 2. 基本設計原則

### 2.1 入力検証

システムはPydanticを使用して入力検証を行います：

- すべてのリクエストはPydanticの`BaseModel`を継承したモデルクラスとして定義されています
- フィールドバリデーションは`field_validator`デコレータを使用して実装されています
- 無効な入力は早期に検出され、明確なエラーメッセージが提供されます

### 2.2 責務の分離

- `server.py`モジュールはFastMCPサーバーとツール関数を提供します
- `service.py`モジュールはObsidianノート固有のビジネスロジックを提供します
- `file_handler.py`モジュールは汎用的なファイル操作関数を提供します
- この分離により、将来的に異なるタイプのノートやドキュメントシステムをサポートすることが容易になります

### 2.3 エラー処理

- すべての例外は適切にログに記録され、上位レイヤーに伝播されます
- ファイル操作関連のエラーは詳細な情報とともに捕捉されます
- エラータイプに基づいて異なるログレベルとメッセージが使用されます：
  - `PermissionError`: アクセス権限の問題を明確に識別
  - `IOError/OSError`: ファイルシステム操作に関連するエラー
  - `UnicodeDecodeError`: テキストとして読み取れないファイル（バイナリなど）
  - その他の例外：予期しないエラー
- 実行環境やデバッグに役立つコンテキスト情報（ファイルパスやパラメータ）がログに含まれます
- ユーザーに意味のあるエラーメッセージが提供されます

## 3. モジュール詳細

### 3.1 server.py - MCPサーバー層

#### 3.1.1 アーキテクチャ設計

FastMCPフレームワークを使用したシンプルなサーバー実装：

```python
# サービスインスタンスを初期化
service = create_minerva_service()

# FastMCPサーバーを作成
mcp = FastMCP("minerva", __version__)

# @mcp.tool()デコレータでツールを直接登録
@mcp.tool()
def read_note(filepath: str) -> str:
    """Read the content of a markdown note from your Obsidian vault."""
    return service.read_note(filepath)
```

#### 3.1.2 提供ツール関数

サーバーは以下のツール関数を提供します：

**リソース操作（読み取り専用）**:
- `read_note(filepath: str) -> str`: ノートの読み取り（`note://{filepath}`リソース）
- `search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]`: ノート内容検索（`search://{query}/{case_sensitive}`リソース）

**ツール操作（状態変更）**:
- `create_note(text: str, filename: str, author: str | None = None, default_path: str | None = None) -> Path`: 新規ノート作成
- `edit_note(text: str, filename: str, author: str | None = None, default_path: str | None = None) -> Path`: 既存ノート編集

**削除操作（2段階プロセス）**:
- `get_note_delete_confirmation(filename: str | None = None, filepath: str | None = None, default_path: str | None = None) -> dict[str, str]`: 削除確認情報の取得
- `perform_note_delete(filename: str | None = None, filepath: str | None = None, default_path: str | None = None) -> Path`: 実際の削除実行

**タグ管理**:
- `add_tag(tag: str, filename: str | None = None, filepath: str | None = None, default_path: str | None = None) -> Path`: タグ追加
- `remove_tag(tag: str, filename: str | None = None, filepath: str | None = None, default_path: str | None = None) -> Path`: タグ削除
- `rename_tag(old_tag: str, new_tag: str, directory: str | None = None) -> list[Path]`: タグ名変更
- `get_tags(filename: str | None = None, filepath: str | None = None, default_path: str | None = None) -> list[str]`: ノートのタグ一覧取得
- `list_all_tags(directory: str | None = None) -> list[str]`: vault全体のタグ一覧
- `find_notes_with_tag(tag: str, directory: str | None = None) -> list[str]`: 特定タグを持つノート検索

#### 3.1.3 設計上の利点

新しいアーキテクチャの利点：

- **コード削減**: ラッパー関数の排除により約5%のコード削減を実現
- **保守性向上**: 重複コードの削除によりメンテナンスが容易
- **直接統合**: サービス層との直接的な統合によりパフォーマンス向上
- **FastMCP活用**: モダンなデコレータベースの実装

### 3.2 file_handler.py

#### 3.2.1 FileWriteRequest

```python
class FileWriteRequest(BaseModel):
    directory: str
    filename: str
    content: str
    overwrite: bool = False
```

#### 3.2.2 FileReadRequest

```python
class FileReadRequest(BaseModel):
    directory: str
    filename: str
```

#### 3.2.3 FileDeleteRequest

```python
class FileDeleteRequest(BaseModel):
    directory: str
    filename: str
```

#### 3.2.4 SearchConfig

```python
class SearchConfig(BaseModel):
    directory: str
    keyword: str
    case_sensitive: bool = True
    file_extensions: list[str] = Field(default_factory=lambda: [".md"])
```

#### 3.2.5 SearchResult

```python
class SearchResult(BaseModel):
    file_path: str
    line_number: int
    context: str
```

### 3.2 file_handler.py

#### 3.2.1 FileOperationRequest

ファイル操作の基本リクエストモデルです。

```python
class FileOperationRequest(BaseModel):
    directory: str
    filename: str
```

**バリデーション**:
- ファイル名が空でないこと
- ファイル名が絶対パスでないこと
- ファイル名に禁止文字を含まないこと

#### 3.2.2 write_file, read_file 関数

```python
def write_file(request: FileWriteRequest) -> Path:
    """
    Write the content to a file in the specified directory.
    """

def read_file(request: FileReadRequest) -> str:
    """
    Read the content from a file in the specified directory.
    """
```

**共通処理**:
1. ファイルパスの検証
2. ディレクトリの存在確認・作成
3. ファイル操作（読み取り/書き込み）の実行
4. 結果の返却

### 3.3 サーバーモジュール (server.py)

Model Context Protocol (MCP) サーバーインターフェースを提供します。以下のツールがサーバーに登録されています：

#### 3.3.1 サーバー設定

```python
# Create an MCP server
mcp = FastMCP("minerva", __version__)

# Register tools
mcp.add_tool(read_note)
mcp.add_tool(search_notes)
mcp.add_tool(create_note)
mcp.add_tool(edit_note)
mcp.add_tool(get_note_delete_confirmation)
mcp.add_tool(perform_note_delete)
```

#### 3.3.2 提供されるAPI

- `read_note`: ノートの読み取り
- `create_note`: 新規ノートの作成
- `edit_note`: 既存ノートの編集
- `search_notes`: ノートの検索
- `get_note_delete_confirmation`: ノート削除の確認 (1段階目)
- `perform_note_delete`: ノート削除の実行 (2段階目)

セキュリティ上の配慮として、ノート削除機能は2段階のプロセスに分割されており、ユーザーは最初に削除対象のファイルを確認した後、明示的に削除を実行する必要があります。これにより、誤った削除操作のリスクを低減しています。

### 3.4 メタデータ処理の改善

#### 3.4.1 日付型処理の一貫性

frontmatterのメタデータ内の日付型は、一貫して処理されるように改善されました：

```python
def _read_existing_frontmatter(file_path: Path) -> dict | None:
    # ...existing code...
    if content.startswith("---\n"):  # If frontmatter exists
        post = frontmatter.loads(content)
        metadata = dict(post.metadata)
        # 日付型の値が文字列として一貫して処理されるようにする
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.isoformat()
        return metadata
    # ...existing code...
```

この改善により、以下のメリットが得られます：

1. メタデータの一貫性: すべての日付値がISO形式の文字列として扱われます
2. シリアライズの簡素化: JSONなどへの変換時に日付型の特別な処理が不要になります
3. 比較操作の信頼性向上: 日付型と文字列型の混在による比較問題を回避できます

## 4. ファイル検索実装

### 4.1 SearchConfig クラス

```python
class SearchConfig(BaseModel):
    directory: str
    keyword: str
    case_sensitive: bool = True
    file_extensions: Optional[list[str]] = None
```

### 4.2 search_keyword_in_files 関数

```python
def search_keyword_in_files(config: SearchConfig) -> list[SearchResult]:
    """
    Search for a keyword in files within a directory.
    """
```

**アルゴリズム**:
1. 大文字小文字を区別しない場合は正規表現パターンを作成
2. 指定ディレクトリを再帰的に探索
3. ファイル拡張子のフィルタリング
4. バイナリファイルの除外
5. 行ごとにキーワードの検索
6. 最初のマッチで検索を停止し、結果を保存
7. すべての結果をリストとして返却

## 5. テスト戦略

### 5.1 単体テスト

テストはPytestフレームワークを使用して実装されています：

- モックオブジェクトを使用した依存関係の分離
- パラメータ化されたテストによる多数のケースのカバレッジ
- フィクスチャを使用したテスト環境のセットアップ

### 5.2 統合テスト

統合テストは実際のファイルシステム操作を伴います：

- 一時ディレクトリを使用したファイル操作のテスト
- 読み取り/書き込み/検索操作の組み合わせ
- エッジケース（空ファイル、サブディレクトリなど）の処理

### 5.3 コードカバレッジ

コードカバレッジについての詳細は、[4. コードカバレッジ](test_guidelines.md#4コードカバレッジ)を参照してください。

## 6. フロントマター管理アーキテクチャ

### 6.1 FrontmatterManagerクラス

フロントマター処理を専用のクラスに分離し、コードの再利用性と保守性を向上させています。

#### 6.1.1 クラス設計

```python
class FrontmatterManager:
    """
    YAML frontmatter metadata management for Obsidian notes.

    This class centralizes all frontmatter-related operations including
    generation, reading, updating, and tag management.
    """

    def __init__(self, default_author: str | None = None):
        """
        Initialize with optional default author.

        Args:
            default_author: Default author for new notes
        """
        self.default_author = default_author or DEFAULT_NOTE_AUTHOR

    def generate_metadata(
        self,
        text: str,
        author: str | None = None,
        is_new_note: bool = True,
        existing_frontmatter: dict | None = None,
        tags: list[str] | None = None,
    ) -> frontmatter.Post:
        """Generate or update YAML frontmatter metadata for a note."""

    def read_existing_metadata(self, file_path: Path) -> dict | None:
        """Read and extract frontmatter metadata from an existing file."""

    def update_tags(self, file_path: Path, tags: list[str]) -> None:
        """Update tags in an existing note's frontmatter."""

    def add_tag(self, file_path: Path, tag: str) -> None:
        """Add a single tag to an existing note's frontmatter."""

    def remove_tag(self, file_path: Path, tag: str) -> None:
        """Remove a single tag from an existing note's frontmatter."""
```

#### 6.1.2 主な機能

- **メタデータ生成**: 新規ノートおよび既存ノートのフロントマター生成
- **メタデータ読み取り**: 既存ファイルからのフロントマター抽出
- **タグ管理**: タグの追加、削除、更新操作
- **日時管理**: ISO 8601形式での作成日時・更新日時の自動管理
- **互換性維持**: 既存のプライベート関数とのAPIの互換性

#### 6.1.3 責務の分離

- **FrontmatterManager**: フロントマター処理に特化
- **service.py**: ビジネスロジックとコアサービス
- **server.py**: MCPツール実装と@mcp.tool()デコレータ
- **file_handler.py**: 低レベルファイル操作

#### 6.1.4 移行戦略

1. **段階的移行**: 既存の関数を一時的にラッパーとして保持
2. **互換性保証**: 既存のAPIに影響を与えない
3. **テスト継続**: 既存のテストケースが継続して動作
4. **漸進的リプレース**: 新しい機能から順次新クラスを使用

### 6.2 将来の拡張

#### 6.2.1 潜在的な機能拡張

- **リンクの解析**: Obsidianのウィキリンク構文の解析と処理
- **テンプレート**: 事前定義されたテンプレートに基づくノートの作成
- **カスタムフィールド**: ユーザー定義のメタデータフィールドのサポート

#### 6.2.2 技術的改善

- **非同期API**: ファイル操作の非同期実装
- **キャッシング**: 頻繁にアクセスされるファイルのキャッシング
- **インデックス作成**: 高速検索のためのインデックス機能
- **バリデーション強化**: より厳密なメタデータバリデーション

## 7. CI/CD技術仕様

### 7.1 GitHub Actions ワークフロー構成

#### 7.1.1 メインCIワークフロー (`.github/workflows/ci.yml`)

**トリガー条件**:
- プルリクエスト（`pull_request` イベント）
- main ブランチへの push

**実行環境**:
- `ubuntu-latest`
- Python マトリックス: `["3.12", "3.13"]`

**ジョブ構成**:

```yaml
jobs:
  lint:
    name: コード品質チェック
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv run ruff check --select ALL --ignore E501,D100,D101,D102,D103,D104,D105
      - run: uv run ruff format --check

  type-check:
    name: 型チェック
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv run mypy src tests

  test:
    name: テスト実行
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv run pytest --cov=minerva --cov-report=xml --cov-report=html
      - uses: codecov/codecov-action@v4 (if: matrix.python-version == '3.12')
```

#### 7.1.2 プルリクエスト専用ワークフロー (`.github/workflows/pr-checks.yml`)

**トリガー条件**:
- プルリクエスト（`pull_request` イベント）

**実行内容**:
- コミットメッセージ形式チェック（Conventional Commits準拠）
- ドキュメント更新確認
- 軽量なクイックチェック

#### 7.1.3 リリースワークフローとの統合

**既存の `.github/workflows/release.yml` との関係**:
- CI成功後にのみリリースが実行される
- `needs: [lint, type-check, test]` 依存関係を設定
- semantic-release による自動バージョニング

### 7.2 使用するGitHub Actions

#### 7.2.1 標準アクション

- `actions/checkout@v4`: リポジトリのチェックアウト
- `actions/upload-artifact@v4`: アーティファクトのアップロード（HTMLカバレッジレポート等）

#### 7.2.2 Python/uv関連

- `astral-sh/setup-uv@v3`: uv環境のセットアップ
  - Python バージョン指定機能
  - 依存関係キャッシュ機能

#### 7.2.3 コードカバレッジ

- `codecov/codecov-action@v4`: Codecovへのカバレッジレポートアップロード
  - トークン設定: `CODECOV_TOKEN` (Secrets)
  - XML形式レポートの自動アップロード

### 7.3 環境変数とSecrets

#### 7.3.1 必要なSecrets

- `CODECOV_TOKEN`: Codecov統合用トークン
- `GITHUB_TOKEN`: 自動生成されるトークン（リリース用）

#### 7.3.2 環境変数

- `PYTHONPATH=src`: テスト実行時のパス設定
- uvの設定はプロジェクト内の `pyproject.toml` を参照

### 7.4 品質ゲート

#### 7.4.1 必須チェック項目

- **Ruff リンティング**: `ruff check` でのコード品質確認
- **フォーマットチェック**: `ruff format --check` での形式確認
- **型チェック**: `mypy` による静的型チェック
- **テスト実行**: 全テストの成功
- **カバレッジ**: 最低カバレッジの維持（現在89%）

#### 7.4.2 パフォーマンス要件

- **実行時間**: 5分以内での完了を目標
- **並列実行**: 可能な限りジョブを並列実行
- **キャッシュ活用**: uvのキャッシュ機能を活用した依存関係高速化

### 7.5 段階的実装計画

#### 7.5.1 Phase 1: 基本ワークフロー

1. メインCIワークフロー（`.github/workflows/ci.yml`）の実装
2. コード品質チェック（Ruff、MyPy）
3. 基本テスト実行とカバレッジ測定

#### 7.5.2 Phase 2: マトリックス対応と最適化

1. Python マトリックステスト（3.12、3.13）
2. Codecov統合
3. パフォーマンス最適化

#### 7.5.3 Phase 3: 高度な機能

1. プルリクエスト専用チェック
2. セキュリティチェック（依存関係の脆弱性スキャン）
3. 既存リリースワークフローとの完全統合
