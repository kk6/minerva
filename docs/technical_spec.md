# Minerva 技術仕様書

この技術仕様書はMinervaプロジェクトの内部実装の詳細と設計思想について説明します。

## 1. アーキテクチャ概要

Minervaは依存性注入パターンを採用した階層化アーキテクチャです：

1. **サービス層** (`services/`) - **モジュール化済み**
   - **ServiceManager**: 全サービス操作の統一インターフェース（ファサードパターン）
   - **専門化されたサービスモジュール**: 機能別に分離されたサービスクラス群
     - **NoteOperations**: ノート作成・編集・削除・読み込み・マージ操作
     - **TagOperations**: タグ追加・削除・一括変更・検索機能
     - **AliasOperations**: エイリアス管理と競合検出
     - **SearchOperations**: 全文検索とフィルタリング機能
     - **FrontmatterOperations**: 汎用フロントマターフィールド操作
   - **MinervaConfig**: 依存性注入用の設定データクラス
   - **create_minerva_service()**: デフォルト設定でのServiceManagerファクトリー関数

1.1. **セマンティック検索層** (`vector/`) - **完全実装済み（v0.15.0）**
- **EmbeddingProvider**: テキスト埋め込み抽象基底クラス（実装済み）
- **SentenceTransformerProvider**: sentence-transformers実装（all-MiniLM-L6-v2モデル、384次元埋め込み、実装済み）
- **VectorIndexer**: DuckDB VSS拡張を使用したベクトルインデックス管理（HNSWインデックス対応、実装済み）
- **VectorSearcher**: コサイン類似度ベクター検索とフィルタリング（実装済み）
- **SearchOperations統合**: セマンティック検索の完全統合（実装済み）
- **オプショナル依存関係管理**: 適切なエラーメッセージとlazy loading実装

1.2. **ノートマージ層** (`services/merge_processors.py`) - **新規実装済み（v0.16.0）**
- **MergeProcessor**: ノートマージの抽象基底クラス（戦略パターン実装）
- **AppendMergeProcessor**: 順次追記戦略（ファイル順での単純結合）
- **ByHeadingMergeProcessor**: 見出しベース統合戦略（見出し別グループ化）
- **ByDateMergeProcessor**: 日付順ソート戦略（フロントマター日付基準）
- **SmartMergeProcessor**: 自動戦略選択（コンテンツ分析による最適化）
- **フロントマター統合**: タグ・エイリアス・メタデータの自動マージ
- **マージ履歴追跡**: 戦略別の詳細な操作履歴記録

2. **MCPサーバー層** (`server.py`) - **MCP 1.9対応済み**
   - **FastMCPサーバー**: MCP 1.9.3準拠、`@mcp.tool()` デコレータを使用した直接的なツール登録
   - **ダイレクトサービス統合**: ラッパー関数を排除し、サービスメソッドを直接呼び出し
   - **ツール機能** (`@mcp.tool`):
     - `read_note()`, `search_notes()` 関数（読み取り操作）
     - `create_note()`, `edit_note()` 関数（状態変更操作）
     - `get_note_delete_confirmation()`, `perform_note_delete()` 関数（2段階削除プロセス）
     - `merge_notes()`, `smart_merge_notes()` 関数（ノート統合機能）
     - `add_tag()`, `remove_tag()`, `rename_tag()`, `get_tags()`, `list_all_tags()`, `find_notes_with_tag()` 関数（タグ管理）
     - `add_alias()`, `remove_alias()`, `get_aliases()`, `search_by_alias()` 関数（エイリアス管理）
     - `get_frontmatter_field()`, `set_frontmatter_field()`, `remove_frontmatter_field()`, `get_all_frontmatter_fields()` 関数（フロントマター管理）
     - `semantic_search()`, `build_vector_index()`, `get_vector_index_status()` 関数（セマンティック検索）
     - `build_vector_index_batch()`, `reset_vector_database()`, `debug_vector_schema()` 関数（ベクター検索デバッグ・管理）
     - **📖 詳細**: [vector_search_api.md](vector_search_api.md)で全9個のベクター検索ツールの完全ドキュメント

3. **設定管理層** (`config.py`) - **セマンティック検索対応済み**
   - **MinervaConfig**: 新しい設定データクラス
   - **セマンティック検索設定**: 実装済みオプション機能設定
     - `vector_search_enabled`: 機能の有効/無効切り替え（デフォルト: false）
     - `vector_db_path`: ベクターデータベースファイルパス（省略時: {vault}/.minerva/vectors.db）
     - `embedding_model`: 使用する埋め込みモデル名（デフォルト: all-MiniLM-L6-v2、384次元）
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
- `services/`ディレクトリのモジュール群がObsidianノート固有のビジネスロジックを提供します
  - `ServiceManager`: 全サービスの統一インターフェース
  - `NoteOperations`, `TagOperations`, `AliasOperations`, `SearchOperations`: 専門化されたサービスクラス
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

**基本ノート操作**:
- `read_note(filepath: str) -> str`: ノートの読み取り
- `search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]`: ノート内容検索
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

