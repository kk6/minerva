# Minerva ノート操作機能仕様書

この仕様書はMinervaプロジェクトにおけるObsidianノートの操作機能について説明します。

## 1. 概要

Minervaは、Obsidian vaultに対して以下の機能を提供します：

### 1.1 基本操作機能
- ノートの作成（create_note）
- ノートの編集（edit_note）
- ノートの読取（read_note）
- ノートの検索（search_notes）
- ノートの削除（get_note_delete_confirmation, perform_note_delete）

### 1.2 タグ管理機能
- タグの追加（add_tag）
- タグの削除（remove_tag）
- タグの名前変更（rename_tag）
- タグの取得（get_tags）
- 全タグのリスト取得（list_all_tags）
- タグによるノート検索（find_notes_with_tag）

### 1.3 エイリアス管理機能
- エイリアスの追加（add_alias）
- エイリアスの削除（remove_alias）
- エイリアスの取得（get_aliases）
- エイリアスによるノート検索（search_by_alias）

これらの機能はPython APIとして提供され、アプリケーションから呼び出すことができます。

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

### 2.3 ノートの削除 (2段階プロセス)

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

## 7. タグ管理機能

Minervaはノートのタグを管理するための包括的な機能セットを提供します。タグは正規化（小文字化、前後の空白削除）されて処理され、特定の禁止文字（`,` `<` `>` `/` `?` `'` `"`）を含むタグは無効とみなされます。

### 7.1 ノートへのタグ追加 (add_tag)

`add_tag`関数は、指定された単一のタグを特定のノートに追加します。

- **主要パラメータ**:
    - `tag`: 追加するタグ文字列。
    - `filename` または `filepath`: 対象ノートを特定します。`filename` を使用する場合、`default_path` も考慮されます。
- **動作**:
    - タグは追加前に正規化されます（例: "My Tag" は "my tag" になります）。
    - 正規化されたタグが既にノートに存在する場合、重複して追加されることはありません。
    - 無効な形式のタグ（例: コンマを含む）を指定するとエラーが発生します。
    - ノートのメタデータが更新され、`updated`タイムスタンプが変更されます。
- **戻り値**: 更新されたノートファイルのパス (`Path`オブジェクト)。
- **主な例外**: `FileNotFoundError` (ノートが存在しない場合)、`ValueError` (タグが無効な場合)。

### 7.2 ノートからのタグ削除 (remove_tag)

`remove_tag`関数は、指定された単一のタグを特定のノートから削除します。

- **主要パラメータ**:
    - `tag`: 削除するタグ文字列。
    - `filename` または `filepath`: 対象ノートを特定します。
- **動作**:
    - 削除するタグの指定は、正規化された形でノート内のタグと比較されます（大文字・小文字を区別しない）。
    - タグがノートから削除されると、ノートのメタデータが更新され、`updated`タイムスタンプが変更されます。
    - 指定されたタグがノートに存在しない場合でもエラーは発生しませんが、`updated`タイムスタンプは更新されます。
    - ノートから最後のタグが削除された場合、フロントマターから `tags` フィールド自体が削除されます。
- **戻り値**: 更新されたノートファイルのパス (`Path`オブジェクト)。
- **主な例外**: `FileNotFoundError` (ノートが存在しない場合)。

### 7.3 ノート間のタグ名変更 (rename_tag)

`rename_tag`関数は、指定されたディレクトリ（またはボールト全体）内のすべてのノートを検索し、特定のタグ名を新しい名前に変更します。

- **主要パラメータ**:
    - `old_tag`: 名前を変更する現在のタグ文字列。
    - `new_tag`: 新しいタグ文字列。
    - `directory` (オプション): 操作対象のディレクトリパス。指定しない場合はボールト全体が対象。
