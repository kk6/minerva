# Pre-commit Setup Guide

このガイドでは、Minervaプロジェクトでpre-commitフックを設定し、trailing whitespaceなどのコードフォーマットの問題を事前に防ぐ方法を説明します。

## Pre-commitとは

Pre-commitは、Gitコミット前に自動でコードチェックとフォーマットを実行するツールです。これにより、CI/CDパイプラインでエラーが発生することを防げます。

## セットアップ手順

### 1. Pre-commitのインストール

```bash
# pipを使用する場合
pip install pre-commit

# uvを使用する場合（推奨）
uv add --dev pre-commit
```

### 2. Pre-commitフックの有効化

プロジェクトルートで以下のコマンドを実行します：

```bash
pre-commit install
```

これにより、`git commit`時に自動でpre-commitフックが実行されるようになります。

### 3. 初回実行

全ファイルに対してpre-commitを実行します：

```bash
pre-commit run --all-files
```

## 設定されているフック

現在のプロジェクトでは以下のフックが設定されています：

### 基本的なファイルフォーマット
- **trailing-whitespace**: 行末の不要な空白を自動削除
- **end-of-file-fixer**: ファイル末尾に改行を追加
- **mixed-line-ending**: 改行コードをLFに統一
- **check-yaml**: YAMLファイルの構文チェック
- **check-toml**: TOMLファイルの構文チェック
- **check-added-large-files**: 大きなファイルのコミットを防止

### Python関連
- **ruff**: Pythonコードのリンターとフォーマッター
- **ruff-format**: Pythonコードの自動フォーマット

## 使用方法

### 通常のコミット

設定後は、通常通り`git commit`を実行するだけで自動的にチェックが実行されます：

```bash
git add .
git commit -m "feat: add new feature"
```

フックが問題を検出した場合、コミットは中断され、修正内容が表示されます。

### 手動実行

コミット前に手動でチェックを実行したい場合：

```bash
# 変更されたファイルのみチェック
pre-commit run

# 全ファイルをチェック
pre-commit run --all-files

# 特定のフックのみ実行
pre-commit run trailing-whitespace
```

### 特定のファイルのみチェック

```bash
pre-commit run --files src/minerva/service.py
```

## トラブルシューティング

### フックの実行をスキップ

緊急時にフックをスキップしてコミットする場合：

```bash
git commit -m "emergency fix" --no-verify
```

**注意**: この方法は緊急時のみ使用し、後でプロジェクトの品質基準に合わせて修正してください。

### フックの更新

Pre-commitフックを最新版に更新：

```bash
pre-commit autoupdate
```

### キャッシュのクリア

問題が発生した場合、キャッシュをクリア：

```bash
pre-commit clean
pre-commit install
```

## CI/CDとの連携

プロジェクトのCI/CDパイプライン（`.github/workflows/pr-checks.yml`）でもpre-commitが実行されます。これにより、ローカルでのチェックを忘れた場合でも、プルリクエスト時に問題が検出されます。

## 推奨ワークフロー

1. **開発開始時**: `pre-commit install`でフックを有効化
2. **開発中**: 通常通りコミット（自動でチェック実行）
3. **プルリクエスト前**: `pre-commit run --all-files`で最終チェック
4. **問題発見時**: 自動修正された内容を確認し、必要に応じて追加修正

## よくある問題と解決策

### Trailing Whitespace

**問題**: 行末に不要な空白があるとCIが失敗する

**解決策**: Pre-commitが自動で修正します。修正後は以下のコマンドでコミット：

```bash
git add .
git commit -m "fix: remove trailing whitespace"
```

### 大きなファイル

**問題**: 大きなファイルをコミットしようとしてエラーが発生

**解決策**: ファイルが本当に必要か確認し、不要な場合は削除。必要な場合は`.gitignore`に追加。

### Python コードフォーマット

**問題**: Pythonコードのフォーマットエラー

**解決策**: Ruffが自動で修正します。修正内容を確認してコミット。

## 設定ファイル

プロジェクトのpre-commit設定は`.pre-commit-config.yaml`に記載されています。新しいフックの追加や設定変更が必要な場合は、このファイルを編集してください。

## まとめ

Pre-commitの導入により：

- ✅ Trailing whitespaceやその他のフォーマット問題を自動修正
- ✅ CI/CDでのエラーを事前に防止
- ✅ コードの品質と一貫性を維持
- ✅ レビュー時のフォーマット指摘を削減

定期的に`pre-commit autoupdate`を実行して、フックを最新状態に保つことを推奨します。
