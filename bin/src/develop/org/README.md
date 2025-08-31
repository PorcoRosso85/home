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
./cli.sh start-worker /path/to/project-a

# Result:
# - Duplicate check performed
# - Claude Code launched in new tmux pane
# - Pane ID recorded in state file
```

### 2. Send Command
```bash
# Send command to project A worker
./cli.sh send-command /path/to/project-a "Fix bugs in this file"

# Result:
# - Identifies Pane ID for directory
# - Sends command reliably to that pane
```

### 3. Check Status
```bash
# Show all worker status
./cli.sh status

# Example output:
# Pane %0: /path/to/project-a (alive)
# Pane %1: /path/to/project-b (alive)
# Pane %2: /path/to/project-c (dead)
```

### 4. Manual Check (When Needed)
```bash
# Attach to tmux session for direct inspection
tmux attach-session -t org-system
# Ctrl-b d to detach (workers continue)
```

## Safety Guarantees

### Directory-based Exclusive Control
- Only one Claude Code instance per directory
- Always checks existing processes at startup
- Managed via state file (`~/.org-state.json`)

### Reliable Identification via Pane ID
```json
{
  "workers": {
    "%0": "/home/user/project-a",
    "%1": "/home/user/project-b"
  }
}
```
- Pane IDs (`%0`, `%1`, etc.) are immutable
- One-to-one mapping of directory to Pane ID
- Commands always sent by Pane ID

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
./cli.sh status
ps aux | grep claude
```

### Q: Command not delivered
A: Verify Pane ID is correct
```bash
./cli.sh status
tmux list-panes -F "#{pane_id} #{pane_current_path}"
```

### Q: State file corrupted
A: Manual reset
```bash
rm ~/.org-state.json
tmux kill-session -t org-system
# Restart workers
```

## License

MIT

## Contributing

Issues and PRs welcome. Please follow KISS/YAGNI principles.