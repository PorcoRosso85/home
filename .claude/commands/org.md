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
### 依頼する側（/orgを実行したClaude）への制限
```bash
# /org実行時の推奨起動方法
claude --allowedTools "Read" "LS" "TodoRead" "TodoWrite" \
       "Bash(git:*)" "Bash(nix:*)" "Bash(cd:*)" "Bash(export:*)" \
       --disallowedTools "Write" "Edit" "MultiEdit" "Task" "WebSearch" "WebFetch"
```

### 依頼される側（作業するClaude）への設定
claude_sdkで`--allow-write`により以下のツールが使用可能：
- `Write`, `Edit`, `MultiEdit` - ファイル編集
- `Bash`, `Read`, `Glob`, `Grep`, `LS` - 開発作業全般

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
4. DuckDBによる進捗監視（stream.jsonlの分析）
5. 完了判定とルール遵守報告の収集
6. 結果の統合とユーザーへの報告

# 関連ツール
- **claude_sdk**: Claudeインスタンスの起動と管理 → `~/bin/src/poc/claude_sdk/`
- **DuckDB**: stream.jsonlの分析とクエリ（`nix run nixpkgs#duckdb`経由）

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

## 4. Claude起動（ルール遵守報告を含む）
```bash
RULE_REPORT="
【重要】タスク完了時には以下を必ず報告してください：
1. 遵守したコーディング規約（CONVENTION.yaml）
2. 実施したテスト方法（TDD、in-source test等）
3. エラー処理の方法
4. その他遵守した規則
最後に必ず「Task completed: [タスク名]」と報告してください。
"

# 各タスクに対してClaude起動（バックグラウンド実行）
PIDS=()
for i in "${!TASK_NAMES[@]}"; do
  TASK="${TASK_NAMES[$i]}"
  TASK_PROMPT="${TASK_PROMPTS[$i]}"
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  
  # claude_sdkパスを検出
  CLAUDE_SDK_PATH="$(find "$GIT_ROOT" -name "claude.ts" -path "*/poc/claude_sdk/*" | head -1)"
  
  nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all \
    "$CLAUDE_SDK_PATH" \
    --claude-id "$TASK-$TIMESTAMP" \
    --uri "$WORKTREE_PATH" \
    --allow-write \
    --print "$TASK_PROMPT $RULE_REPORT" &
  
  PID=$!
  PIDS+=($PID)
  echo "Started Claude for [$TASK] with PID: $PID at $WORKTREE_PATH"
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
```

## 5. 進捗監視
```bash
# DuckDBを使用してタスク進捗を監視
nix run nixpkgs#duckdb -- -json -c "
SELECT 
    worktree_uri,
    process_id,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl') sub
            WHERE sub.worktree_uri = main.worktree_uri 
            AND sub.process_id = main.process_id
            AND json_extract_string(sub.data, '$.type') = 'assistant'
            AND LOWER(json_extract_string(sub.data, '$.message.content[0].text')) LIKE '%task completed%'
        ) THEN 'completed'
        WHEN MAX(timestamp) < datetime('now', '-30 minutes') THEN 'timeout'
        ELSE 'in_progress'
    END as status,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl') sub
            WHERE sub.worktree_uri = main.worktree_uri
            AND sub.process_id = main.process_id
            AND json_extract_string(sub.data, '$.type') = 'assistant'
            AND json_extract_string(sub.data, '$.message.content[0].text') LIKE '%遵守したコーディング規約%'
        ) THEN 'reported'
        ELSE 'not_reported'
    END as rule_compliance,
    MAX(timestamp) as last_activity,
    COUNT(*) as activity_count
FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl') main
GROUP BY worktree_uri, process_id
ORDER BY worktree_uri
"

# より詳細な進捗確認（タスク名ごと）
for TASK in "${TASK_NAMES[@]}"; do
    echo "=== タスク進捗: $TASK ==="
    WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
    
    # 最新のアクティビティを確認
    nix run nixpkgs#duckdb -- -json -c "
    SELECT 
        json_extract_string(data, '$.type') as msg_type,
        SUBSTRING(COALESCE(
            json_extract_string(data, '$.message.content[0].text'),
            json_extract_string(data, '$.message')
        ), 1, 100) as message_preview,
        timestamp
    FROM read_json_auto('$WORKTREE_PATH/stream.jsonl')
    WHERE json_extract_string(data, '$.type') = 'assistant'
    ORDER BY timestamp DESC
    LIMIT 3
    " | jq -r '.[] | "[\(.timestamp)] \(.message_preview)"' 2>/dev/null || echo "進捗なし"
done
```

