"""Application layer for org project - high-level orchestration functions."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import functools
import subprocess

from infrastructure import TmuxConnection, TmuxConnectionError
import domain


# Constants
def get_session_name() -> str:
    """Get current tmux session name from environment.
    
    Returns the session name from $TMUX environment variable if available,
    otherwise returns default 'org-system'.
    """
    tmux_env = os.environ.get('TMUX', '')
    if tmux_env:
        # $TMUX format: /tmp/tmux-1000/default,pid,session_id
        # Extract session name using tmux command
        try:
            result = subprocess.run(
                ['tmux', 'display-message', '-p', '#{session_name}'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
    # Fallback to default
    return "org-system"

SESSION_NAME = get_session_name()


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
        
        # Check if directory is within managers/ subdirectory
        org_base = Path(__file__).parent.resolve()  # org directory
        managers_base = org_base / "managers"
        
        # Check if the resolved path is within managers/
        try:
            dir_path.relative_to(managers_base)
        except ValueError:
            # Path is not within managers/
            return _err(
                f"Workers can only be started in managers/ subdirectories. Got: {directory}",
                "invalid_location"
            )
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


def start_manager(manager_id: str) -> Dict[str, Any]:
    """Start a Manager in a new pane in the current window.
    
    Managers (x, y, z) are started in panes within the orchestrator's window.
    They run in managers/x, managers/y, or managers/z directories.
    
    Args:
        manager_id: Manager identifier ('x', 'y', or 'z')
        
    Returns:
        Dict with success/error status and pane information
    """
    try:
        # Validate manager_id
        if manager_id not in ['x', 'y', 'z']:
            return _err(f"Invalid manager_id: {manager_id}. Must be 'x', 'y', or 'z'", "invalid_manager")
        
        # Build manager directory path
        org_base = Path(__file__).parent.resolve()
        manager_dir = org_base / "managers" / manager_id
        
        if not manager_dir.exists() or not manager_dir.is_dir():
            return _err(f"Manager directory does not exist: {manager_dir}", "missing_directory")
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Get current window (orchestrator window)
        session = tmux.get_or_create_session()
        current_window = session.attached_window
        
        if not current_window:
            return _err("No active window found", "no_window")
        
        # Check if manager is already running in this window
        for pane in current_window.panes:
            try:
                # Get current directory of the pane
                pane_cwd = pane.cmd('display-message', '-p', '#{pane_current_path}').stdout[0]
                if pane_cwd.strip() == str(manager_dir):
                    if _is_pane_alive(pane.id):
                        return _err(f"Manager {manager_id} is already running in pane {pane.id}", "duplicate_manager")
            except:
                continue
        
        # Create new pane in current window
        new_pane = current_window.split_window(vertical=False)  # Horizontal split
        
        # Navigate to manager directory and start Claude
        new_pane.send_keys(f"cd {manager_dir}", enter=True)
        
        # Get Claude launch command
        cmd_result = domain.get_claude_launch_command()
        if cmd_result['ok']:
            new_pane.send_keys(cmd_result['data']['command'], enter=True)
        else:
            return _err(f"Failed to get launch command: {cmd_result['error']['message']}", "launch_error")
        
        return _ok({
            "manager_id": manager_id,
            "directory": str(manager_dir),
            "pane_id": new_pane.id,
            "window_id": current_window.id
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def start_worker(task_directory: str) -> Dict[str, Any]:
    """Start a Worker in a new window for a specific task.
    
    Workers are started in new windows for isolated task execution.
    They can run in any directory (not limited to managers/).
    
    Args:
        task_directory: Directory where the worker should operate
        
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
        tmux.connect()
        
        # Generate window name for worker
        window_name = f"worker:{directory.replace('/', '_')}"
        
        # Check for duplicate worker windows
        session = tmux.get_or_create_session()
        existing_window = session.find_where({"window_name": window_name})
        
        if existing_window:
            for pane in existing_window.panes:
                if _is_pane_alive(pane.id):
                    return _err(f"Worker already exists for directory: {directory}", "duplicate_worker")
        
        # Create new window for worker
        window = session.new_window(window_name=window_name)
        pane = window.panes[0] if window.panes else None
        
        if not pane:
            return _err("Failed to get pane in new window", "pane_error")
        
        # Navigate to task directory and start Claude
        pane.send_keys(f"cd {directory}", enter=True)
        
        # Get Claude launch command
        cmd_result = domain.get_claude_launch_command()
        if cmd_result['ok']:
            pane.send_keys(cmd_result['data']['command'], enter=True)
        else:
            return _err(f"Failed to get launch command: {cmd_result['error']['message']}", "launch_error")
        
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


