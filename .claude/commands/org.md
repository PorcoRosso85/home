※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# /org - Orchestrate multiple Claude workers via worktrees and tmux

## Overview
Manages multiple Claude Code instances via Git worktrees and tmux windows for parallel development.

## Usage
```bash
/org <directory>
```

## Example
```bash
# Start Claude in worktree
/org poc/auth-feature

# Reuse existing worktree
/org poc/auth-feature/backend
```

## How it works
1. Finds flake.nix in parent directories
2. Creates/reuses worktree at flake level (~/worktrees/)
3. Launches Claude in worktree subdirectory via tmux
4. Each worktree has independent branch for clean merges
5. Uses Python application.py for tmux management

## Architecture
```
User → org (orchestrator) → tmux windows → Claude instances
          ├── start_worker_in_directory()
          ├── send_command_to_worker_by_directory()
          ├── get_all_workers_status()
          └── get_claude_history()
```

## Implementation

### 重要: 実装例の参照
**必須**: 以下のファイルを参照して適切なツール使用法を確認：
```bash
# 実装例とベストプラクティス
cat ~/bin/src/develop/org/cli.sh.example
```
このファイルには以下が含まれます：
- application.py関数の使用例
- ワーカー管理パターン
- 非同期処理の実装方法

### tmux操作コマンド
```bash
# 全ワーカー表示
tmux list-windows -t org-system

# 特定ワーカーの出力確認
tmux capture-pane -t org-system:<window番号> -p | tail -50

# ワーカーへ切り替え
tmux select-window -t org-system:<window番号>

# 全ワーカーの状態確認
tmux list-windows -t org-system -F "#{window_index}: #{window_name} - #{pane_current_path}"
```

### 送信後の動作確認（必須）
**重要**: タスク送信後は必ず以下の確認を実施すること：

1. **送信直後の確認**（送信から3秒以内）
```bash
# 送信先のワーカー出力を確認
tmux capture-pane -t org-system:<window番号> -p | tail -20

# プロセスが生きているか確認
tmux list-panes -t org-system:<window番号> -F "#{pane_pid} #{pane_current_command}"
```

2. **処理開始の確認**（送信から10秒後）
```bash
# タスクが実行されているか確認
tmux capture-pane -t org-system:<window番号> -p | grep -A5 "タスク内容の一部"

# エラーメッセージの有無を確認
tmux capture-pane -t org-system:<window番号> -p | grep -i "error\|fail\|denied"
```

3. **定期的な進捗確認**（1分ごと）
```bash
# 進捗状況の確認
while true; do
  clear
  echo "=== Worker Status at $(date) ==="
  tmux capture-pane -t org-system:<window番号> -p | tail -30
  sleep 60
done
```

4. **完了確認のベストプラクティス**
- 送信したタスクの実行開始を確認してから次のタスクを送信
- エラーが発生していないことを確認
- ワーカーが応答可能な状態であることを確認

### Current System (Python-based)
エラー時は必ず cli.sh.example を確認

### Worktree Integration (Proposed)
```bash
#!/usr/bin/env bash
# worktree-based org command implementation

set -euo pipefail

WORKTREE_BASE_DIR="$HOME/worktrees"
ORG_PROJECT_DIR="$HOME/bin/src/develop/org"
BRANCH_PREFIX="work"

# Find flake.nix in parent directories
find_flake_root() {
    local dir="$1"
    local abs_dir
    
    if [[ "$dir" = /* ]]; then
        abs_dir="$dir"
    else
        abs_dir="$(cd "$(pwd)/$dir" 2>/dev/null && pwd)" || abs_dir="$(pwd)/$dir"
    fi
    
    while [ "$abs_dir" != "/" ]; do
        if [ -f "$abs_dir/flake.nix" ]; then
            echo "$abs_dir"
            return 0
        fi
        abs_dir=$(dirname "$abs_dir")
    done
    
    echo "Error: No flake.nix found" >&2
    return 1
}

# Generate worktree name
generate_worktree_name() {
    local flake_path="$1"
    local dir_name=$(basename "$flake_path")
    local hash=$(echo "$flake_path" | md5sum | cut -c1-4)
    echo "${dir_name}-${hash}"
}

# Main
main() {
    local requested_dir="${1:?Usage: $0 <directory>}"
    
    # Find flake root
    local flake_root
    flake_root=$(find_flake_root "$requested_dir")
    
    # Generate worktree name
    local worktree_name
    worktree_name=$(generate_worktree_name "$flake_root")
    local worktree_path="$WORKTREE_BASE_DIR/$worktree_name"
    
    # Create worktree if needed
    if [ ! -d "$worktree_path" ]; then
        git worktree add -b "$BRANCH_PREFIX/$worktree_name" "$worktree_path"
    fi
    
    # Calculate working directory
    local relative_path="${requested_dir#$flake_root}"
    local work_dir="$worktree_path${relative_path:+/$relative_path}"
    
    # Launch Claude via Python org
    cd "$ORG_PROJECT_DIR"
    nix develop -c python3 -c "
from application import start_worker_in_directory
result = start_worker_in_directory('$work_dir')
print(f'Worker: {result}')
"
}

main "$@"
```

## Key features
- **Worktree isolation**: Each feature in independent Git branch
- **Parallel development**: No merge conflicts during work
- **flake-based**: Worktrees created at flake.nix level
- **Reuse**: Existing worktrees automatically detected