## 6. 結果収集
```bash
# DuckDBを使用して結果を収集
echo "=== 結果収集 ==="

# 完了報告とルール遵守報告を抽出
nix run nixpkgs#duckdb -- -json -c "
SELECT 
    worktree_uri,
    json_extract_string(data, '$.message.content[0].text') as message,
    timestamp
FROM read_json_auto('$WORKTREE_BASE/*/stream.jsonl')
WHERE json_extract_string(data, '$.type') = 'assistant'
AND json_extract_string(data, '$.message.content[0].type') = 'text'
AND (
    LOWER(json_extract_string(data, '$.message.content[0].text')) LIKE '%task completed%'
    OR json_extract_string(data, '$.message.content[0].text') LIKE '%遵守したコーディング規約%'
)
ORDER BY worktree_uri, timestamp DESC
" > /tmp/org_results.json

# 結果を整形して表示
if [ -s /tmp/org_results.json ]; then
    cat /tmp/org_results.json | jq -r '.[] | 
        "\n[" + (.worktree_uri | split("/")[-1]) + "] " + (.timestamp) + "\n" + 
        (.message | split("\n")[0:5] | join("\n") | .[0:300]) + "..."
    ' 2>/dev/null || {
        # jqが使えない場合の代替処理
        echo "結果の整形にはjqが必要です。生データ:"
        cat /tmp/org_results.json
    }
else
    echo "完了報告が見つかりませんでした。"
fi

# タスクごとの最終状態を確認
echo -e "\n=== タスク最終状態 ==="
for TASK in "${TASK_NAMES[@]}"; do
    WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
    
    # 最終メッセージを取得
    LAST_MESSAGE=$(nix run nixpkgs#duckdb -- -json -c "
    SELECT json_extract_string(data, '$.message.content[0].text') as text
    FROM read_json_auto('$WORKTREE_PATH/stream.jsonl')
    WHERE json_extract_string(data, '$.type') = 'assistant'
    AND json_extract_string(data, '$.message.content[0].type') = 'text'
    ORDER BY timestamp DESC
    LIMIT 1
    " | jq -r '.[0].text' 2>/dev/null | head -c 200)
    
    # 完了判定
    if echo "$LAST_MESSAGE" | grep -qi "task completed"; then
        STATUS="✓ 完了"
    else
        STATUS="○ 進行中"
    fi
    
    echo "[$TASK] $STATUS"
    echo "  最終メッセージ: ${LAST_MESSAGE}..."
    echo ""
done
```

# ルール遵守の連鎖
1. **/orgを実行したClaude → 各タスク担当Claude**: ルール遵守報告を義務化
2. **各タスク担当Claude → /orgを実行したClaude**: 完了時に遵守内容を報告
3. **/orgを実行したClaude → ユーザー**: 統合報告でルール遵守状況を含める

# 注意事項
- 各Claudeは独立したworktreeで作業（ファイル競合なし）
- session.jsonで会話継続性を保証
- stream.jsonlは削除禁止（分析用）
- ルール遵守報告なしは不完全な完了扱い
- 同時実行数: /orgを実行したClaudeの判断に従う（1〜n個）
- 依頼完了確認: stream.jsonl作成で判定
- 識別子: worktree_uriとprocess_idで各Claudeを識別
- DuckDB分析: `nix run nixpkgs#duckdb`で実行（analyze_jsonl不要）

ARGUMENTS: なし（現在のタスクから自動判断）