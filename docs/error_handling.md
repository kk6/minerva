# エラーハンドリングシステム

この文書では、Minerva アプリケーション全体で一貫したエラー管理、ログ記録、パフォーマンス監視を提供するために実装された包括的なエラーハンドリングシステムについて説明します。

## 概要

エラーハンドリングシステムは以下の要素で構成されています：

1. **カスタム例外階層**: より良いエラー分類のためのドメイン固有の例外
2. **エラーハンドラーユーティリティ**: 一貫したエラーハンドリングのためのデコレーターとユーティリティ
3. **パフォーマンス監視**: 遅い操作の自動ログ記録
4. **セキュリティ機能**: パスのサニタイゼーションとセキュアなログ記録
5. **グレースフルデグラデーション**: 重要でない障害に対する安全な操作パターン

## カスタム例外

すべてのカスタム例外は `MinervaError` を継承し、構造化されたエラーコンテキストとタイムスタンプを提供します。

### 例外階層

```python
MinervaError（基本例外）
├── ValidationError          # 入力検証の失敗
├── NoteNotFoundError       # ノートファイルが見つからない
├── NoteExistsError         # ノートが既に存在する（overwrite=False）
├── TagError                # タグ関連の操作失敗
├── VaultError              # Vault レベルのアクセス問題
├── SearchError             # 検索操作の失敗
├── FrontmatterError        # フロントマターの処理問題
└── ConfigurationError      # 設定に関する問題
```

### 使用例

```python
from minerva.exceptions import ValidationError, NoteNotFoundError

try:
    service.create_note("", "filename.md")
except ValidationError as e:
    print(f"検証が失敗しました: {e}")
    print(f"エラーコンテキスト: {e.context}")
    print(f"操作: {e.operation}")
    print(f"タイムスタンプ: {e.timestamp}")
```

## エラーハンドラーユーティリティ

### MinervaErrorHandler クラス

パスのサニタイゼーションとコンテキスト作成を提供する中央エラーハンドラー：

```python
from minerva.error_handler import MinervaErrorHandler

handler = MinervaErrorHandler(vault_path=Path("/vault"))

# セキュアなログ記録のためのパスのサニタイゼーション
safe_path = handler.sanitize_path("/sensitive/vault/notes/secret.md")
# 結果: "<vault>/notes/secret.md"

# エラーコンテキストの作成
context = handler.create_error_context(
    "create_note",
    file_path="/vault/notes/test.md",
    password="secret123"
)
# 結果: {
#     "operation": "create_note",
#     "file_path": "<vault>/notes/test.md",
#     "password": "<redacted>"
# }
```

### デコレーター

#### @handle_file_operations()

標準のファイルシステム例外を適切な Minerva 例外に変換します：

```python
from minerva.error_handler import handle_file_operations

@handle_file_operations()
def my_file_operation():
    raise FileNotFoundError("File not found")
    # 自動的に NoteNotFoundError に変換される
```

#### @validate_inputs(validators...)

一貫したエラーハンドリングで入力検証を提供します：

```python
from minerva.error_handler import validate_inputs
from minerva.exceptions import ValidationError

def validate_not_empty(*args, **kwargs):
    text = args[1] if len(args) > 1 else kwargs.get('text')
    if not text or not text.strip():
        raise ValidationError("テキストは空にできません")

@validate_inputs(validate_not_empty)
def create_note(self, text: str, filename: str):
    # 検証はメソッド実行前に自動的に実行される
    pass
```

#### @log_performance(threshold_ms=1000)

パフォーマンス監視のために遅い操作をログに記録します：

```python
from minerva.error_handler import log_performance

@log_performance(threshold_ms=500)
def slow_operation():
    time.sleep(0.6)  # ログ出力: "Slow operation completed in 600ms"
```

#### @safe_operation(default_return=None)

重要でない操作に対してグレースフルなエラーハンドリングを提供します：

```python
from minerva.error_handler import safe_operation

@safe_operation(default_return=[], log_errors=True)
def get_tags(self, filepath):
    # これが失敗した場合、クラッシュする代わりに [] を返す
    return self._load_tags_from_file(filepath)
```

## サービス層での統合

エラーハンドリングシステムは `ServiceManager` とその配下のサービスモジュールに統合されています：

### 適用されているメソッド

以下の主要メソッドにエラーハンドリングデコレーターが適用されています：

```python
# ノート作成
@log_performance(threshold_ms=500)
@validate_inputs(_validate_text_content, _validate_filename)
@handle_file_operations()
def create_note(self, text: str, filename: str, ...):
    # メソッドの実装

# ノート編集
@log_performance(threshold_ms=500)
@validate_inputs(_validate_text_content, _validate_filename)
@handle_file_operations()
def edit_note(self, text: str, filename: str, ...):
    # メソッドの実装

# ノート読み取り
@log_performance(threshold_ms=200)
@handle_file_operations()
def read_note(self, filepath: str) -> str:
    # メソッドの実装
```

これにより以下が提供されます：
- パフォーマンスログ記録（設定された閾値を超える場合）
- 入力検証（テキストとファイル名をチェック）
- ファイル操作のエラー変換
- 一貫したエラーコンテキスト

### エラーハンドラーインスタンス

各サービスインスタンスはエラーハンドラーを持ちます：

```python
service = ServiceManager(config, frontmatter_manager)
# service.error_handler は vault_path で自動的に初期化される
```

## セキュリティ機能

### パスのサニタイゼーション

