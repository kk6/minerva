# Minerva 要件定義書

## 1. プロジェクト概要

### 1.1 背景と目的

Minervaは、Claude Desktopと連携し、Obsidianのナレッジベース（Vault）内のMarkdownファイルを効率的に管理・操作するためのツールです。本ツールにより、AIアシスタントとのチャットからMarkdownドキュメントの作成、検索、閲覧を自動化し、ナレッジ管理の効率を向上させることを目的としています。

### 1.2 ターゲットユーザー

- Obsidianをナレッジベースとして使用しているユーザー
- Claude Desktopを活用したい開発者や知識労働者
- AIと連携した文書管理の自動化を求めるユーザー

### 1.3 システム概要

Minervaは、Claude Desktop（MCPプラットフォーム）上で動作するツールとして実装されます。ユーザーはClaudeとのチャットインターフェースを通じて、ナレッジベース内のMarkdownファイルの操作（作成、読取、検索）を行うことができます。

## 2. 機能要件

### 2.1 核となる機能

#### 2.1.1 Markdownファイルの作成（write_note）
- Claudeとのチャットから直接Markdownファイルを作成できる
- ファイル名とコンテンツを指定可能
- 既存ファイルの上書きオプションを提供

#### 2.1.2 Markdownファイルの読取（read_note）
- 指定したMarkdownファイルの内容をClaudeチャット内で表示
- ファイルパスを指定して読み込み

#### 2.1.3 Markdownファイルの検索（search_notes）
- キーワードによるファイル検索機能
- 大文字小文字の区別設定オプションあり
- 検索結果にはファイルパス、該当行番号、コンテキスト情報を含む

### 2.2 追加機能（拡張性）

- 将来的にはObsidianのリンク構造を解析する機能の追加
- タグやプロパティに基づく高度な検索機能の実装
- タグのリストアップや分析機能
- ファイルの自動整理や構造化機能

## 3. 非機能要件

### 3.1 パフォーマンス要件

- 検索機能は大規模なVault（1000ファイル以上）でも1秒以内に結果を返す
- ファイル操作（読み書き）はユーザーの体感で遅延なく実行される

### 3.2 セキュリティ要件

- ローカルファイルシステムへのアクセスは指定されたVaultディレクトリ内に限定
- ファイル名にセキュリティリスク（パス・トラバーサルなど）となる文字を禁止
- バイナリファイルの誤読み込みを防止するための検出機能

### 3.3 互換性要件

- Python 3.12以上での動作保証
- Obsidianの標準的なVault構造との互換性確保
- Claude Desktop/MCPフレームワークとの連携

### 3.4 保守性・拡張性要件

- モジュール分割による機能の疎結合化
- 明確なエラーハンドリングと詳細なログ出力
- テスト自動化によるコード品質の確保

## 4. 技術仕様

### 4.1 システムアーキテクチャ

```
Minerva
├── MCPサーバー (FastMCP)
├── ツール実装 (tools.py)
│   ├── write_note
│   ├── read_note
│   └── search_notes
├── ファイル操作モジュール (file_handler.py)
└── 設定管理 (config.py)
```

### 4.2 技術スタック

- **言語**: Python 3.12以上
- **フレームワーク**: MCP (Claude Desktop連携用)
- **依存ライブラリ**:
  - mcp[cli] >= 1.6.0: Claude Desktopとの連携
  - pydantic >= 2.11.3: データバリデーションと型チェック
  - python-dotenv >= 1.1.0: 環境変数の管理
- **開発・テスト用**:
  - pytest >= 8.3.5: 自動テスト
  - pytest-cov >= 6.1.1: コードカバレッジ確認

### 4.3 データモデル

#### 4.3.1 ファイル操作リクエスト

- `FileWriteRequest`: ファイル書き込み要求モデル
  - directory: 保存先ディレクトリパス
  - filename: ファイル名
  - content: ファイル内容
  - overwrite: 上書きフラグ

- `FileReadRequest`: ファイル読み込み要求モデル
  - directory: 読み込み元ディレクトリパス
  - filename: ファイル名

#### 4.3.2 検索関連

- `SearchConfig`: 検索設定モデル
  - directory: 検索対象ディレクトリ
  - keyword: 検索キーワード
  - case_sensitive: 大文字小文字区別フラグ
  - file_extensions: 検索対象ファイル拡張子リスト

