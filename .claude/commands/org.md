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
CONFIG_PATH="$(find ~/bin/src/poc -name "config.ts" -path "*/claude_config/*" | head -1)"
SDK_PATH="$(find ~/bin/src/poc -name "claude.ts" -path "*/claude_sdk/*" | head -1)"

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

## 2. Worktree作成
```bash
# /orgを実行したClaudeが判断したタスクリストから配列を作成
TASK_NAMES=("auth-feature" "api-design" "test-implementation")
TASK_PROMPTS=("認証機能を実装してください" "API設計書を作成してください" "テストを実装してください")
TASK_PRIORITIES=("high" "high" "medium")

# 現在のリポジトリルートを検出
GIT_ROOT=$(git rev-parse --show-toplevel)
TIMESTAMP=$(date +%s)

# worktreeディレクトリ作成（リポジトリルート相対）
WORKTREE_BASE="$GIT_ROOT/.worktrees/claude-org"
mkdir -p "$WORKTREE_BASE"

# 各タスク用のworktree作成
for TASK in "${TASK_NAMES[@]}"; do
  BRANCH_NAME="claude-${TASK}-$TIMESTAMP"
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
  echo "Created worktree: $WORKTREE_PATH"
done
```

## 3. タスク記録
```bash
# タスク配列から動的に生成
TODO_ITEMS=()
for i in "${!TASK_NAMES[@]}"; do
  TASK="${TASK_NAMES[$i]}"
  PRIORITY="${TASK_PRIORITIES[$i]}"
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  TODO_ITEMS+=("{\"id\": \"${TASK}-$TIMESTAMP\", \"content\": \"[${TASK}] $WORKTREE_PATH\", \"status\": \"in_progress\", \"priority\": \"$PRIORITY\"}")
done

# TodoWriteに記録
TodoWrite: [${TODO_ITEMS[@]}]
```

## 4. Claude起動（権限管理パイプライン経由）
```bash
RULE_REPORT="
【重要】タスク完了時には以下を必ず報告してください：
1. 遵守したコーディング規約（CONVENTION.yaml）
2. 実施したテスト方法（TDD、in-source test等）
3. エラー処理の方法
4. その他遵守した規則
最後に必ず「Task completed: [タスク名]」と報告してください。
"

# パイプラインパスを検出
CONFIG_PATH="$(find "$GIT_ROOT" -name "config.ts" -path "*/poc/claude_config/*" | head -1)"
SDK_PATH="$(find "$GIT_ROOT" -name "claude.ts" -path "*/poc/claude_sdk/*" | head -1)"

# 各タスクに対してClaude起動（バックグラウンド実行）
PIDS=()
for i in "${!TASK_NAMES[@]}"; do
  TASK="${TASK_NAMES[$i]}"
  TASK_PROMPT="${TASK_PROMPTS[$i]}"
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  
  # タスクの種類に応じてモード決定
  if [[ "$TASK_PROMPT" =~ "レビュー" || "$TASK_PROMPT" =~ "確認" ]]; then
    MODE="readonly"
  elif [[ "$TASK_PROMPT" =~ "本番" || "$TASK_PROMPT" =~ "production" ]]; then
    MODE="production"
  else
    MODE="development"  # デフォルトは開発モード
  fi
  
  # 権限管理パイプライン経由で起動
  echo "{\"prompt\": \"$TASK_PROMPT $RULE_REPORT\", \"mode\": \"$MODE\", \"workdir\": \"$WORKTREE_PATH\"}" | \
    nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all "$CONFIG_PATH" | \
    nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all "$SDK_PATH" \
      --claude-id "$TASK-$TIMESTAMP" &
  
  PID=$!
  PIDS+=($PID)
  echo "Started Claude for [$TASK] with mode:$MODE PID:$PID at $WORKTREE_PATH"
done

# 依頼完了確認（各タスクの初期起動を確認）
sleep 5  # 起動待機
for i in "${!TASK_NAMES[@]}"; do
  TASK="${TASK_NAMES[$i]}"
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  
  if [ -f "$WORKTREE_PATH/stream.jsonl" ]; then
    echo "✓ 依頼成功: [$TASK] $WORKTREE_PATH"
  else
    echo "✗ 依頼失敗: [$TASK] $WORKTREE_PATH - stream.jsonlが作成されていません"
  fi
done

echo "=== 監視終了 ==="
echo "すべてのタスクへの依頼が完了しました。"
echo "各Claudeインスタンスが独立して作業を進めています。"
```


# 監視終了後の確認方法

## 1. タスク進捗の監視
```bash
# worktreeベースディレクトリを設定
WORKTREE_BASE="/home/nixos/.worktrees/claude-org"

# 全体の進捗状況を確認
nix run nixpkgs#duckdb -- -json -c "
SELECT 
    worktree_uri,
    process_id,
    MAX(timestamp) as last_activity,
    COUNT(*) as activity_count
FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl')
GROUP BY worktree_uri, process_id
ORDER BY worktree_uri
"

# 特定タスクの最新アクティビティ
TASK="browser-sync-poc"  # タスク名を指定
TIMESTAMP="1735527600"   # タイムスタンプを指定
WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"

nix run nixpkgs#duckdb -- -json -c "
SELECT 
    json_extract_string(data, '$.type') as msg_type,
    SUBSTRING(COALESCE(
        json_extract_string(data, '$.message.content[0].text'),
        json_extract_string(data, '$.message')
    ), 1, 200) as message_preview,
    timestamp
FROM read_json_auto('$WORKTREE_PATH/stream.jsonl')
WHERE json_extract_string(data, '$.type') = 'assistant'
ORDER BY timestamp DESC
LIMIT 5
"
```

## 2. タスク完了の確認
```bash
# 完了報告を検索
nix run nixpkgs#duckdb -- -json -c "
SELECT 
    worktree_uri,
    json_extract_string(data, '$.message.content[0].text') as message,
    timestamp
FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl')
WHERE json_extract_string(data, '$.type') = 'assistant'
AND json_extract_string(data, '$.message.content[0].type') = 'text'
AND LOWER(json_extract_string(data, '$.message.content[0].text')) LIKE '%task completed%'
ORDER BY timestamp DESC
" | jq -r '.[] | "[" + (.worktree_uri | split("/")[-1]) + "] " + (.timestamp)'

# ルール遵守報告の確認
nix run nixpkgs#duckdb -- -json -c "
SELECT 
    worktree_uri,
    json_extract_string(data, '$.message.content[0].text') as message
FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl')
WHERE json_extract_string(data, '$.type') = 'assistant'
AND json_extract_string(data, '$.message.content[0].text') LIKE '%遵守したコーディング規約%'
"
```

## 3. リアルタイム監視（tail -f相当）
```bash
# 特定worktreeの活動を監視
watch -n 2 "tail -n 10 $WORKTREE_PATH/stream.jsonl | grep -E '(assistant|user)' | tail -5"

# 完了待機スクリプト
timeout 300 bash -c 'while true; do
  if grep -q "Task completed" /home/nixos/.worktrees/claude-org/*/stream.jsonl 2>/dev/null; then
    echo "✓ タスク完了を検出"
    break
  fi
  sleep 10
done'
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

## 実際の権限動作例

### 読み取り専用モードの場合
```bash
# Claudeがファイル作成を試みると...
→ "Claude requested permissions to use Write"
# ファイルは作成されない
```

### 本番モードの場合
```bash
# 危険なコマンド（rm -rf等）を実行しようとすると...
→ "Permission to use Bash with command rm -rf has been denied."
→ "The command is being blocked"
```

### 開発モードの場合
```bash
# すべてのツールが使用可能
→ ファイル作成・編集・コマンド実行すべてOK
```

## フック設定例（高度な制御）

### コマンドログ記録
```json
// ~/.claude/settings.json に追加
"hooks": {
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{
      "type": "command",
      "command": "echo $(date) $TOOL_NAME >> /tmp/claude-commands.log"
    }]
  }]
}
```

### 危険コマンドブロック
```json
"hooks": {
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{
      "type": "command", 
      "command": "~/bin/validate-command.py"  // exit 2でブロック
    }]
  }]
}
```

ARGUMENTS: なし（現在のタスクから自動判断）