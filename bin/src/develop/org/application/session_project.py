"""Project session management module.

This module handles all project session-related operations including:
- Creating and managing project-specific tmux sessions
- Sending messages to project sessions
- Managing project session lifecycle
"""

import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any

from variables import SESSION_NAME
from infrastructure import TmuxConnection, TmuxConnectionError


# Result pattern helpers
def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def generate_project_session_name(project_path: str) -> str:
    """Generate a unique session name for a project path.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Unique session name based on project path
    """
    # Create a hash of the full path for uniqueness
    path_hash = hashlib.md5(project_path.encode()).hexdigest()[:8]
    # Use last directory name for readability
    dir_name = Path(project_path).name
    return f"project-{dir_name}-{path_hash}"


def ensure_project_session(project_path: str) -> str:
    """Ensure a project session exists, creating if necessary.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Session name if successful, empty string on failure
    """
    session_name = generate_project_session_name(project_path)
    
    try:
        # Check if session exists
        result = subprocess.run(
            ['tmux', 'has-session', '-t', session_name],
            capture_output=True,
            check=False
        )
        
        if result.returncode != 0:
            # Create new session
            subprocess.run(
                ['tmux', 'new-session', '-d', '-s', session_name, '-c', project_path],
                check=True
            )
        
        return session_name
        
    except subprocess.SubprocessError:
        return ""


def send_to_developer_session(project_path: str, message: str) -> bool:
    """Send a message to a developer in a project session.
    
    Args:
        project_path: Path to the project directory
        message: Message to send
        
    Returns:
        True if successful, False otherwise
    """
    session_name = ensure_project_session(project_path)
    if not session_name:
        return False
    
    try:
        # Find developer window in the session
        result = subprocess.run(
            ['tmux', 'list-windows', '-t', session_name, '-F', '#{window_name}:#{window_id}'],
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.strip().split('\n'):
            if line.startswith('developer:'):
                window_id = line.split(':')[-1]
                # Send to the window
                subprocess.run(
                    ['tmux', 'send-keys', '-t', f"{session_name}:{window_id}", message, 'Enter'],
                    check=True
                )
                return True
        
        return False
        
    except subprocess.SubprocessError:
        return False


def get_project_session_status(project_path: str) -> Dict[str, Any]:
    """Get the status of a project session.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dict with session status information
    """
    session_name = generate_project_session_name(project_path)
    
    try:
        # Check if session exists
        result = subprocess.run(
            ['tmux', 'has-session', '-t', session_name],
            capture_output=True,
            check=False
        )
        
        if result.returncode == 0:
            # Get window list
            windows_result = subprocess.run(
                ['tmux', 'list-windows', '-t', session_name, '-F', '#{window_name}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            windows = windows_result.stdout.strip().split('\n') if windows_result.stdout.strip() else []
            
            # Check for developer windows
            developer_windows = [w for w in windows if w.startswith('developer:')]
            
            return _ok({
                "session_name": session_name,
                "exists": True,
                "windows": windows,
                "developer_windows": developer_windows,
                "window_count": len(windows),
                "project_path": project_path
            })
        else:
            return _ok({
                "session_name": session_name,
                "exists": False,
                "windows": [],
                "developer_windows": [],
                "window_count": 0,
                "project_path": project_path
            })
            
    except subprocess.SubprocessError as e:
        return _err(f"Failed to get session status: {str(e)}", "status_error")


def terminate_project_session(project_path: str) -> bool:
    """Terminate a project session.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        True if successful, False otherwise
    """
    session_name = generate_project_session_name(project_path)
    
    try:
        # Kill the session
        result = subprocess.run(
            ['tmux', 'kill-session', '-t', session_name],
            capture_output=True,
            check=False
        )
        
        return result.returncode == 0
        
    except subprocess.SubprocessError:
        return False


def send_to_project_session(project_path: str, message: str) -> Dict[str, Any]:
    """Send message to project session with Result pattern.
    
    Args:
        project_path: Path to the project directory
        message: Message to send
        
    Returns:
        Dict with success/error status
    """
    try:
        # Validate project path
        path = Path(project_path).resolve()
        if not path.exists() or not path.is_dir():
            return _err(f"Invalid project path: {project_path}", "invalid_path")
        
        # Ensure session exists
        session_name = ensure_project_session(str(path))
        if not session_name:
            return _err(f"Failed to create/access session for: {project_path}", "session_error")
        
        # Send message
        success = send_to_developer_session(str(path), message)
        
        if success:
            return _ok({
                "session_name": session_name,
                "project_path": str(path),
                "message": message
            })
        else:
            return _err(f"No developer window found in session: {session_name}", "no_developer")
            
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def create_integrated_project_session(project_path: str) -> Dict[str, Any]:
    """Create an integrated project session with developer window.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dict with session creation status
    """
    try:
        # Validate project path
        path = Path(project_path).resolve()
        if not path.exists() or not path.is_dir():
            return _err(f"Invalid project path: {project_path}", "invalid_path")
        
        # Generate session name
        session_name = generate_project_session_name(str(path))
        
        # Check if session already exists
        result = subprocess.run(
            ['tmux', 'has-session', '-t', session_name],
            capture_output=True,
            check=False
        )
        
        if result.returncode == 0:
            return _err(f"Session already exists: {session_name}", "session_exists")
        
        # Create new session with developer window
        try:
            # Create session
            subprocess.run(
                ['tmux', 'new-session', '-d', '-s', session_name, '-c', str(path),
                 '-n', f"developer:{str(path).replace('/', '_')}"],
                check=True
            )
            
            # Get claude launcher from infrastructure
            from infrastructure import resolve_claude_launcher
            cmd_result = resolve_claude_launcher()
            
            if cmd_result['ok']:
                # Launch Claude in the developer window
                launch_command = cmd_result['data'] if isinstance(cmd_result['data'], str) else str(cmd_result['data'])
                subprocess.run(
                    ['tmux', 'send-keys', '-t', f"{session_name}:0", launch_command, 'Enter'],
                    check=True
                )
            
            return _ok({
                "session_name": session_name,
                "project_path": str(path),
                "developer_window": f"developer:{str(path).replace('/', '_')}",
                "claude_launched": cmd_result['ok']
            })
            
        except subprocess.SubprocessError as e:
            return _err(f"Failed to create session: {str(e)}", "creation_error")
            
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")