"""Use case for detecting and storing call relationships."""

from typing import List, Union, Optional, Dict, Any, Set
from pathlib import Path
from ..domain.symbol import Symbol
from ..domain.call_relationship import CallRelationship
from ..domain.call_detector import detect_calls_in_file, resolve_call_targets
from ..domain.errors import ErrorDict, create_error, is_error
from ..infrastructure.file_scanner import scan_directory
from ..infrastructure.kuzu_repository import KuzuRepository


def detect_calls_in_directory(
    directory: str,
    symbols: List[Symbol],
    extensions: Optional[List[str]] = None
) -> Union[List[CallRelationship], ErrorDict]:
    """
    Detect all call relationships in a directory.
    
    Args:
        directory: Directory path to scan
        symbols: List of all known symbols
        extensions: Optional list of file extensions to include
        
    Returns:
        List of CallRelationship entities or error
    """
    # Scan for files
    files = scan_directory(directory, extensions)
    if is_error(files):
        return files
    
    # Create symbol name set for quick lookup
    symbol_names = {s.name for s in symbols}
    
    # Detect calls in each file
    all_calls = []
    
    for file_path in files:
        # Only process Python files for now
        if not file_path.endswith('.py'):
            continue
        
        calls = detect_calls_in_file(file_path, symbols, symbol_names)
        if is_error(calls):
            # Skip files with errors (e.g., syntax errors)
            continue
        
        all_calls.extend(calls)
    
    # Resolve call targets to actual symbol URIs
    relationships = resolve_call_targets(all_calls, symbols)
    
    return relationships


def detect_and_store_calls(
    directory: str,
    repository: KuzuRepository,
    extensions: Optional[List[str]] = None
) -> Union[Dict[str, Any], ErrorDict]:
    """
    Detect call relationships and store them in KuzuDB.
    
    Args:
        directory: Directory to analyze
        repository: KuzuDB repository
        extensions: Optional file extensions
        
    Returns:
        Summary dictionary or error
    """
    # First, get all symbols from the database
    symbols_result = repository.execute_cypher(
        "MATCH (s:Symbol) RETURN s.name, s.kind, s.location_uri, s.scope, s.signature"
    )
    if is_error(symbols_result):
        return symbols_result
    
    # Convert to Symbol objects
    symbols = []
    for row in symbols_result:
        symbols.append(Symbol(
            name=row[0],
            kind=row[1],
            location_uri=row[2],
            scope=row[3],
            signature=row[4]
        ))
    
    if not symbols:
        return create_error(
            "NO_SYMBOLS_FOUND",
            "No symbols found in database. Extract symbols first.",
            {}
        )
    
    # Detect relationships
    relationships = detect_calls_in_directory(directory, symbols, extensions)
    if is_error(relationships):
        return relationships
    
    # Store relationships
    store_result = repository.store_call_relationships(relationships)
    if is_error(store_result):
        return store_result
    
    return {
        'directory': str(Path(directory).resolve()),
        'symbols_analyzed': len(symbols),
        'calls_detected': len(relationships),
        'calls_stored': store_result
    }


def detect_calls_for_file(
    file_path: str,
    repository: KuzuRepository
) -> Union[Dict[str, Any], ErrorDict]:
    """
    Detect and store call relationships for a single file.
    
    Args:
        file_path: Path to Python file
        repository: KuzuDB repository
        
    Returns:
        Summary or error
    """
    # Get all symbols
    symbols_result = repository.execute_cypher(
        "MATCH (s:Symbol) RETURN s.name, s.kind, s.location_uri, s.scope, s.signature"
    )
    if is_error(symbols_result):
        return symbols_result
    
    symbols = []
    for row in symbols_result:
        symbols.append(Symbol(
            name=row[0],
            kind=row[1],
            location_uri=row[2],
            scope=row[3],
            signature=row[4]
        ))
    
    if not symbols:
        return {
            'file': str(Path(file_path).resolve()),
            'calls_detected': 0,
            'calls_stored': 0
        }
    
    # Detect calls in file
    symbol_names = {s.name for s in symbols}
    calls = detect_calls_in_file(file_path, symbols, symbol_names)
    if is_error(calls):
        return calls
    
    # Resolve and store
    relationships = resolve_call_targets(calls, symbols)
    
    if relationships:
        store_result = repository.store_call_relationships(relationships)
        if is_error(store_result):
            return store_result
    else:
        store_result = 0
    
    return {
        'file': str(Path(file_path).resolve()),
        'calls_detected': len(relationships),
        'calls_stored': store_result
    }