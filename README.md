# Minerva

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/kk6/minerva)

Minervaは、Claude Desktopと連携し、チャットからMarkdown文書の書き出しなどを自動化するツールです。

## プロジェクト概要

Minervaを使用すると、Obsidianのナレッジベース（Vault）内のMarkdownファイルを効率的に管理・操作できます。
Claude Desktopを通じて、以下の操作が可能です：

### 基本操作
- Markdownファイルの新規作成（create_note）
- Markdownファイルの編集（edit_note）
- Markdownファイルの読取（read_note）
- Markdownファイル内のキーワード検索（search_notes）
- Markdownファイルの削除（2段階プロセス: get_note_delete_confirmation, perform_note_delete）

### タグ管理機能
- タグの追加（add_tag）
- タグの削除（remove_tag）
- タグの名前変更（rename_tag）
- タグの取得（get_tags）
- 全タグのリスト取得（list_all_tags）
- タグによるノート検索（find_notes_with_tag）

### エイリアス管理機能
- エイリアスの追加（add_alias）
- エイリアスの削除（remove_alias）
- エイリアスの取得（get_aliases）
- エイリアスによるノート検索（search_by_alias）

### セマンティック検索機能（v0.15.0以降）
- ベクターインデックスの構築（build_vector_index）
- セマンティック検索によるノート発見（semantic_search）
- インデックス状況確認（get_vector_index_status）
- 小規模バッチ処理（build_vector_index_batch）
- ベクターデータベースのリセット（reset_vector_database）

## 必要なもの

