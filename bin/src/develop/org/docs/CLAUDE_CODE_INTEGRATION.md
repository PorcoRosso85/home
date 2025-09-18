# Claude Code Integration for org System

## Overview
This document describes how the org system integrates with Claude Code for launching and managing worker instances.

## Claude Code Launch Mechanism

### Dependency
The org system depends on the Claude Code launcher scripts located at:
- `/home/nixos/bin/src/develop/claude/ui/claude-shell.sh` - Main launcher script
- `/home/nixos/bin/src/develop/claude/ui/scripts/launch-claude` - Core launch implementation

### Launch Command Structure

Claude Code can be launched in two ways:

1. **Direct command (if in PATH)**
   ```bash
   env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
   ```

2. **Via Nix run (fallback)**
   ```bash
   env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
   ```

### Integration Points for org System

#### infrastructure.py Implementation

```python
def launch_claude_code_in_pane(pane_id: str, directory: str) -> dict:
    """
    Launch Claude Code in a tmux pane
    
    Returns:
        dict: {'ok': True, 'data': {...}} or {'ok': False, 'error': {...}}
    """
    # Change to target directory
    result = send_keys_to_pane(pane_id, f"cd {directory}")
    if not result['ok']:
        return result
    
    # Launch Claude Code using the same mechanism as launch-claude script
    launch_command = get_claude_launch_command()
    if not launch_command['ok']:
        return launch_command
    
    result = send_keys_to_pane(pane_id, launch_command['data']['command'])
    return result
```

#### variables.py Configuration

```python
def get_claude_launch_command() -> dict:
    """
    Get the appropriate Claude Code launch command
    
    Checks if claude-code is in PATH, otherwise uses nix run
    """
    import shutil
    
    # Check if claude-code is available in PATH
    if shutil.which('claude-code'):
        command = 'env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions'
    else:
        # Use nix run as fallback
        command = 'env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions'
    
    return {
        'ok': True,
        'data': {
            'command': command,
            'environment': {
                'NIXPKGS_ALLOW_UNFREE': '1'
            }
        }
    }
```

## Required Environment Variables

- `NIXPKGS_ALLOW_UNFREE=1` - Required for Claude Code to run (proprietary software)

## Launch Sequence in org System

1. **Check for existing worker** (domain.py)
   - Load state from `~/.org-state.json`
   - Verify no worker exists for target directory

2. **Create tmux pane** (infrastructure.py)
   - Connect to tmux server
   - Create or get session
   - Create new pane for worker

3. **Launch Claude Code** (infrastructure.py)
   - Change to target directory
   - Execute launch command
   - Record pane ID in state

4. **Verify launch** (application.py)
   - Check pane is alive
   - Update state file
   - Return success/failure

## Error Handling

### Common Launch Failures

1. **Claude Code not installed**
   - Fallback to nix run method
   - Requires internet connection for first download

2. **Directory access issues**
   - Verify directory exists and is accessible
   - Return appropriate error message

3. **tmux pane creation failure**
   - Check tmux server is running
   - Ensure session exists

## Testing Considerations

### Unit Tests
```python
def test_get_claude_launch_command():
    """Test command selection logic"""
    result = get_claude_launch_command()
    assert result['ok']
    assert 'claude-code' in result['data']['command']
    assert '--dangerously-skip-permissions' in result['data']['command']
```

### Integration Tests
```python
def test_launch_claude_code_in_pane():
    """Test actual Claude Code launch in tmux"""
    # Create test pane
    # Launch Claude Code
    # Verify process is running
    # Cleanup
```

## Future Improvements

1. **Launch verification**
   - Add health check after launch
   - Implement retry mechanism

2. **Configuration options**
   - Support for custom Claude Code flags
   - Configurable launch timeout

3. **MCP server integration**
   - Ensure MCP servers are configured (already handled by claude-shell.sh)
   - Pass project-specific MCP configurations if needed

## Related Files

- `README.md` - User-facing documentation
- `ARCHITECTURE.md` - System architecture overview
- `cli.sh.example` - CLI usage examples
- `/home/nixos/bin/src/develop/claude/ui/` - Claude launcher implementation