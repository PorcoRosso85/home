"""Application layer for org project - high-level orchestration functions."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from domain import Worker, WorkerRegistry, WorkerNotFoundError, WorkerValidationError
from infrastructure import TmuxConnection, TmuxConnectionError


# Constants
SESSION_NAME = "org-system"


def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


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


# === Naming Convention Utilities ===

def _directory_to_window_name(directory: str) -> str:
    """Convert directory path to tmux window name (our convention)."""
    return f"claude:{directory.replace('/', '_')}"


def _directory_to_jsonl_patterns(directory: str) -> List[str]:
    """Generate possible Claude history directory patterns.
    
    重要：jsonlディレクトリ名は本来一意だが、Claudeの実装が不明なため
    複数パターンで検索する。見つからないことより、確実に見つけることを優先。
    この実装は意図的にfuzzy/緩いマッチングを行う。
    
    Args:
        directory: Target directory path
        
    Returns:
        List of possible patterns (in priority order)
    """
    patterns = []
    # Pattern 1: No leading slash, hyphen separator
    patterns.append(directory.lstrip('/').replace('/', '-'))
    # Pattern 2: With leading hyphen
    patterns.append('-' + directory.lstrip('/').replace('/', '-'))
    # Pattern 3: Full path version
    patterns.append(directory.replace('/', '-'))
    return patterns


def _find_claude_history_path(directory: str) -> Optional[Path]:
    """Find actual Claude history directory.
    
    Returns first match found (assumes uniqueness in practice).
    None means no history exists (not an error).
    """
    base_path = Path.home() / ".claude/projects"
    if not base_path.exists():
        return None
        
    for pattern in _directory_to_jsonl_patterns(directory):
        candidate = base_path / pattern
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


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
        
        # Connect to tmux and check for duplicates
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
        
        # Return worker data
        worker_data = {
            "directory": directory,
            "pane_id": pane_id,
            "window_name": window.name
        }
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