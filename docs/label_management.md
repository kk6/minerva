# Minerva ラベル管理ガイド

このドキュメントでは、Minervaプロジェクトにおけるラベルの管理と使用方法について説明します。

## ラベル体系の概要

Minervaプロジェクトでは、以下の階層化されたラベル体系を使用しています：

```
type:       必須 - Issue/PRの基本分類
feature:    推奨 - 機能領域の特定
area:       任意 - 開発領域の明示
priority:   推奨 - 重要度の設定
status:     任意 - 現在の状態
scope:      任意 - 影響範囲の明示
pr:         PR専用 - プルリクエストの状態
```

## ラベルカテゴリの詳細

### Type系ラベル（必須）

すべてのIssue/PRに必ず1つのtype系ラベルを設定してください。

| ラベル | 用途 | 例 |
|--------|------|-----|
| `type:feature` | 新機能追加 | 新しいAPI追加、UI機能拡張 |
| `type:bug` | バグ修正 | エラーの修正、動作不正の改善 |
| `type:docs` | ドキュメント関連 | README更新、API文書追加 |
| `type:refactor` | リファクタリング | コード整理、構造改善 |
| `type:test` | テスト関連 | テスト追加、テスト修正 |
| `type:chore` | メンテナンス作業 | 依存関係更新、設定変更 |
| `type:ci` | CI/CD関連 | ワークフロー修正、デプロイ設定 |

### Feature系ラベル（推奨）

機能領域が明確な場合に使用します。

| ラベル | 用途 |
|--------|------|
| `feature:obsidian` | Obsidian連携機能 |
| `feature:claude` | Claude連携機能 |
| `feature:markdown` | Markdown処理 |
| `feature:create` | ノート作成機能 |
| `feature:edit` | ノート編集機能 |
| `feature:read` | ノート読み取り機能 |
| `feature:search` | ノート検索機能 |
| `feature:tags` | タグ管理機能 |
| `feature:delete` | ノート削除機能 |
| `feature:config` | 設定関連機能 |

### Area系ラベル（任意）

開発領域や担当分野を明示する場合に使用します。

| ラベル | 用途 |
|--------|------|
| `area:backend` | バックエンド実装 |
| `area:ci` | CI/CD関連作業 |
| `area:docs` | ドキュメント関連作業 |

### Priority系ラベル（推奨）

プロジェクト管理のため優先度を設定します。

| ラベル | 用途 | 対応目安 |
|--------|------|----------|
| `priority:high` | 緊急・重要 | 即座に対応 |
| `priority:medium` | 通常の重要度 | 計画的に対応 |
| `priority:low` | 低優先度 | 時間がある時に対応 |

### Status系ラベル（任意）

作業状態を明示する場合に使用します。

| ラベル | 用途 |
|--------|------|
| `status:wip` | 作業中 |
| `status:review` | レビュー待ち |
| `status:blocked` | ブロック中 |
| `status:ready` | 実装準備完了 |

### Scope系ラベル（任意）

影響範囲を明示する場合に使用します。

| ラベル | 用途 |
|--------|------|
| `scope:core` | コア機能への影響 |
| `scope:ui` | UI/UXへの影響 |
| `scope:performance` | パフォーマンスへの影響 |
| `scope:security` | セキュリティへの影響 |

### PR系ラベル（PR専用）

プルリクエストの状態を明示します。

| ラベル | 用途 |
|--------|------|
| `pr:ready` | レビュー準備完了 |
| `pr:wip` | 作業進行中 |
| `pr:needs-rebase` | リベース必要 |
| `pr:needs-tests` | テスト追加必要 |

## ラベル使用のベストプラクティス

### ラベル選択の基本フロー

1. **Type系ラベルを選択**（必須）
2. **Feature系ラベルを検討**（該当機能がある場合）
3. **Priority系ラベルを設定**（プロジェクト管理上重要）
4. **その他必要に応じて追加**

### 典型的なラベルパターン

```
# 新機能開発
type:feature + feature:create + priority:medium + scope:core

# バグ修正
type:bug + feature:search + priority:high

# ドキュメント更新
type:docs + area:docs + priority:low

# リファクタリング
type:refactor + area:backend + priority:medium + scope:performance

# CI/CD改善
type:ci + area:ci + priority:medium
```

### 避けるべきパターン

❌ **悪い例:**
- type系ラベルなし
- 曖昧すぎるラベルの組み合わせ
- 矛盾するラベルの組み合わせ

✅ **良い例:**
- type系ラベルを必ず含む
- 明確で一貫性のあるラベル
- プロジェクトの文脈に適したラベル

## ラベル管理の自動化

### GitHub CLI を使用したラベル操作

```bash
# ラベル一覧表示
gh label list

# ラベル作成
gh label create "feature:新機能" --description "新機能関連" --color "e99695"

# ラベル編集
gh label edit "ラベル名" --description "新しい説明" --color "新しい色"

# Issue/PRにラベル追加
gh issue edit 番号 --add-label "type:feature,priority:high"
```

### 新機能追加時のラベル作成フロー

1. 新機能に対応する `feature:` ラベルが必要か検討
2. 必要な場合は適切な色（`#e99695`）で作成
3. 関連するIssue/PRにラベルを設定
4. ドキュメントを更新

## ラベルカラーコード

| カテゴリ | カラーコード | 色 |
|----------|-------------|-----|
| type: | `#0366d6` | 青 |
| feature: | `#e99695` | 薄いピンク |
| area: | `#1d76db` | 濃い青 |
| priority:high | `#b60205` | 赤 |
| priority:medium | `#d93f0b` | オレンジ |
| priority:low | `#fbca04` | 黄 |
| status: | `#9BE9A8`, `#0E8A16`, `#B60205` | 緑/濃い緑/赤 |
| scope: | `#1d76db`, `#B60205` | 濃い青/赤 |
| pr: | `#6f42c1`, `#d4c5f9` | 紫/薄い紫 |

## 関連ドキュメント

- [GitHub開発プロセス](github_workflow.md) - ラベルを含む開発フロー全体
- [Issueと PR の効果的な活用ガイド](issue_pr_guide.md) - Issue/PR作成時のラベル使用法
- [GitHub Copilot カスタム指示ガイドライン](copilot_guidelines.md) - AI支援でのラベル活用

## ラベルの進化

ラベル体系は、プロジェクトの成長とともに進化します：

1. **新機能追加時**: 対応する `feature:` ラベルの検討
2. **開発体制変更時**: `area:` ラベルの見直し
3. **プロジェクト成熟時**: 不要ラベルの統廃合

ラベル変更時は必ずドキュメントも更新し、チーム全体で共有してください。
