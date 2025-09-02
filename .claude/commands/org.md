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

### Current System (Python-based)
For current tmux orchestration examples, see:
```
~/bin/src/develop/org/cli.sh.example
```

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