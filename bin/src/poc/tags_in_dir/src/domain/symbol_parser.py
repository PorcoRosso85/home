"""Pure functions for parsing ctags output into Symbol entities."""

from typing import List, Dict, Any, Union
from pathlib import Path
from .symbol import Symbol
from .errors import ErrorDict, create_error


def parse_ctags_output(ctags_output: str, base_path: str) -> Union[List[Symbol], ErrorDict]:
    """
    Parse ctags output into Symbol entities.
    
    Args:
        ctags_output: Raw output from ctags command
        base_path: Base directory path for constructing URIs
        
    Returns:
        List of Symbol entities or error dictionary
    """
    if not ctags_output.strip():
        return []
    
    symbols = []
    base_path_obj = Path(base_path).resolve()
    
    for line in ctags_output.strip().split('\n'):
        if line.startswith('!'):  # Skip ctags header comments
            continue
            
        parts = line.split('\t')
        if len(parts) < 4:
            continue
            
        name = parts[0]
        file_path = parts[1]
        line_pattern = parts[2]
        kind = parts[3]
        
        # Extract line number from pattern
        line_number = extract_line_number(line_pattern)
        if not line_number:
            continue
            
        # Construct absolute path
        if Path(file_path).is_absolute():
            abs_path = Path(file_path)
        else:
            abs_path = (base_path_obj / file_path).resolve()
            
        # Create location URI
        location_uri = f"file://{abs_path}#L{line_number}"
        
        # Extract additional fields
        scope = None
        signature = None
        
        for field in parts[4:]:
            if field.startswith('scope:'):
                scope = field[6:]
            elif field.startswith('signature:'):
                signature = field[10:]
                
        try:
            symbol = Symbol(
                name=name,
                kind=kind,
                location_uri=location_uri,
                scope=scope,
                signature=signature
            )
            symbols.append(symbol)
        except ValueError as e:
            return create_error(
                "SYMBOL_VALIDATION_ERROR",
                f"Invalid symbol data: {str(e)}",
                {"line": line}
            )
            
    return symbols


def extract_line_number(pattern: str) -> Union[int, None]:
    """
    Extract line number from ctags pattern.
    
    Args:
        pattern: Ctags search pattern (e.g., '/^def function(/:' or '42;"')
        
    Returns:
        Line number or None if not found
    """
    # Check if pattern is a line number
    if pattern.isdigit():
        return int(pattern)
    
    # For regex patterns, we need line number from extended fields
    if pattern.endswith(';"'):
        number = pattern[:-2].strip()
        if number.isdigit():
            return int(number)
            
    return None


def filter_symbols_by_kind(symbols: List[Symbol], kinds: List[str]) -> List[Symbol]:
    """Filter symbols by their kind."""
    return [s for s in symbols if s.kind in kinds]


def filter_symbols_by_file(symbols: List[Symbol], file_path: str) -> List[Symbol]:
    """Filter symbols by file path."""
    abs_path = Path(file_path).resolve()
    file_uri_prefix = f"file://{abs_path}#"
    return [s for s in symbols if s.location_uri.startswith(file_uri_prefix)]