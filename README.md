# Minerva

Minervaは、Claude Desktopと連携し、チャットからMarkdown文書の書き出しなどを自動化するツールです。

## 必要なもの

- Python 3.12 以上
- [uv](https://github.com/astral-sh/uv)

## インストール

依存パッケージがある場合は、事前にインストールしてください。

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

チャットで「write_note を利用して今回の内容のMarkdownを書き出してください」などと入力すると、MinervaがMarkdownファイルを書き出します。

### 出力例
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

## pytest

pytestを使用して、テストを実行することができます。

```bash
uv run pytest
```