- **動作**:
    - `old_tag` の検索と `new_tag` の比較は正規化された形で行われます。
    - `new_tag` が無効な形式の場合はエラーが発生します。
    - `old_tag` と `new_tag` が正規化後に同じになる場合、操作は行われません。
    - `new_tag` がノート内で（正規化後に）既に存在する別のタグと同じ場合、タグは効果的にマージされます（重複は発生しません）。
    - タグが変更されたノートのみが更新され、`updated`タイムスタンプが変更されます。
- **戻り値**: 変更が加えられたノートファイルのパスのリスト (`list[Path]`)。
- **主な例外**: `FileNotFoundError` (指定された `directory` が存在しない場合)、`ValueError` (`new_tag` が無効な場合)。

### 7.4 ノートからのタグ取得 (get_tags)

`get_tags`関数は、特定のノートからタグのリストを取得します。

- **主要パラメータ**:
    - `filename` または `filepath`: 対象ノートを特定します。
- **動作**:
    - ノートのフロントマターから `tags` フィールドを読み取ります。
    - タグの元のケーシング（大文字・小文字）を保持して返します。
    - ファイルが存在しない、読み取れない、フロントマターが不正、または `tags` フィールドが存在しないかリスト形式でない場合は、空のリストを返します（エラーは発生しません）。
- **戻り値**: タグ文字列のリスト (`list[str]`)。
- **主な例外**: Pydanticモデルのバリデーションエラー（例：`filename`も`filepath`も提供されない場合）は発生する可能性がありますが、ファイル読み取りやパースに関する一般的な問題では発生しません。

### 7.5 全ユニークタグのリスト化 (list_all_tags)

`list_all_tags`関数は、指定されたディレクトリ（またはボールト全体）内のすべてのMarkdownファイルから、すべてのユニークなタグを収集しリスト化します。

- **主要パラメータ**:
    - `directory` (オプション): スキャンするディレクトリパス。指定しない場合はボールト全体が対象。
- **動作**:
    - 各ノートからタグを取得し（`get_tags`を使用）、それらを正規化します。
    - 正規化されたタグのユニークなセットを作成し、アルファベット順にソートして返します。
    - 空の正規化タグ（例：タグが空白文字のみで構成されていた場合）は結果に含まれません。
- **戻り値**: ソートされたユニークな正規化タグ文字列のリスト (`list[str]`)。
- **主な例外**: `FileNotFoundError` (指定された `directory` が存在しない場合)。

### 7.6 特定タグを持つノートの検索 (find_notes_with_tag)

`find_notes_with_tag`関数は、指定されたタグを含むすべてのノートを検索し、それらのファイルパスをリスト化します。

- **主要パラメータ**:
    - `tag`: 検索対象のタグ文字列。
    - `directory` (オプション): スキャンするディレクトリパス。指定しない場合はボールト全体が対象。
- **動作**:
    - 指定された `tag` は正規化されて検索に使用されます。
    - 各ノートのタグリスト（正規化済み）と指定タグを比較します。
    - 検索対象の正規化タグが空文字列になる場合（例: 入力タグが空白のみ）、空のリストが返されます。
- **戻り値**: 指定されたタグを含むノートのファイルパス（文字列）のリスト (`list[str]`)。
- **主な例外**: `FileNotFoundError` (指定された `directory` が存在しない場合)。

## 8. エイリアス管理機能

Minervaはノートのエイリアス（別名）を管理するための機能セットを提供します。エイリアスは、ノートに複数の名前を付けることで、自然言語での参照や検索を可能にします。この機能はObsidianの標準的なエイリアスシステムと完全に互換性があります。

### 8.1 エイリアスの概念

エイリアスは以下の特徴を持ちます：

- ノートのフロントマターの`aliases`フィールドに文字列のリストとして保存されます
- 大文字・小文字を区別しない検索と比較が行われます
- 既存のファイル名や他のノートのエイリアスとの重複を防ぐオプションがあります
- Obsidianのエイリアス機能と完全に互換性があります

### 8.2 ノートへのエイリアス追加 (add_alias)

