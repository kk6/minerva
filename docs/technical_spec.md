# Minerva 技術仕様書

この技術仕様書はMinervaプロジェクトの内部実装の詳細と設計思想について説明します。

## 1. アーキテクチャ概要

Minervaは階層化されたアーキテクチャを採用しています：

1. **ユーザー向けAPI層** (`tools.py`)
   - `WriteNoteRequest`, `ReadNoteRequest`, `SearchNoteRequest` クラス
   - `write_note()`, `read_note()`, `search_notes()` 関数

2. **ファイル操作層** (`file_handler.py`)
   - `FileWriteRequest`, `FileReadRequest`, `SearchConfig` クラス
   - `write_file()`, `read_file()`, `search_keyword_in_files()` 関数

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
- ユーザーに意味のあるエラーメッセージが提供されます

## 3. モジュール詳細

### 3.1 tools.py

#### 3.1.1 WriteNoteRequest

Obsidianノートの作成・更新リクエストを表すモデルクラスです。

```python
class WriteNoteRequest(BaseModel):
    text: str
    filename: str
    is_overwrite: bool = False
```

**バリデーション**:
- `filename`フィールドは`.md`拡張子を持たない場合、自動的に追加されます

#### 3.1.2 write_note 関数

```python
def write_note(request: WriteNoteRequest) -> Path:
    """
    Write a note to a file in the Obsidian vault.
    """
```

**処理フロー**:
1. ファイル名の検証
2. サブディレクトリのパスとベースファイル名の分離
3. 必要なディレクトリの作成
4. 下位層の`write_file`関数の呼び出し
5. ファイルパスの返却

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

## 6. 将来の拡張

### 6.1 潜在的な機能拡張

- **タグのサポート**: Obsidianのタグシステムとの統合
- **リンクの解析**: Obsidianのウィキリンク構文の解析と処理
- **テンプレート**: 事前定義されたテンプレートに基づくノートの作成

### 6.2 技術的改善

- **非同期API**: ファイル操作の非同期実装
- **キャッシング**: 頻繁にアクセスされるファイルのキャッシング
- **インデックス作成**: 高速検索のためのインデックス機能
