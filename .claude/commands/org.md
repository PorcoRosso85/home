# org
/org

# 説明
複数のClaudeインスタンスを使った並列タスク実行を管理する

# 重要な制約
**/orgを実行したClaudeは作業禁止**
- /orgを実行したClaudeは依頼者であり、管理者である
- 自らTaskツールで作業してはならない
- 他のClaudeインスタンスに依頼し、結果を収集するのみ
- すべての実作業（調査、分析、コーディング）は委任先のClaudeが行う

## ツール制限の推奨設定

### 権限管理パイプライン

#### 今すぐ使える例
```bash
# /orgで使う場合のCONFIG_PATHとSDK_PATHの設定
CONFIG_PATH="$(find ~/bin/src/poc -name "config.ts" -path "*/develop/claude/config/*" | head -1)"
SDK_PATH="$(find ~/bin/src/poc -name "claude.ts" -path "*/develop/claude/sdk/*" | head -1)"

# 1. 読み取り専用（ファイル編集不可）
echo '{"prompt": "src/のコードをレビューして", "mode": "readonly"}' | \
  deno run --allow-all $CONFIG_PATH | deno run --allow-all $SDK_PATH

# 2. 開発モード（すべて許可）
echo '{"prompt": "新機能を実装して", "mode": "development"}' | \
  deno run --allow-all $CONFIG_PATH | deno run --allow-all $SDK_PATH

# 3. 本番モード（rm/dd等の危険コマンドブロック）
echo '{"prompt": "本番環境のログを確認", "mode": "production"}' | \
  deno run --allow-all $CONFIG_PATH | deno run --allow-all $SDK_PATH
```

#### プリセットの中身（~/bin/src/poc/claude_config/src/config.ts）
```typescript
readonly: {
  allowedTools: ["Read", "Glob", "Grep", "LS"],
  settings: { permissions: { /* 読み取りのみ */ } }
}

development: {
  allowedTools: ["*"],  // すべて許可
  permissionMode: "acceptEdits"
}

production: {
  disallowedTools: ["Bash", "Write", "Edit"],
  settings: {
    permissions: {
      deny: ["rm:**", "dd:**", "mkfs:**", "/etc/**"]
    }
  }
}
```

### 依頼する側に許可されるツール
- `Read`, `LS` - 進捗確認のためのファイル読み取り
- `TodoRead`, `TodoWrite` - タスク管理
- `Bash(git:*)` - worktree作成とブランチ管理
- `Bash(nix:*)` - Claude SDKとDuckDB実行
- `Bash(cd:*)` - ディレクトリ移動
- `Bash(export:*)`, `Bash(echo:*)` - 環境変数設定

### 依頼する側に禁止されるツール
- `Write`, `Edit`, `MultiEdit` - ファイル変更禁止
- `Task` - 自ら作業することを防ぐ
- `WebSearch`, `WebFetch` - 外部調査の防止

**注意**: DuckDB実行は`nix run nixpkgs#duckdb`経由で許可される

# 実行内容
1. タスクの識別（ユーザー要求を解釈、分割は自分で判断）
2. 各タスクに対してworktreeを作成
3. 各タスクごとにClaudeインスタンスを起動して依頼（並列実行）
4. stream.jsonl生成開始の確認（DuckDBで確認）
5. 監視終了（依頼完了時点で終了）

# 関連ツール
- **claude_config**: 権限設定生成 → `~/bin/src/poc/claude_config/`
- **claude_sdk**: Claudeインスタンスの起動と管理 → `~/bin/src/poc/claude_sdk/`
- **claude_orchestra**: 統合テストと動作検証 → `~/bin/src/poc/claude_orchestra/`
- **DuckDB**: stream.jsonlの分析とクエリ（`nix run nixpkgs#duckdb`経由）

## 詳細ドキュメント
- 権限とフックの完全仕様 → `~/bin/src/poc/claude_permission_principle.md`

# 実行フロー

## sparse-checkout worktree作成
テンプレート: `~/bin/src/poc/develop/claude/org/template.sh`

```bash
# テンプレートを読み込む
source ~/bin/src/poc/develop/claude/org/template.sh

# 使用例を表示
source ~/bin/src/poc/develop/claude/org/template.sh --examples

# worktree作成
WORKTREE=$(create_sparse_worktree "task-name" "target/dir")

# Claude起動
launch_claude_sdk "task-name" "$WORKTREE" "タスクの説明" "development"
```

### 引数不足時
1. `org.sh --list`で既存worktree確認
2. 不足情報をユーザーに依頼
   - task_name: タスク名
   - target_dir: sparse対象ディレクトリ
   - prompt: タスク説明
   - mode: readonly/development/production

## 1. タスク分割（/orgを実行したClaudeが判断）
```bash
# /orgを実行したClaudeがユーザー要求を解釈してタスクを識別
# 例: "AとBを同時に調査して" → タスク1: A調査, タスク2: B調査
# Taskツールは使用せず、/orgを実行したClaudeが直接判断する
# タスクの例:
# - "auth-feature": 認証機能を実装
# - "api-design": API設計書を作成
# - "test-implementation": テストを実装
```

## 2. タスク実行
```bash
# テンプレートを読み込む
source ~/bin/src/poc/develop/claude/org/template.sh

# worktree作成と並列実行
WORKTREE1=$(create_sparse_worktree "auth-feature" "src/auth")
WORKTREE2=$(create_sparse_worktree "api-design" "docs/api")
WORKTREE3=$(create_sparse_worktree "test-impl" "tests")

launch_claude_sdk "auth-feature" "$WORKTREE1" "認証機能実装" "development" &
launch_claude_sdk "api-design" "$WORKTREE2" "API設計" "readonly" &
launch_claude_sdk "test-impl" "$WORKTREE3" "テスト実装" "development" &
wait
```

## 3. タスク記録
TodoWriteで各タスクをin_progressとして記録

## 4. 監視
org.shの起動確認がorg.sh内で完結。stream.jsonl作成を監視


# 進捗確認
```bash
# 進捗監視
nix run nixpkgs#duckdb -- -json -c "SELECT worktree_uri, MAX(timestamp) FROM read_json_auto('.worktrees/claude-org/*/stream.jsonl') GROUP BY worktree_uri"

# 完了確認
grep -l "Task completed" .worktrees/claude-org/*/stream.jsonl
```

# 注意事項
- 各Claudeは独立したworktreeで作業（ファイル競合なし）
- session.jsonで会話継続性を保証
- stream.jsonlは削除禁止（分析用）
- 同時実行数: /orgを実行したClaudeの判断に従う（1〜n個）
- 依頼完了確認: stream.jsonl作成で判定
- **監視は依頼時点で終了**（タスク完了を待たない）
- 識別子: worktree_uriとprocess_idで各Claudeを識別
- DuckDB分析: `nix run nixpkgs#duckdb`で実行（analyze_jsonl不要）

## worktree内作業の保証
- **作業ディレクトリ**: Claude SDKは`cwd: workdir`で起動され、worktree内で作業
- **設定保存**: 以下がworktree内に保存される
  - `session.json`: 会話履歴とコンテキスト
  - `stream.jsonl`: 全入出力ログ
  - `.claude/settings.json`: 権限設定
- **再利用時**: 既存worktreeを再利用すると過去のコンテキストが継承される

