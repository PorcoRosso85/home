"""Application layer for org project - high-level orchestration functions."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import functools
import subprocess

from infrastructure import TmuxConnection, TmuxConnectionError
import domain


# Constants
SESSION_NAME = "org-system"


def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def _is_pane_alive(pane_id: str) -> bool:
    """Check if a tmux pane is alive.
    
    Args:
        pane_id: tmux pane ID (e.g., '%1', '%2')
        
    Returns:
        bool: True if pane exists and is alive, False otherwise
    """
    try:
        # List all pane IDs to see if this one exists
        result = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{pane_id}"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return False
        
        # Check if our pane_id is in the output
        pane_ids = result.stdout.strip().split('\n')
        return pane_id in pane_ids
        
    except Exception:
        return False


# === Multi-tool Support ===
# To add a new tool, create three functions and use functools.partial:
# 1. window_namer: Callable[[str], str] - converts directory to window name
# 2. launch_command: Callable[[], Dict[str, Any]] - returns command to launch tool
# 3. history_patterns: Callable[[str], List[str]] - generates history directory patterns
# Example: new_tool_start = functools.partial(_generic_start_worker, window_namer=my_namer, launch_cmd=my_cmd)

# Tool-specific function types
WindowNamer = Callable[[str], str]
LaunchCommand = Callable[[], Dict[str, Any]]  
HistoryPatterns = Callable[[str], List[str]]

def _generic_start_worker(directory: str, window_namer: WindowNamer, launch_cmd: LaunchCommand) -> Dict[str, Any]:
    """Generic worker start function."""
    try:
        dir_path = Path(directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return _err(f"Directory does not exist: {directory}", "invalid_directory")
        
        directory = str(dir_path)
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Check for duplicates using tool-specific window naming
        session = tmux.get_or_create_session()
        window_name = window_namer(directory)
        existing_window = session.find_where({"window_name": window_name})
        
        if existing_window:
            for pane in existing_window.panes:
                if _is_pane_alive(pane.id):
                    return _err(f"Worker window already exists for directory: {directory}", "duplicate_worker")
        
        # Create window and launch tool
        window = session.new_window(window_name=window_name)
        pane = window.panes[0] if window.panes else None
        if not pane:
            return _err("Failed to get pane", "pane_error")
        
        pane.send_keys(f"cd {directory}", enter=True)
        cmd_result = launch_cmd()
        if cmd_result['ok']:
            pane.send_keys(cmd_result['data']['command'], enter=True)
        
        return _ok({"directory": directory, "pane_id": pane.id, "window_name": window.name})
        
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")

def _generic_find_history_path(directory: str, history_patterns: HistoryPatterns) -> Optional[Path]:
    """Generic function to find tool history directory."""
    base_path = Path.home() / ".claude/projects"  # Could be made configurable
    if not base_path.exists():
        return None
        
    for pattern in history_patterns(directory):
        candidate = base_path / pattern
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None

# === Naming Convention Utilities ===


# Create Claude-specific history finder using partial
_find_claude_history_path = functools.partial(
    _generic_find_history_path,
    history_patterns=domain.generate_claude_history_patterns
)


# Claude-specific functions using functools.partial for backward compatibility
start_worker_in_directory = functools.partial(
    _generic_start_worker,
    window_namer=domain.generate_claude_window_name,
    launch_cmd=domain.get_claude_launch_command
)


def send_command_to_worker_by_directory(directory: str, command: str) -> Dict[str, Any]:
    """Send command to worker in specified directory.
    
    Args:
        directory: Target directory path
        command: Command to send to the worker
        
    Returns:
        Dict with success/error status
    """
    try:
        # Validate inputs
        if not command.strip():
            return _err("Command cannot be empty", "invalid_command")
        
        directory = str(Path(directory).resolve())
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Find worker window
        window = tmux.find_worker_window_by_directory(directory)
        if not window:
            return _err(f"No worker found for directory: {directory}", "worker_not_found")
        
        # Check if pane is alive
        if not window.panes:
            return _err(f"No panes found in worker window for directory: {directory}", "no_panes")
        
        pane = window.panes[0]
        if not _is_pane_alive(pane.id):
            return _err(f"Worker pane is dead for directory: {directory}", "dead_pane")
        
        # Send command
        pane.send_keys(command)
        
        return _ok({"directory": directory, "command": command, "pane_id": pane.id})
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def get_all_workers_status() -> Dict[str, Any]:
    """Get status of all workers (alive/dead).
    
    Returns:
        Dict with workers list and total count
    """
    try:
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Get all worker windows
        worker_windows = tmux.list_all_worker_windows()
        
        workers = []
        for window in worker_windows:
            # Extract directory from window name (claude:path_with_underscores)
            directory = window.name[7:].replace('_', '/')  # Remove "claude:" prefix
            
            # Check pane status
            status = "dead"
            pane_id = None
            if window.panes:
                pane = window.panes[0]
                pane_id = pane.id
                if _is_pane_alive(pane_id):
                    status = "alive"
            
            workers.append({
                "directory": directory,
                "pane_id": pane_id,
                "window_name": window.name,
                "status": status
            })
        
        return _ok({
            "workers": workers,
            "total": len(workers)
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def check_worker_has_history(directory: str) -> Dict[str, Any]:
    """Check if Claude history exists for a worker (verification only).
    
    This is for verifying Claude Code started successfully and is generating history.
    Does NOT read the actual history content, just checks existence.
    
    Args:
        directory: Target directory path
        
    Returns:
        Dict with history existence status
    """
    try:
        dir_path = Path(directory).resolve()
        history_path = _find_claude_history_path(str(dir_path))
        
        if not history_path:
            return _ok({
                "directory": str(dir_path),
                "has_history": False,
                "message": "No history directory found"
            })
        
        # Check if any jsonl files exist
        jsonl_files = list(history_path.glob("*.jsonl"))
        has_jsonl = len(jsonl_files) > 0
        
        return _ok({
            "directory": str(dir_path),
            "has_history": has_jsonl,
            "history_path": str(history_path),
            "file_count": len(jsonl_files),
            "message": f"Found {len(jsonl_files)} conversation file(s)" if has_jsonl else "Directory exists but no jsonl files yet"
        })
        
    except Exception as e:
        return _err(f"Failed to check history: {str(e)}", "check_error")


def get_claude_history(directory: str, last_n: int = 20) -> Dict[str, Any]:
    """Get Claude conversation history for a directory (search feature).
    
    Reads actual conversation content from jsonl files.
    
    Args:
        directory: Target directory path
        last_n: Number of recent messages to retrieve
        
    Returns:
        Dict with conversation messages or error
    """
    try:
        import json
        
        dir_path = Path(directory).resolve()
        history_path = _find_claude_history_path(str(dir_path))
        
        if not history_path:
            return _err(f"No history found for directory: {directory}", "history_not_found")
        
        # Get latest jsonl file
        jsonl_files = sorted(history_path.glob("*.jsonl"), key=lambda x: x.stat().st_mtime)
        if not jsonl_files:
            return _err("No conversation files found", "no_jsonl_files")
        
        latest_file = jsonl_files[-1]
        
        # Read messages from latest file
        messages = []
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Get last N messages
        recent_messages = messages[-last_n:] if len(messages) > last_n else messages
        
        return _ok({
            "directory": str(dir_path),
            "history_path": str(history_path),
            "latest_file": latest_file.name,
            "messages": recent_messages,
            "total_messages": len(messages),
            "showing": len(recent_messages)
        })
        
    except Exception as e:
        return _err(f"Failed to read history: {str(e)}", "read_error")


def clean_dead_workers_from_state() -> Dict[str, Any]:
    """Remove dead worker windows.
    
    Returns:
        Dict with count of removed workers
    """
    try:
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Get all worker windows
        worker_windows = tmux.list_all_worker_windows()
        
        removed_count = 0
        for window in worker_windows:
            # Check if any pane in window is alive
            has_live_pane = False
            for pane in window.panes:
                if _is_pane_alive(pane.id):
                    has_live_pane = True
                    break
            
            # Kill window if no live panes
            if not has_live_pane:
                window.kill_window()
                removed_count += 1
        
        return _ok({"removed": removed_count})
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")