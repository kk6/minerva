# Minerva 技術仕様書

この技術仕様書はMinervaプロジェクトの内部実装の詳細と設計思想について説明します。

## 1. アーキテクチャ概要

Minervaは階層化されたアーキテクチャを採用しています：

1. **ユーザー向けAPI層** (`tools.py`)
   - **基本操作**:
     - `CreateNoteRequest`, `EditNoteRequest`, `ReadNoteRequest`, `SearchNoteRequest` クラス
     - `create_note()`, `edit_note()`, `read_note()`, `search_notes()` 関数
     - `get_note_delete_confirmation()`, `perform_note_delete()` 関数（2段階削除プロセス）
   - **タグ管理**:
     - `AddTagRequest`, `RemoveTagRequest`, `RenameTagRequest` クラス
     - `add_tag()`, `remove_tag()`, `rename_tag()`, `get_tags()`, `list_all_tags()`, `find_notes_with_tag()` 関数
   - **レガシー**:
     - `WriteNoteRequest` クラス
     - `write_note()` 関数（後方互換性のため提供）

2. **ファイル操作層** (`file_handler.py`)
   - `FileWriteRequest`, `FileReadRequest`, `FileDeleteRequest`, `SearchConfig` クラス
   - `write_file()`, `read_file()`, `delete_file()`, `search_keyword_in_files()` 関数

## 2. 基本設計原則

### 2.1 入力検証

システムはPydanticを使用して入力検証を行います：

- すべてのリクエストはPydanticの`BaseModel`を継承したモデルクラスとして定義されています
- フィールドバリデーションは`field_validator`デコレータを使用して実装されています
- 無効な入力は早期に検出され、明確なエラーメッセージが提供されます

### 2.2 責務の分離

- `tools.py`モジュールはObsidianノート固有の機能を提供します
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

### 3.1 tools.py

#### 3.1.1 基本ノート操作

以下のリクエストモデルと対応する関数が実装されています：

- `CreateNoteRequest`: 新規ノート作成リクエスト
- `EditNoteRequest`: 既存ノート編集リクエスト
- `ReadNoteRequest`: ノート読取リクエスト
- `SearchNoteRequest`: ノート検索リクエスト
- `DeleteConfirmationRequest`: ノート削除確認リクエスト
- `DeleteNoteRequest`: ノート削除実行リクエスト
- `WriteNoteRequest`: レガシーノート作成・更新リクエスト（後方互換性用）

#### 3.1.2 タグ管理機能

タグ操作のための以下のリクエストモデルと関数が実装されています：

- `AddTagRequest`: タグ追加リクエスト
  - `tag`: 追加するタグ文字列
  - `filename` または `filepath`: 対象ノート
  - `default_path`: デフォルトディレクトリパス

- `RemoveTagRequest`: タグ削除リクエスト
  - `tag`: 削除するタグ文字列
  - `filename` または `filepath`: 対象ノート
  - `default_path`: デフォルトディレクトリパス

- `RenameTagRequest`: タグ名変更リクエスト
  - `old_tag`: 変更元のタグ名
  - `new_tag`: 変更後のタグ名
  - `directory`: 対象ディレクトリ（省略時はvault全体）

- `GetTagsRequest`: タグ取得リクエスト
  - `filename` または `filepath`: 対象ノート
  - `default_path`: デフォルトディレクトリパス

- `ListAllTagsRequest`: 全タグリスト取得リクエスト
  - `directory`: 対象ディレクトリ（省略時はvault全体）

- `FindNotesWithTagRequest`: タグによるノート検索リクエスト
  - `tag`: 検索対象のタグ
  - `directory`: 対象ディレクトリ（省略時はvault全体）

#### 3.1.3 共通ユーティリティ関数

タグ管理のための内部処理関数：

- `_normalize_tag()`: タグの正規化（小文字化、空白削除）
- `_validate_tag()`: タグの形式検証（禁止文字チェック）
- `_generate_note_metadata()`: フロントマターの生成と更新

#### 3.1.4 フロントマター処理

ノートのメタデータ管理は、python-frontmatterパッケージを使用して実装されています。すべてのノートには以下の情報が自動的に追加されます：

```python
def _generate_note_metadata(
    text: str,
    author: str | None = None,
    is_new_note: bool = True,
    existing_frontmatter: dict | None = None,
    tags: list[str] | None = None,
) -> frontmatter.Post:
    """
    Generate metadata for a new or existing note.

    Args:
        text: The text content of the note
        author: Optional author name to include in the metadata
        is_new_note: Whether this is a new note or updating an existing one
        existing_frontmatter: Any existing frontmatter to preserve
        tags: Optional list of tags to include/update in the metadata

    Returns:
        A frontmatter.Post object with the note content and metadata
    """
```

このメタデータには以下の情報が含まれます：

- `created`: ノート作成日時（ISO 8601形式）- 新規作成時のみ追加
- `updated`: 最終更新日時（ISO 8601形式）- 常に現在時刻に更新
- `author`: 作成者名（指定された場合）
- `tags`: タグのリスト（タグ管理機能で追加された場合）

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
- **tools.py**: 高レベルAPIとビジネスロジック
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
