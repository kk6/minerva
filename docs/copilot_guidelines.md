# GitHub Copilot カスタム指示ガイドライン

このドキュメントでは、Minervaプロジェクトにおける GitHub Copilot のリポジトリカスタム指示の設定と使用方法について説明します。

## 1. 概要

Minervaプロジェクトでは、開発効率の向上と一貫したコード品質を保つために、GitHub Copilotのリポジトリカスタム指示機能を活用しています。これにより、プロジェクト固有のコーディング規約や開発プラクティスをCopilotに伝えることが可能になり、より適切なコード補完とサジェスチョンが得られます。

## 2. カスタム指示の構成

カスタム指示は `.github/copilot/` ディレクトリに配置されており、以下のような構成になっています：

```
.github/
  copilot/
    reference.md      # プロジェクト全体のリファレンス情報
    python.md         # Python固有のコーディング規約
    commit.md         # コミットメッセージルール
    patterns/         # 特定のパターンやコンポーネント向け指示
      logging.md      # ロギングに関する指示
      testing.md      # テストに関する指示
      error_handling.md  # エラー処理に関する指示
      file_operations.md # ファイル操作に関する指示
      frontmatter.md  # フロントマター処理に関する指示
```

## 3. 各指示ファイルの役割

### 3.1 reference.md

プロジェクト全体に関するリファレンス情報を提供します：
- プロジェクト概要
- 重要な参照先ドキュメント（README.md、docs/以下のファイル）
- アーキテクチャ構成
- 開発環境と依存関係

### 3.2 python.md

Pythonコーディングに関する規約とベストプラクティスを定義します：
- PEP 8準拠のスタイルガイド
- インデントや命名規則
- インポート順序
- 特にロギング時のf-strings禁止などの重要ルール

### 3.3 commit.md

コミットメッセージに関するガイドラインを提供します：
- Conventional Commits規約に基づく形式
- 主なタイプ（feat, fix, docs, etc.）の説明
- スコープ指定の方法
- 具体的な例

### 3.4 patterns/logging.md

ロギングに関する具体的なパターンと例を提供します：
- ロガーの取得方法
- ログレベルの適切な使い分け
- f-strings禁止の理由と代替手段
- 例外情報のロギング方法
- 機密情報の扱い

### 3.5 patterns/testing.md

テストに関するパターンとベストプラクティスを提供します：
- AAAパターン（Arrange-Act-Assert）の実装方法
- テストdocstringの形式
- フィクスチャとモックの適切な使用法
- パラメータ化テストの実装
- エッジケースのテスト方法

### 3.6 patterns/error_handling.md

エラー処理に関するパターンを提供します：
- 基本的なtry-exceptパターン
- 例外の伝播と変換
- コンテキスト情報の提供
- リソースクリーンアップのためのfinallyブロック

### 3.7 patterns/file_operations.md

ファイル操作に関するパターンを提供します：
- パスの検証と正規化
- ディレクトリの存在確認と作成
- ファイル読み書きの標準パターン
- バイナリファイルの検出

### 3.8 patterns/frontmatter.md

フロントマター処理に関するパターンを提供します：
- フロントマターの生成と更新
- 既存フロントマターの読み取り
- 日時形式の統一
- タグと属性の処理

## 4. 開発者向けガイドライン

### 4.1 カスタム指示の使い方

1. **新機能開発時**：
   - 開発開始前に `reference.md` を参照し、関連するドキュメントを確認する
   - 実装時は `python.md` の規約に従う
   - 特定のパターン（ロギング、エラー処理など）を実装する際は、対応する`patterns/`内のファイルを参照する

2. **コミット時**：
   - `commit.md` に従ってコミットメッセージを作成する
   - 関連するIssue番号を適切に記載する

3. **テスト作成時**：
   - `patterns/testing.md` に従いAAAパターンでテストを構造化する
   - 適切なdocstringをテスト関数に含める

### 4.2 カスタム指示の更新

カスタム指示の内容は、プロジェクトの進化に伴い更新が必要になる場合があります：

1. 新しいパターンやベストプラクティスが確立された場合、対応するファイルを更新または新規作成する
2. 変更はプルリクエストを通じて行い、チームでレビューする
3. 更新内容はチーム全体に通知し、必要に応じて説明を行う

## 5. VSCodeでのCopilotの設定

VSCodeでGitHub Copilotを効果的に使用するための設定：

1. **Copilotの有効化**：
   - VSCode拡張機能「GitHub Copilot」をインストール
   - GitHub アカウントでサインイン

2. **推奨設定**：
   ```json
   {
     "github.copilot.enable": true,
     "github.copilot.editor.enableAutoCompletions": true,
     "editor.inlineSuggest.enabled": true
   }
   ```

3. **キーボードショートカット**：
   - 提案を受け入れる: `Tab`
   - 提案を拒否する: `Esc`
   - 次の提案を表示: `Alt+]`
   - 前の提案を表示: `Alt+[`

## 6. 参考リンク

- [GitHub Copilot公式ドキュメント](https://docs.github.com/en/copilot)
- [リポジトリカスタム指示の追加](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot?tool=vscode)
- [Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)
- [Minervaプロジェクトのgithub_workflow.md](../github_workflow.md)

## 7. よくある質問

### Q: カスタム指示が反映されていないようです。どうすればいいですか？

A: VSCodeを再起動し、`.github/copilot/` ディレクトリが正しく作成されていることを確認してください。また、GitHub Copilot拡張機能が最新バージョンであることも確認してください。

### Q: カスタム指示の優先順位はどうなっていますか？

A: 一般的に、より具体的なファイル（例：`patterns/logging.md`）の内容は、より一般的なファイル（例：`python.md`）よりも優先されます。ただし、これは絶対的なルールではなく、Copilotの実装に依存します。

### Q: 新しいパターンを追加したい場合はどうすればいいですか？

A: `.github/copilot/patterns/` ディレクトリに新しいMarkdownファイルを作成し、パターンの説明と具体的な例を記載してください。その後、このドキュメントを更新して新しいパターンについて説明を追加してください。
