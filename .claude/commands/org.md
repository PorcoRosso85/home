# org
/org

# 説明
複数のClaudeインスタンスを使った並列タスク実行を管理する

# 実行内容
1. 複数タスクの識別と分割（Taskツール使用）
2. 各タスクに対してworktreeを作成
3. 各タスクごとにClaudeインスタンスを起動（並列実行）
4. analyze_jsonlによる進捗監視
5. 完了判定とルール遵守報告の収集
6. 結果の統合とユーザーへの報告

# 実行フロー

## 1. タスク分割（Taskツール使用）
```bash
# Taskツールで独立タスクを識別（1つでもn個でも）
Task: "タスク分割" 
  prompt: "以下の要求を分析し、独立実行可能なタスクに分割してください：
  [ユーザー要求]
  
  【独立性チェック基準】
  - ファイル競合がないか確認
  - 依存関係がないか確認  
  - 並列実行可能か確認
  
  【出力形式（JSONで返す）】
  {
    "tasks": [
      {
        "name": "auth-feature",
        "prompt": "認証機能を実装してください",
        "priority": "high",
        "dependencies": []
      }
    ]
  }"

# Taskツールの結果をパース（実際の実装では自動化）
```

## 2. Worktree作成
```bash
# Taskツールの結果から配列を作成
# 注意: 実際はTaskツールのJSON出力をパースして動的に生成
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
```python
# analyze_jsonlで監視
# DuckDB用ライブラリパス（環境依存のため要調整）
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-/nix/store/*/gcc-*-lib/lib/}"
export WORKTREE_BASE="$WORKTREE_BASE"
export TIMESTAMP="$TIMESTAMP"
export TASK_NAMES="${TASK_NAMES[*]}"  # 配列をスペース区切りの文字列に
python3 << 'EOF'
import sys
import os
git_root = os.environ.get('GIT_ROOT', '')
analyze_path = os.path.join(git_root, 'bin/src/poc/analyze_jsonl')
if os.path.exists(analyze_path):
    sys.path.append(analyze_path)
else:
    print(f"Warning: analyze_jsonl not found at {analyze_path}")
from core import create_analyzer

# 動的にworktreeパスのリストを生成
worktree_paths = []
for task in os.environ.get('TASK_NAMES', '').split():
    if task:
        worktree_paths.append(
            os.path.join(os.environ['WORKTREE_BASE'], f'{task}-{os.environ["TIMESTAMP"]}')
        )

analyzer = create_analyzer(worktree_paths)

# 各worktreeのstream.jsonlを登録
for i, path in enumerate(worktree_paths):
    # 個別のビューとして登録
    analyzer.register_jsonl_files(path, 'stream.jsonl', f'stream_{i}')

# 統合ビューを作成
analyzer.create_unified_view('stream_jsonl')

# 完了とルール遵守を確認
result = analyzer.query("""
SELECT 
    worktree_uri,
    process_id,
    CASE
        WHEN json_extract(data, '$.type') = 'assistant' 
         AND json_extract(data, '$.message') LIKE '%Task completed:%' THEN 'completed'
        WHEN MAX(timestamp) < datetime('now', '-30 minutes') THEN 'timeout'
        ELSE 'in_progress'
    END as status,
    CASE
        WHEN json_extract(data, '$.message') LIKE '%遵守したコーディング規約%' THEN 'reported'
        ELSE 'not_reported'
    END as rule_compliance
FROM stream_jsonl
GROUP BY worktree_uri, process_id
""")
print(result)
EOF
```

## 6. 結果収集
```bash
# ルール遵守報告の抽出
for TASK in "${TASK_NAMES[@]}"; do
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  echo "=== [$TASK] ==="
  
  if [ -f "$WORKTREE_PATH/stream.jsonl" ]; then
    tail -100 "$WORKTREE_PATH/stream.jsonl" | \
      grep -E "(Task completed:|遵守したコーディング規約)" | \
      jq -r '.data' 2>/dev/null || echo "報告なし"
  else
    echo "stream.jsonlが見つかりません"
  fi
done

# 成果物確認
echo -e "\n=== 成果物確認 ==="
for TASK in "${TASK_NAMES[@]}"; do
  WORKTREE_PATH="$WORKTREE_BASE/${TASK}-$TIMESTAMP"
  BRANCH_NAME="claude-${TASK}-$TIMESTAMP"
  
  echo "[$TASK]:"
  cd "$WORKTREE_PATH" && git status --porcelain
done

# 必要に応じてメインブランチにマージ
cd "$GIT_ROOT"
git checkout main
for TASK in "${TASK_NAMES[@]}"; do
  BRANCH_NAME="claude-${TASK}-$TIMESTAMP"
  # git merge "$BRANCH_NAME"  # 実際のマージはユーザー判断で
done
```

# ルール遵守の連鎖
1. **Claude0 → 各タスク担当Claude**: ルール遵守報告を義務化
2. **各タスク担当Claude → Claude0**: 完了時に遵守内容を報告
3. **Claude0 → ユーザー**: 統合報告でルール遵守状況を含める

# 注意事項
- 各Claudeは独立したworktreeで作業（ファイル競合なし）
- session.jsonで会話継続性を保証
- stream.jsonlは削除禁止（分析用）
- ルール遵守報告なしは不完全な完了扱い
- 同時実行数: Taskツールの判断に従う（1〜n個）
- 依頼完了確認: stream.jsonl作成で判定

ARGUMENTS: なし（現在のタスクから自動判断）