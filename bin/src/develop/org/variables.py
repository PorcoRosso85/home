"""Variables and configuration for org project."""

import shutil
from typing import Dict, Any


def get_claude_launch_command() -> Dict[str, Any]:
    """Get the appropriate Claude Code launch command.
    
    Checks if claude-code is in PATH, otherwise uses nix run.
    
    Returns:
        Dict with 'ok' status and command data or error
    """
    # Check if claude-code is available in PATH
    if shutil.which('claude-code'):
        command = 'env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions'
    elif shutil.which('claude'):
        # Check for simpler 'claude' command
        command = 'claude'
    else:
        # Use nix run as fallback
        command = 'env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions'
    
    return {
        'ok': True,
        'data': {
            'command': command,
            'environment': {
                'NIXPKGS_ALLOW_UNFREE': '1'
            }
        }
    }