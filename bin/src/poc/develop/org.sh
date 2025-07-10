#!/bin/bash
# Claude parallel task execution with sparse-checkout

set -e

# Show usage or source code when no arguments
if [ $# -eq 0 ]; then
    cat "$0"
    exit 0
fi

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

# Arguments
TASK_NAME="$1"
TARGET_DIR="$2"
PROMPT="$3"
MODE="${4:-development}"
BASE_BRANCH="${5:-$(git rev-parse --abbrev-ref HEAD)}"

# Validate required arguments
if [ -z "$TASK_NAME" ] || [ -z "$TARGET_DIR" ] || [ -z "$PROMPT" ]; then
    echo "Usage: $0 <task_name> <target_dir> <prompt> [mode] [base_branch]"
    echo "  task_name: Name of the task (e.g., auth-feature)"
    echo "  target_dir: Directory to sparse-checkout (e.g., src/auth)"
    echo "  prompt: Task description for Claude"
    echo "  mode: Permission mode (readonly/development/production, default: development)"
    echo "  base_branch: Base branch for worktree (default: current branch)"
    echo ""
    list_work_sparse
    exit 1
fi

# Setup paths
GIT_ROOT=$(git rev-parse --show-toplevel)
TIMESTAMP=$(date +%s)
WORKTREE_BASE="$GIT_ROOT/.worktrees/claude-org"
mkdir -p "$WORKTREE_BASE"

# Check for existing worktree/sparse
EXISTING=$(find "$WORKTREE_BASE" -name "${TASK_NAME}-*" -type d 2>/dev/null | head -1)
if [ -n "$EXISTING" ] && [ -d "$EXISTING" ]; then
    WORKTREE_PATH="$EXISTING"
    echo "Reusing existing worktree: $WORKTREE_PATH"
    TIMESTAMP=$(basename "$EXISTING" | cut -d'-' -f2)
else
    # Create new worktree
    WORKTREE_PATH="$WORKTREE_BASE/${TASK_NAME}-$TIMESTAMP"
    BRANCH_NAME="claude-${TASK_NAME}-$TIMESTAMP"
    
    echo "Creating new worktree: $WORKTREE_PATH"
    git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH"
    
    # Configure sparse-checkout
    cd "$WORKTREE_PATH"
    git sparse-checkout init --cone
    git sparse-checkout set "$TARGET_DIR"
    echo "Sparse-checkout configured for: $TARGET_DIR"
    cd -
fi

# Find Claude pipeline paths
CONFIG_PATH="$(find "$GIT_ROOT" -name "config.ts" -path "*/poc/claude_config/*" 2>/dev/null | head -1)"
SDK_PATH="$(find "$GIT_ROOT" -name "claude.ts" -path "*/poc/claude_sdk/*" 2>/dev/null | head -1)"

if [ -z "$CONFIG_PATH" ] || [ -z "$SDK_PATH" ]; then
    echo "Error: Claude pipeline files not found"
    echo "CONFIG_PATH: $CONFIG_PATH"
    echo "SDK_PATH: $SDK_PATH"
    exit 1
fi

# Add rule reporting requirement
RULE_REPORT="
【重要】タスク完了時には以下を必ず報告してください：
1. 遵守したコーディング規約（CONVENTION.yaml）
2. 実施したテスト方法（TDD、in-source test等）
3. エラー処理の方法
4. その他遵守した規則
最後に必ず「Task completed: [$TASK_NAME]」と報告してください。
"

# Launch Claude with permission pipeline
echo "Launching Claude instance..."
echo "  Task: $TASK_NAME"
echo "  Mode: $MODE"
echo "  Working directory: $WORKTREE_PATH"
echo "  Target directory: $TARGET_DIR"

# Create JSON with proper escaping using jq
PROMPT_FULL="$PROMPT $RULE_REPORT"
JSON_INPUT=$(jq -n \
  --arg prompt "$PROMPT_FULL" \
  --arg mode "$MODE" \
  --arg workdir "$WORKTREE_PATH" \
  '{prompt: $prompt, mode: $mode, workdir: $workdir}')

# First get config output
CONFIG_OUTPUT=$(echo "$JSON_INPUT" | nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all "$CONFIG_PATH")

# Extract prompt from config output (it should contain the prompt)
PROMPT_FOR_SDK=$(echo "$CONFIG_OUTPUT" | jq -r '.prompt // empty')

# If no prompt in config output, use original
if [ -z "$PROMPT_FOR_SDK" ]; then
    PROMPT_FOR_SDK="$PROMPT_FULL"
fi

# Run SDK with proper arguments
nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all "$SDK_PATH" \
    --claude-id "$TASK_NAME-$TIMESTAMP" \
    --uri "$WORKTREE_PATH" \
    --print "$PROMPT_FOR_SDK" \
    --allow-write &

PID=$!
echo "Claude started with PID: $PID"

# Wait for stream.jsonl creation
echo -n "Waiting for Claude initialization..."
for i in {1..30}; do
    if [ -f "$WORKTREE_PATH/stream.jsonl" ]; then
        echo " Done!"
        echo "✓ Task delegation successful: $WORKTREE_PATH/stream.jsonl"
        exit 0
    fi
    echo -n "."
    sleep 1
done

echo " Failed!"
echo "✗ Task delegation failed: stream.jsonl not created within 30 seconds"
exit 1