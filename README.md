# Minerva

Minervaは、Claude Desktopと連携し、チャットからMarkdown文書の書き出しなどを自動化するツールです。

## プロジェクト概要

Minervaを使用すると、Obsidianのナレッジベース（Vault）内のMarkdownファイルを効率的に管理・操作できます。
Claude Desktopを通じて、以下の操作が可能です：

- Markdownファイルの新規作成（create_note）
- Markdownファイルの編集（edit_note）
- Markdownファイルの読取（read_note）
- Markdownファイル内のキーワード検索（search_notes）
- Markdownファイルの作成・更新（write_note）※後方互換性のため提供

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
uv run mcp dev src/minerva/server.py:mcp
```

## Claude Desktop にインストールする
```bash
uv run mcp install src/minerva/server.py:mcp -f .env --with python-frontmatter
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

## 将来の開発方針

Minervaは現在、基本的なノート操作（作成、読取、検索）をサポートしていますが、今後は以下の機能の実装を検討しています：

### 優先度：高（Must）
- **Front Matter 編集支援** - YAMLメタデータの構造を保った属性追加／変更
- **変更プレビュー／承認フロー** - ファイル変更前に差分を表示し確認する機能
- **バージョン履歴統合** - Git連携による変更履歴管理

### 優先度：中（Should）
- **一括リファクタリング** - ファイル名変更やフォルダ移動時のリンク整合性維持
- **要約／抄録生成** - 長文ノートの要約を自動生成しfrontmatterに追加
- **リンク候補提示** - 類似ノートの推薦と自動リンク
- **日次／週次テンプレート発行** - 日付ベースのノートテンプレート自動生成
- **タスク抽出 & 集計** - チェックボックスタスクの集計と表示
- **マークダウン整形リント** - 見出し階層やコードブロックなどの検査と修正

### 優先度：低（Could）
- **孤立ノート検出** - バックリンクがないノートの特定と連携提案
- **タグ階層自動整理** - タグの統合・階層化支援
- **自然言語→Dataview変換** - 自然言語からDataviewクエリの自動生成
- **メディア埋め込み支援** - 画像等の相対パス変換・キャプション挿入
- **カスタムコマンド登録** - ユーザー定義の操作をショートカットとして登録

Minervaの目標は、Claude Desktopと連携してObsidianの操作を自然言語で行える環境を構築し、知的生産の効率を高めることです。

## ドキュメント

詳細な仕様や開発ガイドラインについては、以下のドキュメントを参照してください：

- [要件定義書](docs/requirements.md) - プロジェクトの要件と仕様の詳細
- [ノート操作機能仕様書](docs/note_operations.md) - ノートの作成、読み取り、検索機能の詳細仕様
- [技術仕様書](docs/technical_spec.md) - 内部実装の詳細と設計思想
- [テストガイドライン](docs/test_guidelines.md) - テスト作成のガイドラインとAAA（Arrange-Act-Assert）パターンの解説
- [開発ワークフロー](docs/development_workflow.md) - 開発プロセス、ブランチ戦略、コードレビュー、リリースフロー
- [GitHub開発プロセス](docs/github_workflow.md) - GitHubを使用した開発プロセスの詳細
- [Issueと PR の効果的な活用ガイド](docs/issue_pr_guide.md) - IssueとPRの効果的な活用方法

## 開発ガイド

### Claude Desktop からの起動時の import エラーについて

Claude Desktop から Minerva サーバーを起動する場合、Python の import パス（sys.path）がコマンドライン実行時と異なるため、
`from minerva.tools import ...` のような絶対importで「No module named 'minerva'」エラーが発生することがあります。

この問題を回避するため、`server.py` の先頭で以下のように sys.path に親ディレクトリを追加しています。

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

これにより、コマンドライン実行・Claude Desktop どちらの環境でも minerva パッケージの import エラーが発生しなくなります。

## ライセンス

MIT
