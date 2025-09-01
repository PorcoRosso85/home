"""Domain layer - Business rules and domain services for worker orchestration.

This module contains all business logic and domain knowledge, following
functional programming principles without classes.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path


# === Tool-specific Business Rules ===

def generate_claude_window_name(directory: str) -> str:
    """Generate tmux window name for Claude worker.
    
    Business rule: Claude windows use 'claude:' prefix with underscored path.
    
    Args:
        directory: Directory path for the worker
        
    Returns:
        Window name following Claude naming convention
    """
    return f"claude:{directory.replace('/', '_')}"


def generate_claude_history_patterns(directory: str) -> List[str]:
    """Generate patterns for finding Claude history directory.
    
    Business rule: Claude stores history in various formats, need fuzzy matching.
    
    Args:
        directory: Target directory path
        
    Returns:
        List of possible patterns in priority order
    """
    patterns = []
    # Pattern 1: No leading slash, hyphen separator
    patterns.append(directory.lstrip('/').replace('/', '-'))
    # Pattern 2: With leading hyphen
    patterns.append('-' + directory.lstrip('/').replace('/', '-'))
    # Pattern 3: Full path version
    patterns.append(directory.replace('/', '-'))
    return patterns


def get_claude_default_command() -> str:
    """Get default Claude tool command.
    
    Business rule: Claude uses 'claude' as default command.
    
    Returns:
        Default command string
    """
    return "claude"


def get_claude_history_base_path() -> Path:
    """Get base path for Claude history storage.
    
    Business rule: Claude stores history in ~/.claude/projects/
    
    Returns:
        Path to Claude history base directory
    """
    return Path.home() / ".claude/projects"


def get_claude_launch_command() -> Dict[str, Any]:
    """Get Claude launch command from variables module or fallback.
    
    Business rule: Try variables module first, fallback to simple 'claude' command.
    
    Returns:
        Dict with success status and command data
    """
    try:
        import variables
        return variables.get_claude_launch_command()
    except ImportError:
        # Fallback to simple claude command
        return {
            'ok': True,
            'data': {
                'command': 'claude'
            }
        }


# === Generic Worker Business Rules ===

def extract_directory_from_window_name(window_name: str, tool_prefix: str = "claude:") -> str:
    """Extract directory path from window name.
    
    Business rule: Reverse transformation of window naming convention.
    
    Args:
        window_name: tmux window name
        tool_prefix: Tool-specific prefix (default: "claude:")
        
    Returns:
        Original directory path
    """
    if window_name.startswith(tool_prefix):
        # Remove prefix and convert underscores back to slashes
        path_part = window_name[len(tool_prefix):]
        return path_part.replace('_', '/')
    return ""


def is_worker_window(window_name: str, tool_prefix: str = "claude:") -> bool:
    """Check if a window name represents a worker.
    
    Business rule: Worker windows have tool-specific prefixes.
    
    Args:
        window_name: tmux window name to check
        tool_prefix: Tool-specific prefix to look for
        
    Returns:
        True if this is a worker window
    """
    return window_name.startswith(tool_prefix)


def should_check_pane_alive() -> bool:
    """Business rule: Determine if pane alive check is needed.
    
    Business rule: Always check pane status for worker health.
    
    Returns:
        True (always check pane status)
    """
    return True




# === Worker State Business Rules ===

def determine_worker_status(has_pane: bool, pane_id: Optional[str], is_pane_alive: bool = False) -> str:
    """Determine worker status based on pane state.
    
    Business rule: Worker is alive if it has a live pane, dead otherwise.
    
    Args:
        has_pane: Whether worker has any panes
        pane_id: ID of the pane (if exists)
        is_pane_alive: Whether the pane is alive (from infrastructure check)
        
    Returns:
        Status string: "alive" or "dead"
    """
    if not has_pane or not pane_id:
        return "dead"
    return "alive" if is_pane_alive else "dead"


# === History Management Business Rules ===

def find_history_directory(directory: str, patterns: List[str], base_path: Path) -> Optional[Path]:
    """Find history directory using pattern matching.
    
    Business rule: Search for history directory using fuzzy pattern matching.
    
    Args:
        directory: Original directory path
        patterns: List of patterns to try
        base_path: Base path to search in
        
    Returns:
        Path to history directory if found, None otherwise
    """
    if not base_path.exists():
        return None
        
    for pattern in patterns:
        candidate = base_path / pattern
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def validate_history_content(history_path: Path) -> Dict[str, Any]:
    """Validate history directory has actual content.
    
    Business rule: History is valid if directory contains .jsonl files.
    
    Args:
        history_path: Path to history directory
        
    Returns:
        Validation result with file count and status
    """
    jsonl_files = list(history_path.glob("*.jsonl"))
    has_history = len(jsonl_files) > 0
    
    return {
        "has_history": has_history,
        "file_count": len(jsonl_files),
        "latest_file": jsonl_files[-1].name if jsonl_files else None
    }


# === Future Tool Support ===
# Add new tool-specific functions here following the same pattern:
# - generate_{tool}_window_name()
# - generate_{tool}_history_patterns()
# - get_{tool}_launch_command()