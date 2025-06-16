# ベクター検索（セマンティック検索）トラブルシューティングガイド

このドキュメントは、Minervaのセマンティック検索機能で発生する可能性のある問題と、その解決方法について説明します。

**📖 関連ドキュメント**:
- **[vector_search_api.md](vector_search_api.md)** - 完全なAPIリファレンスと使用例
- **[technical_spec.md](technical_spec.md)** - 技術仕様とアーキテクチャ

## 目次

1. [よくある問題と解決方法](#よくある問題と解決方法)
2. [次元ミスマッチエラーの対処法](#次元ミスマッチエラーの対処法)
3. [MCP Inspector を使ったデバッグ手順](#mcp-inspector-を使ったデバッグ手順)
4. [本番環境での安全なインデックス化手順](#本番環境での安全なインデックス化手順)
5. [パフォーマンス問題の解決](#パフォーマンス問題の解決)

## よくある問題と解決方法

### 1. セマンティック検索が有効にならない

**症状**: `semantic_search` コマンドが「機能が有効ではありません」エラーを返す

**原因と解決方法**:
```bash
# 1. 環境変数の確認
# .env ファイルで以下が設定されているかチェック
VECTOR_SEARCH_ENABLED=true

# 2. オプション依存関係のインストール確認
# 以下のライブラリがインストールされているかチェック
pip list | grep -E "(duckdb|sentence-transformers|numpy)"

# 必要に応じてインストール
pip install duckdb sentence-transformers numpy
```

### 2. DuckDB ホームディレクトリエラー

**症状**: "IO Error: Can't find the home directory" エラー

**原因**: iCloud同期環境でのDuckDB設定問題

**解決方法**:
- 通常は自動的に解決されます（フォールバック機能実装済み）
- 問題が継続する場合は、カスタムベクターDBパスを設定：
```bash
# .env ファイルに追加
VECTOR_DB_PATH=/Users/yourusername/custom/vectors.db
```

### 3. インデックス化のタイムアウト

**症状**: MCP Inspector で 3秒タイムアウトが発生

**解決方法**:
```bash
# Claude Desktop で以下のコマンドを使用
build_vector_index_batch 関数を使って、max_files を 5 以下に設定してください。

# または MCP Inspector で小さなバッチ処理
{"name": "build_vector_index_batch", "arguments": {"max_files": 5, "force_rebuild": true}}
```

## 次元ミスマッチエラーの対処法

### 問題の症状

Claude Desktop で以下のエラーが発生：
```
Binder Error: array_cosine_similarity: Array arguments must be of the same size
```

### 根本原因

部分的なインデックス化と完全なインデックス化を組み合わせた際に、異なる次元のベクターが混在することで発生。

**問題が発生するシナリオ**:
1. `build_vector_index_batch` で一部ファイル（例：10件）をインデックス化
2. `build_vector_index` で全ファイルをインデックス化
3. 一部のファイルで異なる次元のベクターが生成される
4. `semantic_search` 実行時にベクター次元不整合エラーが発生

### 解決方法（vault規模別）

#### 小規模vault（100ファイル未満）- 推奨：完全リセット

```bash
# Claude Desktop での指示例
"reset_vector_database を実行してから、build_vector_index で全ファイルをインデックス化してください。"
```

**メリット**: シンプルで確実
**デメリット**: 既存インデックスが全て失われる

#### 中規模vault（100-1000ファイル）- 推奨：選択的修復

```bash
# 1. 問題の診断
"debug_vector_schema を実行して現在の状況を確認してください。"

# 2. 問題ファイルの特定と削除（将来実装予定）
# remove_problematic_vectors 関数で異常な次元のベクターのみ削除

# 3. 削除されたファイルの再インデックス化
"build_vector_index を force_rebuild=false で実行してください。"
```

**メリット**: 大部分のデータを保持
**デメリット**: 将来のツール実装待ち

#### 大規模vault（1000ファイル以上）- 推奨：スキーマ移行

```bash
# 将来実装予定の高度な修復機能
# fix_vector_dimension_mismatch 関数でデータを保持しながら次元統一
```

**メリット**: 全データ保持、処理時間最適化
**デメリット**: 将来のツール実装待ち

### 予防策

今後同様の問題を避けるための安全なワークフロー：

```bash
# 1. クリーンスタート
"reset_vector_database を実行してください。"

# 2. 小規模テスト
"build_vector_index_batch を max_files=5, force_rebuild=true で実行してください。"

# 3. 動作確認
"semantic_search でテストクエリを実行して正常動作を確認してください。"

# 4. 全体インデックス化
"build_vector_index を実行して全ファイルをインデックス化してください。"
```

## MCP Inspector を使ったデバッグ手順

### 1. MCP Inspector の起動

```bash
# プロジェクトルートで実行
make dev

# ポート競合エラーの場合
lsof -ti:6277 | xargs kill
make dev
```

### 2. 段階的デバッグ手順

#### ステップ1: 設定と状態の確認
```json
{"name": "get_vector_index_status", "arguments": {}}
```
期待される結果: `vector_search_enabled: true`, `database_exists` の確認

#### ステップ2: 詳細診断
```json
{"name": "debug_vector_schema", "arguments": {}}
```
期待される結果: `test_embedding_dimension: 384`, 一貫した次元の確認

#### ステップ3: 最小限のテスト
```json
{"name": "build_vector_index_batch", "arguments": {"max_files": 1, "force_rebuild": true}}
```
期待される結果: `processed: 1`, `errors: []`

#### ステップ4: 機能テスト
```json
{"name": "semantic_search", "arguments": {"query": "テスト", "limit": 3}}
```
期待される結果: 検索結果の正常取得

### 3. よくあるデバッグパターン

#### 次元ミスマッチの診断
```json
// 1. 現在の状態確認
{"name": "debug_vector_schema", "arguments": {}}

// 2. 期待される結果
{
  "embedding_model": "all-MiniLM-L6-v2",
  "test_embedding_dimension": 384,
  "database_exists": true
}

// 3. 異常な場合の対処
{"name": "reset_vector_database", "arguments": {}}
```

#### インデックス化の問題
```json
// バッチサイズを段階的に増加
{"name": "build_vector_index_batch", "arguments": {"max_files": 1}}
{"name": "build_vector_index_batch", "arguments": {"max_files": 5}}
{"name": "build_vector_index_batch", "arguments": {"max_files": 10}}
```

## 本番環境での安全なインデックス化手順

### 初回セットアップ

```bash
# 1. 環境変数の設定確認
# .env ファイルで VECTOR_SEARCH_ENABLED=true を確認

# 2. Claude Desktop での初期化
"get_vector_index_status を実行してベクター検索が有効か確認してください。"

# 3. 安全な段階的インデックス化
"reset_vector_database を実行してからbuild_vector_index_batch を max_files=5 で実行してください。"

# 4. 動作テスト
"semantic_search で短いクエリをテストしてください。"

# 5. 全体インデックス化
"build_vector_index を実行して全ファイルをインデックス化してください。"
```

### 定期メンテナンス

```bash
# 1. インデックス状況の確認
"get_vector_index_status を実行してインデックス化済みファイル数を確認してください。"

# 2. 新しいファイルの追加
"build_vector_index を force_rebuild=false で実行して新しいファイルのみインデックス化してください。"

# 3. 動作確認
"semantic_search で検索テストを実行してください。"
```

### 問題発生時の緊急対応

```bash
# 1. 問題の特定
"debug_vector_schema を実行して問題箇所を特定してください。"

# 2. クイック修復（小規模vault）
"reset_vector_database を実行してから build_vector_index で再構築してください。"

# 3. 一時的な回避策
# セマンティック検索を無効化して通常のキーワード検索を使用
# .env で VECTOR_SEARCH_ENABLED=false に設定
```

## パフォーマンス問題の解決

### インデックス化が遅い

**対策**:
1. バッチ処理の活用: `build_vector_index_batch` で段階的処理
2. ファイル数の確認: 大量のファイルがある場合は時間がかかるのが正常
3. リソース確認: CPU・メモリ使用量をモニタリング

### 検索結果が期待と異なる

**対策**:
1. クエリの改善: より具体的で長い検索クエリを使用
2. 閾値の調整: `threshold` パラメータで類似度の最低値を設定
3. 結果数の調整: `limit` パラメータで適切な結果数を設定

### メモリ使用量が多い

**対策**:
1. バッチサイズの調整: `max_files` を小さくして処理
2. 不要なファイルの除外: コードファイルなど、セマンティック検索に不適切なファイルを除外
3. 定期的なクリーンアップ: 削除されたファイルのベクターをデータベースから削除

## トラブルシューティング チェックリスト

### 基本設定の確認

- [ ] `.env` ファイルで `VECTOR_SEARCH_ENABLED=true` が設定されている
- [ ] 必要な依存関係（duckdb, sentence-transformers, numpy）がインストールされている
- [ ] Obsidian vault のパスが正しく設定されている
- [ ] `.minerva` ディレクトリに書き込み権限がある

### 機能テストの実行

- [ ] `get_vector_index_status` で機能が有効になっている
- [ ] `debug_vector_schema` で正常な次元（384）が表示される
- [ ] `build_vector_index_batch` で小規模テストが成功する
- [ ] `semantic_search` で検索結果が返される

### パフォーマンステスト

- [ ] インデックス化が合理的な時間で完了する
- [ ] 検索結果が期待される内容と合致する
- [ ] メモリ使用量が許容範囲内である

## 追加リソース

- **[vector_search_api.md](vector_search_api.md)** - 完全なAPIリファレンスと詳細な使用例
- [CLAUDE.md](../CLAUDE.md) - 開発者向け詳細情報
- [technical_spec.md](technical_spec.md) - 技術仕様
- [test_guidelines.md](test_guidelines.md) - テスト作成ガイドライン

## サポート

問題が解決しない場合：
1. [GitHub Issues](https://github.com/kk6/minerva/issues) で問題を報告
2. `debug_vector_schema` の出力結果を含める
3. エラーメッセージの全文を記載
4. 使用環境（OS、Python バージョン、vault サイズ）を明記