`add_alias`関数は、指定された単一のエイリアスを特定のノートに追加します。

- **主要パラメータ**:
    - `alias`: 追加するエイリアス文字列
    - `filename` または `filepath`: 対象ノートを特定します
    - `allow_conflicts` (オプション): 既存のファイル名やエイリアスとの重複を許可するかどうか（デフォルト: False）
- **動作**:
    - エイリアスは追加前にバリデーションされます（空文字列、長すぎる文字列、禁止文字の検査）
    - 重複チェックが行われ、既存のファイル名や他のノートのエイリアスとの衝突を防ぎます
    - 大文字・小文字を区別しない重複チェックが行われます
    - ノートのメタデータが更新され、`updated`タイムスタンプが変更されます
- **戻り値**: 更新されたノートファイルのパス (`Path`オブジェクト)
- **主な例外**:
    - `FileNotFoundError` (ノートが存在しない場合)
    - `ValueError` (エイリアスが無効、または重複が検出された場合)

#### 使用例
```python
from minerva.tools import add_alias

# 基本的なエイリアス追加
file_path = add_alias(
    alias="last week's meeting",
    filename="meeting_20250523.md"
)

# 重複を許可してエイリアス追加
file_path = add_alias(
    alias="project alpha",
    filename="project_notes.md",
    allow_conflicts=True
)
```

### 8.3 ノートからのエイリアス削除 (remove_alias)

`remove_alias`関数は、指定された単一のエイリアスを特定のノートから削除します。

- **主要パラメータ**:
    - `alias`: 削除するエイリアス文字列
    - `filename` または `filepath`: 対象ノートを特定します
- **動作**:
    - 削除するエイリアスの指定は、正規化された形でノート内のエイリアスと比較されます（大文字・小文字を区別しない）
    - エイリアスがノートから削除されると、ノートのメタデータが更新され、`updated`タイムスタンプが変更されます
    - 指定されたエイリアスがノートに存在しない場合でもエラーは発生しませんが、`updated`タイムスタンプは更新されます
    - ノートから最後のエイリアスが削除された場合、フロントマターから `aliases` フィールド自体が削除されます
- **戻り値**: 更新されたノートファイルのパス (`Path`オブジェクト)
- **主な例外**: `FileNotFoundError` (ノートが存在しない場合)

#### 使用例
```python
from minerva.tools import remove_alias

# エイリアスの削除
file_path = remove_alias(
    alias="old name",
    filename="updated_note.md"
)
```

### 8.4 ノートからのエイリアス取得 (get_aliases)

`get_aliases`関数は、特定のノートからエイリアスのリストを取得します。

- **主要パラメータ**:
    - `filename` または `filepath`: 対象ノートを特定します
- **動作**:
    - ノートのフロントマターから `aliases` フィールドを読み取ります
    - エイリアスの元のケーシング（大文字・小文字）を保持して返します
    - ファイルが存在しない、読み取れない、フロントマターが不正、または `aliases` フィールドが存在しないかリスト形式でない場合は、空のリストを返します（エラーは発生しません）
- **戻り値**: エイリアス文字列のリスト (`list[str]`)
- **主な例外**: 一般的なファイル読み取りやパースの問題では例外は発生しません

#### 使用例
```python
from minerva.tools import get_aliases

# ノートのエイリアス取得
aliases = get_aliases(filename="project_notes.md")
print(f"エイリアス: {aliases}")
```

### 8.5 エイリアスによるノート検索 (search_by_alias)

`search_by_alias`関数は、指定されたエイリアスを含むすべてのノートを検索し、それらのファイルパスをリスト化します。

- **主要パラメータ**:
    - `alias`: 検索対象のエイリアス文字列
    - `directory` (オプション): スキャンするディレクトリパス。指定しない場合はボールト全体が対象
