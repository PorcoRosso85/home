"""Infrastructure layer for org project - tmux connection functionality."""

import libtmux
from typing import Optional, List


class TmuxConnectionError(Exception):
    """Exception raised when tmux connection fails."""
    pass


class TmuxConnection:
    """Manages connection to tmux server and session operations."""
    
    def __init__(self, session_name: Optional[str]):
        """Initialize TmuxConnection with session name.
        
        Args:
            session_name: Name of the tmux session to connect to
            
        Raises:
            ValueError: If session_name is None or empty
        """
        if not session_name:
            raise ValueError("Session name is required")
        
        self.session_name = session_name
        self._server: Optional[libtmux.Server] = None
        self._session: Optional[libtmux.Session] = None
        
    def connect(self) -> bool:
        """Connect to tmux server.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            TmuxConnectionError: If connection fails
        """
        try:
            self._server = libtmux.Server()
            return True
        except Exception as e:
            raise TmuxConnectionError(f"Failed to connect to tmux: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to tmux server.
        
        Returns:
            bool: True if connected
        """
        return self._server is not None
    
    def get_or_create_session(self) -> libtmux.Session:
        """Get existing session or create new one.
        
        Returns:
            libtmux.Session: The session object
            
        Raises:
            TmuxConnectionError: If not connected
        """
        if not self.is_connected():
            raise TmuxConnectionError("Not connected to tmux")
            
        # Try to find existing session
        session = self._server.find_where({"session_name": self.session_name})
        
        if session is None:
            # Create new session if not found
            session = self._server.new_session(self.session_name)
            
        self._session = session
        return session
    
    def send_command(self, command: str, window_name: str, pane_name: str) -> None:
        """Send command to specified window and pane.
        
        Args:
            command: Command to send
            window_name: Name of target window
            pane_name: Name of target pane
            
        Raises:
            TmuxConnectionError: If not connected
        """
        if not self.is_connected():
            raise TmuxConnectionError("Not connected to tmux")
            
        if not self._session:
            self.get_or_create_session()
            
        window = self._session.find_where({"window_name": window_name})
        if window:
            pane = window.find_where({"pane_name": pane_name})
            if pane:
                pane.send_keys(command)
    
    def create_worker_window(self, directory: str) -> libtmux.Window:
        """Create a new worker window with directory-based naming.
        
        Args:
            directory: Directory path for the worker
            
        Returns:
            libtmux.Window: The created window
            
        Raises:
            TmuxConnectionError: If not connected or session not available
        """
        if not self.is_connected():
            raise TmuxConnectionError("Not connected to tmux")
            
        if not self._session:
            self.get_or_create_session()
        
        # Create window name from directory
        window_name = f"claude:{directory.replace('/', '_')}"
        
        # Create new window
        window = self._session.new_window(window_name=window_name)
        return window
    
    def find_worker_window_by_directory(self, directory: str) -> Optional[libtmux.Window]:
        """Find existing worker window by directory.
        
        Args:
            directory: Directory path to search for
            
        Returns:
            Optional[libtmux.Window]: The window if found, None otherwise
            
        Raises:
            TmuxConnectionError: If not connected
        """
        if not self.is_connected():
            raise TmuxConnectionError("Not connected to tmux")
            
        if not self._session:
            self.get_or_create_session()
        
        # Create expected window name
        window_name = f"claude:{directory.replace('/', '_')}"
        
        # Search for window
        return self._session.find_where({"window_name": window_name})
    
    def list_all_worker_windows(self) -> List[libtmux.Window]:
        """List all worker windows with claude: prefix.
        
        Returns:
            list[libtmux.Window]: List of claude worker windows
            
        Raises:
            TmuxConnectionError: If not connected
        """
        if not self.is_connected():
            raise TmuxConnectionError("Not connected to tmux")
            
        if not self._session:
            self.get_or_create_session()
        
        # Filter windows by claude: prefix
        worker_windows = []
        for window in self._session.windows:
            if window.name.startswith("claude:"):
                worker_windows.append(window)
        
        return worker_windows
    
    def launch_claude_in_window(self, window: libtmux.Window, directory: str) -> None:
        """Launch Claude Code in the specified window and directory.
        
        Args:
            window: The tmux window to launch Claude in
            directory: The directory to change to before launching
            
        Raises:
            TmuxConnectionError: If window or pane operations fail
        """
        try:
            # Get the first pane of the window
            pane = window.panes[0] if window.panes else None
            if not pane:
                raise TmuxConnectionError(f"No pane available in window {window.name}")
            
            # Change to the specified directory
            pane.send_keys(f"cd {directory}", enter=True)
            
            # Get the Claude launch command from variables
            from variables import get_claude_launch_command
            launch_cmd = get_claude_launch_command()
            
            # Launch Claude Code with proper command
            if launch_cmd['ok']:
                pane.send_keys(launch_cmd['data']['command'], enter=True)
            else:
                # Fallback to simple claude command
                pane.send_keys("claude", enter=True)
            
        except Exception as e:
            raise TmuxConnectionError(f"Failed to launch Claude in window: {e}")