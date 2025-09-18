"""Infrastructure layer for org project - tmux connection functionality."""

import libtmux
import shutil
from typing import Optional, List, Dict, Any
import variables


# Result pattern helpers
def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def resolve_claude_launcher() -> Dict[str, Any]:
    """Resolve Claude launcher command (environment variable only, no fallback).
    
    Configuration:
    - CLAUDE_LAUNCHER environment variable must be set
    - No implicit fallback to scripts or system commands
    
    Returns:
        Dict[str, Any]: Success result with launcher command or error
    """
    # Environment variable only - no fallback
    pref_result = variables.get_claude_command_preference()
    if pref_result['ok']:
        return pref_result
    
    # No fallback - return clear error with action
    return {
        'ok': False,
        'error': (
            "launcher_not_configured: Claude launcher not configured. "
            "Action required: Set CLAUDE_LAUNCHER environment variable. "
            "Example: export CLAUDE_LAUNCHER='claude-code --dangerously-skip-permissions'"
        )
    }


# Connection state type
def create_tmux_connection(session_name: Optional[str]) -> Dict[str, Any]:
    """Create a tmux connection state.
    
    Args:
        session_name: Name of the tmux session to connect to
        
    Returns:
        Dict: Success result with connection state or error
    """
    if not session_name:
        return _err("Session name is required", "invalid_session_name")
    
    connection_state = {
        "session_name": session_name,
        "server": None,
        "session": None
    }
    
    return _ok(connection_state)


# Functional tmux operations
def connect_to_tmux_server(connection_state: Dict[str, Any]) -> Dict[str, Any]:
    """Connect to tmux server using connection state.
    
    Args:
        connection_state: Dict containing connection information
        
    Returns:
        Dict: Success result with updated connection state or error
    """
    try:
        server = libtmux.Server()
        updated_state = connection_state.copy()
        updated_state["server"] = server
        return _ok(updated_state)
    except Exception as e:
        return _err(f"Failed to connect to tmux: {e}", "connection_failed")


def is_tmux_connected(connection_state: Dict[str, Any]) -> bool:
    """Check if connected to tmux server.
    
    Args:
        connection_state: Dict containing connection information
        
    Returns:
        bool: True if connected
    """
    return connection_state.get("server") is not None


def get_or_create_tmux_session(connection_state: Dict[str, Any]) -> Dict[str, Any]:
    """Get existing session or create new one.
    
    Args:
        connection_state: Dict containing connection information
        
    Returns:
        Dict: Success result with updated connection state or error
    """
    if not is_tmux_connected(connection_state):
        return _err("Not connected to tmux", "not_connected")
    
    server = connection_state["server"]
    session_name = connection_state["session_name"]
    
    # Try to find existing session
    session = server.find_where({"session_name": session_name})
    
    if session is None:
        # Create new session if not found
        session = server.new_session(session_name)
    
    updated_state = connection_state.copy()
    updated_state["session"] = session
    return _ok(updated_state)


def send_command_to_pane(connection_state: Dict[str, Any], command: str, window_name: str, pane_name: str) -> Dict[str, Any]:
    """Send command to specified window and pane.
    
    Args:
        connection_state: Dict containing connection information
        command: Command to send
        window_name: Name of target window
        pane_name: Name of target pane
        
    Returns:
        Dict: Success result with updated connection state or error
    """
    if not is_tmux_connected(connection_state):
        return _err("Not connected to tmux", "not_connected")
    
    # Ensure session exists
    updated_state = connection_state.copy()
    if not updated_state.get("session"):
        session_result = get_or_create_tmux_session(updated_state)
        if not session_result["ok"]:
            return session_result
        updated_state = session_result["data"]
    
    session = updated_state["session"]
    window = session.find_where({"window_name": window_name})
    if window:
        pane = window.find_where({"pane_name": pane_name})
        if pane:
            pane.send_keys(command)
    
    return _ok(updated_state)


