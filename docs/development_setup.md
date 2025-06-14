# 開発環境セットアップガイド

このドキュメントは、Minervaプロジェクトの開発環境セットアップと、一般的な開発ワークフローについて説明します。

## 前提条件

- Python 3.12以上
- [uv](https://github.com/astral-sh/uv) - 依存関係管理とパッケージインストール用

## 環境セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/minerva.git
cd minerva
```

### 2. 開発用依存関係のインストール

#### Makefileを使用（推奨）

```bash
# 依存関係のインストール
make install

# 開発環境の完全セットアップ（依存関係インストール + pre-commit設定）
make setup-dev
```

#### 直接uvコマンドを使用

```bash
uv pip install -e ".[dev]"
```

これにより、プロジェクトとその開発用依存関係がインストールされます。

### 3. 環境変数の設定

`.env.example`ファイルをコピーして`.env`ファイルを作成し、必要な環境変数を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の変数を設定します：

#### 必須環境変数
```
OBSIDIAN_VAULT_ROOT=<Obsidianのvaultルートディレクトリのパス>
DEFAULT_VAULT=<デフォルトで使用するvault名>
```

#### 開発・テスト用オプション環境変数
```
# テスト実行時は自動的に設定されるため、通常は設定不要
# CI/CDや特殊なテスト環境で.envファイルの読み込みを無効化する場合のみ設定
MINERVA_SKIP_DOTENV=1

# ベクター検索機能（オプション、Phase 1実装済み）
VECTOR_SEARCH_ENABLED=false  # "true"でセマンティック検索機能を有効化
VECTOR_DB_PATH=/custom/path/to/vectors.db  # カスタムベクターDB保存場所（オプション）
EMBEDDING_MODEL=all-MiniLM-L6-v2  # テキスト埋め込みモデル（オプション）
```

**注意**:
- `MINERVA_SKIP_DOTENV`は通常の開発では設定不要。pytestが自動的にテスト環境を検出し制御します。
- **ベクター検索機能**はPhase 1が完成しており、オプションで有効化可能です。

### 4. pre-commit フックのセットアップ

pre-commitを使用して、コミット前に自動的にコードスタイルのチェックと修正を行います。

```bash
# 開発依存関係として pre-commit をインストール（まだインストールしていない場合）
uv add --dev pre-commit

# pre-commit フックの設定
pre-commit install
```

これにより、コミット前に以下のチェックが自動的に実行されます：
- トレイリングスペース（行末の余分なスペース）の削除
- ファイル末尾の改行の確認
- 混合行末の修正（CRLF→LF）
- Ruff によるコードの自動フォーマットとリント
- カスタムトレイリングスペースチェック

手動でpre-commitフックを実行する場合は、以下のコマンドを使用します：

```bash
pre-commit run --all-files
```

## 開発ワークフロー

### 1. ブランチの作成

新機能や修正を開発する場合は、常に新しいブランチを作成します：

```bash
git checkout -b feature/your-feature-name
```

または

```bash
git checkout -b fix/your-fix-name
```

### 2. テストの実行

開発中は、定期的にテストを実行して、コードが正常に動作することを確認します。

#### 日常開発用（推奨）
```bash
# Makefileを使用（推奨）
make test-fast          # 高速テスト（約5秒、487テスト）

# または直接pytestを使用
pytest -m "not slow"    # 遅いテストを除外
```

**メリット**: 遅いMLモデルテストを除外して、85%の速度向上を実現。コード変更後の迅速なフィードバックに最適。

#### 完全テスト（プルリクエスト前）
```bash
# Makefileを使用（推奨）
make test               # 全テスト（約22秒、492テスト）

# または直接pytestを使用
uv run pytest           # 全テスト実行
```

#### 特定テストの実行
```bash
# 特定のテストファイル
pytest tests/test_specific.py

# 特定のテストメソッド
pytest tests/path/to/test.py::TestClass::test_method

# 遅いテストのみ実行（MLモデルテストなど）
make test-slow          # または pytest -m "slow"
```

#### カバレッジレポート
```bash
make test-cov                                                    # Makefileを使用
pytest --cov=minerva --cov-report=html --cov-report=term        # 直接実行
```

#### テストパフォーマンスガイド
- **日常開発**: `make test-fast` を使用して迅速なフィードバックを得る
- **プルリクエスト前**: `make test` で完全なテストを実行
- **CI/CD**: 段階実行で早期エラー検出とリソース効率化を実現

### 3. コード品質チェック

#### 日常開発用（高速）
```bash
make check-fast         # リント + 型チェック + 高速テスト（約6秒）
```

#### 完全チェック（プルリクエスト前）
```bash
make check-all          # リント + 型チェック + 全テスト（約23秒）
```

#### 個別チェック
```bash
# リントチェック
make lint               # または uv run ruff check

# 型チェック
make type-check         # または uv run mypy src tests

# コードフォーマット
make format             # または uv run ruff format

# トレイリングスペース修正
make fix-whitespace     # pre-commitフックを使用した安全な修正
```

コードスタイルとリントを確認するには：

```bash
# リント
uv run ruff check src/ tests/

# フォーマット
uv run ruff format src/ tests/

# 型チェック
uv run mypy src tests
```

### 4. トレイリングスペースのチェック

ファイル内のトレイリングスペースをチェックするには：

```bash
python scripts/check_trailing_whitespace.py
```

トレイリングスペースを自動的に修正するには：

```bash
find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) \
  -not -path "*/.git/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.venv/*" \
  -not -path "*/venv/*" \
  -not -path "*/.egg-info/*" \
  -exec sed -i 's/[ \t]*$//' {} \;
```

### 5. コミット

変更をコミットする前に、pre-commitフックが自動的に実行されます。問題がある場合は修正してから再度コミットしてください。

```bash
git add .
git commit -m "feat(component): your meaningful commit message"
```

コミットメッセージは[Conventional Commits](https://www.conventionalcommits.org/)形式に従ってください。

### 6. プルリクエスト

開発が完了したら、GitHubにプッシュしてプルリクエストを作成します：

```bash
git push origin feature/your-feature-name
```

## 問題が発生した場合

### pre-commitフックのスキップ

緊急時に一時的にpre-commitフックをスキップする必要がある場合：

```bash
git commit -m "your message" --no-verify
```

ただし、これはGitHub Actions CIチェックを通過しない可能性があるため、通常は避けてください。

## その他の開発コマンド

### MCP Inspectorの起動

```bash
uv run mcp dev src/minerva/server.py:mcp
```

### Claude Desktopへのインストール

```bash
uv run mcp install src/minerva/server.py:mcp -f .env --with-editable .
```

**重要**: `--with-editable .` オプションにより、プロジェクトをeditable modeでインストールします。これにより、Claude Desktop環境でも`minerva`パッケージとその依存関係が適切に認識されます。

### ログの確認（MacOS）

```bash
tail -f ~/Library/Logs/Claude/mcp-server-minerva.log
```
