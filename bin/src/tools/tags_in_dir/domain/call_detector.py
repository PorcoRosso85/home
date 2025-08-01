"""Pure functions for detecting call relationships in code."""

import ast
from typing import List, Tuple, Set, Dict, Any, Union, Optional
from pathlib import Path
from .symbol import Symbol
from .call_relationship import CallRelationship, create_call_relationship
from .errors import ErrorDict, create_error


def detect_calls_in_file(
    file_path: str,
    symbols: List[Symbol],
    symbol_names: Set[str]
) -> Union[List[Tuple[str, str, int]], ErrorDict]:
    """
    Detect function calls in a Python file.
    
    Args:
        file_path: Path to the Python file
        symbols: List of all known symbols
        symbol_names: Set of all symbol names for quick lookup
        
    Returns:
        List of (from_symbol, to_symbol, line_number) tuples or error
    """
    abs_path = Path(file_path).resolve()
    
    try:
        with open(abs_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return create_error(
            "FILE_READ_ERROR",
            f"Failed to read file: {str(e)}",
            {"file_path": str(abs_path)}
        )
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        # Not a Python file or syntax error, skip
        return []
    
    # Filter symbols from this file
    file_uri_prefix = f"file://{abs_path}#"
    file_symbols = [s for s in symbols if s.location_uri.startswith(file_uri_prefix)]
    
    # Create mapping of line number to symbol
    line_to_symbol: Dict[int, Symbol] = {}
    for symbol in file_symbols:
        line_num = int(symbol.location_uri.split('#L')[1])
        line_to_symbol[line_num] = symbol
    
    visitor = CallVisitor(symbol_names, line_to_symbol)
    visitor.visit(tree)
    
    return visitor.calls


class CallVisitor(ast.NodeVisitor):
    """AST visitor to detect function calls."""
    
    def __init__(self, symbol_names: Set[str], line_to_symbol: Dict[int, Symbol]):
        self.symbol_names = symbol_names
        self.line_to_symbol = line_to_symbol
        self.calls: List[Tuple[str, str, int]] = []
        self.current_function: Optional[Symbol] = None
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track current function context."""
        old_function = self.current_function
        
        # Find symbol for this function definition
        if node.lineno in self.line_to_symbol:
            self.current_function = self.line_to_symbol[node.lineno]
        
        self.generic_visit(node)
        self.current_function = old_function
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track current async function context."""
        self.visit_FunctionDef(node)  # Same logic
        
    def visit_Call(self, node: ast.Call) -> None:
        """Detect function calls."""
        if not self.current_function:
            self.generic_visit(node)
            return
            
        # Extract called function name
        called_name = extract_call_name(node)
        if called_name and called_name in self.symbol_names:
            self.calls.append((
                self.current_function.location_uri,
                called_name,
                node.lineno
            ))
            
        self.generic_visit(node)


def extract_call_name(node: ast.Call) -> Optional[str]:
    """Extract function name from a call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    elif isinstance(node.func, ast.Attribute):
        # For method calls like obj.method(), return 'method'
        return node.func.attr
    return None


def resolve_call_targets(
    calls: List[Tuple[str, str, int]],
    symbols: List[Symbol]
) -> List[CallRelationship]:
    """
    Resolve call targets to actual symbol URIs.
    
    Args:
        calls: List of (from_uri, to_name, line_number) tuples
        symbols: List of all symbols
        
    Returns:
        List of CallRelationship entities
    """
    # Create name to symbols mapping
    name_to_symbols: Dict[str, List[Symbol]] = {}
    for symbol in symbols:
        if symbol.name not in name_to_symbols:
            name_to_symbols[symbol.name] = []
        name_to_symbols[symbol.name].append(symbol)
    
    relationships = []
    
    for from_uri, to_name, line_number in calls:
        if to_name not in name_to_symbols:
            continue
            
        # Find the best match for the target
        # For now, just use the first match
        # TODO: Implement more sophisticated resolution based on scope
        target_symbols = name_to_symbols[to_name]
        if target_symbols:
            target = target_symbols[0]
            result = create_call_relationship(
                from_location_uri=from_uri,
                to_location_uri=target.location_uri,
                line_number=line_number
            )
            # Since we know the URIs are valid (they come from existing symbols),
            # we can safely assume this won't return an error
            if not isinstance(result, dict):  # Not an ErrorDict
                relationships.append(result)
    
    return relationships