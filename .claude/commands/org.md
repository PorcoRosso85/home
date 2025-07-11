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
1. Creates isolated Git worktree for the task
2. Sets up sparse-checkout for the target directory
3. Launches Claude with the task description
4. Claude works autonomously in the isolated environment

## Template location
View the evolved org template:
```bash
cat ~/bin/src/poc/develop/claude/org/main.sh.template
```

## Member tools
Individual member tools are available at:
```bash
cat ~/bin/src/poc/develop/claude/member/main.sh.template
```

## Advanced options (from evolved template)
- `--spec-id`: Use GraphDB specification
- `--resume`: Resume previous task
- `--test-driven`: Start with test implementation
- `--list`: List active Claude processes
- `--cleanup`: Remove zombie worktrees
- `--status`: Show all task statuses

## Directory structure
```
poc/develop/claude/
├── org/                    # Organization coordination
│   └── main.sh.template   # Org-level guardrails
└── member/                # Individual member tools
    ├── sdk/              # Execution environment
    ├── config/           # Configuration
    └── main.sh.template  # Individual tool templates
```