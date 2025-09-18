"""Designer management module.

This module handles all Designer-related operations including:
- Starting Designer instances in panes within the current window
- Sending commands to Designers
- Optimized message sending to Designers
"""

import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any

import libtmux

from variables import SESSION_NAME
from infrastructure import TmuxConnection, TmuxConnectionError, resolve_claude_launcher


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


def start_designer(designer_id: str) -> Dict[str, Any]:
    """Start a Designer in a new pane in the current window.
    
    Designers (x, y, z) are started in panes within the definer's window.
    They run in designers/x, designers/y, or designers/z directories.
    
    Args:
        designer_id: Designer identifier ('x', 'y', or 'z')
        
    Returns:
        Dict with success/error status and pane information
    """
    try:
        # Validate designer_id
        if designer_id not in ['x', 'y', 'z']:
            return _err(f"Invalid designer_id: {designer_id}. Must be 'x', 'y', or 'z'", "invalid_designer")
        
        # Build designer directory path
        org_base = Path(__file__).parent.parent.resolve()
        designer_dir = org_base / "designers" / designer_id
        
        if not designer_dir.exists() or not designer_dir.is_dir():
            return _err(f"Designer directory does not exist: {designer_dir}", "missing_directory")
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        if not tmux.is_valid():
            return _err(f"Failed to create tmux connection: {tmux.get_init_error()}", "tmux_connection_failed")
            
        connect_result = tmux.connect()
        if not connect_result["ok"]:
            return _err(f"Failed to connect to tmux: {connect_result['error']}", "tmux_connect_failed")
        
        # Get current window (definer window)
        session_result = tmux.get_or_create_session()
        if not session_result["ok"]:
            return _err(f"Failed to get session: {session_result['error']}", "tmux_session_failed")
        session = session_result["data"]
        current_window = session.attached_window
        
        if not current_window:
            return _err("No current window found", "no_window")
        
        # Split the window to create a new pane
        new_pane = current_window.split_window(vertical=False)  # Horizontal split
        
        if not new_pane:
            return _err("Failed to create new pane", "pane_creation_failed")
        
        # Navigate to designer directory using quoted path
        quoted_dir = shlex.quote(str(designer_dir))
        new_pane.send_keys(f"cd -- {quoted_dir}", enter=True)
        
        # Get Claude launch command from infrastructure module
        cmd_result = resolve_claude_launcher()
        if cmd_result['ok']:
            # Treat data as a string directly
            launch_command = cmd_result['data'] if isinstance(cmd_result['data'], str) else str(cmd_result['data'])
            new_pane.send_keys(launch_command, enter=True)
        else:
            return _err(f"Failed to resolve Claude launcher: {cmd_result['error']}", "launch_error")
        
        return _ok({
            "designer_id": designer_id,
            "directory": str(designer_dir),
            "pane_id": new_pane.id,
            "window_id": current_window.id
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def send_command_to_designer(designer_id: str, command: str) -> Dict[str, Any]:
    """Send command to a Designer pane.
    
    Sends a command to a Designer (x, y, or z) running in a pane.
    The Designer must be already running in the current window.
    
    Args:
        designer_id: Designer identifier ('x', 'y', or 'z')
        command: Command to send to the Designer
        
    Returns:
        Dict with success/error status
    """
    try:
        # Validate inputs
        if designer_id not in ['x', 'y', 'z']:
            return _err(f"Invalid designer_id: {designer_id}. Must be 'x', 'y', or 'z'", "invalid_designer")
        
        if not command or not command.strip():
            return _err("Command cannot be empty", "empty_command")
        
        # Build designer directory path to identify the pane
        org_base = Path(__file__).parent.parent.resolve()
        designer_dir = org_base / "designers" / designer_id
        
        # Connect to tmux
        tmux = TmuxConnection(SESSION_NAME)
        if not tmux.is_valid():
            return _err(f"Failed to create tmux connection: {tmux.get_init_error()}", "tmux_connection_failed")
            
        connect_result = tmux.connect()
        if not connect_result["ok"]:
            return _err(f"Failed to connect to tmux: {connect_result['error']}", "tmux_connect_failed")
        
        # Get current window
        session_result = tmux.get_or_create_session()
        if not session_result["ok"]:
            return _err(f"Failed to get session: {session_result['error']}", "tmux_session_failed")
        session = session_result["data"]
        current_window = session.attached_window
        
        if not current_window:
            return _err("No current window found", "no_window")
        
        # Find the Designer pane by checking pane's current directory
        target_pane = None
        for pane in current_window.panes:
            try:
                # Get pane's current directory
                pane_pwd = pane.cmd('display-message', '-p', '#{pane_current_path}').stdout[0]
                if pane_pwd and Path(pane_pwd).resolve() == designer_dir.resolve():
                    target_pane = pane
                    break
            except Exception:
                continue
        
        if not target_pane:
            return _err(f"Designer {designer_id} is not running in any pane", "designer_not_found")
        
        # Check if pane is alive before sending
        if not _is_pane_alive(target_pane.id):
            return _err(f"Designer {designer_id} pane is dead", "pane_dead")
        
        # Send the command
        target_pane.send_keys(command, enter=True)
        
        return _ok({
            "designer_id": designer_id,
            "command": command,
            "pane_id": target_pane.id
        })
        
    except TmuxConnectionError as e:
        return _err(f"Tmux connection error: {str(e)}", "tmux_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def send_to_designer_optimized(designer_id: str, message: str, use_window: bool = True) -> Dict[str, Any]:
    """Send optimized message to a Designer with intelligent routing.
    
    This function provides optimized message sending with fallback logic:
    1. Try to find existing Designer pane
    2. If not found and use_window=True, start new Designer
    3. Send the message
    
    Args:
        designer_id: Designer identifier ('x', 'y', or 'z')
        message: Message to send to the Designer
        use_window: Whether to auto-start Designer if not found (default: True)
        
    Returns:
        Dict with success/error status and routing information
    """
    try:
        # Validate inputs
        if designer_id not in ['x', 'y', 'z']:
            return _err(f"Invalid designer_id: {designer_id}. Must be 'x', 'y', or 'z'", "invalid_designer")
        
        # First try to send to existing Designer
        send_result = send_command_to_designer(designer_id, message)
        
        if send_result["ok"]:
            # Successfully sent to existing Designer
            return _ok({
                "designer_id": designer_id,
                "message": message,
                "method": "existing_pane",
                "pane_id": send_result["data"]["pane_id"]
            })
        
        # If Designer not found and use_window is True, start a new one
        if use_window and "designer_not_found" in str(send_result.get("error", {})):
            start_result = start_designer(designer_id)
            
            if not start_result["ok"]:
                return _err(f"Failed to start Designer {designer_id}: {start_result['error']}", "start_failed")
            
            # Try sending again after starting
            import time
            time.sleep(1)  # Brief delay to ensure Designer is ready
            
            send_retry = send_command_to_designer(designer_id, message)
            
            if send_retry["ok"]:
                return _ok({
                    "designer_id": designer_id,
                    "message": message,
                    "method": "new_pane",
                    "pane_id": send_retry["data"]["pane_id"]
                })
            else:
                return _err(f"Failed to send message after starting Designer: {send_retry['error']}", "send_after_start_failed")
        
        # Return the original error if we couldn't handle it
        return send_result
        
    except Exception as e:
        return _err(f"Unexpected error in optimized send: {str(e)}", "unexpected_error")