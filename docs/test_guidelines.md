# Minerva テストガイドライン

このドキュメントでは、Minervaプロジェクトにおけるテスト作成のガイドラインとベストプラクティスについて説明します。

## 1. テスト戦略

Minervaプロジェクトでは、以下のテスト戦略を採用しています：

1. **単体テスト**: 個別の関数やメソッドの動作を検証
2. **統合テスト**: 複数のコンポーネントが連携して動作することを検証
3. **例外テスト**: エラー条件とその処理が正しく機能することを検証
4. **Property-basedテスト**: Hypothesisを使用したエッジケースの自動発見

すべてのテストは `pytest` フレームワークを使用して実装し、モックやパラメータ化テストの機能を活用しています。

### 1.1 パフォーマンス最適化と pytest マーカー

Minervaでは、開発効率を高めるためにテストを以下のマーカーで分類しています：

#### マーカーの種類
- **`@pytest.mark.slow`**: 実行時間が長いテスト（MLモデル読み込み、大容量データ処理など）
- **`@pytest.mark.unit`**: 高速な単体テスト
- **`@pytest.mark.integration`**: 統合テスト

#### 実行パフォーマンス
- **高速テスト**: 487テストを約5秒で実行（日常開発用）
- **遅いテスト**: 5テストを約17秒で実行（MLモデル関連）
- **全体テスト**: 492テストを約22秒で実行

#### 実行コマンド
```bash
# 日常開発用（85%高速化）
make test-fast          # 遅いテストを除外
pytest -m "not slow"    # 直接実行

# 完全テスト
make test              # 全テスト実行
pytest                 # 直接実行

# 遅いテストのみ
make test-slow         # 遅いテストのみ
pytest -m "slow"       # 直接実行
```

#### マーカーの使用例
```python
@pytest.mark.slow
def test_embedding_generation():
    """MLモデルを使用する遅いテスト例"""
    provider = SentenceTransformerProvider()
    result = provider.embed("test text")
    assert isinstance(result, np.ndarray)

@pytest.mark.unit
def test_fast_validation():
    """高速な単体テスト例"""
    assert validate_filename("test.md") is True
```

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
    directory=str(tmp_path),
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
assert file_path == tmp_path / "test.txt"
assert file_path.exists()
content = file_path.read_text(encoding=ENCODING)
assert content == "Hello, World!"
```

### 2.2 例外テストの特別なケース

例外をテストする場合、Act と Assert は `pytest.raises` コンテキストマネージャーで結合されることがあります：

```python
# ==================== Act & Assert ====================
with pytest.raises(FileExistsError):
    write_file(request)
```

#### 例外テストでのハマりどころ ⚠️ **重要**

**問題**: `pytest.raises` が期待する例外をキャッチできない場合があります。特に以下のケースで発生します：

1. **カスタム例外の継承階層の問題**
2. **モジュールキャッシングによる例外クラスの不一致**
3. **例外が複数のレイヤーで変換される場合**

**解決策**: `try/except` を使った明示的な例外テスト：

```python
# 問題のあるテスト（pytest.raises が機能しない場合）
with pytest.raises(NoteNotFoundError):
    server.read_note("/non/existent/file.md")  # 失敗する可能性

# 推奨される解決策
try:
    server.read_note("/non/existent/file.md")
    assert False, "Expected an exception but none was raised"
except Exception as e:
    # 動的インポートで正しい例外クラスを取得
    from minerva.exceptions import NoteNotFoundError as MinervaNotFoundError
    assert isinstance(e, (FileNotFoundError, MinervaNotFoundError)), f"Unexpected exception type: {type(e)}"
```

**重要なポイント**:
- テスト内での動的インポートで例外クラスの不一致を回避
- 複数の例外タイプを許可する（継承関係やエラーハンドラーによる変換を考慮）
- 詳細なエラーメッセージで実際の例外タイプを表示
- 例外が発生しない場合の明示的な失敗

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

### 3.1 MinervaTestHelperの使用 ⭐ **推奨**

新しくテストを作成する際は、統一されたテストヘルパークラス `MinervaTestHelper` を使用してください：

```python
from tests.helpers import MinervaTestHelper

