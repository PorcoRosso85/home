"""Variables and configuration for org project.

Purified configuration retrieval module - only handles getting configuration values.
All functions follow Result pattern and never throw exceptions.
"""

import os
from typing import Dict, Any


# === Window Management Constants ===
# Single source of truth for window naming conventions
DEVELOPER_WINDOW_PREFIX = "developer:"


# === Session Management ===
def get_session_name() -> str:
    """Get current tmux session name from environment.
    
    Returns the session name from $TMUX environment variable if available,
    otherwise returns default 'org-system'.
    """
    import subprocess
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


def get_claude_command_preference() -> Dict[str, Any]:
    """Get Claude command preference from environment variable.
    
    Returns:
        Dict with 'ok' status and command preference or error
    """
    try:
        cmd = os.getenv('CLAUDE_LAUNCHER')
        if cmd:
            return {'ok': True, 'data': cmd}
        return {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
    except Exception:
        return {'ok': False, 'error': 'Failed to read CLAUDE_LAUNCHER environment variable'}


