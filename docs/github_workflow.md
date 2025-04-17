# GitHub開発プロセス

このドキュメントでは、Minervaプロジェクトの開発に使用するGitHubの管理プロセスについて説明します。

## Issueの活用

Issueは次の目的で活用します：

- バグの報告と追跡
- 新機能のアイデアと提案
- 既存機能の改善提案
- ドキュメントの追加・更新要求

### Issueテンプレート

以下の4種類のIssueテンプレートを用意しています：

1. **バグ報告**: バグや不具合を報告するためのテンプレート
2. **機能リクエスト**: 新機能の提案のためのテンプレート
3. **改善提案**: 既存機能の改善案を提出するためのテンプレート
4. **ドキュメント関連**: ドキュメントの追加・修正・改善に関する提案のためのテンプレート

各テンプレートには、必要な情報を漏れなく記入するためのガイドが含まれています。

## ラベルの活用

Issueとプルリクエストを整理するために、以下のラベルを使用します：

### タイプ別ラベル
- `feature`: 新機能追加に関するIssue/PR
- `bug`: バグ修正に関するIssue/PR
- `docs`: ドキュメント関連のIssue/PR
- `refactor`: コードリファクタリングに関するIssue/PR
- `test`: テスト関連のIssue/PR
- `chore`: メンテナンス作業に関するIssue/PR

### 機能別ラベル
- `obsidian`: Obsidian連携関連のIssue/PR
- `claude`: Claude連携関連のIssue/PR
- `markdown`: Markdown処理関連のIssue/PR
- `write`: write_note機能関連のIssue/PR
- `read`: read_note機能関連のIssue/PR
- `search`: search_notes機能関連のIssue/PR
- `config`: 設定関連のIssue/PR

### 優先度ラベル
- `priority:high`: 高優先度のIssue/PR
- `priority:medium`: 中優先度のIssue/PR
- `priority:low`: 低優先度のIssue/PR

### ステータスラベル
- `status:wip`: 作業中のIssue/PR
- `status:review`: レビュー待ちのIssue/PR
- `status:blocked`: ブロック中のIssue/PR
- `status:ready`: 実装準備完了のIssue

### スコープラベル
- `scope:core`: コア機能への影響があるIssue/PR
- `scope:ui`: ユーザーインターフェースへの影響があるIssue/PR
- `scope:performance`: パフォーマンスへの影響があるIssue/PR
- `scope:security`: セキュリティへの影響があるIssue/PR

### PRラベル
- `pr:ready`: レビュー準備完了のPR
- `pr:wip`: 作業進行中のPR
- `pr:needs-rebase`: リベースが必要なPR
- `pr:needs-tests`: テスト追加が必要なPR

## 開発ワークフロー

### 1. Issue作成

新しい機能追加やバグ修正を行う前に、まずIssueを作成します。適切なテンプレートを選び、必要な情報を記入します。

### 2. ブランチ作成

Issueに基づいて、適切な命名規則に従ったブランチを作成します：

- 機能追加: `feature/issue-番号-短い説明`
- バグ修正: `fix/issue-番号-短い説明`
- リファクタリング: `refactor/issue-番号-短い説明`
- ドキュメント: `docs/issue-番号-短い説明`

例：`feature/issue-42-add-obsidian-sync`

### 3. 開発

ブランチ上で開発を行い、適宜コミットします。コミットメッセージは以下の形式を推奨します：

```
タイプ(スコープ): 変更内容の要約

変更内容の詳細説明（必要な場合）

Issue #番号
```

例：`feat(obsidian): Add support for note synchronization`

### 4. プルリクエスト作成

開発が完了したら、プルリクエストを作成します。PRテンプレートに従って必要な情報を記入します。

### 5. レビューとマージ

プルリクエストをレビューし、問題がなければマインブランチにマージします。

## リリースプロセス

プロジェクトのリリースは以下の手順で行います：

1. リリース用のブランチを作成（`release/vX.Y.Z`）
2. リリースに含める変更をレビュー
3. バージョン番号の更新
4. リリースノートの作成
5. GitHubリリースの作成

## 参考資料

- [GitHub Flow](https://docs.github.com/ja/get-started/quickstart/github-flow)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