- `SearchResult`: 検索結果モデル
  - file_path: ファイルパス
  - line_number: 検出行番号
  - context: 検出コンテキスト

## 5. 設定と環境

### 5.1 環境変数

- `OBSIDIAN_VAULT_ROOT`: Obsidianのvaultルートディレクトリのパス
- `DEFAULT_VAULT`: デフォルトで使用するvault名

### 5.2 セットアップ

1. 必要な環境変数を`.env`ファイルに設定
2. 依存パッケージのインストール: `uv` パッケージマネージャを使用
3. MCPサーバーの起動: `uv run mcp dev server.py`
4. Claude Desktopへのインストール: `uv run mcp install server.py --with python-frontmatter`

### 5.3 依存関係の管理

#### 5.3.1 プロジェクト開発環境と実行環境の違い

Minervaプロジェクトでは、以下の2つの異なる環境での依存関係管理を理解する必要があります：

1. **プロジェクト開発環境**：
   - `pyproject.toml`と`uv.lock`で管理
   - 開発、テスト、CI/CD環境で使用
   - `uv pip install -e .`などで依存関係をインストール

2. **Claude Desktop実行環境**：
   - `/Users/<ユーザー名>/Library/Application Support/Claude/claude_desktop_config.json`で設定
   - `uv run --with`コマンドによる一時的な実行環境
   - 明示的に必要なパッケージをすべて指定する必要あり

#### 5.3.2 Claude Desktop設定の例

```json
"minerva": {
  "command": "uv",
  "args": [
    "run",
    "--with",
    "mcp[cli],python-frontmatter",
    "mcp",
    "run",
    "/path/to/minerva/server.py"
  ]
}
```

重要: パッケージの**インストール名**（例: `python-frontmatter`）と**インポート名**（例: `import frontmatter`）が異なる場合があるため、両方の名前を正確に把握する必要があります。

## 6. テスト戦略

### 6.1 単体テスト

- 各ツール機能（write_note, read_note, search_notes）の単体テスト
- ファイル操作関連の例外ハンドリングテスト
- バリデーション機能の確認テスト

### 6.2 統合テスト

- MCPサーバーとの連携テスト
- Claude Desktopからの呼び出しシミュレーション

### 6.3 テスト自動化

- pytestによるテスト自動化
- カバレッジレポート生成

## 7. 運用・保守

### 7.1 ログ記録

- ログレベルの適切な設定
- 主要操作のログ記録（ファイル作成、読取、検索）
- エラー時の詳細ログ出力

### 7.2 エラーハンドリング

- ファイル関連のエラー（存在しないファイル、上書き、権限エラーなど）
- 検索関連のエラー（無効なキーワード、大規模ファイルなど）
- ユーザーへわかりやすいエラーメッセージの提供

## 8. 制約事項

- バイナリファイルやObsidianの特殊構文の一部は正確に処理できない可能性あり
- 特定の文字（`<>:"\/|?*`）をファイル名に使用不可
- Python 3.12以上の環境が必要

## 9. 今後のロードマップ

- Obsidianの高度な機能（埋め込み、リンク、メタデータなど）のサポート
- 複数Vaultの同時操作機能
- ファイル内容の更新・差分管理機能
- テンプレート機能の追加

## 10. 使用例

### 10.1 基本的な使用例

```
# ファイル作成例
write_note 関数を使用して、先ほど作成したMarkdown文書を書き出します。

minerva(ローカル)からの write_note の結果を表示 >

Markdown文書を「web_development_best_practices.md」というファイル名で書き出しました。
```

### 10.2 高度な使用例

```
# 検索と内容読み取りの連携例
search_notes関数でキーワード「Python」を含むファイルを検索し、最も関連性の高いファイルをread_note関数で表示する。

# 構造化ドキュメントの作成例
Claudeとの対話で得た情報をwrite_note関数を使って体系的なドキュメントとして保存し、ナレッジベースを充実させる。
```

## 11. 用語集

- **MCP**: Model Control Protocol - Claude Desktopが使用するツール連携のためのプロトコル
- **Vault**: Obsidianにおけるローカルのナレッジベースディレクトリ
- **Claude Desktop**: Anthropic社のAIアシスタント「Claude」のデスクトップアプリケーション
