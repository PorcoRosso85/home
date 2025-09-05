# org - tmux-based Multi-Agent Orchestration System

Orchestrates multiple AI CLI tool instances via tmux windows with directory-based isolation.

## Orchestrator Pattern

**User → Worker 0 (Orchestrator) → Workers 1,2,3...**

Instead of directly managing multiple Claude instances, you communicate with a single orchestrator (Worker 0) that:
- Monitors all worker states (`get_all_workers_status()`)
- Routes commands to any worker (`send_command_to_worker_by_directory()`)
- Reads worker histories (`get_claude_history()`)
- Manages worker lifecycle (start/stop/clean)

This eliminates the need to switch between multiple tmux windows manually.

## Core Specifications

1. **Architecture**: Extensible multi-tool support via function composition
2. **Isolation**: One directory = One tmux window = One tool instance
3. **Identification**: Window naming pattern `{tool}:_path_with_underscores`
4. **History**: Tool-specific locations (Claude: `~/.claude/projects/*.jsonl`)
5. **Safety**: Duplicate prevention + reliable command routing via window names

## API Functions (Current: Claude Implementation)

| Function | Purpose | Returns |
|----------|---------|---------|
| `start_worker_in_directory(path)` | Launch tool in directory | `{ok, data: {pane_id, directory}}` |
| `send_command_to_worker_by_directory(path, cmd)` | Send command to specific worker | `{ok, data: {pane_id, directory, command}}` |
| `get_all_workers_status()` | List all workers with alive/dead status | `{ok, data: {workers[], total}}` |
| `clean_dead_workers_from_state()` | Remove dead worker windows | `{ok, data: {removed}}` |
| `check_worker_has_history(path)` | Verify tool started logging | `{ok, data: {has_history, file_count}}` |
| `get_claude_history(path, last_n)` | Read Claude conversation from JSONL | `{ok, data: {messages[], total_messages}}` |

## Prerequisites

- tmux
- libtmux (`pip install libtmux` or via nix flake)
- AI CLI tool (Currently: Claude Code)

## Usage Examples

### Start Worker
```bash
nix develop -c python3 -c "
from application import start_worker_in_directory
result = start_worker_in_directory('/path/to/project')
print(result)"
```

### Send Command
```bash
nix develop -c python3 -c "
from application import send_command_to_worker_by_directory
result = send_command_to_worker_by_directory('/path/to/project', 'analyze code')
print(result)"
```

### Check History
```bash
nix develop -c python3 -c "
from application import get_claude_history
result = get_claude_history('/path/to/project', last_n=10)
if result['ok']:
    for msg in result['data']['messages']:
        print(f\"{msg.get('role')}: {msg.get('content')[:100]}...\")"
```

### Monitor Status
```bash
nix develop -c python3 -c "
from application import get_all_workers_status
result = get_all_workers_status()
for worker in result['data']['workers']:
    print(f\"{worker['directory']}: {worker['status']}\")"
```

## System Guarantees

### ✅ What Works
- **Duplicate Prevention**: Blocks multiple instances per directory
- **Reliable Delivery**: Commands routed correctly via window names
- **Session Persistence**: Survives SSH disconnects (tmux feature)
- **History Access**: Read conversations from JSONL without tmux capture

### ❌ Limitations
- **No Auto-Recovery**: Dead workers need manual restart
- **No Result Streaming**: Check history via JSONL files
- **No Inter-Worker Sync**: Each worker operates independently
- **Session Loss on Reboot**: tmux sessions not persistent across machine restarts

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Worker won't start | Check existing: `get_all_workers_status()` |
| Command not delivered | Verify window: `tmux list-windows -t org-system` |
| Can't read history | Check path: `~/.claude/projects/` |
| Session cleanup needed | Kill all: `tmux kill-session -t org-system` |

## Adding New Tools

The architecture supports any CLI tool via function composition:

```python
# Add new tool in 3 functions + 1 partial application
def codex_window_name(dir): return f"codex:{dir.replace('/', '_')}"
def codex_launch_cmd(): return {"ok": True, "data": "codex"}
def codex_patterns(dir): return [dir.replace('/', '_')]

import functools
start_codex = functools.partial(_generic_start_worker, 
                                window_namer=codex_window_name,
                                launch_cmd=codex_launch_cmd)
```

## Worker Placement Rules

### Orchestrator → Managers
- **Tool**: application.py (managers/ directories only)
- **Placement**: Same window, different panes
- **Directories**: `/managers/x`, `/managers/y`, `/managers/z`
- **Restriction**: Only managers/ paths are accepted

### Managers → Workers  
- **Tool**: Task tool or direct Claude launch
- **Placement**: Separate windows for each worker
- **Directories**: Any project path (no restrictions)

### Automatic Placement Logic
- `/managers/*` paths → Pane mode (same window)
- Other paths → Window mode (separate windows)
- Orchestrator can only manage managers/ directories

## Design Principles

- **KISS**: Minimal features, maximum clarity
- **YAGNI**: No premature optimization
- **Single Source of Truth**: tmux state only (no external state files)

## License

MIT