#### 3.2.6 MergeStrategy

ノートマージ戦略の列挙型です。

```python
class MergeStrategy(Enum):
    APPEND = "append"           # 順次追記
    BY_HEADING = "by_heading"   # 見出しベース統合
    BY_DATE = "by_date"         # 日付順ソート
    SMART = "smart"             # 自動戦略選択
```

#### 3.2.7 MergeResult

ノートマージ操作の結果データクラスです。

```python
@dataclass
class MergeResult:
    target_file: Path               # 作成されたマージファイルのパス
    source_files: list[str]         # マージ元ファイルのリスト
    merge_strategy: str             # 使用されたマージ戦略
    files_processed: int            # 処理されたファイル数
    merge_history: dict[str, Any]   # マージ履歴の詳細情報
    warnings: list[str]             # 警告メッセージ
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

### 3.5 サービス層詳細実装 (services/)

#### 3.5.1 ServiceManager - 統一ファサードパターン

ServiceManagerはすべてのサービス操作への統一アクセスポイントを提供します：

```python
class ServiceManager:
    """Facade for all Minerva service operations with dependency injection."""

    def __init__(self, config: MinervaConfig, frontmatter_manager: FrontmatterManager):
        self.config = config
        self.frontmatter_manager = frontmatter_manager

        # 専門化されたサービスの初期化
        self.note_operations = NoteOperations(config, frontmatter_manager)
        self.tag_operations = TagOperations(config, frontmatter_manager)
        self.alias_operations = AliasOperations(config, frontmatter_manager)
        self.search_operations = SearchOperations(config)
```

**主要メソッド**（27の公開メソッド）:
- ノート操作の委譲: `create_note()`, `edit_note()`, `read_note()`, `delete_note()`
- タグ管理の委譲: `add_tag()`, `remove_tag()`, `rename_tag()`, `get_tags()`
- エイリアス管理の委譲: `add_alias()`, `remove_alias()`, `get_aliases()`
- 検索機能の委譲: `search_notes()`, `semantic_search()`, `find_duplicate_notes()`
- マージ機能の委譲: `merge_notes()`, `smart_merge_notes()`

#### 3.5.2 NoteOperations - 自動インデックス統合

NoteOperationsはノートのCRUD操作に加えて、自動ベクターインデックス更新を統合しています：

```python
class NoteOperations(BaseService):
    """Note CRUD operations with automatic vector indexing integration."""

    def create_note(self, text: str, filename: str, author: str | None = None,
                   default_path: str | None = None) -> Path:
        """Create note with automatic vector indexing."""
        # 1. ノート作成
        file_path = self._create_note_file(text, filename, author, default_path)

        # 2. 自動インデックス更新
        self._update_vector_index_if_enabled(file_path)

        return file_path

    def edit_note(self, text: str, filename: str, author: str | None = None,
                 default_path: str | None = None) -> Path:
        """Edit note with automatic vector index update."""
        # 1. ノート更新
        file_path = self._update_note_file(text, filename, author, default_path)

        # 2. 自動インデックス更新
        self._update_vector_index_if_enabled(file_path)

        return file_path
```

**自動インデックス統合メソッド**:

- `_update_vector_index_if_enabled(file_path: Path)`: インデックス有効時の更新制御
- `_update_vector_index_immediate(file_path: Path)`: 即座にインデックス更新
- `_update_vector_index_batched(file_path: Path)`: バッチキューへの追加
- `_remove_from_vector_index_if_enabled(file_path: Path)`: ファイル削除時のインデックス除去
- `_should_auto_update_index() -> bool`: 自動更新条件の判定

**自動インデックス戦略**:

1. **immediate**: ファイル操作時に即座にベクターインデックスを更新
   - 利点: 常に最新のインデックス状態
   - 欠点: ファイル操作の遅延
   - 適用: 小規模vault、リアルタイム性重視

2. **batch**: ファイル変更をバッチキューに追加し、後で一括処理
   - 利点: 効率的な処理、システム負荷の分散
   - 欠点: インデックス更新の遅延
   - 適用: 中規模vault、効率重視

3. **background**: バックグラウンドでの継続的インデックス処理
   - 利点: ユーザー操作をブロックしない
   - 欠点: 実装の複雑性、デバッグの困難
   - 適用: 大規模vault、パフォーマンス重視

#### 3.5.3 SearchOperations - セマンティック検索統合

SearchOperationsは従来の全文検索に加えて、ベクター検索による意味的検索を提供します：

```python
class SearchOperations(BaseService):
    """Full-text and semantic search operations."""

    # 従来の全文検索
    def search_notes(self, query: str, case_sensitive: bool = True) -> list[SearchResult]:
        """Traditional keyword-based search in note contents."""

    # セマンティック検索機能
    def semantic_search(self, query: str, limit: int = 10,
                       threshold: float | None = None,
                       directory: str | None = None) -> list[SemanticSearchResult]:
        """Natural language semantic search using vector embeddings."""

    def find_duplicate_notes(self, similarity_threshold: float = 0.85,
                           directory: str | None = None,
                           min_content_length: int = 100,
                           exclude_frontmatter: bool = True) -> DuplicateDetectionResult:
        """Find potentially duplicate notes using semantic similarity."""