def create_worker_window_for_directory(connection_state: Dict[str, Any], directory: str) -> Dict[str, Any]:
    """Create a new worker window with directory-based naming.
    
    Args:
        connection_state: Dict containing connection information
        directory: Directory path for the worker
        
    Returns:
        Dict: Success result with connection state and window or error
    """
    if not is_tmux_connected(connection_state):
        return _err("Not connected to tmux", "not_connected")
    
    # Ensure session exists
    updated_state = connection_state.copy()
    if not updated_state.get("session"):
        session_result = get_or_create_tmux_session(updated_state)
        if not session_result["ok"]:
            return session_result
        updated_state = session_result["data"]
    
    # Create window name from directory using domain function
    from domain import generate_claude_window_name
    window_name = generate_claude_window_name(directory)
    
    # Create new window
    session = updated_state["session"]
    window = session.new_window(window_name=window_name)
    
    return _ok({"connection_state": updated_state, "window": window})


def find_worker_window_by_directory(connection_state: Dict[str, Any], directory: str) -> Dict[str, Any]:
    """Find existing worker window by directory.
    
    Args:
        connection_state: Dict containing connection information
        directory: Directory path to search for
        
    Returns:
        Dict: Success result with connection state and window (None if not found) or error
    """
    if not is_tmux_connected(connection_state):
        return _err("Not connected to tmux", "not_connected")
    
    # Ensure session exists
    updated_state = connection_state.copy()
    if not updated_state.get("session"):
        session_result = get_or_create_tmux_session(updated_state)
        if not session_result["ok"]:
            return session_result
        updated_state = session_result["data"]
    
    # Search for window with developer: prefix
    session = updated_state["session"]
    window_name = f"developer:{directory.replace('/', '_')}"
    window = session.find_where({"window_name": window_name})
    
    # Return window if found, None otherwise
    return _ok({"connection_state": updated_state, "window": window})


def list_all_worker_windows(connection_state: Dict[str, Any]) -> Dict[str, Any]:
    """List all worker windows with developer: prefix.
    
    Args:
        connection_state: Dict containing connection information
        
    Returns:
        Dict: Success result with connection state and list of windows or error
    """
    if not is_tmux_connected(connection_state):
        return _err("Not connected to tmux", "not_connected")
    
    # Ensure session exists
    updated_state = connection_state.copy()
    if not updated_state.get("session"):
        session_result = get_or_create_tmux_session(updated_state)
        if not session_result["ok"]:
            return session_result
        updated_state = session_result["data"]
    
    # Filter windows by developer: prefix using domain function
    from domain import is_developer_window
    session = updated_state["session"]
    worker_windows = []
    for window in session.windows:
        if is_developer_window(window.name):
            worker_windows.append(window)
    
    return _ok({"connection_state": updated_state, "windows": worker_windows})


def launch_claude_in_window(window: libtmux.Window, directory: str) -> Dict[str, Any]:
    """Launch Claude Code in the specified window and directory.
    
    Args:
        window: The tmux window to launch Claude in
        directory: The directory to change to before launching
        
    Returns:
        Dict: Success result or error
    """
    try:
        # Get the first pane of the window
        pane = window.panes[0] if window.panes else None
        if not pane:
            return _err(f"No pane available in window {window.name}", "no_pane")
        
        # Change to the specified directory
        pane.send_keys(f"cd {directory}", enter=True)
        
        # Get the Claude launch command using new unified resolver
        launcher_result = resolve_claude_launcher()
        
        # Launch Claude with resolved command or return error
        if launcher_result['ok']:
            pane.send_keys(launcher_result['data'], enter=True)
            return _ok(None)
        else:
            return _err(f"Failed to resolve Claude launcher: {launcher_result['error']}", "launcher_not_found")
        
    except Exception as e:
        return _err(f"Failed to launch Claude in window: {e}", "launch_failed")


# Compatibility class to maintain API compatibility
class TmuxConnectionError(Exception):
    """Exception raised when tmux connection fails."""
    pass