- **動作**:
    - 指定された `alias` は正規化されて検索に使用されます
    - 各ノートのエイリアスリスト（正規化済み）と指定エイリアスを比較します
    - 検索対象の正規化エイリアスが空文字列になる場合（例: 入力エイリアスが空白のみ）、例外が発生します
- **戻り値**: 指定されたエイリアスを含むノートのファイルパス（文字列）のリスト (`list[str]`)
- **主な例外**:
    - `ValueError` (エイリアスが空または無効な場合)
    - `FileNotFoundError` (指定された `directory` が存在しない場合)

#### 使用例
```python
from minerva.tools import search_by_alias

# エイリアスでノート検索
results = search_by_alias("meeting notes")
for file_path in results:
    print(f"見つかったノート: {file_path}")

# 特定ディレクトリ内でのエイリアス検索
results = search_by_alias(
    alias="project alpha",
    directory="projects"
)
```

### 8.6 エイリアスのバリデーション

エイリアスには以下の制約があります：

- 空文字列や空白のみの文字列は許可されません
- 最大100文字までの長さ制限があります
- Obsidianと互換性を保つため、以下の文字は使用できません: `|`, `#`, `^`, `[`, `]`
- 大文字・小文字を区別しない重複チェックが行われます

### 8.7 競合検出と回避

デフォルトでは、`add_alias`関数は以下の競合を防ぎます：

- 既存のファイル名（.md拡張子を除く）との重複
- 他のノートの既存エイリアスとの重複

この動作は `allow_conflicts=True` を指定することで無効化できますが、推奨されません。

### 8.8 Obsidianとの互換性

- エイリアスは標準的なYAMLフロントマターの`aliases`フィールドに保存されます
- Obsidianで作成されたエイリアスもMinervaで正常に読み取り・操作できます
- Minervaで作成されたエイリアスもObsidianで正常に認識されます

## 9. ノートマージ機能

### 9.1 概要

ノートマージ機能は、複数のノートを1つのファイルに統合する機能です。散在したメモの整理、関連トピックの統合、月次レポートの作成などに活用できます。

提供される機能：
- `merge_notes`: 詳細なオプション指定によるノートマージ
- `smart_merge_notes`: 内容を自動分析してマージ戦略を選択する賢いマージ

### 9.2 マージ戦略

#### 9.2.1 append（単純追加）
- ファイルを指定された順序で単純に連結
- 各ノートにファイル名ベースのセクションヘッダーを追加
- オプションで目次を自動生成
- セパレーターで各セクションを区切り

#### 9.2.2 by_heading（見出しベース）
- Markdownの見出し（# ## ###）を基準にコンテンツをグループ化
- 同じ見出しの下にあるコンテンツを統合
- 見出しの階層構造を保持

#### 9.2.3 by_date（日付ベース）
- フロントマターの作成日時または更新日時でソート
- 時系列順に整理されたマージ結果を生成
- 日付情報がない場合はファイルの更新時刻を使用

#### 9.2.4 smart（スマートマージ）
- ノートの内容を自動分析して最適な戦略を選択
- 共通の見出しが多い場合：by_heading
- 日付情報が豊富な場合：by_date
- その他の場合：append

### 9.3 merge_notes関数

#### 機能概要
複数のノートを指定された戦略とオプションでマージし、新しいノートを作成します。

#### パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `source_files` | `list[str]` | (必須) | マージするソースファイルのパスリスト |
| `target_filename` | `str` | (必須) | 作成するマージファイルの名前 |
| `merge_strategy` | `str` | `"append"` | マージ戦略（"append", "by_heading", "by_date", "smart"） |
| `separator` | `str` | `"\n\n---\n\n"` | セクション間のセパレーター（append戦略用） |
| `preserve_frontmatter` | `bool` | `True` | ソースファイルのフロントマターを統合するか |
| `delete_sources` | `bool` | `False` | マージ後にソースファイルを削除するか |
| `create_toc` | `bool` | `True` | 目次を自動生成するか（対応戦略のみ） |
| `author` | `str \| None` | `None` | マージファイルの著者名 |
| `default_path` | `str \| None` | `None` | 保存先のサブフォルダ |

