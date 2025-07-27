# /org - Delegate tasks to multiple Claude instances

## Overview
Delegates tasks to Claude instances working in parallel using Git worktrees with sparse-checkout.

## Usage
```bash
/org <task_name> <target_directory> <description>
```

## Example
```bash
/org auth-feature src/auth "Implement JWT authentication with tests"
```

## How it works
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. Creates isolated Git worktree for the task
2. Sets up sparse-checkout for the target directory
3. Provides DB_URI environment variable for GraphDB access
4. Claude works autonomously based on directory context

## Directory-based context
Each Claude member:
- Identifies its location via pwd and flake.nix
- Queries GraphDB for expected state based on directory path
- Works autonomously to achieve the expected state
- Explains error context before querying solutions

## Template locations
```bash
# Organization coordination template
cat ~/bin/src/poc/develop/claude/org/main.sh.template

# Member tool templates
cat ~/bin/src/poc/develop/claude/member/main.sh.template
```

## Management commands
- `--list`: List active Claude processes
- `--cleanup`: Remove zombie worktrees
- `--status`: Show all task statuses
- `--resume-task ID`: Force resume specific task

## Directory structure
```
poc/develop/claude/
├── org/                    # Organization coordination
│   └── main.sh.template   # Minimal environment setup
└── member/                # Individual member tools
    ├── sdk/              # Execution environment
    ├── config/           # Configuration
    └── main.sh.template  # Directory context tools
```

## Key principles
- No spec_id needed (directory path is the context)
- No graph_context.json (direct GraphDB access via DB_URI)
- Stream.jsonl is automatically recorded (no explicit logging)
- Error handling includes background explanation