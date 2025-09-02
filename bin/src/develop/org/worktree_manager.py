"""Worktree management for org orchestrator."""

import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib


def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def generate_worktree_name(task_name: str, directories: List[str]) -> str:
    """Generate unique worktree name from task and directories.
    
    Args:
        task_name: Human-readable task name
        directories: List of directories to include
        
    Returns:
        Worktree name like 'auth-feature-a3f2'
    """
    # Create hash from directories for uniqueness
    dir_hash = hashlib.md5(''.join(sorted(directories)).encode()).hexdigest()[:4]
    # Sanitize task name
    safe_name = task_name.lower().replace(' ', '-').replace('/', '-')
    return f"{safe_name}-{dir_hash}"


def create_worktree_with_sparse(
    task_name: str,
    directories: List[str],
    base_path: Path = Path.home() / "worktrees"
) -> Dict[str, Any]:
    """Create worktree with sparse-checkout for specific directories.
    
    Args:
        task_name: Task description
        directories: Directories to include via sparse-checkout
        base_path: Base path for worktrees
        
    Returns:
        Result with worktree path or error
    """
    try:
        worktree_name = generate_worktree_name(task_name, directories)
        worktree_path = base_path / worktree_name
        
        # Check if already exists
        if worktree_path.exists():
            return _ok({
                "path": str(worktree_path),
                "name": worktree_name,
                "existed": True
            })
        
        # Create worktree
        base_path.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return _err(f"Failed to create worktree: {result.stderr}", "worktree_error")
        
        # Setup sparse-checkout
        sparse_file = worktree_path / ".git/info/sparse-checkout"
        sparse_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sparse_file, 'w') as f:
            for directory in directories:
                f.write(f"{directory}\n")
        
        # Enable sparse-checkout
        subprocess.run(
            ["git", "sparse-checkout", "init", "--cone"],
            cwd=worktree_path,
            check=True
        )
        
        subprocess.run(
            ["git", "sparse-checkout", "set"] + directories,
            cwd=worktree_path,
            check=True
        )
        
        return _ok({
            "path": str(worktree_path),
            "name": worktree_name,
            "directories": directories,
            "existed": False
        })
        
    except subprocess.CalledProcessError as e:
        return _err(f"Git command failed: {str(e)}", "git_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def list_worktrees() -> Dict[str, Any]:
    """List all git worktrees.
    
    Returns:
        Dict with worktrees list or error
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        worktrees = []
        current = {}
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                if current:
                    worktrees.append(current)
                    current = {}
            elif line.startswith("worktree "):
                current["path"] = line[9:]
            elif line.startswith("branch "):
                current["branch"] = line[7:]
            elif line.startswith("HEAD "):
                current["head"] = line[5:]
        
        if current:
            worktrees.append(current)
        
        return _ok({"worktrees": worktrees, "count": len(worktrees)})
        
    except subprocess.CalledProcessError as e:
        return _err(f"Failed to list worktrees: {str(e)}", "git_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def remove_worktree(worktree_path: str, force: bool = False) -> Dict[str, Any]:
    """Remove a git worktree.
    
    Args:
        worktree_path: Path to the worktree
        force: Force removal even if there are changes
        
    Returns:
        Result dict
    """
    try:
        cmd = ["git", "worktree", "remove", worktree_path]
        if force:
            cmd.append("--force")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return _err(f"Failed to remove worktree: {result.stderr}", "remove_error")
        
        return _ok({"removed": worktree_path})
        
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def get_sparse_checkout_dirs(worktree_path: str) -> Dict[str, Any]:
    """Get sparse-checkout directories for a worktree.
    
    Args:
        worktree_path: Path to the worktree
        
    Returns:
        Dict with directories list or error
    """
    try:
        result = subprocess.run(
            ["git", "sparse-checkout", "list"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        directories = [d.strip() for d in result.stdout.strip().split('\n') if d.strip()]
        
        return _ok({"directories": directories, "path": worktree_path})
        
    except subprocess.CalledProcessError as e:
        return _err(f"Failed to get sparse-checkout: {str(e)}", "git_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")