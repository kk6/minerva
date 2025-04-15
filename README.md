# Minerva

## MCP Inspector を起動する
```bash
uv run mcp dev server.py
```

## Claude Desktop にインストールする
```bash
uv run mcp install server.py
```

## Claude Desktop での使い方

チャットで「write_note を利用して今回の内容のMarkdownを書き出してください」とか入れれば使ってくれるはず

### 出力例
```
write_note 関数を使用して、先ほど作成したMarkdown文書を書き出します。

minerva(ローカル)からの write_note の結果を表示 >

Markdown文書を「web_development_best_practices.md」というファイル名で書き出しました。ファイルが正常に作成されたことが確認できました。このファイルには、先ほど作成したWebアプリケーション開発のベストプラクティスに関する内容が保存されています。
```
