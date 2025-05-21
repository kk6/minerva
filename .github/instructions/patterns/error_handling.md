---
applyTo: 'src/**/*.py'
---

# Error Handling Patterns for Minerva

## Basic Principles

The Minerva project follows these principles for error handling:

1. **Exception Propagation and Transformation**: Convert low-level exceptions into more meaningful high-level exceptions
2. **Appropriate Logging**: Log all exceptions at appropriate log levels
3. **Clear Error Messages**: Provide user-friendly error messages for end users
4. **Detailed Context**: Include helpful information for debugging in errors

## Exception Types

### 1. Input Validation Errors

Example of input validation using Pydantic:

```python
class FileOperationRequest(BaseModel):
    """Base request model for file operations."""

    directory: str = Field(description="Directory for the file operation")
    filename: str = Field(description="Name of the file")

    @field_validator("filename")
    def validate_filename(cls, v):
        """Validate the filename."""
        if not v:
            raise ValueError("Filename cannot be empty")
        if os.path.isabs(v):
            raise ValueError("Filename cannot be an absolute path")
        if any(char in v for char in FORBIDDEN_CHARS):
            raise ValueError(
                f"Filename contains forbidden characters: {FORBIDDEN_CHARS}"
            )
        return v
```

### 2. File Operation Errors

Error handling related to file operations:

```python
def write_file(request: FileWriteRequest) -> Path:
    """Write the content to a file in the specified directory."""
    file_path = _get_validated_file_path(request.directory, request.filename)

    # Ensure the directory exists
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists() and not request.overwrite:
        raise FileExistsError(
            f"File {file_path} already exists and overwrite is set to False"
        )

    # Write the content to the file
    try:
        with open(file_path, "w", encoding=ENCODING) as f:
            f.write(request.content)
        return file_path
    except IOError as e:
        logger.error("Error writing to file %s: %s", file_path, e)
        raise IOError(f"Failed to write to file {file_path}: {e}") from e
```

## try-except Patterns

### 1. Basic Pattern

```python
try:
    # Potentially exception-raising operation
    result = potentially_failing_operation()
except SpecificException as e:
    # Handle the exception appropriately
    logger.error("Operation failed: %s", e)
    # Raise a more specific exception if needed
    raise CustomException("Failed to perform operation") from e
```

### 2. Using finally Blocks

When resource cleanup is needed:

```python
resource = None
try:
    resource = acquire_resource()
    result = use_resource(resource)
    return result
except Exception as e:
    logger.error("Resource operation failed: %s", e)
    raise
finally:
    # Resource cleanup (executed even if an exception occurs)
    if resource:
        release_resource(resource)
```

### 3. Using else Blocks

Processing that only executes if no exception occurs:

```python
try:
    data = parse_input(user_input)
except ValueError as e:
    logger.error("Invalid input: %s", e)
    raise InvalidInputError("Input could not be parsed") from e
else:
    # Only executes if no exception occurred
    process_valid_data(data)
```

### 4. 詳細なエラーログ記録パターン

コードベースでは、エラータイプに応じた詳細なログ記録が実装されています：

```python
def search_notes(query: str, case_sensitive: bool = True) -> list[SearchResult]:
    """
    Search for a keyword in all files in the Obsidian vault.
    """
    if not query:
        raise ValueError("Query cannot be empty")

    try:
        search_config = SearchConfig(
            directory=str(VAULT_PATH),
            keyword=query,
            file_extensions=[".md"],
            case_sensitive=case_sensitive,
        )
        matching_files = search_keyword_in_files(search_config)
        logger.info("Found %s files matching the query: %s", len(matching_files), query)
    except PermissionError as e:  # 特定の権限エラーを処理
        logger.error(
            "Permission denied during search for query '%s' in vault %s: %s",
            query,
            VAULT_PATH,
            e,
        )
        raise
    except (IOError, OSError) as e:  # ファイルシステムの問題を処理
        logger.error(
            "File system error during search for query '%s' in vault %s: %s",
            query,
            VAULT_PATH,
            e,
        )
        raise
    except ValueError as e:  # 検証エラーを処理
        logger.error("Invalid search parameters for query '%s': %s", query, e)
        raise
    except Exception as e:  # 本当に予期しない問題のみキャッチ
        logger.error(
            "Unexpected error searching for query '%s' in vault %s: %s",
            query,
            VAULT_PATH,
            e,
        )
        raise RuntimeError(
            f"Unexpected error occurred during search for query '{query}': {e}"
        ) from e

    return matching_files
```

#### 改善されたエラーログのポイント

1. **エラータイプによる分類**：
   - 権限エラー（PermissionError）
   - ファイルシステムエラー（IOError、OSError）
   - 入力検証エラー（ValueError）
   - 予期しないエラー（その他のException）

2. **コンテキスト情報の充実**：
   - 関連するパラメータ（query、ディレクトリなど）がログに含まれる
   - 原因となる例外情報が保持される（`from e`構文）

3. **適切なエラー変換**：
   - 低レベルの例外を意味のある高レベルの例外に変換
   - 例：`raise RuntimeError(...) from e`

4. **ログメッセージの詳細化**：
   - エラーが発生した操作の具体的な説明
   - 関連するパラメータ値の表示
   - エラーの原因と可能な解決策のヒント

## 7. セキュリティ重視設計パターン

### 7.1 2段階での破壊的操作

Minerva では、データ削除などの破壊的な操作は、2段階のプロセスで実装するパターンを採用しています：

```python
# 1. 確認ステップ
def get_note_delete_confirmation(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> DeleteConfirmationResult:
    """
    Get confirmation for deleting a note from the Obsidian vault.
    """
    # 存在確認などのチェック
    # ...

    # 確認情報を返す（実際の削除は行わない）
    message = f"File found at {file_path}. To delete, call 'perform_note_delete' with the same identification parameters."
    return DeleteConfirmationResult(file_path=str(file_path), message=message)

# 2. 実行ステップ
def perform_note_delete(
    filename: str | None = None,
    filepath: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Perform the deletion of a note from the Obsidian vault.
    """
    # 存在確認などのチェック
    # ...

    # 実際の削除操作を実行
    file_delete_request = FileDeleteRequest(
        directory=str(file_path.parent),
        filename=file_path.name,
    )

    deleted_path = delete_file(file_delete_request)
    return deleted_path
```

#### このパターンを使用する理由

- **意図的な実行**：削除などの破壊的操作が意図的に実行されることを保証する
- **ユーザー確認**：最初のステップで返される情報をユーザーに表示し、確認を得ることができる
- **データ保護**：誤操作によるデータ損失のリスクを軽減する
- **スクリプト実行の安全性**：自動化スクリプトでも、2段階の操作を明示的に実装する必要があるため安全

#### 適用シナリオ

このパターンは以下の操作に特に適しています：

1. データ削除
2. 既存ファイルの上書き
3. システム設定の変更
4. 外部システムとの連携操作

## Error Handling Best Practices

1. **Catch Specific Exceptions**: Catch specific exception classes rather than `Exception`

2. **Provide Error Context**: Include information in error messages that clearly explains what happened

3. **Preserve the Cause of Exceptions**: Use the `raise ... from e` syntax to preserve the original exception

4. **Appropriate Error Abstraction**: At API boundaries, return errors at an appropriate level of abstraction that doesn't leak internal implementation details

5. **Consistent Error Responses**: Keep error messages returned to users in a consistent format

6. **Early Input Validation**: Validate inputs early in the process to detect invalid inputs as soon as possible
