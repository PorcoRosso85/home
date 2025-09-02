# /org - Orchestrate multiple Claude workers via tmux

## Overview
Manages multiple Claude Code instances in parallel using tmux windows, with directory-based isolation.

## Usage
```bash
/org <command> <directory> [message]
```

## Commands
- `start <directory>` - Start new Claude worker in directory
- `send <directory> <message>` - Send command to worker
- `status` - Show all workers status
- `clean` - Remove dead workers
- `history <directory>` - Get Claude conversation history

## Example
```bash
# Start worker
/org start /home/nixos/bin/src/poc/auth-feature

# Send command
/org send /home/nixos/bin/src/poc/auth-feature "Implement JWT authentication"

# Check status
/org status
```

## How it works
1. Uses Python application.py in ~/bin/src/develop/org/
2. Creates tmux window named `claude:_path_with_underscores`
3. Launches Claude Code with `nix run` command
4. Routes commands via tmux pane IDs
5. Tracks history in ~/.claude/projects/*.jsonl

## Architecture
```
User → org (orchestrator) → tmux windows → Claude instances
          ├── start_worker_in_directory()
          ├── send_command_to_worker_by_directory()
          ├── get_all_workers_status()
          └── get_claude_history()
```

## Implementation
```bash
cd ~/bin/src/develop/org
nix develop -c python3 -c "
from application import start_worker_in_directory
result = start_worker_in_directory('$TARGET_DIR')
print(result)
"
```

## Key features
- **Isolation**: One directory = One tmux window = One Claude instance
- **Duplicate prevention**: Checks for existing workers before starting
- **Dead worker cleanup**: Removes crashed instances
- **History tracking**: Reads Claude's JSONL conversation logs