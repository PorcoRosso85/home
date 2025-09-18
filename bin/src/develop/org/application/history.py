"""History management module.

This module handles all history-related operations including:
- Checking if a Developer has Claude history
- Reading Claude conversation history from JSONL files
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


# Result pattern helpers
def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def _find_claude_history_file(directory: str) -> Optional[Path]:
    """Find Claude history file for a given directory.
    
    Claude stores history in ~/.claude/projects/ with encoded directory names.
    
    Args:
        directory: Directory path to search for
        
    Returns:
        Path to history file if found, None otherwise
    """
    # Normalize directory path
    dir_path = Path(directory).resolve()
    directory_str = str(dir_path)
    
    # Encode directory name for Claude history filename
    # Claude uses URL-safe encoding: / becomes -, spaces become underscores
    encoded_name = directory_str.replace('/', '-').replace(' ', '_')
    if encoded_name.startswith('-'):
        encoded_name = encoded_name[1:]  # Remove leading dash
    
    # Check for history file
    claude_projects = Path.home() / '.claude' / 'projects'
    if not claude_projects.exists():
        return None
    
    # Look for matching JSONL files
    for jsonl_file in claude_projects.glob('*.jsonl'):
        # Check if filename contains the encoded directory name
        if encoded_name in str(jsonl_file.name):
            return jsonl_file
    
    return None


def check_developer_has_history(directory: str) -> Dict[str, Any]:
    """Check if a Developer has started logging (has Claude history).
    
    Args:
        directory: Directory where the Developer is running
        
    Returns:
        Dict with has_history status and file information
    """
    try:
        # Validate directory
        dir_path = Path(directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return _err(f"Directory does not exist: {directory}", "invalid_directory")
        
        # Find history file
        history_file = _find_claude_history_file(str(dir_path))
        
        if history_file and history_file.exists():
            # Count messages in the history file
            try:
                with open(history_file, 'r') as f:
                    message_count = sum(1 for line in f if line.strip())
                
                return _ok({
                    "has_history": True,
                    "file_path": str(history_file),
                    "message_count": message_count,
                    "directory": str(dir_path)
                })
            except Exception as e:
                return _err(f"Failed to read history file: {str(e)}", "read_error")
        else:
            return _ok({
                "has_history": False,
                "file_path": None,
                "message_count": 0,
                "directory": str(dir_path)
            })
    
    except Exception as e:
        return _err(f"Unexpected error checking history: {str(e)}", "unexpected_error")


def get_claude_history(directory: str, last_n: int = 20) -> Dict[str, Any]:
    """Read Claude conversation history from JSONL file.
    
    Args:
        directory: Directory where the Developer is running
        last_n: Number of recent messages to return (default: 20)
        
    Returns:
        Dict with messages from history file
    """
    try:
        # Validate directory
        dir_path = Path(directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return _err(f"Directory does not exist: {directory}", "invalid_directory")
        
        # Find history file
        history_file = _find_claude_history_file(str(dir_path))
        
        if not history_file or not history_file.exists():
            return _ok({
                "messages": [],
                "total_messages": 0,
                "directory": str(dir_path),
                "file_path": None
            })
        
        # Read messages from JSONL file
        messages = []
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            messages.append(msg)
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
            
            # Get last N messages
            recent_messages = messages[-last_n:] if last_n > 0 else messages
            
            return _ok({
                "messages": recent_messages,
                "total_messages": len(messages),
                "returned_count": len(recent_messages),
                "directory": str(dir_path),
                "file_path": str(history_file)
            })
            
        except Exception as e:
            return _err(f"Failed to read history file: {str(e)}", "read_error")
    
    except Exception as e:
        return _err(f"Unexpected error reading history: {str(e)}", "unexpected_error")