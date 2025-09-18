"""File system scanning utilities."""

from typing import List, Union, Optional, Dict, Any
from pathlib import Path
from ..domain.errors import ErrorDict, create_error


def scan_directory(
    directory: str,
    extensions: Optional[List[str]] = None,
    max_depth: Optional[int] = None
) -> Union[List[str], ErrorDict]:
    """
    Scan directory for files with specified extensions.
    
    Args:
        directory: Directory path to scan
        extensions: List of file extensions to include (e.g., [".py", ".js"])
        max_depth: Maximum directory depth to scan
        
    Returns:
        List of file paths or error dictionary
    """
    dir_path = Path(directory).resolve()
    
    if not dir_path.exists():
        return create_error(
            "DIRECTORY_NOT_FOUND",
            f"Directory does not exist: {dir_path}",
            {"directory": str(dir_path)}
        )
    
    if not dir_path.is_dir():
        return create_error(
            "NOT_A_DIRECTORY",
            f"Path is not a directory: {dir_path}",
            {"path": str(dir_path)}
        )
    
    files = []
    
    try:
        for file_path in walk_directory(dir_path, max_depth):
            if file_path.is_file():
                if extensions is None or any(file_path.suffix == ext for ext in extensions):
                    files.append(str(file_path))
    except Exception as e:
        return create_error(
            "SCAN_ERROR",
            f"Error scanning directory: {str(e)}",
            {"directory": str(dir_path)}
        )
    
    return files


def walk_directory(directory: Path, max_depth: Optional[int] = None) -> List[Path]:
    """
    Walk directory tree up to specified depth.
    
    Args:
        directory: Directory path
        max_depth: Maximum depth to walk
        
    Returns:
        Generator of Path objects
    """
    if max_depth is None:
        # Use rglob for unlimited depth
        yield from directory.rglob('*')
    else:
        # Manual depth control
        def walk_with_depth(path: Path, current_depth: int):
            if current_depth > max_depth:
                return
            
            try:
                for item in path.iterdir():
                    yield item
                    if item.is_dir():
                        yield from walk_with_depth(item, current_depth + 1)
            except PermissionError:
                # Skip directories we can't read
                pass
        
        yield from walk_with_depth(directory, 0)


def read_file_lines(file_path: str) -> Union[List[str], ErrorDict]:
    """
    Read file and return lines.
    
    Args:
        file_path: Path to file
        
    Returns:
        List of lines or error dictionary
    """
    path = Path(file_path).resolve()
    
    if not path.exists():
        return create_error(
            "FILE_NOT_FOUND",
            f"File does not exist: {path}",
            {"file_path": str(path)}
        )
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        return create_error(
            "FILE_READ_ERROR",
            f"Failed to read file: {str(e)}",
            {"file_path": str(path)}
        )


def get_file_info(file_path: str) -> Union[Dict[str, Any], ErrorDict]:
    """
    Get file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file info or error
    """
    path = Path(file_path).resolve()
    
    if not path.exists():
        return create_error(
            "FILE_NOT_FOUND",
            f"File does not exist: {path}",
            {"file_path": str(path)}
        )
    
    try:
        stat = path.stat()
        return {
            'path': str(path),
            'name': path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'suffix': path.suffix
        }
    except Exception as e:
        return create_error(
            "FILE_INFO_ERROR",
            f"Failed to get file info: {str(e)}",
            {"file_path": str(path)}
        )