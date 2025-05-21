# Minerva ノート操作機能仕様書

この仕様書はMinervaプロジェクトにおけるObsidianノートの操作機能について説明します。

## 1. 概要

Minervaは、Obsidian vaultに対してノートの作成、編集、読み取り、検索といった基本的な操作を提供します。これらの機能は、Python APIとして提供され、アプリケーションから呼び出すことができます。

## 2. 主要機能

### 2.1 ノートの作成 (create_note)

#### 機能概要
指定されたテキストを新しいObsidian vault内のファイルに書き込みます。ファイルが既に存在する場合はエラーが発生します。コンテンツにはfrontmatter（メタデータ）が自動的に追加されます。

#### パラメータ
- `text`: ファイルに書き込むコンテンツ
- `filename`: 書き込むファイル名（`.md`拡張子は自動的に追加されます）
- `author`: frontmatterに追加する著者名（デフォルト: None、指定されない場合はシステム設定の著者名が使用されます）
- `default_path`: サブディレクトリが指定されていない場合に使用するデフォルトディレクトリ（デフォルト: 環境設定のDEFAULT_NOTE_DIR値）

#### 戻り値
- 書き込まれたファイルのパス（Path型）

#### 例外
- `ValueError`: ファイル名が空または無効な場合
- `FileExistsError`: ファイルが既に存在する場合
- `pydantic.ValidationError`: ファイル名に禁止文字（`<>:"/\|?*`）が含まれる場合

#### 使用例
```python
from minerva.tools import create_note

# 基本的な使用例
file_path = create_note(
    text="This is a new note",
    filename="example_note"  # .md拡張子は自動的に追加されます
)
print(f"新しいノートが作成されました: {file_path}")

# 著者情報とデフォルトパスを指定する例
file_path = create_note(
    text="This is a note with author information",
    filename="authored_note",
    author="AI Assistant",
    default_path="ai_generated"
)
print(f"著者情報付きノートが作成されました: {file_path}")
```

### 2.2 ノートの編集 (edit_note)

#### 機能概要
Obsidian vault内の既存のファイルを編集します。指定されたファイルが存在しない場合はエラーが発生します。コンテンツにはfrontmatter（メタデータ）が自動的に追加または更新されます。

#### パラメータ
- `text`: ファイルに書き込む新しいコンテンツ
- `filename`: 編集するファイル名（`.md`拡張子は自動的に追加されます）
- `author`: frontmatterに追加する著者名（デフォルト: None、指定されない場合はシステム設定の著者名が使用されます）
- `default_path`: サブディレクトリが指定されていない場合に使用するデフォルトディレクトリ（デフォルト: 環境設定のDEFAULT_NOTE_DIR値）

#### 戻り値
- 編集されたファイルのパス（Path型）

#### 例外
- `ValueError`: ファイル名が空または無効な場合
- `FileNotFoundError`: 編集対象のファイルが存在しない場合
- `pydantic.ValidationError`: ファイル名に禁止文字（`<>:"/\|?*`）が含まれる場合

#### 使用例
```python
from minerva.tools import edit_note

# 基本的な使用例
file_path = edit_note(
    text="This is updated content",
    filename="existing_note"  # .md拡張子は自動的に追加されます
)
print(f"ノートが更新されました: {file_path}")

# 著者情報を更新する例
file_path = edit_note(
    text="Content with updated author information",
    filename="existing_note",
    author="Editor"
)
print(f"著者情報が更新されたノート: {file_path}")
```

### 2.3 ノートの作成・更新 (write_note) [非推奨]

#### 機能概要
指定されたテキストをObsidian vault内のファイルに書き込みます。ファイルが存在しない場合は新規作成し、存在する場合は上書きオプションに基づいて処理します。コンテンツにはfrontmatter（メタデータ）が自動的に追加されます。

**注意**: この関数は後方互換性のために維持されていますが、新しいコードでは目的に応じて `create_note` または `edit_note` 関数を使用することを推奨します。

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

### 2.4 ノートの削除 (2段階プロセス)

Minervaでは、ノートの削除は誤った削除を防ぐために2段階のプロセスで行われます：

1. `get_note_delete_confirmation`: 削除対象のファイルを確認
2. `perform_note_delete`: 実際にファイルを削除

#### 2.4.1 ノートの削除確認 (get_note_delete_confirmation)

##### 機能概要
Obsidian vault内の削除対象となるファイルが存在するかを確認し、削除確認情報を返します。

##### パラメータ
- `filename`: 削除するファイル名（`.md`拡張子は自動的に追加されます）（オプション）
- `filepath`: 削除するファイルの完全なパス（指定された場合、filenameは無視されます）（オプション）
- `default_path`: サブディレクトリが指定されていない場合に使用するデフォルトディレクトリ（デフォルト: 環境設定のDEFAULT_NOTE_DIR値）

##### 戻り値
- 削除確認情報（DeleteConfirmationResult型）
  - `file_path`: 削除対象のファイルパス
  - `message`: 確認メッセージ

##### 例外
- `ValueError`: filenameとfilepathの両方が指定されていない場合
- `FileNotFoundError`: 削除対象のファイルが存在しない場合

#### 2.4.2 ノートの削除実行 (perform_note_delete)

##### 機能概要
Obsidian vault内の既存のファイルを実際に削除します。

##### パラメータ
- `filename`: 削除するファイル名（`.md`拡張子は自動的に追加されます）（オプション）
- `filepath`: 削除するファイルの完全なパス（指定された場合、filenameは無視されます）（オプション）
- `default_path`: サブディレクトリが指定されていない場合に使用するデフォルトディレクトリ（デフォルト: 環境設定のDEFAULT_NOTE_DIR値）

