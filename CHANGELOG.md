# CHANGELOG


## v0.2.0 (2025-05-22)

### Bug Fixes

- **pyproject**: スクリプトセクションの位置を修正し、mypyのオーバーライド設定を整理
  ([`4e37d44`](https://github.com/kk6/minerva/commit/4e37d4424e787823470de565444fbb1269d3491b))

- **tools**: タグ操作機能のコード品質改善
  ([`25664a7`](https://github.com/kk6/minerva/commit/25664a74885816755b9e5deb056fb5464f42b5d9))

1. rename_tag関数の構文エラー修正（if条件文の: が不足） 2. list_all_tags、find_notes_with_tag関数のドキュメント修正 3.
  rename_tag関数のディレクトリ処理に関するコメント修正

Issue #5

### Chores

- 各種ドキュメントに適用対象を追加
  ([`0ce069d`](https://github.com/kk6/minerva/commit/0ce069d58297cac87e212bc83c6069ad88e2653e))

### Documentation

- Add CLAUDE.md for project guidelines and commands
  ([`dbbf98d`](https://github.com/kk6/minerva/commit/dbbf98d9d9af5c72b990da58f5e67c43c8830fd3))

- エラーハンドリングとファイル操作のパターンを更新し、詳細なエラーログ記録を追加
  ([`480d86a`](https://github.com/kk6/minerva/commit/480d86a500ec98696832f11dae9d6517cc04a6e0))

- カスタム指示のディレクトリ名を修正
  ([`a877ad4`](https://github.com/kk6/minerva/commit/a877ad4238e1aa3526c2934badddcfde43a924ce))

- ノート削除機能の2段階プロセスを追加し、テストガイドラインを更新
  ([`010548b`](https://github.com/kk6/minerva/commit/010548b68cac90ec6409a58ad8ebed8f89806636))

### Features

- Implement comprehensive tag management features
  ([`a70d986`](https://github.com/kk6/minerva/commit/a70d98642d9ac857bf9a7f6c372ff7ed0f534b29))

This commit introduces a suite of features for managing tags in notes within the Minerva system.

Key functionalities added:

1. **Tag Manipulation:** * `add_tag`: Adds a new tag to a specified note. Handles normalization,
  validation, and prevents duplicates. * `remove_tag`: Removes an existing tag from a specified
  note. * `rename_tag`: Renames a tag across all notes in a specified directory or the entire vault.
  Handles case variations and merging if the new tag name already exists.

2. **Tag Querying:** * `get_tags`: Retrieves all tags from a single specified note. *
  `list_all_tags`: Lists all unique, normalized tags across a specified directory or the entire
  vault. * `find_notes_with_tag`: Finds all notes that contain a specific tag.

3. **Core Logic Enhancements:** * The `_generate_note_metadata` function in `tools.py` has been
  updated to process and store tags in the front matter. * Helper functions `_normalize_tag` (for
  lowercasing and stripping whitespace) and `_validate_tag` (for checking invalid characters) have
  been added to ensure tag consistency and validity.

4. **Request Models:** * Pydantic request models (`AddTagRequest`, `RemoveTagRequest`, etc.) have
  been implemented for each new public function, ensuring structured and validated input.

5. **Unit Tests:** * A comprehensive suite of unit tests has been added in
  `tests/tools/test_tag_operations.py` covering all new tag management functions and their various
  scenarios, including edge cases and error handling. A `mock_vault` fixture was created for
  managing test data.

6. **Documentation:** * The `docs/note_operations.md` file has been updated with a new "Tag
  Management" section detailing the usage of the new features. * Detailed Python docstrings have
  been added to all new public functions, Pydantic models, and relevant private helper functions in
  `src/minerva/tools.py`.

These changes address issue #5 (kk6/minerva#5) by providing robust functionality for adding,
  removing, renaming, and querying tags, thereby enhancing the organizational and search
  capabilities of the Minerva knowledge base.

- タグの追加・削除・リネーム機能の実装 #5
  ([`7f2b00b`](https://github.com/kk6/minerva/commit/7f2b00b89981c7fd84663be0b22e5431640978f9))

### Refactoring

- Rename .github/copilot to .github/instructions
  ([`245a109`](https://github.com/kk6/minerva/commit/245a109006758a1e3fe104d1d4895927661f0ea8))

- **tests**: タグ操作に関するテストでリスト型の確認を追加し、可読性を向上
  ([`669a663`](https://github.com/kk6/minerva/commit/669a66392e41845214000da9b889dc6fcc002d60))

- **tests**: リクエストファクトリの型ヒントを追加し、可読性を向上
  ([`d4c5702`](https://github.com/kk6/minerva/commit/d4c57025b8cd8c86b22a7dcaf1d6fa35f6b43196))

- **tools**: 一貫した日付処理のためのコメントを英語に変更
  ([`3238f30`](https://github.com/kk6/minerva/commit/3238f3062eea094919632c09bbe840ca5d7ca051))


## v0.1.0 (2025-05-20)

### Bug Fixes

- Default_pathの型チェックを追加し、空白文字列を無視するように修正
  ([`71a8d52`](https://github.com/kk6/minerva/commit/71a8d52751ce76696512ebb420e191783fac5d7d))

- **file**: Correct typo in warning message for delete_file function
  ([`3a1ae17`](https://github.com/kk6/minerva/commit/3a1ae171a27bb73a3fcf38c765110aa3f313f82e))

- **file**: Enhance error logging in delete_file function for better debugging
  ([`0882cb8`](https://github.com/kk6/minerva/commit/0882cb89f95fc24f122cfe571f16372da2a59612))

- **file**: Improve error handling in delete_file function
  ([`41413b4`](https://github.com/kk6/minerva/commit/41413b46e5b66f63ca3b4f9d5699df6db2869720))

- **file**: Improve error logging in delete_file function for better clarity
  ([`0db7fac`](https://github.com/kk6/minerva/commit/0db7fac5836f0ba240e922f152a5bfde15466225))

- **search**: Optimize regex compilation for case-sensitive and case-insensitive searches
  ([`9aaa8e7`](https://github.com/kk6/minerva/commit/9aaa8e7ef615b4e22ad18bbf908675faf12bbd9a))

- **tests**: Update error handling in delete_note test for missing parameters
  ([`3326df9`](https://github.com/kk6/minerva/commit/3326df978befd6dc047bba9447b8241d8745e795))

- **tests**: テストでのファイル名のアサーションを修正し、最新の実装に合わせる
  ([`41b8fd0`](https://github.com/kk6/minerva/commit/41b8fd0dbb941abc862a8cd51b73407222335855))

- **tools**: Improve error handling in delete_note function
  ([`4295d97`](https://github.com/kk6/minerva/commit/4295d97acbc1449a6e53f56d9ab6eb752c01cc42))

- **tools**: Read_note関数の引数を修正し、readnoterequestから直接filepathを受け取るように変更
  ([`bf7dcc2`](https://github.com/kk6/minerva/commit/bf7dcc2ee1940744e969131e9ec6666bdbc5b777))

- **version**: Improve version mismatch error message in check_version script
  ([`07c9531`](https://github.com/kk6/minerva/commit/07c9531d079d1451ae9772b58ce53a3eb0853118))

### Chores

- Licenseファイルを追加し、readme.mdにライセンス情報を更新
  ([`cd4141f`](https://github.com/kk6/minerva/commit/cd4141f6e886edacf3b2e1624acbbe438d942bcd))

- **deps**: Remove tomli dependency from project
  ([`ae9fd23`](https://github.com/kk6/minerva/commit/ae9fd23bef03b6ac27c9edda9de8a956156266ae))

- **release**: Install 'uv' dependency in release workflow
  ([`2020156`](https://github.com/kk6/minerva/commit/2020156352b6baf2f23e352af04bf2649f598797))

### Code Style

- **tools.py**: 不要な空白を削除し、警告メッセージのフォーマットを改善
  ([`7edc466`](https://github.com/kk6/minerva/commit/7edc466ae7708bfa43e13748459f6dc4c8e8d06b))

### Documentation

- .vscode/settings.jsonにコミットメッセージ生成の指示を追加
  ([`b4d7dea`](https://github.com/kk6/minerva/commit/b4d7dead26c860a037ed17bfa6ef546a14a5a123))

- Add GitHub workflow documentation
  ([`edc9449`](https://github.com/kk6/minerva/commit/edc94494879052220514eba096aadbd1908fa80d))

- Add guidelines for GitHub Copilot custom instructions and project patterns
  ([`d3a3f9b`](https://github.com/kk6/minerva/commit/d3a3f9b88f24dbfde34682b2883df7916c1a29c8))

- Claude Desktopのインストール手順にpython-frontmatterオプションを追加
  ([`df1768c`](https://github.com/kk6/minerva/commit/df1768c136dca423afa1cbe6d8b5c9e75f1dc755))

- Claude Desktopへのインストール手順にpython-frontmatterオプションを追加
  ([`8a516af`](https://github.com/kk6/minerva/commit/8a516af6a2bf3e506ea59b77a175c72a4c9e4ea8))

- Readme.mdにgithub開発プロセスとissue/pr活用ガイドのリンクを追加
  ([`e087d6f`](https://github.com/kk6/minerva/commit/e087d6fbbdf43f685cdbc596780666ff5c873987))

- Readmeにdeepwikiバッジを追加
  ([`4682aef`](https://github.com/kk6/minerva/commit/4682aef4d79f20e662f11e433c41c7ad7d2405af))

- Remove Japanese commit message guideline from Copilot instructions
  ([`dd5f2c0`](https://github.com/kk6/minerva/commit/dd5f2c03dae8d08ed25b0f11df63124797c82797))

- Update feature priorities in README for better clarity
  ([`7eefe32`](https://github.com/kk6/minerva/commit/7eefe32af9b7ed831c935866d21fac1d90901ed4))

- ノート操作に関するreadmeと仕様書を更新し、関数名を明確化
  ([`ebb8ca1`](https://github.com/kk6/minerva/commit/ebb8ca1a38c805eb443a1fec164e70c6afc5ae6b))

- 依存関係管理に関するベストプラクティスを追加
  ([`b3283d0`](https://github.com/kk6/minerva/commit/b3283d002ac6c7f22db2e0fc56eaadadf9ce4229))

- 将来の開発方針をreadmeに追加
  ([`685b90b`](https://github.com/kk6/minerva/commit/685b90b77ea1ad2fb4b8ff4c982841f5e84aa639))

### Features

- Write_note関数をcreate_noteとedit_noteに分割 (closes #11)
  ([`0aa88e8`](https://github.com/kk6/minerva/commit/0aa88e8db247930109fa8eed8386e534319e2f5f))

- ノート作成機能にfrontmatterを追加し、著者情報とデフォルトディレクトリを設定可能に
  ([`fbcfbec`](https://github.com/kk6/minerva/commit/fbcfbec26848a7826e5983288b1f91eb11e5796e))

- **tools**: Write_note関数の引数を変更し、空のファイル名に対するバリデーションを追加
  ([`4c9333d`](https://github.com/kk6/minerva/commit/4c9333ddeef20abe178b4312bd996dd52f951365))

- **version**: バージョン管理の自動化
  ([`7475888`](https://github.com/kk6/minerva/commit/74758881f3889158aca17fc999316da04b457ea4))

- バージョン番号を一元管理するための仕組みを導入 - python-semantic-releaseを導入し、バージョン自動更新を設定 - GitHub
  Actionsによる自動リリースワークフローを追加 - バージョン一貫性チェックスクリプトを追加 - リリースプロセスのドキュメントを作成

Issue #19

### Refactoring

- _prepare_note_for_writing関数の戻り値を修正し、不要なディレクトリ作成コードを削除
  ([`384ea33`](https://github.com/kk6/minerva/commit/384ea3384e7b2edbd83766b460206eacb1be904b))

- パッケージ構造の標準化とサーバーコードの改善
  ([`f7c0fc6`](https://github.com/kk6/minerva/commit/f7c0fc6548cb04ae448a548a8569ae2650922cd1))

- **check_version**: Simplify version file path handling and improve error message formatting
  ([`14fd390`](https://github.com/kk6/minerva/commit/14fd3908ba8cd89c297ae8b7f6f4c76a41cdb587))

- **docs**: 使用例からリクエストオブジェクトを削除し、直接関数を呼び出す形式に変更
  ([`6fbd322`](https://github.com/kk6/minerva/commit/6fbd3221e0a6f318eaa52ab0f606968fa3988d3f))

- **file_handler, tools**: ロギングメッセージのフォーマットを改善
  ([`d240393`](https://github.com/kk6/minerva/commit/d24039362fde0c779167fe115b22654f28dcd3c0))

- **server.py**: Sys.pathの挿入を__main__ブロックから削除
  ([`ae65b61`](https://github.com/kk6/minerva/commit/ae65b616c6ad4256511b56a34e1b164bc882498b))

- **server.py**: Write_noteを削除し、mcpのバージョンを0.2.0に更新
  ([`f9bcc9b`](https://github.com/kk6/minerva/commit/f9bcc9b38c633919c44263d8ea8db056a3370af5))

- **tools**: Search_notes関数の引数を変更し、searchnoterequestから直接queryとcase_sensitiveを受け取るように修正
  ([`b15dfbe`](https://github.com/kk6/minerva/commit/b15dfbeebc25d82e5d73bbb073d7f499d22fe1a0))

- **tools**: Write_note関数の引数のフォーマットを改善し、search_notes関数の引数を整理
  ([`546460a`](https://github.com/kk6/minerva/commit/546460ae1b9d225c96e4de1c9b53b2d87ef04c76))

- **tools.py**: フロントマターの生成とノート準備の関数名を変更し、ドキュメントを改善
  ([`1e760ec`](https://github.com/kk6/minerva/commit/1e760ec95b39a3f0abed2720130ec47fde1a2e27))

### Testing

- **tests/test_tools.py**: Readnoteおよびsearchnotesのテストを追加
  ([`62b8d6e`](https://github.com/kk6/minerva/commit/62b8d6ec0b001a1e7546bbee24e1070e60797a69))