#### 戻り値
- `dict`: マージ結果の詳細情報
  - `source_files`: マージされたソースファイルのリスト
  - `target_file`: 作成されたマージファイルのパス
  - `merge_strategy`: 使用されたマージ戦略
  - `files_processed`: 処理されたファイル数
  - `warnings`: 警告メッセージのリスト
  - `merge_history`: マージ履歴の詳細情報

#### 使用例

```python
# 基本的なマージ
result = merge_notes(
    source_files=["meeting1.md", "meeting2.md"],
    target_filename="monthly_summary.md"
)

# 日付順でマージし、ソースファイルを削除
result = merge_notes(
    source_files=["daily1.md", "daily2.md", "daily3.md"],
    target_filename="weekly_report.md",
    merge_strategy="by_date",
    delete_sources=True
)

# カスタムセパレーターを使用
result = merge_notes(
    source_files=["note1.md", "note2.md"],
    target_filename="combined.md",
    separator="\n\n🔗 ────────────────\n\n"
)
```

#### 例外

- `ValueError`: ソースファイルが2つ未満、無効なマージ戦略、ファイル読み取りエラー
- `FileNotFoundError`: ソースファイルが存在しない
- `FileExistsError`: ターゲットファイルが既に存在する

### 9.4 smart_merge_notes関数

#### 機能概要
ノートの内容を自動分析し、最適なマージ戦略を選択してマージを実行します。

#### パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `source_files` | `list[str]` | (必須) | マージするソースファイルのパスリスト |
| `target_filename` | `str` | (必須) | 作成するマージファイルの名前 |
| `group_by` | `str` | `"heading"` | グループ化のヒント（"heading", "tag", "date"） |
| `author` | `str \| None` | `None` | マージファイルの著者名 |
| `default_path` | `str \| None` | `None` | 保存先のサブフォルダ |

#### 戻り値
- `dict`: マージ結果（merge_notesと同じ形式）+ 選択された戦略の情報

#### 使用例

```python
# スマートマージ（自動戦略選択）
result = smart_merge_notes(
    source_files=["research1.md", "research2.md", "research3.md"],
    target_filename="research_summary.md"
)

# 日付を重視したヒント付きスマートマージ
result = smart_merge_notes(
    source_files=["diary1.md", "diary2.md"],
    target_filename="week_summary.md",
    group_by="date"
)
```

### 9.5 フロントマター統合

マージ時に各ソースファイルのフロントマターは以下のルールで統合されます：

#### 9.5.1 統合されるフィールド

- **`tags`**: 全ソースファイルのタグを重複排除してマージ
- **`aliases`**: 全ソースファイルのエイリアスを統合
- **`created`**: 新しいマージファイルの作成日時
- **`modified`**: 新しいマージファイルの更新日時
- **`author`**: 指定された著者名またはデフォルト設定

#### 9.5.2 保存される元情報

- **`original_created`**: ソースファイルの最も古い作成日時
- **`original_modified`**: ソースファイルの最も新しい更新日時
- **`original_authors`**: ソースファイルの全著者のリスト
- **`merged_from`**: ソースファイルのパスリスト
- **`merge_date`**: マージ実行日時

### 9.6 マージ履歴

各マージ操作では詳細な履歴情報が記録されます：

#### 9.6.1 基本情報
- マージに使用された戦略
- 処理されたファイル数
- エラーや警告の詳細

#### 9.6.2 戦略別の詳細情報

**append戦略の場合:**
```json
{
  "sections": [
    {
      "source_file": "/path/to/file1.md",
      "section_title": "file1",
      "content_length": 256
    }
  ]
}
```