def test_create_note_with_helper(tmp_path, minerva_test_helper):
    """統一されたヘルパーを使用したテスト例."""
    # ==================== Arrange ====================
    content = "Test note content"
    frontmatter_data = {"tags": ["test"], "author": "Test Author"}

    # ==================== Act ====================
    note_path = minerva_test_helper.create_temp_note(
        tmp_path,
        "test_note.md",
        content,
        frontmatter_data
    )

    # ==================== Assert ====================
    minerva_test_helper.assert_note_content(note_path, content, frontmatter_data)
    minerva_test_helper.assert_frontmatter_fields(
        note_path,
        {"tags": list, "author": str}
    )
```

#### 主なメソッド：
- `create_temp_note()`: テスト用ノートの作成
- `assert_note_content()`: ノート内容の検証
- `assert_frontmatter_fields()`: フロントマターフィールドの検証
- `setup_test_vault()`: テスト用Vault環境の初期化
- `create_sample_notes()`: サンプルノートの作成

#### 共通フィクスチャ：
- `minerva_test_helper`: MinervaTestHelperのインスタンス
- `test_vault`: 標準的なVault構造を持つテスト環境
- `sample_notes`: テスト用サンプルノート

### 3.2 フィクスチャの活用

共通のセットアップコードは pytest フィクスチャに抽出し、再利用しましょう：

```python
# 推奨: pytest標準のtmp_pathフィクスチャを使用
def test_file_operation(tmp_path):
    """標準のtmp_pathフィクスチャを使用した例"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content", encoding="utf-8")
    assert file_path.exists()
```

### 3.3 モックの適切な使用

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

#### 3.3.1 モンキーパッチングのベストプラクティス ⭐ **推奨**

テスト内で関数やメソッドをモックする際は、pytestの `monkeypatch` フィクスチャを使用してください：

```python
# ❌ 避けるべき: 手動でMonkeyPatchインスタンスを作成
def test_with_manual_monkeypatch(self):
    with pytest.MonkeyPatch().context() as m:
        m.setattr("module.function", mock_function)
        # テスト実装

# ✅ 推奨: monkeypatchフィクスチャを使用
def test_with_monkeypatch_fixture(self, monkeypatch):
    monkeypatch.setattr("module.function", mock_function)
    # テスト実装
```

**メリット**:
- **自動スコープ管理**: テスト終了時に自動的にパッチが元に戻される
- **コードの簡素化**: ネストしたコンテキストマネージャーが不要
- **pytestベストプラクティス**: 標準的なpytestパターンに準拠
- **可読性の向上**: より明確で読みやすいテストコード

**Property-based testingでの使用例**:
```python
@given(st.text(min_size=1, max_size=50))
def test_with_hypothesis_and_monkeypatch(self, query: str, monkeypatch):
    """Hypothesisとmonkeypatchフィクスチャの組み合わせ例"""
    monkeypatch.setattr(
        "minerva.services.search_operations.search_keyword_in_files",
        lambda *args, **kwargs: []
    )
    # テスト実装
```

### 3.4 パラメータ化テスト

複数のテストケースを効率的にテストするには、パラメータ化テストを使用しましょう：

```python
@pytest.mark.parametrize(
    "filename,expected_message",
    [
        ("", "Filename cannot be empty"),
        ("/absolute/path/to/file.txt", "Filename cannot be an absolute path"),
    ],
)
def test_invalid_filename_validation(self, tmp_path, filename, expected_message):
    # テスト実装
```

### 3.5 テストの独立性

各テストは他のテストに依存せず、独立して実行できる必要があります。テスト間で状態を共有しないようにしましょう。

#### 3.5.1 モジュールキャッシングの問題と対策 ⚠️ **重要**

Pythonのモジュールキャッシング機能により、テスト間でモジュールの状態が共有されてしまう問題があります。特に、以下のような場合に問題が発生します：

**問題のケース**:
- 環境変数を `patch.dict()` で変更するテスト
- モジュールレベルでサービスやオブジェクトを初期化するコード
- 複数のテストが同じモジュールをインポートする場合

**具体的な問題例**:
```python
# 問題のあるテスト例
def test_with_different_env():
    with patch.dict(os.environ, {"VAULT_PATH": "/test/path"}):
        from minerva import server  # モジュールが既にキャッシュされている場合、
                                   # 新しい環境変数が反映されない
        # テストが期待通りに動作しない
```

**解決策 - モジュールキャッシュのクリア**:

テスト環境の分離を確実にするため、テスト前にモジュールキャッシュをクリアします：

```python
def test_with_fresh_module():
    with patch.dict(os.environ, {"VAULT_PATH": "/test/path"}):
        # 関連するモジュールキャッシュをクリア
        sys.modules.pop("minerva.server", None)
        sys.modules.pop("minerva.service", None)
        sys.modules.pop("minerva.config", None)

        from minerva import server  # noqa: E402
        # これで新しい環境変数が正しく反映される
```

**フィクスチャでの実装例**:
```python
@pytest.fixture
def temp_vault_env(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"VAULT_ROOT": tmpdir}):
            # モジュールキャッシュをクリア
            modules_to_clear = [
                "minerva.server",
                "minerva.service",
                "minerva.config"
            ]
            for module in modules_to_clear:
                sys.modules.pop(module, None)

            from minerva import server  # noqa: E402
            yield server
```

**重要なポイント**:
- モジュールキャッシュクリアは環境変数パッチング**前**に行う
- 依存関係のあるモジュールも合わせてクリアする
- `# noqa: E402` コメントで import の位置警告を抑制する
- 全てのminerva関連モジュールをクリアする場合：
  ```python
  modules_to_clear = [name for name in sys.modules.keys() if name.startswith("minerva")]
  for module in modules_to_clear:
      sys.modules.pop(module, None)
  ```

### 3.6 エッジケースのテスト

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

## 5. テスト環境の自動制御

### 5.1 環境変数の自動管理

Minervaのテストは、実際のObsidian保管庫に影響を与えることなく安全に実行されるよう設計されています。この機能は以下の仕組みで実現されています：

#### 自動的なテスト環境検出

`conftest.py`で`MINERVA_SKIP_DOTENV=1`が自動的に設定され、テスト実行時に`.env`ファイルの読み込みが無効化されます：

```python
@pytest.fixture(scope="session", autouse=True)
def skip_dotenv_in_tests():
    """Automatically skip .env loading during all tests."""
    os.environ["MINERVA_SKIP_DOTENV"] = "1"
    yield
    # Cleanup after tests
    os.environ.pop("MINERVA_SKIP_DOTENV", None)
```

#### 遅延サービス初期化

`server.py`では遅延初期化パターンを採用し、テスト時の環境変数パッチが確実に反映されるようになっています：

```python
# テスト用の遅延初期化
def get_service():
    global service
    if service is None:
        service = create_minerva_service()
    return service
```

#### CI/CDでの環境変数制御

CI/CDパイプラインでは、明示的に`MINERVA_SKIP_DOTENV=1`を設定することで、`.env`ファイルに依存しない実行が可能です：

```bash
# GitHub Actions例
env:
  MINERVA_SKIP_DOTENV: "1"
  OBSIDIAN_VAULT_ROOT: "/tmp/test-vault"
  DEFAULT_VAULT: "test"
```

### 5.2 テスト隔離の改善

この改善により、以下の問題が解決されました：

- ✅ テスト実行時に実際のObsidian保管庫にファイルが作成されない
- ✅ 環境変数のパッチが確実に反映される
- ✅ 異なるテスト環境（ローカル、CI/CD）での一貫した動作
- ✅ モジュールキャッシュ問題の大幅な軽減

## 6. テスト実行

### 6.1 全テストの実行

```bash
pytest
```

### 6.2 特定のテストファイルの実行

```bash
pytest tests/test_file_handler.py
```

### 6.3 特定のテストメソッドの実行

```bash
pytest tests/test_file_handler.py::TestFileHandler::test_write_file_success
```

### 6.4 マーカーベースのテスト実行

```bash
# 高速テストのみ実行（日常開発用）
pytest -m "not slow"
make test-fast

# 遅いテストのみ実行（CI/リリース前確認用）
pytest -m "slow"
make test-slow

# 単体テストのみ実行
pytest -m "unit"

# 統合テストのみ実行
pytest -m "integration"

# 複数マーカーの組み合わせ
pytest -m "unit and not slow"  # 高速な単体テストのみ
pytest -m "integration or slow"  # 統合テストまたは遅いテスト
```

### 6.5 開発ワークフローでの使い分け

#### 日常開発時
```bash
make test-fast    # または pytest -m "not slow"
```
- **実行時間**: 約5秒
- **対象**: 487テスト（遅いテスト5個を除外）
- **用途**: コード変更後の迅速なフィードバック

#### プルリクエスト前/CI実行時
```bash
make test         # または pytest
```
- **実行時間**: 約22秒
- **対象**: 492テスト（全テスト）
- **用途**: 完全な動作確認

#### CI/CDでの最適化
```bash
# 段階実行でより早いフィードバック
make test-fast    # 第1段階: 高速テスト
make test-slow    # 第2段階: 遅いテスト（並列実行可能）
```

## 7. CI/CD との統合

継続的インテグレーションパイプラインでは、すべてのプルリクエストに対して自動的にテストが実行されます。テストが失敗した場合、プルリクエストはマージできません。

### 7.1 CI/CDでのパフォーマンス最適化

マーカーベースのテスト実行により、CI/CDパイプラインでも効率的なフィードバックループを実現できます：

#### 段階実行戦略
```yaml
# GitHub Actions例
jobs:
  fast-tests:
    name: "Fast Tests (Unit & Integration)"
    runs-on: ubuntu-latest
    steps:
      - name: Run fast tests
        run: pytest -m "not slow"
        # 5秒で487テストを実行、早期フィードバック

  slow-tests:
    name: "Slow Tests (ML & Heavy Processing)"
    runs-on: ubuntu-latest
    needs: fast-tests  # 高速テスト成功後に実行
    steps:
      - name: Run slow tests
        run: pytest -m "slow"
        # 17秒で5テストを実行
```

#### メリット
- **早期フィードバック**: 基本的なエラーを5秒で検出
- **並列実行**: 高速テストと遅いテストを並列実行可能
- **リソース効率**: 高速テストが失敗した場合、遅いテストをスキップ
- **開発者体験**: プルリクエストでの迅速なエラー通知

## 8. テストマーカーのガイドライン

### 8.1 slow マーカーを使用すべきケース

以下の条件に該当するテストには `@pytest.mark.slow` を付与してください：

- **MLモデルの読み込み**: SentenceTransformerなどの機械学習モデル
- **大容量データ処理**: 大きなファイルやデータセットの処理
- **外部サービス呼び出し**: APIコールやデータベース接続
- **実行時間が3秒以上**: 経験的な閾値

```python
@pytest.mark.slow
def test_vector_embedding_real():
    """実際のMLモデルを使用する遅いテスト"""
    provider = SentenceTransformerProvider()
    result = provider.embed("test text")
    assert result.shape[1] > 0
```

### 8.2 fast テストの設計指針

高速テストを維持するための設計指針：

- **モック活用**: 外部依存関係はモックで代替
- **単純データ**: 最小限のテストデータを使用
- **分離テスト**: 1テスト1責任で設計

```python
def test_embedding_provider_init():
    """初期化のみをテストする高速テスト"""
    provider = SentenceTransformerProvider("test-model")
    assert provider.model_name == "test-model"
    assert provider._model is None  # モデル未読み込み状態
```

### 8.3 マーカー付与の判断基準

| 実行時間 | マーカー | 用途 | 例 |
|---------|---------|------|----|
| < 1秒 | なし（または `unit`） | 日常開発 | バリデーション、計算ロジック |
| 1-3秒 | `integration` | 統合確認 | ファイルI/O、サービス連携 |
| > 3秒 | `slow` | CI/リリース前 | MLモデル、大容量処理 |

## 9. 新しいテスト

### 9.1 サーバーテスト (`test_server.py`)

サーバーモジュールのテストが追加され、MCP (Model Context Protocol) サーバーが適切に設定され、すべてのツールが正しく登録されていることを検証します。

```python
def test_server_initialization():
    """Test that the MCP server initializes correctly."""
    # ツールが登録されていることを確認
    assert hasattr(mcp, "tools")
    assert len(mcp.tools) > 0

    # 必要なツールがすべて登録されていることを確認
    tool_functions = [t.function for t in mcp.tools]
    assert read_note in tool_functions
    assert search_notes in tool_functions
    assert create_note in tool_functions
    assert edit_note in tool_functions
    assert get_note_delete_confirmation in tool_functions
    assert perform_note_delete in tool_functions
```

### 9.2 プライベート関数テスト (`test_private_functions.py`)

内部ヘルパー関数のテストが追加され、これらの関数が期待通りに動作することを検証します。これは特に、コードの広範な改善と整理に関連して重要です。

```python
def test_read_existing_frontmatter_with_datetime():
    """Test that datetime values in frontmatter are converted to ISO format strings."""
    # テスト用の日付を含むfrontmatterファイルを作成
    mock_date = datetime(2025, 5, 1, 12, 30, 45)
    post = frontmatter.Post("Test content")
    post.metadata["created"] = mock_date

    # 一時ファイルに書き込み
    temp_file = tmp_path / "date_test.md"
    with open(temp_file, "w") as f:
        f.write(frontmatter.dumps(post))

    # 関数を実行
    metadata = _read_existing_frontmatter(temp_file)

    # datetimeがISO文字列に変換されたことを確認
    assert isinstance(metadata["created"], str)
    assert metadata["created"] == mock_date.isoformat()
```

### 9.3 エラー処理テスト

エラー処理機能の改善に伴い、対応するテストも強化されました。特に、ファイル名のバリデーションと適切なエラーメッセージに焦点を当てています。

```python
def test_empty_filename_validation():
    """Test that empty filenames are properly rejected."""
    # 空のファイル名でリクエストを作成
    with pytest.raises(ValueError, match="Filename cannot be empty"):
        WriteNoteRequest(text="Content", filename="")

    # 空のパス部分を持つファイル名でも検証
    with pytest.raises(ValueError, match="Filename cannot be empty"):
        full_dir_path, base_filename = _build_file_path("path/to/")
```

### 9.4 メインメソッドテスト (`test_main.py`)

アプリケーションのエントリーポイントとしての`__main__.py`の機能をテストします。このテストは、コマンドラインからアプリケーションが正しく起動されることを検証します。

## 10. 既存テストの移行ガイドライン

### 10.1 段階的移行アプローチ

既存のテストファイルは一度にすべて移行するのではなく、段階的に移行することを推奨します：

1. **新しいテスト**: `MinervaTestHelper` を使用して作成
2. **メンテナンス時**: 既存テストを修正する際に新しいパターンへ移行
3. **リファクタリング時**: 大幅な変更が必要な場合に移行

### 10.2 移行例

従来のパターンから新しいパターンへの移行例：

```python
# === 従来のパターン ===
def test_create_note_old_style(tmp_path):
    file_path = tmp_path / "test.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Test content")

    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8")
    assert content == "Test content"

# === 新しいパターン ===
def test_create_note_new_style(tmp_path, minerva_test_helper):
    note_path = minerva_test_helper.create_temp_note(
        tmp_path, "test.md", "Test content"
    )

    minerva_test_helper.assert_file_exists(note_path)
    minerva_test_helper.assert_note_content(note_path, "Test content")
```

### 10.3 後方互換性

新しいヘルパーは既存のフィクスチャと共存できるよう設計されています。既存のテストが期待通りに動作することを確認してください。

## 11. まとめ

テストは製品コードと同様に重要なアセットです。テストコードも読みやすく、メンテナンスしやすく、そして何よりも信頼性の高いものにしましょう。Arrange-Act-Assertパターンを一貫して適用することで、テストの意図と構造が明確になり、長期的なメンテナンス性が向上します。

**新しいテストを作成する際は、必ず `MinervaTestHelper` の使用を検討してください。** これにより、テストコードの一貫性と保守性が大幅に向上します。
