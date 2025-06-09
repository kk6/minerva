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
- `type:feature`: 新機能追加に関するIssue/PR
- `type:bug`: バグ修正に関するIssue/PR
- `type:docs`: ドキュメント関連のIssue/PR
- `type:refactor`: コードリファクタリングに関するIssue/PR
- `type:test`: テスト関連のIssue/PR
- `type:chore`: メンテナンス作業に関するIssue/PR
- `type:ci`: CI/CD関連のIssue/PR

### 機能別ラベル
- `feature:obsidian`: Obsidian連携関連のIssue/PR
- `feature:claude`: Claude連携関連のIssue/PR
- `feature:markdown`: Markdown処理関連のIssue/PR
- `feature:create`: create_note機能関連のIssue/PR
- `feature:edit`: edit_note機能関連のIssue/PR
- `feature:read`: read_note機能関連のIssue/PR
- `feature:search`: search_notes機能関連のIssue/PR
- `feature:tags`: タグ管理機能関連のIssue/PR
- `feature:delete`: ノート削除機能関連のIssue/PR
- `feature:config`: 設定関連のIssue/PR

### エリア別ラベル
- `area:backend`: バックエンド関連のIssue/PR
- `area:ci`: CI/CD関連のIssue/PR
- `area:docs`: ドキュメント関連（エリア）のIssue/PR

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

### ラベル使用例

#### 典型的なラベルの組み合わせ

**新機能開発のIssue例:**
- `type:feature` + `feature:create` + `priority:medium` + `scope:core`

**バグ修正のIssue例:**
- `type:bug` + `feature:search` + `priority:high`

**ドキュメント更新のIssue例:**
- `type:docs` + `area:docs` + `priority:low`

**CI/CD改善のIssue例:**
- `type:ci` + `area:ci` + `priority:medium`

**プルリクエスト例:**
- `type:feature` + `feature:tags` + `pr:ready`

#### ラベル選択のガイドライン

1. **必須**: 必ず `type:` ラベルを1つ選択する
2. **機能特定**: 関連する機能がある場合は `feature:` ラベルを追加
3. **エリア指定**: 開発領域が明確な場合は `area:` ラベルを追加
4. **優先度設定**: プロジェクト管理のため `priority:` ラベルを設定
5. **スコープ明示**: 影響範囲が明確な場合は `scope:` ラベルを追加

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

ブランチ上で開発を行い、適宜コミットします。コミットメッセージは[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)の規約に従って以下の形式で記述します：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### 主なタイプ (type)

- `feat`: 新機能の追加
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響を与えない変更（空白、フォーマット、セミコロンの欠落など）
- `refactor`: バグを修正せず、機能を追加しないコード変更
- `perf`: パフォーマンスを向上させるコード変更
- `test`: 不足しているテストの追加または既存のテストの修正
- `build`: ビルドシステムまたは外部依存関係に影響を与える変更
- `ci`: CI設定ファイルとスクリプトの変更
- `chore`: その他の変更（上記に該当しないもの）

#### スコープ (scope)

変更の範囲を示す名詞を括弧内に記述することができます（オプション）：
- `(obsidian)`
- `(claude)`
- `(file-handler)`
- `(tools)`
- `(config)`
など

#### 例

- `feat(obsidian): Add support for note synchronization`
- `fix(tools): Fix incorrect path handling in search_notes function`
- `docs: Update installation instructions`
- `test(file-handler): Add unit tests for create_note function`
- `refactor: Move common functions to utils module`

フッターには関連するIssue番号を記載します：
```
Issue #42
```

または複数のIssueを閉じる場合：
```
Closes #42, #43
```

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
- [Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)