##### 戻り値
- 削除されたファイルのパス（Path型）

##### 例外
- `ValueError`: filenameとfilepathの両方が指定されていない場合
- `FileNotFoundError`: 削除対象のファイルが存在しない場合

#### 使用例
```python
from minerva.tools import get_note_delete_confirmation, perform_note_delete

# 削除前の確認
confirmation = get_note_delete_confirmation(filename="note_to_delete")
print(confirmation.message)  # "File found at /path/to/note_to_delete.md. To delete, call 'perform_note_delete' with the same identification parameters."

# 確認後、実際に削除
deleted_path = perform_note_delete(filename="note_to_delete")
print(f"ファイルが削除されました: {deleted_path}")

# パスを直接指定して削除（確認 → 削除の2段階）
confirmation = get_note_delete_confirmation(filepath="/path/to/another_note.md")
print(confirmation.message)

deleted_path = perform_note_delete(filepath="/path/to/another_note.md")
print(f"ファイルが削除されました: {deleted_path}")
```

> **注意**: 以前は単一の `delete_note` 関数で確認と削除を1つの関数で行っていましたが、より明示的な2段階プロセスに変更されました。この変更により、誤ってファイルを削除するリスクが低減されます。

### 2.5 ノートの読み取り (read_note)

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

### 2.6 ノートの検索 (search_notes)

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

## 3. フロントマターのメタデータ

### 3.1 自動追加されるメタデータ

ノートの作成・編集時に、以下のメタデータが自動的にフロントマターに追加されます：

- `author`: 著者情報（パラメータで指定するか、デフォルト値が使用されます）
- `created`: ノートの作成日時（ISO形式、新規作成時のみ自動追加）
- `updated`: ノートの更新日時（ISO形式、更新時のみ自動追加）

これらのメタデータは、ノートの管理や検索に役立ちます。また、既存のノートを更新する場合、元の`created`フィールドは保持されます。

#### 日時フォーマット

日時情報はISO 8601形式で格納されます（例: `2025-05-02T12:34:56.789012`）。
これにより以下のようなメリットがあります：

- 日時の解析が容易
- ソート可能な形式
- 国際的に標準化された形式

#### 使用例

```python
from minerva.tools import create_note, edit_note, read_note
import frontmatter

# 新規ノートの作成（created フィールドが自動的に追加される）
file_path = create_note(
    text="This is a new note with creation date",
    filename="dated_note"
)

# ノートの内容を読み取る
content = read_note(str(file_path))
note = frontmatter.loads(content)
print(f"作成日: {note.metadata['created']}")  # ISO形式の作成日が表示される

# ノートの編集（updated フィールドが自動的に追加される）
file_path = edit_note(
    text="This note was updated",
    filename="dated_note"
)

# 更新後のノートを読み取る
content = read_note(str(file_path))
note = frontmatter.loads(content)
print(f"作成日: {note.metadata['created']}")  # 元の作成日が保持されている
print(f"更新日: {note.metadata['updated']}")  # 新しい更新日が表示される
```

### 3.2 サブディレクトリのサポート

ノート作成機能は以下のようなサブディレクトリの作成と利用をサポートしています：

- サブディレクトリを含むファイル名を指定できます（例：`projects/minerva/notes.md`）
- 指定されたサブディレクトリが存在しない場合、自動的に作成されます
- 複数レベルのネストされたディレクトリもサポートされています（例：`level1/level2/level3/note.md`）

### 3.3 ファイル名のバリデーション

ファイル名に関する制約：

- 空のファイル名は許可されません（各ステップで厳密なチェックが行われます）
- ファイル名に禁止文字（`<>:"/\|?*`）を含めることはできません
- 絶対パスをファイル名として使用することはできません

バリデーションは複数のレベルで行われます：
1. リクエストモデルのバリデーション（Pydanticによる入力検証）
2. `_build_file_path`関数内での追加検証
3. 下位層のファイル操作関数での検証

## 4. エラー処理

### 4.1 ファイル操作のエラー

- `create_note`: ファイルが既に存在する場合に`FileExistsError`が発生します
- `edit_note`: ファイルが存在しない場合に`FileNotFoundError`が発生します
- `write_note`: ファイルが存在し、上書きフラグがFalseの場合に`FileExistsError`が発生します
- 読み取りが要求されたファイルが存在しない場合：`FileNotFoundError`が発生します
- ファイル名が無効な場合：`ValueError`または`pydantic.ValidationError`が発生します

### 4.2 検索操作のエラー

- 検索クエリが空の場合：`ValueError`が発生します
- ディレクトリが存在しない場合：`ValueError`が発生します

## 5. 制限事項

- 検索機能は、各ファイルの最初のマッチのみを返します
- すべてのファイル操作はUTF-8エンコーディングを使用します
- バイナリファイルは検索対象から除外されます

## 6. ベストプラクティス

### 6.1 関数の選択

ノート操作において、意図を明確にするために以下のガイドラインに従うことを推奨します：

- 新しいノートを作成する場合は、`create_note`を使用してください。これにより意図せずに既存のノートを上書きするリスクが低減されます。
- 既存のノートを編集する場合は、`edit_note`を使用してください。これにより編集対象のノートが存在することが保証されます。
- 後方互換性のために`write_note`関数も引き続き利用可能ですが、新しいコードでは意図を明確にするために`create_note`または`edit_note`の使用を推奨します。
