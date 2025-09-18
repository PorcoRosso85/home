"""Use case for extracting symbols from a codebase."""

from typing import List, Union, Optional, Dict, Any
from pathlib import Path
from ..domain.symbol import Symbol
from ..domain.symbol_parser import parse_ctags_output
from ..domain.errors import ErrorDict, create_error, is_error
from ..infrastructure.ctags_runner import run_ctags_standard_format
from ..infrastructure.file_scanner import scan_directory
from ..infrastructure.kuzu_repository import KuzuRepository


def extract_symbols_from_path(
    path: str,
    extensions: Optional[List[str]] = None,
    ctags_path: str = "ctags"
) -> Union[List[Symbol], ErrorDict]:
    """
    Extract symbols from a file or directory.
    
    Args:
        path: File or directory path
        extensions: Optional list of file extensions to include
        ctags_path: Path to ctags executable
        
    Returns:
        List of Symbol entities or error dictionary
    """
    abs_path = Path(path).resolve()
    
    if not abs_path.exists():
        return create_error(
            "PATH_NOT_FOUND",
            f"Path does not exist: {abs_path}",
            {"path": str(abs_path)}
        )
    
    # Run ctags
    ctags_output = run_ctags_standard_format(str(abs_path), extensions, ctags_path)
    if is_error(ctags_output):
        return ctags_output
    
    # Parse output
    base_path = str(abs_path.parent) if abs_path.is_file() else str(abs_path)
    symbols = parse_ctags_output(ctags_output, base_path)
    
    return symbols


def extract_and_store_symbols(
    path: str,
    repository: KuzuRepository,
    extensions: Optional[List[str]] = None,
    ctags_path: str = "ctags"
) -> Union[Dict[str, Any], ErrorDict]:
    """
    Extract symbols and store them in KuzuDB.
    
    Args:
        path: File or directory path
        repository: KuzuDB repository instance
        extensions: Optional list of file extensions
        ctags_path: Path to ctags executable
        
    Returns:
        Summary dictionary or error
    """
    # Extract symbols
    symbols = extract_symbols_from_path(path, extensions, ctags_path)
    if is_error(symbols):
        return symbols
    
    # Store symbols
    store_result = repository.store_symbols(symbols)
    if is_error(store_result):
        return store_result
    
    return {
        'path': str(Path(path).resolve()),
        'symbols_extracted': len(symbols),
        'symbols_stored': store_result
    }


def extract_symbols_from_files(
    files: List[str],
    extensions: Optional[List[str]] = None,
    ctags_path: str = "ctags"
) -> Union[List[Symbol], ErrorDict]:
    """
    Extract symbols from multiple files.
    
    Args:
        files: List of file paths
        extensions: Optional list of file extensions to filter
        ctags_path: Path to ctags executable
        
    Returns:
        Combined list of symbols or error
    """
    all_symbols = []
    
    for file_path in files:
        # Filter by extension if specified
        if extensions:
            file_ext = Path(file_path).suffix
            if file_ext not in extensions:
                continue
        
        symbols = extract_symbols_from_path(file_path, None, ctags_path)
        if is_error(symbols):
            return symbols
        
        all_symbols.extend(symbols)
    
    return all_symbols


def extract_and_store_from_multiple_paths(
    paths: List[str],
    repository: KuzuRepository,
    extensions: Optional[List[str]] = None,
    ctags_path: str = "ctags"
) -> Union[List[Dict[str, Any]], ErrorDict]:
    """
    Extract and store symbols from multiple paths.
    
    Args:
        paths: List of file or directory paths
        repository: KuzuDB repository
        extensions: Optional file extensions
        ctags_path: Path to ctags executable
        
    Returns:
        List of summaries or error
    """
    results = []
    
    for path in paths:
        result = extract_and_store_symbols(path, repository, extensions, ctags_path)
        if is_error(result):
            return result
        results.append(result)
    
    return results