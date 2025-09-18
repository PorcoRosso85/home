"""Developer management module.

This module handles all Developer-related operations including:
- Starting Developer instances in new tmux windows
- Sending commands to Developers by directory
- Monitoring Developer status
- Cleaning up dead Developer windows
"""

import shlex
from pathlib import Path
from typing import Dict, Any, List

import libtmux

from variables import SESSION_NAME, DEVELOPER_WINDOW_PREFIX
from infrastructure import TmuxConnection, TmuxConnectionError, resolve_claude_launcher
from domain import is_developer_window, extract_directory_from_window_name


# Result pattern helpers
def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def _is_pane_alive(pane_id: str) -> bool:
    """Check if a pane is alive using tmux directly.
    
    Args:
        pane_id: Pane ID to check (e.g., '%0', '%1')
        
    Returns:
        bool: True if pane exists and is alive
    """
    import subprocess
    try:
        result = subprocess.run(
            ['tmux', 'list-panes', '-t', pane_id, '-F', '#{pane_id}'],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0 and pane_id in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def start_developer(task_directory: str) -> Dict[str, Any]:
    """Start a Developer in a new window for a specific task.
    
    Developers are started in new windows for isolated task execution.
    They can run in any directory (not limited to designers/).
    
    Args:
        task_directory: Directory where the developer should operate
        
    Returns:
        Dict with success/error status and window information
    """
    try:
        # Resolve and validate directory
        dir_path = Path(task_directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return _err(f"Directory does not exist: {task_directory}", "invalid_directory")
        
        directory = str(dir_path)
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        if not tmux.is_valid():
            return _err(f"Failed to create tmux connection: {tmux.get_init_error()}", "tmux_connection_failed")
            
        connect_result = tmux.connect()
        if not connect_result["ok"]:
            return _err(f"Failed to connect to tmux: {connect_result['error']}", "tmux_connect_failed")
        
        # Generate window name for developer
        window_name = f"developer:{directory.replace('/', '_')}"
        
        # Check for duplicate developer windows
        session_result = tmux.get_or_create_session()
        if not session_result["ok"]:
            return _err(f"Failed to get session: {session_result['error']}", "tmux_session_failed")
        session = session_result["data"]
        
        # Check for developer: prefix duplicate
        existing_window = session.find_where({"window_name": window_name})
        if existing_window:
            for pane in existing_window.panes:
                if _is_pane_alive(pane.id):
                    return _err(f"Developer already exists for directory: {directory}", "duplicate_developer")
        
        # Re-check just before creation (TOCTOU mitigation)
        existing_window = session.find_where({"window_name": window_name})
        if existing_window:
            for pane in existing_window.panes:
                if _is_pane_alive(pane.id):
                    return _err(f"Developer already exists for directory: {directory} (race condition detected)", "duplicate_developer")
        
        # Create new window for developer
        window = session.new_window(window_name=window_name)
        pane = window.panes[0] if window.panes else None
        
        if not pane:
            return _err("Failed to get pane in new window", "pane_error")
        
        # Navigate to task directory using quoted path
        quoted_dir = shlex.quote(directory)
        pane.send_keys(f"cd -- {quoted_dir}", enter=True)
        
        # Get Claude launch command from infrastructure module
        cmd_result = resolve_claude_launcher()
        if cmd_result['ok']:
            # Treat data as a string directly (no data['command'] reference)
            launch_command = cmd_result['data'] if isinstance(cmd_result['data'], str) else str(cmd_result['data'])
            pane.send_keys(launch_command, enter=True)
        else:
            return _err(f"Failed to resolve Claude launcher: {cmd_result['error']}", "launch_error")
        
        return _ok({
            "directory": directory,
            "window_id": window.id,
            "window_name": window_name,
            "pane_id": pane.id
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def send_command_to_developer_by_directory(directory: str, command: str) -> Dict[str, Any]:
    """Send command to a Developer window identified by directory.
    
    Args:
        directory: Directory path that identifies the Developer window
        command: Command to send to the Developer
        
    Returns:
        Dict with success/error status
    """
    try:
        # Resolve and validate directory
        dir_path = Path(directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return _err(f"Directory does not exist: {directory}", "invalid_directory")
        
        directory = str(dir_path)
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        if not tmux.is_valid():
            return _err(f"Failed to create tmux connection: {tmux.get_init_error()}", "tmux_connection_failed")
            
        connect_result = tmux.connect()
        if not connect_result["ok"]:
            return _err(f"Failed to connect to tmux: {connect_result['error']}", "tmux_connect_failed")
        
        # Get session
        session_result = tmux.get_or_create_session()
        if not session_result["ok"]:
            return _err(f"Failed to get session: {session_result['error']}", "tmux_session_failed")
        session = session_result["data"]
        
        # Find developer window for this directory (developer: prefix only)
        window_name = f"developer:{directory.replace('/', '_')}"
        window = session.find_where({"window_name": window_name})
        
        if not window:
            return _err(f"No developer found for directory: {directory}", "developer_not_found")
        
        # Get the first pane and send command
        pane = window.panes[0] if window.panes else None
        if not pane:
            return _err(f"No pane found in developer window for: {directory}", "pane_not_found")
        
        # Check if pane is alive before sending
        if not _is_pane_alive(pane.id):
            return _err(f"Developer pane is dead for directory: {directory}", "pane_dead")
        
        # Send the command
        pane.send_keys(command, enter=True)
        
        return _ok({
            "directory": directory,
            "command": command,
            "window_id": window.id,
            "pane_id": pane.id
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def get_all_developers_status() -> Dict[str, Any]:
    """Get status of all Developer windows.
    
    Returns:
        Dict with list of developers and their status (alive/dead)
    """
    try:
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        if not tmux.is_valid():
            return _err(f"Failed to create tmux connection: {tmux.get_init_error()}", "tmux_connection_failed")
            
        connect_result = tmux.connect()
        if not connect_result["ok"]:
            return _err(f"Failed to connect to tmux: {connect_result['error']}", "tmux_connect_failed")
        
        # Get session
        session_result = tmux.get_or_create_session()
        if not session_result["ok"]:
            return _err(f"Failed to get session: {session_result['error']}", "tmux_session_failed")
        session = session_result["data"]
        
        # Find all developer windows (developer: prefix only)
        developers = []
        for window in session.windows:
            if is_developer_window(window.name):
                # Extract directory from window name
                directory = extract_directory_from_window_name(window.name)
                
                # Check if first pane is alive
                pane = window.panes[0] if window.panes else None
                status = "alive" if pane and _is_pane_alive(pane.id) else "dead"
                
                developers.append({
                    "directory": directory,
                    "window_name": window.name,
                    "window_id": window.id,
                    "status": status
                })
        
        return _ok({
            "developers": developers,
            "total": len(developers)
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def clean_dead_developers_from_state() -> Dict[str, Any]:
    """Remove dead Developer windows from tmux.
    
    Identifies Developer windows with dead panes and removes them.
    
    Returns:
        Dict with number of windows removed
    """
    try:
        # Get all developers status first
        status_result = get_all_developers_status()
        if not status_result["ok"]:
            return status_result
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        if not tmux.is_valid():
            return _err(f"Failed to create tmux connection: {tmux.get_init_error()}", "tmux_connection_failed")
            
        connect_result = tmux.connect()
        if not connect_result["ok"]:
            return _err(f"Failed to connect to tmux: {connect_result['error']}", "tmux_connect_failed")
        
        # Get session
        session_result = tmux.get_or_create_session()
        if not session_result["ok"]:
            return _err(f"Failed to get session: {session_result['error']}", "tmux_session_failed")
        session = session_result["data"]
        
        # Find and remove dead developer windows
        removed = 0
        dead_developers = [d for d in status_result["data"]["developers"] if d["status"] == "dead"]
        
        for dev in dead_developers:
            window = session.find_where({"window_name": dev["window_name"]})
            if window:
                try:
                    window.kill_window()
                    removed += 1
                except Exception:
                    # Window might already be gone
                    pass
        
        return _ok({
            "removed": removed,
            "dead_developers": dead_developers
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")