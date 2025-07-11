#!/bin/bash
# Claude parallel task execution templates
# Usage: Source this file and use the functions

set -e

# Function to list existing worktrees with sparse settings
list_work_sparse() {
    local GIT_ROOT=$(git rev-parse --show-toplevel)
    local WORKTREE_BASE="$GIT_ROOT/.worktrees/claude-org"
    
    if [ ! -d "$WORKTREE_BASE" ]; then
        return
    fi
    
    echo "=== Existing worktree/sparse configurations ==="
    for worktree in "$WORKTREE_BASE"/*/; do
        if [ -d "$worktree" ]; then
            local TASK_NAME=$(basename "$worktree" | cut -d'-' -f1)
            local SPARSE_DIRS=$(cd "$worktree" && git sparse-checkout list 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
            echo "Task: $TASK_NAME"
            echo "  Path: $worktree"
            echo "  Sparse: ${SPARSE_DIRS:-not configured}"
            echo ""
        fi
    done
}

# Check for --list option
if [ "$1" = "--list" ]; then
    list_work_sparse
    exit 0
fi

# Template function for creating sparse worktree
# Usage: create_sparse_worktree <task_name> <target_dir> <base_branch>
create_sparse_worktree() {
    local TASK_NAME="$1"
    local TARGET_DIR="$2"
    local BASE_BRANCH="${3:-$(git rev-parse --abbrev-ref HEAD)}"
    
    local GIT_ROOT=$(git rev-parse --show-toplevel)
    local TIMESTAMP=$(date +%s)
    local WORKTREE_BASE="$GIT_ROOT/.worktrees/claude-org"
    local WORKTREE_PATH="$WORKTREE_BASE/${TASK_NAME}-$TIMESTAMP"
    
    mkdir -p "$WORKTREE_BASE"
    
    # Check for existing worktree
    local EXISTING=$(find "$WORKTREE_BASE" -name "${TASK_NAME}-*" -type d 2>/dev/null | head -1)
    if [ -n "$EXISTING" ] && [ -d "$EXISTING" ]; then
        echo "$EXISTING"
        return 0
    fi
    
    # Create new worktree
    local BRANCH_NAME="claude-${TASK_NAME}-$TIMESTAMP"
    git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH"
    
    # Configure sparse-checkout
    cd "$WORKTREE_PATH"
    git sparse-checkout init --cone
    git sparse-checkout set "$TARGET_DIR"
    cd - > /dev/null
    
    echo "$WORKTREE_PATH"
}

# Template function for launching Claude with SDK
# Usage: launch_claude_sdk <task_name> <worktree_path> <prompt> <mode>
launch_claude_sdk() {
    local TASK_NAME="$1"
    local WORKTREE_PATH="$2"
    local PROMPT="$3"
    local MODE="${4:-development}"
    
    local GIT_ROOT=$(git rev-parse --show-toplevel)
    local TIMESTAMP=$(basename "$WORKTREE_PATH" | cut -d'-' -f2)
    
    # Find Claude pipeline paths
    local CONFIG_PATH="$(find "$GIT_ROOT" -name "config.ts" -path "*/poc/develop/claude/config/*" 2>/dev/null | head -1)"
    local SDK_PATH="$(find "$GIT_ROOT" -name "claude.ts" -path "*/poc/develop/claude/sdk/*" 2>/dev/null | head -1)"
    
    if [ -z "$CONFIG_PATH" ] || [ -z "$SDK_PATH" ]; then
        echo "Error: Claude pipeline files not found" >&2
        return 1
    fi
    
    # Add rule reporting requirement
    local RULE_REPORT="【重要】タスク完了時には以下を必ず報告してください：1. 遵守したコーディング規約（CONVENTION.yaml） 2. 実施したテスト方法（TDD、in-source test等） 3. エラー処理の方法 4. その他遵守した規則 最後に必ず「Task completed: [$TASK_NAME]」と報告してください。"
    
    local PROMPT_FULL="$PROMPT $RULE_REPORT"
    local JSON_INPUT=$(jq -n \
      --arg prompt "$PROMPT_FULL" \
      --arg mode "$MODE" \
      --arg workdir "$WORKTREE_PATH" \
      '{prompt: $prompt, mode: $mode, workdir: $workdir}')
    
    # Run Claude SDK
    nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all "$SDK_PATH" \
        --claude-id "$TASK_NAME-$TIMESTAMP" \
        --uri "$WORKTREE_PATH" \
        --print "$PROMPT_FULL" \
        --allow-write &
    
    local PID=$!
    echo "Claude started with PID: $PID"
    
    # Wait for initialization
    local count=0
    while [ $count -lt 30 ]; do
        if [ -f "$WORKTREE_PATH/stream.jsonl" ]; then
            echo "✓ Task delegation successful"
            return 0
        fi
        sleep 1
        ((count++))
    done
    
    echo "✗ Task delegation failed: stream.jsonl not created" >&2
    return 1
}

# Example usage functions
example_parallel_tasks() {
    echo "Example: Running multiple tasks in parallel"
    echo ""
    echo "# Create worktrees"
    echo 'WORKTREE1=$(create_sparse_worktree "auth-feature" "src/auth")'
    echo 'WORKTREE2=$(create_sparse_worktree "api-design" "docs/api")'
    echo ""
    echo "# Launch tasks"
    echo 'launch_claude_sdk "auth-feature" "$WORKTREE1" "Implement authentication" "development" &'
    echo 'launch_claude_sdk "api-design" "$WORKTREE2" "Design REST API" "readonly" &'
    echo 'wait'
}

# Show examples if sourced with --examples
if [ "${1:-}" = "--examples" ]; then
    example_parallel_tasks
fi