def send_command_to_manager(manager_id: str, command: str) -> Dict[str, Any]:
    """Send command to a Manager pane.
    
    Sends a command to a Manager (x, y, or z) running in a pane.
    The Manager must be already running in the current window.
    
    Args:
        manager_id: Manager identifier ('x', 'y', or 'z')
        command: Command to send to the Manager
        
    Returns:
        Dict with success/error status
    """
    try:
        # Validate inputs
        if manager_id not in ['x', 'y', 'z']:
            return _err(f"Invalid manager_id: {manager_id}. Must be 'x', 'y', or 'z'", "invalid_manager")
        
        if not command.strip():
            return _err("Command cannot be empty", "invalid_command")
        
        # Build manager directory path
        org_base = Path(__file__).parent.resolve()
        manager_dir = org_base / "managers" / manager_id
        
        if not manager_dir.exists():
            return _err(f"Manager directory does not exist: {manager_dir}", "missing_directory")
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        tmux.connect()
        
        # Get current window
        session = tmux.get_or_create_session()
        current_window = session.attached_window
        
        if not current_window:
            return _err("No active window found", "no_window")
        
        # Find the Manager pane in current window
        manager_pane = None
        for pane in current_window.panes:
            try:
                # Get current directory of the pane
                pane_cwd = pane.cmd('display-message', '-p', '#{pane_current_path}').stdout[0]
                if pane_cwd.strip() == str(manager_dir):
                    if _is_pane_alive(pane.id):
                        manager_pane = pane
                        break
            except:
                continue
        
        if not manager_pane:
            return _err(f"Manager {manager_id} is not running. Start it first with start_manager('{manager_id}')", "manager_not_found")
        
        # Send the command to the Manager pane
        manager_pane.send_keys(command, enter=True)
        
        return _ok({
            "manager_id": manager_id,
            "command": command,
            "pane_id": manager_pane.id,
            "directory": str(manager_dir)
        })
        
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
        
        # For multi-line tools like Claude, ensure submission with Enter
        # This helps when the tool is waiting for explicit submission
        if command.strip():  # Only add Enter after non-empty commands
            import time
            time.sleep(0.1)  # Small delay to ensure command is received
            pane.send_keys('', enter=True)  # Send actual Enter key
        
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
        
        # Get all jsonl files, prefer larger ones (more content)
        jsonl_files = sorted(history_path.glob("*.jsonl"), key=lambda x: x.stat().st_size, reverse=True)
        if not jsonl_files:
            return _err("No conversation files found", "no_jsonl_files")
        
        # Collect ALL data from ALL files (fuzzy approach)
        all_messages = []
        all_raw_data = []
        files_read = []
        
        for jsonl_file in jsonl_files:
            file_messages = []
            file_raw = []
            
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        file_raw.append(data)  # Keep raw data for diagnostics
                        
                        # Try multiple extraction patterns (fuzzy matching)
                        extracted = None
                        
                        # Pattern 1: Claude UI format with message field
                        if 'message' in data and data['message']:
                            extracted = data['message']
                        # Pattern 2: Direct message format
                        elif 'role' in data:
                            extracted = data
                        # Pattern 3: Content with role in separate fields
                        elif 'content' in data:
                            extracted = {
                                'role': data.get('type', 'unknown'),
                                'content': data['content']
                            }
                        
                        if extracted:
                            file_messages.append(extracted)
                            
                    except json.JSONDecodeError as e:
                        # Keep going, don't fail on bad lines
                        continue
            
            if file_messages or file_raw:
                files_read.append({
                    'file': jsonl_file.name,
                    'messages': len(file_messages),
                    'raw_lines': len(file_raw)
                })
                all_messages.extend(file_messages)
                all_raw_data.extend(file_raw)
        
        # If no messages extracted, return raw data for debugging
        if not all_messages and all_raw_data:
            return _ok({
                "directory": str(dir_path),
                "history_path": str(history_path),
                "files_read": files_read,
                "messages": [],  # No messages extracted
                "raw_data": all_raw_data[-last_n:],  # Show raw data for debugging
                "total_messages": 0,
                "total_raw_lines": len(all_raw_data),
                "showing": min(last_n, len(all_raw_data)),
                "note": "No messages could be extracted, showing raw JSONL data"
            })
        
        # Return messages if found
        messages = all_messages
        
        # Get last N messages
        recent_messages = messages[-last_n:] if len(messages) > last_n else messages
        
        return _ok({
            "directory": str(dir_path),
            "history_path": str(history_path),
            "files_read": files_read,
            "messages": recent_messages,
            "total_messages": len(messages),
            "total_raw_lines": len(all_raw_data),
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