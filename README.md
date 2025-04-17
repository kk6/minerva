# Minerva

Minervaは、Claude Desktopと連携し、チャットからMarkdown文書の書き出しなどを自動化するツールです。

## プロジェクト概要

Minervaを使用すると、Obsidianのナレッジベース（Vault）内のMarkdownファイルを効率的に管理・操作できます。
Claude Desktopを通じて、以下の操作が可能です：

- Markdownファイルの作成（write_note）
- Markdownファイルの読取（read_note）
- Markdownファイル内のキーワード検索（search_notes）

## 必要なもの

- Python 3.12 以上
- [uv](https://github.com/astral-sh/uv)
- Claude Desktop（MCP対応版）

## 設定方法

保存パッケージがある場合は、事前にインストールしてください。

### 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、以下の環境変数を設定します：

```
OBSIDIAN_VAULT_ROOT=<Obsidianのvaultルートディレクトリのパス>
DEFAULT_VAULT=<デフォルトで使用するvault名>
```

## MCP Inspector を起動する

プロジェクトルートで以下を実行してください。

```bash
uv run mcp dev server.py
```

## Claude Desktop にインストールする
```bash
uv run mcp install server.py
```

## Claude Desktop での使い方

チャットで「write_note を使用して今回の内容のMarkdownを書き出してください」などと入力すると、Minervaが指定されたフォルダにMarkdownファイルを書き出します。

### 使用例
```
write_note 関数を使用して、先ほど作成したMarkdown文書を書き出します。

minerva(ローカル)からの write_note の結果を表示 >

Markdown文書を「web_development_best_practices.md」というファイル名で書き出しました。ファイルが正常に作成されたことが確認できました。このファイルには、先ほど作成したWebアプリケーション開発のベストプラクティスに関する内容が保存されています。
```

## Claude Desktop のログの確認

MacOSの場合、以下のコマンドでログを確認できます。

```bash
tail -f ~/Library/Logs/Claude/mcp-server-minerva.log
```

## テスト実行

pytestを使用して、テストを実行することができます。

```bash
uv run pytest
```

## ドキュメント

詳細な仕様や開発ガイドラインについては、以下のドキュメントを参照してください：

- [要件定義書](docs/requirements.md) - プロジェクトの要件と仕様の詳細
- [ノート操作機能仕様書](docs/note_operations.md) - ノートの作成、読み取り、検索機能の詳細仕様
- [技術仕様書](docs/technical_spec.md) - 内部実装の詳細と設計思想
- [テストガイドライン](docs/test_guidelines.md) - テスト作成のガイドラインとAAA（Arrange-Act-Assert）パターンの解説
- [開発ワークフロー](docs/development_workflow.md) - 開発プロセス、ブランチ戦略、コードレビュー、リリースフロー
- [GitHub開発プロセス](docs/github_workflow.md) - GitHubを使用した開発プロセスの詳細
- [Issueと PR の効果的な活用ガイド](docs/issue_pr_guide.md) - IssueとPRの効果的な活用方法

## ライセンス

[ライセンス情報をここに記載]