class TmuxConnection:
    """Manages connection to tmux server and session operations."""
    
    def __init__(self, session_name: Optional[str]):
        """Initialize TmuxConnection with session name.
        
        Args:
            session_name: Name of the tmux session to connect to
            
        Note:
            Does not raise exceptions. Use is_valid() to check initialization success.
        """
        result = create_tmux_connection(session_name)
        if not result["ok"]:
            # Store error state instead of raising exception
            self._state = None
            self._init_error = result["error"]
        else:
            self._state = result["data"]
            self._init_error = None
        
    def is_valid(self) -> bool:
        """Check if connection is valid (initialization was successful)."""
        return self._state is not None and self._init_error is None
        
    def get_init_error(self) -> Optional[dict]:
        """Get initialization error if any."""
        return self._init_error
    
    @property
    def session_name(self) -> str:
        """Get session name."""
        if not self.is_valid():
            return ""
        return self._state["session_name"]
    
    @property
    def _server(self) -> Optional[libtmux.Server]:
        """Get server instance."""
        return self._state["server"]
    
    @_server.setter
    def _server(self, value: Optional[libtmux.Server]) -> None:
        """Set server instance."""
        self._state["server"] = value
    
    @property 
    def _session(self) -> Optional[libtmux.Session]:
        """Get session instance."""
        return self._state["session"]
    
    @_session.setter
    def _session(self, value: Optional[libtmux.Session]) -> None:
        """Set session instance."""
        self._state["session"] = value
        
    def connect(self) -> dict:
        """Connect to tmux server.
        
        Returns:
            dict: Result object with ok/error structure
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = connect_to_tmux_server(self._state)
        if not result["ok"]:
            return result
        
        self._state = result["data"]
        return {"ok": True, "data": True}
    
    def is_connected(self) -> bool:
        """Check if connected to tmux server.
        
        Returns:
            bool: True if connected
        """
        return is_tmux_connected(self._state)
    
    def get_or_create_session(self) -> dict:
        """Get existing session or create new one.
        
        Returns:
            dict: Result object with ok/error structure, data contains session
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = get_or_create_tmux_session(self._state)
        if not result["ok"]:
            return result
        
        self._state = result["data"]
        return {"ok": True, "data": self._state["session"]}
    
    def send_command(self, command: str, window_name: str, pane_name: str) -> dict:
        """Send command to specified window and pane.
        
        Args:
            command: Command to send
            window_name: Name of target window
            pane_name: Name of target pane
            
        Returns:
            dict: Result object with ok/error structure
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = send_command_to_pane(self._state, command, window_name, pane_name)
        if not result["ok"]:
            return result
        
        self._state = result["data"]
        return {"ok": True, "data": None}
    
    def create_worker_window(self, directory: str) -> dict:
        """Create a new worker window with directory-based naming.
        
        Args:
            directory: Directory path for the worker
            
        Returns:
            dict: Result object with ok/error structure, data contains window
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = create_worker_window_for_directory(self._state, directory)
        if not result["ok"]:
            return result
        
        self._state = result["data"]["connection_state"]
        return {"ok": True, "data": result["data"]["window"]}
    
    def find_worker_window_by_directory(self, directory: str) -> dict:
        """Find existing worker window by directory.
        
        Args:
            directory: Directory path to search for
            
        Returns:
            dict: Result object with ok/error structure, data contains window (may be None)
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = find_worker_window_by_directory(self._state, directory)
        if not result["ok"]:
            return result
        
        self._state = result["data"]["connection_state"]
        return {"ok": True, "data": result["data"]["window"]}
    
    def list_all_worker_windows(self) -> dict:
        """List all worker windows with developer: prefix.
        
        Returns:
            dict: Result object with ok/error structure, data contains windows list
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = list_all_worker_windows(self._state)
        if not result["ok"]:
            return result
        
        self._state = result["data"]["connection_state"]
        return {"ok": True, "data": result["data"]["windows"]}
    
    def launch_claude_in_window(self, window: libtmux.Window, directory: str) -> dict:
        """Launch Claude Code in the specified window and directory.
        
        Args:
            window: The tmux window to launch Claude in
            directory: The directory to change to before launching
            
        Returns:
            dict: Result object with ok/error structure
        """
        if not self.is_valid():
            return {"ok": False, "error": self._init_error}
            
        result = launch_claude_in_window(window, directory)
        if not result["ok"]:
            return result
        
        return {"ok": True, "data": None}