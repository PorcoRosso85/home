# org - tmux-based Multi-Agent Orchestration System

Multiple Claude Code instances management and control orchestration system

## What This System Guarantees

### Can Do (What to Expect)

1. **Duplicate Prevention**
   - No multiple Claude Code instances in the same directory
   - Warns and blocks new launches if already running

2. **Reliable Command Delivery**
   - Commands reach the specified worker reliably
   - No accidental cross-worker command sending
   - Managed by immutable Pane ID identifiers

3. **Persistent Sessions**
   - Workers continue running after SSH disconnect
   - Work continues even after closing terminal
   - Check status anytime with tmux attach

### Cannot Do (Do Not Expect)

1. **Automatic Result Retrieval**
   - No external result fetching from workers
   - Each Claude Code completes work independently

2. **Complex Synchronization**
   - No inter-worker dependency management
   - No pipeline execution support

3. **Auto Error Recovery**
   - No automatic restart of dead workers (manual restart required)
   - No task retry or re-execution

## Prerequisites

- tmux installed
- libtmux installed (`pip install libtmux`)
- Claude Code available

## Basic Usage

### 1. Start Worker
```bash
# Start Claude Code in project A
nix develop -c python3 -c "
from application import start_worker_in_directory
result = start_worker_in_directory('/path/to/project-a')
if result['ok']:
    print(f\"Started worker {result['data']['pane_id']} for {result['data']['directory']}\")
else:
    print(f\"Error: {result['error']['message']}\")
"

# Result:
# - Duplicate check performed
# - Claude Code launched in new tmux window
# - Pane ID recorded for tracking
```

### 2. Send Command
```bash
# Send command to project A worker
nix develop -c python3 -c "
from application import send_command_to_worker_by_directory
result = send_command_to_worker_by_directory('/path/to/project-a', 'Fix bugs in this file')
if result['ok']:
    print('Command sent successfully')
else:
    print(f\"Error: {result['error']['message']}\")
"

# Result:
# - Identifies window for directory
# - Sends command reliably to that pane
```

### 3. Check Status
```bash
# Show all workers status
nix develop -c python3 -c "
from application import get_all_workers_status
result = get_all_workers_status()
if result['ok']:
    for worker in result['data']['workers']:
        print(f\"Pane {worker['pane_id']}: {worker['directory']} ({worker['status']})\")
    print(f\"Total: {result['data']['total']} workers\")
else:
    print(f\"Error: {result['error']['message']}\")
"

# Example output:
# Pane %0: /path/to/project-a (alive)
# Pane %1: /path/to/project-b (alive)
# Pane %2: /path/to/project-c (dead)
# Total: 3 workers
```

### 4. Clean Dead Workers
```bash
# Remove dead workers from state
nix develop -c python3 -c "
from application import clean_dead_workers_from_state
result = clean_dead_workers_from_state()
if result['ok']:
    print(f\"Cleaned {result['data']['removed']} dead workers\")
else:
    print(f\"Error: {result['error']['message']}\")
"
```

### 5. Manual Check (When Needed)
```bash
# Attach to tmux session for direct inspection
tmux attach-session -t org-system
# Ctrl-b d to detach (workers continue)
```

## Safety Guarantees

### Directory-based Exclusive Control
- Only one Claude Code instance per directory
- Always checks existing processes at startup
- Managed via tmux window naming convention

### Reliable Identification via Window Naming
- Window names follow pattern: `claude:_path_with_underscores`
- Example: `/home/user/project` → `claude:_home_user_project`
- Commands are sent to the correct pane via window lookup
- No external state file needed - tmux is the single source of truth

## Design Philosophy

### KISS (Keep It Simple, Stupid)
- No complex features like result retrieval
- Each Claude Code completes work independently
- Maximize use of basic tmux features

### YAGNI (You Ain't Gonna Need It)
- No advanced features like auto-recovery
- Implement only minimum necessary features
- Manual operation suffices where automation isn't critical

## Limitations

1. **Machine Restart**
   - tmux sessions are lost
   - Manual restart required
   - (tmux-continuum auto-restore for future)

2. **Error Handling**
   - No notification when Claude Code stops with error
   - Check periodically with `status` command

3. **Scalability**
   - Designed for ~10 concurrent workers
   - Beyond that is unsupported

## Troubleshooting

### Q: Worker won't start
A: Check if Claude Code already running in same directory
```bash
nix develop -c python3 -c "
from application import get_all_workers_status
result = get_all_workers_status()
if result['ok']:
    for worker in result['data']['workers']:
        print(f\"{worker['directory']}: {worker['status']}\")
"
ps aux | grep claude
```

### Q: Command not delivered
A: Verify window exists and pane is alive
```bash
tmux list-windows -t org-system -F "#{window_name}"
tmux list-panes -a -F "#{pane_id} #{pane_current_path}"
```

### Q: Session cleanup needed
A: Manual reset
```bash
tmux kill-session -t org-system
# Restart workers as needed
```

## License

MIT

## Contributing

Issues and PRs welcome. Please follow KISS/YAGNI principles.