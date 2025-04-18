# Minerva ノート操作機能仕様書

この仕様書はMinervaプロジェクトにおけるObsidianノートの操作機能について説明します。

## 1. 概要

Minervaは、Obsidian vaultに対してノートの作成、読み取り、検索といった基本的な操作を提供します。これらの機能は、Python APIとして提供され、アプリケーションから呼び出すことができます。

## 2. 主要機能

### 2.1 ノートの作成・更新 (write_note)

#### 機能概要
指定されたテキストをObsidian vault内のファイルに書き込みます。ファイルが存在しない場合は新規作成し、存在する場合は上書きオプションに基づいて処理します。コンテンツにはfrontmatter（メタデータ）が自動的に追加されます。

#### パラメータ
- `text`: ファイルに書き込むコンテンツ
- `filename`: 書き込むファイル名（`.md`拡張子は自動的に追加されます）
- `is_overwrite`: ファイルが既に存在する場合に上書きするかどうかのフラグ（デフォルト: False）
- `author`: frontmatterに追加する著者名（デフォルト: None、指定されない場合はシステム設定の著者名が使用されます）
- `default_path`: サブディレクトリが指定されていない場合に使用するデフォルトディレクトリ（デフォルト: 環境設定のDEFAULT_NOTE_DIR値）

#### 戻り値
- 書き込まれたファイルのパス（Path型）

#### 例外
- `ValueError`: ファイル名が空または無効な場合
- `FileExistsError`: ファイルが既に存在し、`is_overwrite`がFalseの場合
- `pydantic.ValidationError`: ファイル名に禁止文字（`<>:"/\|?*`）が含まれる場合

#### 特記事項
- サブディレクトリを含むパスを指定した場合、自動的にディレクトリが作成されます
- 複数レベルのディレクトリ（例：`level1/level2/note.md`）もサポートされています
- すべてのノートには自動的にfrontmatterが追加され、少なくとも著者情報が含まれます
- 入力コンテンツに既にfrontmatterが含まれている場合は、そのメタデータは保持され、著者情報のみが追加または更新されます
- サブディレクトリが指定されていない場合、`default_path`パラメータで指定されたディレクトリに保存されます

#### 使用例
```python
from minerva.tools import write_note

# 基本的な使用例
file_path = write_note(
    text="This is a test note",
    filename="example_note",  # .md拡張子は自動的に追加されます
    is_overwrite=False
)
print(f"ノートが保存されました: {file_path}")

# 著者情報とデフォルトパスを指定する例
file_path = write_note(
    text="This is a note with author information",
    filename="authored_note",
    is_overwrite=False,
    author="AI Assistant",
    default_path="ai_generated"
)
print(f"著者情報付きノートが保存されました: {file_path}")

# 既存のfrontmatterを持つコンテンツの例
frontmatter_content = """---
title: Existing Title
tags: [test, frontmatter]
---
Content with existing frontmatter"""

file_path = write_note(
    text=frontmatter_content,
    filename="frontmatter_note",
    is_overwrite=False,
    author="AI Assistant"
)
print(f"frontmatter付きノートが保存されました: {file_path}")
```

### 2.2 ノートの読み取り (read_note)

#### 機能概要
Obsidian vault内の指定されたファイルからコンテンツを読み取ります。

#### パラメータ
- `filepath`: 読み取るファイルの絶対パス

#### 戻り値
- ファイルの内容（文字列）

#### 例外
- `FileNotFoundError`: ファイルが存在しない場合
- `Exception`: ファイル読み取りに失敗した場合

#### 使用例
```python
from minerva.tools import read_note

# ファイルパスを直接指定する
content = read_note("/path/to/vault/example_note.md")
print(f"ノートの内容: {content}")
```

### 2.3 ノートの検索 (search_notes)

#### 機能概要
Obsidian vault内のすべてのマークダウンファイル（`.md`）から指定されたキーワードを検索します。

#### パラメータ
- `query`: 検索するキーワード
- `case_sensitive`: 大文字と小文字を区別するかどうかのフラグ（デフォルト: True）

#### 戻り値
- 検索結果のリスト。各結果には以下の情報が含まれます：
  - `file_path`: マッチしたファイルのパス
  - `line_number`: キーワードが見つかった行番号
  - `context`: キーワードを含む行のコンテキスト

#### 例外
- `ValueError`: 検索クエリが空の場合
- `Exception`: 検索処理中にエラーが発生した場合

#### 特記事項
- 検索は各ファイルの最初のマッチのみを返します
- バイナリファイルは検索対象から自動的に除外されます

#### 使用例
```python
from minerva.tools import search_notes

# 基本的な使用例（大文字小文字を区別）
results = search_notes(query="important", case_sensitive=True)

# 大文字小文字を区別しない検索
results = search_notes(query="important", case_sensitive=False)

# 結果の処理
for result in results:
    print(f"ファイル: {result.file_path}")
    print(f"行番号: {result.line_number}")
    print(f"コンテキスト: {result.context}")
    print("---")
```

## 3. ファイルパス処理

### 3.1 サブディレクトリのサポート

ノート作成機能は以下のようなサブディレクトリの作成と利用をサポートしています：

- サブディレクトリを含むファイル名を指定できます（例：`projects/minerva/notes.md`）
- 指定されたサブディレクトリが存在しない場合、自動的に作成されます
- 複数レベルのネストされたディレクトリもサポートされています（例：`level1/level2/level3/note.md`）

### 3.2 ファイル名のバリデーション

ファイル名に関する制約：

- 空のファイル名は許可されません
- ファイル名に禁止文字（`<>:"/\|?*`）を含めることはできません
- 絶対パスをファイル名として使用することはできません

## 4. エラー処理

### 4.1 ファイル操作のエラー

- ファイルが存在し、上書きフラグがFalseの場合：`FileExistsError`が発生します
- ファイルが存在せず、読み取りが要求された場合：`FileNotFoundError`が発生します
- ファイル名が無効な場合：`ValueError`または`pydantic.ValidationError`が発生します

### 4.2 検索操作のエラー

- 検索クエリが空の場合：`ValueError`が発生します
- ディレクトリが存在しない場合：`ValueError`が発生します

## 5. 制限事項

- 検索機能は、各ファイルの最初のマッチのみを返します
- すべてのファイル操作はUTF-8エンコーディングを使用します
- バイナリファイルは検索対象から除外されます