- Python 3.12 以上
- [uv](https://github.com/astral-sh/uv)
- Claude Desktop（MCP対応版）

### オプション依存関係
セマンティック検索機能を使用する場合の追加要件：
- DuckDB 1.1.3以上（ベクターデータベース、VSS拡張機能付き）
- sentence-transformers 3.3.1以上（テキスト埋め込み生成）
- numpy 1.24.0以上（数値計算とベクター操作）

注意：これらの依存関係は`VECTOR_SEARCH_ENABLED=true`に設定した場合のみ必要です。セマンティック検索を使用しない場合、標準的なキーワード検索は引き続き利用可能です。

## 設定方法

保存パッケージがある場合は、事前にインストールしてください。

### 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、以下の環境変数を設定します：

#### 必須環境変数
```
OBSIDIAN_VAULT_ROOT=<Obsidianのvaultルートディレクトリのパス>
DEFAULT_VAULT=<デフォルトで使用するvault名>
```

#### オプション環境変数
```
# テスト環境やCI/CDで.envファイルの読み込みをスキップする場合
MINERVA_SKIP_DOTENV=1

# セマンティック検索機能（オプション）
VECTOR_SEARCH_ENABLED=false  # "true"でセマンティック検索機能を有効化
VECTOR_DB_PATH=/custom/path/to/vectors.db  # カスタムベクターDB保存場所（省略時: {vault}/.minerva/vectors.db）
EMBEDDING_MODEL=all-MiniLM-L6-v2  # テキスト埋め込みモデル（384次元、省略時: all-MiniLM-L6-v2）
```

### pre-commit フックの設定

コードの品質を維持するために、pre-commit フックを設定することをお勧めします。これにより、コミット前に自動的にコードスタイルのチェックや修正が行われ、CI/CDでのエラーを防げます。

```bash
# pre-commit のインストール（開発依存関係として）
uv add --dev pre-commit

# pre-commit フックの設定
pre-commit install
```

pre-commit は以下のチェックを自動的に実行します：
- **トレイリングスペース（行末の余分なスペース）の削除** - プルリクエストでよく発生する問題を防止
- ファイル末尾の改行の確認
- 混合行末の修正（CRLF→LF）
- YAMLとTOMLファイルの構文チェック
- Ruff によるPythonコードの自動フォーマットとリント

詳細な設定とトラブルシューティングについては、[Pre-commit Setup Guide](docs/pre-commit-guide.md) を参照してください。

## 開発環境のセットアップ

### Makefileを使用した開発（推奨）

Minervaでは開発タスクの統一的なインターフェースとして、Makefileを提供しています。

```bash
# 利用可能なコマンドを表示
make help

# 依存関係のインストール
make install

# 開発環境のセットアップ
make setup-dev

# ビルドアーティファクトのクリーンアップ
make clean

# テストの実行
make test

# 高速テストのみ実行（遅いテストを除外、日常開発用）
make test-fast

# 遅いテストのみ実行（ML処理など、CI/リリース前用）
make test-slow

# カバレッジ付きテスト
make test-cov

# Property-basedテストのみ実行
uv run pytest tests/*_properties.py

# コードの品質チェック（lint、type-check、testを一括実行）
make check-all

# 高速品質チェック（遅いテストを除外、日常開発用）
make check-fast
```

### MCP Inspector を起動する

プロジェクトルートで以下を実行してください。

```bash
# Makefileを使用（推奨）
make dev

# または直接uvコマンドを使用
uv run mcp dev src/minerva/server.py:mcp
```

## Claude Desktop にインストールする

`-f .env` フラグは、環境変数を設定するための `.env` ファイルを指定します。このファイルには、プロジェクトの設定に必要な変数が含まれています。
```bash
uv run mcp install src/minerva/server.py:mcp -f .env --with-editable .
```

**重要**: `--with-editable .` オプションにより、プロジェクトをeditable modeでインストールします。これにより、Claude Desktop環境でも`minerva`パッケージとその依存関係（`python-frontmatter`など）が適切に認識されます。

## Claude Desktop での使い方

チャットで以下のような指示を入力することで、各種機能を利用できます：

### 基本的な使用例

#### ノートの作成
```
create_note 関数を使用して、この会話内容からMarkdownノートを作成してください。ファイル名は「meeting_notes」としてください。
```

#### ノートの編集
```
edit_note 関数を使用して、先ほど作成した「meeting_notes」ノートに追加情報を記載してください。
```

#### ノートの読み取り
```
read_note 関数で「research_ideas」ファイルの内容を確認してください。
```

#### ノートの検索
```
search_notes 関数を使用して「マイクロサービス」というキーワードを含むノートを検索してください。
```

#### タグ管理（v0.2.0以降）
```
add_tag 関数を使って「meeting_notes」ファイルに「project」タグを追加してください。
```

#### エイリアス管理（v0.9.2以降）
```
add_alias 関数を使って「project_notes」ファイルに「プロジェクトα」エイリアスを追加してください。
```

```
search_by_alias 関数を使って「会議メモ」というエイリアスでノートを検索してください。
```

#### セマンティック検索（v0.15.0以降）
```text
ベクターインデックスを構築してセマンティック検索を有効にしてください。まず build_vector_index を実行してからsemantic_search で「機械学習」に関連するノートを探してください。
```

```text
semantic_search 関数を使って「プロジェクト管理」に関連するノートを類似度0.7以上で5件まで検索してください。
```

## Claude Desktop のログの確認

MacOSの場合、以下のコマンドでログを確認できます。

```bash
tail -f ~/Library/Logs/Claude/mcp-server-minerva.log
```

## テスト実行

pytestを使用して、テストを実行することができます。

```bash
# Makefileを使用（推奨）
make test          # 全テスト実行
make test-fast     # 高速テスト（日常開発用、約5秒）
make test-slow     # 遅いテスト（MLモデル読み込みなど、約17秒）

# カバレッジ付きテスト
make test-cov

# または直接uvコマンドを使用
uv run pytest                    # 全テスト実行
uv run pytest -m "not slow"      # 高速テストのみ
uv run pytest -m "slow"          # 遅いテストのみ
```

## 現在のバージョン

Minervaの現在のバージョンは `v0.15.0` です。詳細な変更履歴については[CHANGELOG.md](CHANGELOG.md)を参照してください。

## 将来の開発方針

Minervaは現在、基本的なノート操作（作成、読取、検索）と高度なタグ管理機能をサポートしていますが、今後は以下の機能の実装を検討しています：

### 優先度：高（Must）
- [x] **タグ管理機能** - タグの追加・削除・リネーム・検索など（v0.2.0で実装済み）
- [x] **スマートエイリアス機能** - 複数のエイリアス（別名）でノートを参照（v0.9.2で実装済み）
- [✅] **セマンティック検索機能** - ベクター埋め込みによる意味的類似度検索でノート発見支援（v0.15.0で実装完了：埋め込み生成・ベクターインデックス・DuckDB VSS統合・セマンティック検索・MCP統合）
- [ ] **Front Matter 編集支援** - YAMLメタデータの構造を保った属性追加／変更
- [x] **変更プレビュー／承認フロー** - ファイル変更前に差分を表示し確認する機能
- [ ] **バージョン履歴統合** - Git連携による変更履歴管理
- [ ] **要約／抄録生成** - 長文ノートの要約を自動生成しfrontmatterに追加
- [ ] **ノートのアーカイブ機能** - 古いノートを別ディレクトリに移動しつつ、リンクを維持

### 優先度：中（Should）
- [x] **ノート削除機能の強化** - 2段階削除プロセスの実装（v0.2.0で実装済み）
- [ ] **一括リファクタリング** - ファイル名変更やフォルダ移動時のリンク整合性維持
- [ ] **日次／週次テンプレート発行** - 日付ベースのノートテンプレート自動生成
- [ ] **タスク抽出 & 集計** - チェックボックスタスクの集計と表示
- [ ] **マークダウン整形リント** - 見出し階層やコードブロックなどの検査と修正
- [ ] **ノート間の重複検出** - 類似内容のノートを検出して統合を提案
- [ ] **定期レビュー支援** - 最終更新から一定期間経過したノートをリストアップ
- [ ] **ノートのマージ機能** - 複数のノートを1つに統合

### 優先度：低（Could）
- [ ] **孤立ノート検出** - バックリンクがないノートの特定と連携提案
- [ ] **メディア埋め込み支援** - 画像等の相対パス変換・キャプション挿入
- [ ] **カスタムコマンド登録** - ユーザー定義の操作をショートカットとして登録
- [ ] **ノートの一括エクスポート機能** - 特定条件でノートを選択してまとめてエクスポート
- [ ] **ノートの分割機能** - 長大なノートを見出しベースで複数のノートに分割

実装を推奨しない項目（Not Recommended）

- [ ] **リンク候補提示** - 類似ノートの推薦と自動リンク（実装の複雑さと誤提案のリスク）
- [ ] **タグ階層自動整理** - タグの統合・階層化支援（ユーザーの意図しない整理のリスク）
- [ ] **自然言語→Dataview変換** - 自然言語からDataviewクエリの自動生成（技術的難易度とメンテナンスコスト）

Minervaの目標は、Claude Desktopと連携してObsidianの操作を自然言語で行える環境を構築し、知的生産の効率を高めることです。

## ドキュメント

詳細な仕様や開発ガイドラインについては、以下のドキュメントを参照してください：

- [要件定義書](docs/requirements.md) - プロジェクトの要件と仕様の詳細
- [ノート操作機能仕様書](docs/note_operations.md) - ノートの作成、読み取り、検索、タグ管理機能の詳細仕様
- [技術仕様書](docs/technical_spec.md) - 内部実装の詳細と設計思想
- [テストガイドライン](docs/test_guidelines.md) - テスト作成のガイドラインとAAA（Arrange-Act-Assert）パターンの解説
- [Property-basedテストガイド](docs/property_based_testing.md) - Hypothesisを使用したProperty-basedテストの実装と運用ガイド
- [開発ワークフロー](docs/development_workflow.md) - 開発プロセス、ブランチ戦略、コードレビュー、リリースフロー
- [GitHub開発プロセス](docs/github_workflow.md) - GitHubを使用した開発プロセスの詳細
- [ラベル管理ガイド](docs/label_management.md) - GitHubラベルの体系的な管理と使用方法
- [Issueと PR の効果的な活用ガイド](docs/issue_pr_guide.md) - IssueとPRの効果的な活用方法
- [GitHub Copilot カスタム指示ガイドライン](docs/copilot_guidelines.md) - GitHub Copilotのカスタム指示を使用した開発ガイドライン
- [Claude Code カスタムスラッシュコマンドガイドライン](docs/claude_code_commands.md) - Claude Codeのカスタムスラッシュコマンドの使用方法
- [ベクター検索トラブルシューティング](docs/vector_search_troubleshooting.md) - セマンティック検索機能の問題解決ガイド
- [リリースプロセス](docs/release_process.md) - リリースプロセスと自動化の詳細

## 開発ガイド

### フロントマター処理について

Minervaでは、すべてのノートにフロントマター（YAML形式のメタデータ）を自動的に付与します。これには以下の情報が含まれます：

- **created**: ノート作成日時（ISO 8601形式）
- **updated**: 最終更新日時（ISO 8601形式）
- **author**: 作成者名
- **tags**: タグのリスト（タグ管理機能で追加した場合）
- **aliases**: エイリアスのリスト（エイリアス管理機能で追加した場合）

例えば：
```yaml
---
created: '2025-05-22T10:15:30+09:00'
updated: '2025-05-22T14:35:45+09:00'
author: Claude 3.7 Sonnet
tags:
  - project
  - documentation
aliases:
  - プロジェクト文書
  - 設計書
---
```

既存のノートを編集する場合、作成日時は保持され、更新日時のみが変更されます。

## Claude Desktop からの起動時の import エラーについて

Claude Desktop から Minerva サーバーを起動する場合、Python の import パス（sys.path）がコマンドライン実行時と異なるため、
`from minerva.service import ...` のような絶対importで「No module named 'minerva'」エラーが発生することがあります。

この問題を回避するため、`server.py` の先頭で以下のように sys.path に親ディレクトリを追加しています。

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

これにより、コマンドライン実行・Claude Desktop どちらの環境でも minerva パッケージの import エラーが発生しなくなります。

## ライセンス

MIT
