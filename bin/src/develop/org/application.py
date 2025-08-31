"""Application layer for org project - high-level orchestration functions."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from domain import Worker, WorkerRegistry, WorkerNotFoundError, WorkerValidationError
from infrastructure import TmuxConnection, TmuxConnectionError


# Constants
SESSION_NAME = "org-system"
STATE_FILE = Path.home() / ".org-state.json"


def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def _load_state() -> Dict[str, Any]:
    """Load worker state from disk."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"workers": []}
    except Exception:
        return {"workers": []}


def _save_state(state: Dict[str, Any]) -> None:
    """Save worker state to disk."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass  # Fail silently for state persistence


def _is_pane_alive(pane_id: str) -> bool:
    """Check if a tmux pane is still alive."""
    try:
        import subprocess
        result = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{pane_id}"],
            capture_output=True, text=True, check=False
        )
        return pane_id in result.stdout.split('\n')
    except Exception:
        return False


def start_worker_in_directory(directory: str) -> Dict[str, Any]:
    """Start Claude Code worker in specified directory.
    
    Checks for duplicates, creates tmux window, and launches Claude.
    
    Args:
        directory: Target directory path for the worker
        
    Returns:
        Dict with success/error and worker data including pane_id
    """
    try:
        # Validate directory exists
        dir_path = Path(directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return _err(f"Directory does not exist: {directory}", "invalid_directory")
        
        directory = str(dir_path)
        
        # Load current state and check for duplicates
        state = _load_state()
        for worker_data in state["workers"]:
            if worker_data["directory"] == directory and _is_pane_alive(worker_data["pane_id"]):
                return _err(f"Worker already running in directory: {directory}", "duplicate_worker")
        
        # Connect to tmux and create worker
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Check if window already exists
        existing_window = tmux.find_worker_window_by_directory(directory)
        if existing_window:
            # Check if any pane in the window is alive
            for pane in existing_window.panes:
                if _is_pane_alive(pane.id):
                    return _err(f"Worker window already exists for directory: {directory}", "duplicate_worker")
        
        # Create new window and launch Claude
        window = tmux.create_worker_window(directory)
        tmux.launch_claude_in_window(window, directory)
        
        # Get pane ID for tracking
        pane_id = window.panes[0].id if window.panes else None
        if not pane_id:
            return _err("Failed to get pane ID", "pane_error")
        
        # Update state
        worker_data = {
            "directory": directory,
            "pane_id": pane_id,
            "window_name": window.name
        }
        state["workers"].append(worker_data)
        _save_state(state)
        
        return _ok(worker_data)
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


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


def clean_dead_workers_from_state() -> Dict[str, Any]:
    """Remove dead worker windows and clean state file.
    
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
        
        # Clean state file - remove entries for dead panes
        state = _load_state()
        if "workers" in state:
            alive_workers = []
            for worker_data in state["workers"]:
                if _is_pane_alive(worker_data["pane_id"]):
                    alive_workers.append(worker_data)
            
            state["workers"] = alive_workers
            _save_state(state)
        
        return _ok({"removed": removed_count})
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")