機密ファイルパスはログ内でサニタイズされます：

```python
handler = MinervaErrorHandler(vault_path=Path("/home/user/vault"))

# Vault 相対パス
handler.sanitize_path("/home/user/vault/notes/secret.md")
# 結果: "<vault>/notes/secret.md"

# 外部パス
handler.sanitize_path("/etc/passwd")
# 結果: "<external>/passwd"

# 長いパス
handler.sanitize_path("a/very/long/path/with/many/parts/file.md")
# 結果: "a/.../many/parts/file.md"
```

### 認証情報の編集

機密情報は自動的に編集されます：

```python
context = handler.create_error_context(
    "operation",
    password="secret123",
    token="abc123",
    api_key="xyz789"
)
# すべての機密フィールドが "<redacted>" になる
```

## パフォーマンス監視

### 高精度タイミング測定

パフォーマンス測定には `time.perf_counter()` を使用しており、以下の利点があります：
- 高解像度の単調増加タイマー
- NTPジャンプやシステム時刻変更の影響を受けない
- マイクロ秒単位の正確な測定

### 自動ログ記録

閾値を超える操作は自動的にログに記録されます：

```python
# ログ内容:
# INFO: Slow operation minerva.service.create_note completed in 756.23ms
# ERROR: Operation minerva.service.read_note failed after 45.67ms: File not found
```

### 操作タイプ別の閾値

- **ファイル作成/編集**: 500ms
- **ファイル読み取り**: 200ms
- **タグ操作**: 300ms
- **検索操作**: 1000ms

## ベストプラクティス

### 1. 適切な例外タイプを使用する

```python
# 良い例
raise ValidationError("無効なタグ形式")
raise NoteNotFoundError("ノートファイルが存在しません")

# 避けるべき例
raise ValueError("何かが間違っています")
raise Exception("一般的なエラー")
```

### 2. コンテキストを提供する

```python
# 良い例
raise ValidationError(
    "無効なタグ形式",
    context={"tag": tag, "valid_pattern": "^[a-z0-9-]+$"},
    operation="add_tag"
)

# 基本例
raise ValidationError("無効なタグ形式")
```

### 3. 重要でないコードには安全な操作を使用する

```python
@safe_operation(default_return=[], log_errors=True)
def get_optional_metadata(self, filepath):
    # これが失敗してもアプリケーションはクラッシュしない
    return self._extract_metadata(filepath)
```

### 4. 適切なレベルでログを記録する

- **ERROR**: 操作完了を妨げる重大な障害
- **WARNING**: 回復可能な問題、検証失敗
- **INFO**: 成功した操作、パフォーマンス情報

### 5. エラーハンドリングの一貫性を保つ

- すべてのファイル操作メソッド（`create_note`、`edit_note`、`read_note`など）には`@handle_file_operations()`を適用
- テストでは具体的なMinerva例外（`NoteNotFoundError`など）を期待し、汎用的な`Exception`は避ける
- デコレーターの適用順序を統一：`@log_performance` → `@validate_inputs` → `@handle_file_operations`

## エラー回復パターン

### 1. グレースフルデグラデーション

```python
@safe_operation(default_return=[])
def get_tags(self, filepath):
    # タグ抽出が失敗した場合、空のリストを返す
    pass
```

### 2. フォールバック付きリトライ

```python
def robust_file_read(self, filepath):
    try:
        return self.read_note(filepath)
    except NoteNotFoundError:
        logger.warning("ノートが見つかりません、空のノートを作成します")
        return ""
```

### 3. ユーザーフレンドリーなエラーメッセージ

```python
try:
    service.create_note(content, filename)
except ValidationError as e:
    return {"error": "無効な入力", "details": str(e)}
except VaultError as e:
    return {"error": "アクセス拒否", "details": "ファイル権限を確認してください"}
```

## エラーハンドリングのテスト

### カスタム例外のテスト

```python
def test_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        service.create_note("", "filename.md")

    assert "empty" in str(exc_info.value)
    assert exc_info.value.operation is not None
```

### エラー変換のテスト

```python
@patch('minerva.file_handler.read_file')
def test_file_not_found_conversion(mock_read):
    mock_read.side_effect = FileNotFoundError("File not found")

    with pytest.raises(NoteNotFoundError):
        service.read_note("/path/to/file.md")
```

### パフォーマンスログのテスト

```python
def test_slow_operation_logging(caplog):
    # 操作が閾値を超えたときにログに記録されることをテスト
    with caplog.at_level(logging.INFO):
        slow_service_operation()

    assert "Slow operation" in caplog.text
```

## 移行ガイド

古いエラーハンドリングパターンを使用している既存のコードの場合：

### 変更前（古いパターン）
```python
try:
    result = some_operation()
except Exception as e:
    logger.error("操作が失敗しました: %s", e)
    raise
```

### 変更後（新しいパターン）
```python
@handle_file_operations()
@log_performance()
def some_operation():
    # 自動的なエラーハンドリングとログ記録
    pass
```

### 例外マッピング

- `ValueError` → `ValidationError`（入力検証用）
- `FileNotFoundError` → `NoteNotFoundError`
- `FileExistsError` → `NoteExistsError`
- `PermissionError` → `VaultError`
- `IOError`/`OSError` → `VaultError`

このエラーハンドリングシステムは、可能な限り後方互換性を保ちながら、Minerva アプリケーション全体で一貫性があり、セキュアで、保守可能なエラー管理を提供します。