```

**セマンティック検索アーキテクチャ**:

1. **VectorIndexer統合**: DuckDB VSS拡張を使用したベクター保存
2. **EmbeddingProvider**: sentence-transformers（all-MiniLM-L6-v2、384次元）
3. **類似度計算**: コサイン類似度によるランキング
4. **結果フィルタリング**: 閾値、ディレクトリ、コンテンツ長による制限

**重複検出アルゴリズム**:

```python
def _find_duplicate_groups(self, similarity_matrix: np.ndarray,
                          file_paths: list[Path],
                          threshold: float) -> list[DuplicateGroup]:
    """Group files by semantic similarity using clustering algorithm."""
    # 1. 類似度行列から類似ペアを抽出
    # 2. 連結成分アルゴリズムでグループ化
    # 3. グループ内統計情報の計算
    # 4. 統合推奨事項の生成
```

**サポートメソッド**:
- `_create_semantic_search_result()`: 検索結果の構造化
- `_find_duplicate_groups()`: 類似ノートのグループ化アルゴリズム
- `_create_duplicate_file()`: 重複ファイル情報の作成

#### 3.5.4 FrontmatterOperations - 汎用フロントマター管理

FrontmatterOperationsは、ノートのフロントマター（YAMLメタデータ）に対する汎用的な操作を提供します：

```python
class FrontmatterOperations(BaseService):
    """Generic frontmatter field operations for notes."""

    def get_field(self, field_name: str, filename: str | None = None,
                  filepath: str | None = None, default_path: str | None = None) -> Any:
        """Get specific frontmatter field value from a note."""

    def set_field(self, field_name: str, value: Any, filename: str | None = None,
                  filepath: str | None = None, default_path: str | None = None) -> Path:
        """Set specific frontmatter field value in a note."""

    def remove_field(self, field_name: str, filename: str | None = None,
                     filepath: str | None = None, default_path: str | None = None) -> Path:
        """Remove specific frontmatter field from a note."""

    def get_all_fields(self, filename: str | None = None,
                       filepath: str | None = None, default_path: str | None = None) -> dict[str, Any]:
        """Get all frontmatter fields from a note."""
```

**主要機能**:

1. **任意フィールドアクセス**: 標準フィールド（tags, aliases）以外のカスタムフィールドにもアクセス
2. **型安全性**: Any型での値の保存・取得により、文字列、数値、リスト、辞書などに対応
3. **自動フロントマター管理**: フィールド追加時のフロントマター自動生成
4. **統一インターフェース**: `filename`/`filepath`パラメータによる柔軟なファイル指定

**使用例**:

```python
# カスタムフィールドの設定
frontmatter_ops.set_field("priority", "high", filename="task.md")
frontmatter_ops.set_field("due_date", "2024-12-31", filename="task.md")
frontmatter_ops.set_field("categories", ["work", "urgent"], filename="task.md")

# フィールド値の取得
priority = frontmatter_ops.get_field("priority", filename="task.md")
all_fields = frontmatter_ops.get_all_fields(filename="task.md")

# フィールドの削除
frontmatter_ops.remove_field("draft", filename="published.md")
```

**統合パターン**:

- **FrontmatterManager連携**: 低レベルYAML処理の委譲
- **TagOperations統合**: `tags`フィールドを特殊化したタグ専用操作
- **AliasOperations統合**: `aliases`フィールドを特殊化したエイリアス専用操作
- **NoteOperations連携**: ノート作成・編集時の自動フロントマター生成

**Obsidian Properties互換性**:

- Obsidian Properties UIで設定したフィールドの読み取り・編集に対応
- カスタムプロパティタイプ（日付、数値、選択肢）のサポート
- プロパティスキーマとの自動統合

#### 3.5.5 ベクター検索統合アーキテクチャ

**コンポーネント間の相互作用**:

```
NoteOperations ─── 自動インデックス更新 ──→ VectorIndexer
                                          ↓
SearchOperations ─── セマンティック検索 ──→ VectorSearcher
                                          ↓
MCP Tools ────────── 統一インターフェース ──→ ServiceManager
```

**設定統合**:

- `AUTO_INDEX_ENABLED`: NoteOperationsでの自動インデックス制御
- `AUTO_INDEX_STRATEGY`: インデックス更新戦略の選択
- `VECTOR_SEARCH_ENABLED`: SearchOperationsでのベクター検索有効化
- `EMBEDDING_MODEL`: 埋め込みモデルの指定

**エラーハンドリング**:

- 依存関係不足: 明確なインストール指示
- インデックス不整合: 自動修復機能
- 戦略設定エラー: フォールバック処理

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
- **ServiceManager**: 全サービス操作の統一ファサード
- **専門化サービス群**: NoteOperations, TagOperations, AliasOperations, SearchOperations
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
