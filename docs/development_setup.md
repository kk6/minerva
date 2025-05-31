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

```
OBSIDIAN_VAULT_ROOT=<Obsidianのvaultルートディレクトリのパス>
DEFAULT_VAULT=<デフォルトで使用するvault名>
```

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

開発中は、定期的にテストを実行して、コードが正常に動作することを確認します：

```bash
uv run pytest
```

特定のテストを実行する場合：

```bash
uv run pytest tests/path/to/test.py::TestClass::test_method
```

カバレッジレポートを生成する場合：

```bash
uv run pytest --cov=minerva --cov-report=html
```

### 3. コードスタイルとリント

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
uv run mcp install src/minerva/server.py:mcp -f .env --with python-frontmatter
```

### ログの確認（MacOS）

```bash
tail -f ~/Library/Logs/Claude/mcp-server-minerva.log
```
