# Minerva テストガイドライン

このドキュメントでは、Minervaプロジェクトにおけるテスト作成のガイドラインとベストプラクティスについて説明します。

## 1. テスト戦略

Minervaプロジェクトでは、以下のテスト戦略を採用しています：

1. **単体テスト**: 個別の関数やメソッドの動作を検証
2. **統合テスト**: 複数のコンポーネントが連携して動作することを検証
3. **例外テスト**: エラー条件とその処理が正しく機能することを検証

すべてのテストは `pytest` フレームワークを使用して実装し、モックやパラメータ化テストの機能を活用しています。

## 2. テスト構造

### 2.1 Arrange-Act-Assert (AAA) パターン

すべてのテストは **Arrange-Act-Assert** パターンに従って構造化する必要があります：

#### Arrange（準備）
テスト対象のシステムを適切な初期状態に設定します。
- テストデータの準備
- モックオブジェクトの設定
- 前提条件の構築

```python
# ==================== Arrange ====================
request = FileWriteRequest(
    directory=temp_dir,
    filename="test.txt",
    content="Hello, World!",
    overwrite=True,
)
```

#### Act（実行）
テスト対象のコードを実行します。通常は一つの関数またはメソッドの呼び出しです。

```python
# ==================== Act ====================
file_path = write_file(request)
```

#### Assert（検証）
結果が期待通りであることを検証します。

```python
# ==================== Assert ====================
assert file_path == Path(temp_dir) / "test.txt"
assert file_path.exists()
with open(file_path, "r", encoding=ENCODING) as f:
    content = f.read()
    assert content == "Hello, World!"
```

### 2.2 例外テストの特別なケース

例外をテストする場合、Act と Assert は `pytest.raises` コンテキストマネージャーで結合されることがあります：

```python
# ==================== Act & Assert ====================
with pytest.raises(FileExistsError):
    write_file(request)
```

### 2.3 docstring の形式

各テストメソッドには、以下の構造を持つ docstring を含めてください：

```python
def test_some_functionality(self):
    """テストの目的を簡潔に説明する文。

    Arrange:
        - 準備ステップの説明1
        - 準備ステップの説明2
    Act:
        - 実行ステップの説明
    Assert:
        - 検証ステップの説明1
        - 検証ステップの説明2
    """
```

## 3. テスト作成のベストプラクティス

### 3.1 フィクスチャの活用

共通のセットアップコードは pytest フィクスチャに抽出し、再利用しましょう：

```python
@pytest.fixture
def temp_dir():
    """ファイル操作のための一時ディレクトリを提供するフィクスチャ"""
    with TemporaryDirectory() as tempdir:
        yield tempdir
```

### 3.2 モックの適切な使用

外部依存関係は適切にモック化して、テストを分離しましょう：

```python
@pytest.fixture
def mock_write_setup(self, tmp_path):
    """書き込みテスト用の共通モックセットアップを提供するフィクスチャ"""
    with (
        mock.patch("minerva.tools.write_file") as mock_write_file,
        mock.patch("minerva.tools.VAULT_PATH", tmp_path),
    ):
        yield {"mock_write_file": mock_write_file, "tmp_path": tmp_path}
```

### 3.3 パラメータ化テスト

複数のテストケースを効率的にテストするには、パラメータ化テストを使用しましょう：

```python
@pytest.mark.parametrize(
    "filename,expected_message",
    [
        ("", "Filename cannot be empty"),
        ("/absolute/path/to/file.txt", "Filename cannot be an absolute path"),
    ],
)
def test_invalid_filename_validation(self, temp_dir, filename, expected_message):
    # テスト実装
```

### 3.4 テストの独立性

各テストは他のテストに依存せず、独立して実行できる必要があります。テスト間で状態を共有しないようにしましょう。

### 3.5 エッジケースのテスト

基本機能だけでなく、以下のようなエッジケースもテストしましょう：
- 空の入力
- 不正な入力
- 境界値
- リソース制約（大きなファイル、多数のファイルなど）

## 4. コードカバレッジ

Minervaプロジェクトでは、高いコードカバレッジを目指しています：

- 目標カバレッジ: 行カバレッジ 90%以上
- 現在の実績カバレッジ: 89%（2025年5月20日時点）
- カバレッジレポートの生成: `pytest --cov=minerva --cov-report=html`

カバレッジは量だけでなく質も重要です。重要なビジネスロジックや複雑な条件分岐は特に注意深くテストしましょう。

### 4.1 カバレッジ例外ファイル

以下のファイルはカバレッジ対象から除外またはカバレッジが低い状態で許容されています：

- **src/minerva/__main__.py** (0%): エントリーポイントであり、主にサーバー起動のみを行うためテスト対象外
- **src/minerva/server.py** (0%): MCPサーバー設定ファイルであり、統合テストでのみ検証

これらのファイルは主にインフラ層のコードであり、ビジネスロジックを含まないため、単体テストの対象外としています。

## 5. テスト実行

### 5.1 全テストの実行

```bash
pytest
```

### 5.2 特定のテストファイルの実行

```bash
pytest tests/test_file_handler.py
```

### 5.3 特定のテストメソッドの実行

```bash
pytest tests/test_file_handler.py::TestFileHandler::test_write_file_success
```

## 6. CI/CD との統合

継続的インテグレーションパイプラインでは、すべてのプルリクエストに対して自動的にテストが実行されます。テストが失敗した場合、プルリクエストはマージできません。

## 7. まとめ

テストは製品コードと同様に重要なアセットです。テストコードも読みやすく、メンテナンスしやすく、そして何よりも信頼性の高いものにしましょう。Arrange-Act-Assertパターンを一貫して適用することで、テストの意図と構造が明確になり、長期的なメンテナンス性が向上します。