**by_heading戦略の場合:**
```json
{
  "heading_groups": {
    "プロジェクトA": [
      {
        "source_file": "/path/to/file1.md",
        "content_length": 128
      }
    ]
  }
}
```

**by_date戦略の場合:**
```json
{
  "sort_strategy": "created",
  "date_order": [
    {
      "file": "/path/to/file1.md",
      "date": "2024-01-01T10:00:00"
    }
  ]
}
```

**smart戦略の場合:**
```json
{
  "smart_strategy_selected": "by_heading",
  "sections": [...],
  "heading_groups": [...]
}
```

### 9.7 ベストプラクティス

#### 9.7.1 マージ前の準備
- ソースファイルのバックアップを作成
- 関連性のあるファイルのみをマージ対象に選択
- フロントマターのタグやメタデータを事前に整理

#### 9.7.2 戦略の選択指針

**append戦略を使用する場合:**
- 会議録の時系列まとめ
- 異なるトピックの単純な結合
- 元のファイル構造を保持したい場合

**by_heading戦略を使用する場合:**
- 同じプロジェクトの異なる観点のメモ
- 構造化された研究ノート
- カテゴリ別に整理したい場合

**by_date戦略を使用する場合:**
- 日記やログの統合
- 時系列が重要なドキュメント
- 進捗レポートの作成

**smart戦略を使用する場合:**
- 最適な戦略が不明な場合
- 混在したコンテンツタイプ
- 自動化されたワークフロー

#### 9.7.3 注意事項

- `delete_sources=True`は慎重に使用（取り消し不可）
- 大量ファイルのマージ時はメモリ使用量に注意
- ファイル参照（リンクや画像）は手動で調整が必要な場合がある
- マージ結果は必ず内容を確認してから使用する

### 9.8 エラー処理

#### 9.8.1 一般的なエラー

**入力値エラー:**
- マージ対象ファイルが2つ未満
- 無効なマージ戦略の指定
- 空のファイル名や無効なパス

**ファイルエラー:**
- ソースファイルが存在しない
- ターゲットファイルが既に存在
- ファイル読み取り権限がない
- ディスク容量不足

#### 9.8.2 エラー対処法

**FileNotFoundError:**
```python
try:
    result = merge_notes(source_files, target_filename)
except FileNotFoundError as e:
    print(f"ファイルが見つかりません: {e}")
    # ファイルパスを確認し、再試行
```

**FileExistsError:**
```python
try:
    result = merge_notes(source_files, target_filename)
except FileExistsError as e:
    print(f"ターゲットファイルが既に存在します: {e}")
    # 別のファイル名を選択するか、既存ファイルを削除
```

### 9.9 実用的な使用例

#### 9.9.1 月次会議録の統合

```python
# 2024年12月の全会議録をマージ
meeting_files = [
    "meetings/2024-12-05-weekly.md",
    "meetings/2024-12-12-weekly.md",
    "meetings/2024-12-19-weekly.md",
    "meetings/2024-12-26-weekly.md"
]

result = merge_notes(
    source_files=meeting_files,
    target_filename="2024-12-summary.md",
    merge_strategy="by_date",
    create_toc=True,
    default_path="summaries"
)
```

#### 9.9.2 プロジェクト資料の統合

```python
# プロジェクトの各種メモを見出しベースで統合
project_files = [
    "project/requirements.md",
    "project/design_notes.md",
    "project/meeting_notes.md",
    "project/issues.md"
]

result = smart_merge_notes(
    source_files=project_files,
    target_filename="project_overview.md",
    group_by="heading"
)
```

#### 9.9.3 研究ノートの整理

```python
# 関連する研究ノートを統合し、元ファイルを削除
research_files = [
    "research/ai_models.md",
    "research/benchmarks.md",
    "research/related_work.md"
]

result = merge_notes(
    source_files=research_files,
    target_filename="ai_research_summary.md",
    merge_strategy="by_heading",
    delete_sources=True,  # 慎重に使用
    author="研究者名"
)
```
