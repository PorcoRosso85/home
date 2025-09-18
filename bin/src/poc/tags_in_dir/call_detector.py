#!/usr/bin/env python3
"""
Call relationship detection using pattern matching.

This module analyzes source code to detect function call relationships
using pattern matching and AST parsing for Python files.
"""

import ast
import re
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class CallRelationship:
    """Represents a function call relationship."""
    
    from_location_uri: str
    to_function_name: str
    line_number: int
    confidence: float  # 0.0 to 1.0, based on detection method


class CallDetector:
    """Detects function call relationships in source code."""
    
    def __init__(self, symbols: List[Dict[str, Any]]):
        """
        Initialize the call detector with known symbols.
        
        Args:
            symbols: List of symbol dictionaries from KuzuStorage
        """
        self.symbols = symbols
        self._build_symbol_index()
    
    def _build_symbol_index(self):
        """Build indices for quick symbol lookup."""
        # Index by name
        self.symbols_by_name = {}
        for symbol in self.symbols:
            name = symbol["name"]
            if name not in self.symbols_by_name:
                self.symbols_by_name[name] = []
            self.symbols_by_name[name].append(symbol)
        
        # Index by file
        self.symbols_by_file = {}
        for symbol in self.symbols:
            file_path = self._extract_file_path(symbol["location_uri"])
            if file_path not in self.symbols_by_file:
                self.symbols_by_file[file_path] = []
            self.symbols_by_file[file_path].append(symbol)
    
    def _extract_file_path(self, location_uri: str) -> str:
        """Extract file path from location URI."""
        # Remove file:// prefix and line number suffix
        if location_uri.startswith("file://"):
            path = location_uri[7:]
            if "#" in path:
                path = path.split("#")[0]
            return path
        return location_uri
    
    def _extract_line_number(self, location_uri: str) -> Optional[int]:
        """Extract line number from location URI."""
        if "#L" in location_uri:
            try:
                return int(location_uri.split("#L")[1])
            except (ValueError, IndexError):
                pass
        return None
    
    def detect_calls_in_file(self, file_path: str) -> List[CallRelationship]:
        """
        Detect function calls in a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of detected call relationships
        """
        abs_path = os.path.abspath(file_path)
        
        # Check file extension
        if file_path.endswith(".py"):
            return self._detect_python_calls(abs_path)
        else:
            # For non-Python files, use regex-based detection
            return self._detect_calls_with_regex(abs_path)
    
    def _detect_python_calls(self, file_path: str) -> List[CallRelationship]:
        """
        Detect function calls in Python files using AST parsing.
        
        Args:
            file_path: Absolute path to the Python file
            
        Returns:
            List of detected call relationships
        """
        relationships = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            
            # Get functions defined in this file
            file_functions = self.symbols_by_file.get(file_path, [])
            
            # Visit all nodes in the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Find the corresponding symbol for this function
                    func_symbol = None
                    for symbol in file_functions:
                        if symbol["name"] == node.name and symbol["kind"] == "function":
                            symbol_line = self._extract_line_number(symbol["location_uri"])
                            if symbol_line and abs(symbol_line - node.lineno) <= 1:
                                func_symbol = symbol
                                break
                    
                    if func_symbol:
                        # Analyze function body for calls
                        calls = self._find_calls_in_function(node, func_symbol["location_uri"])
                        relationships.extend(calls)
            
        except Exception as e:
            print(f"Error parsing Python file {file_path}: {e}")
        
        return relationships
    
    def _find_calls_in_function(self, func_node: ast.FunctionDef, from_location_uri: str) -> List[CallRelationship]:
        """
        Find all function calls within a function definition.
        
        Args:
            func_node: AST node for the function
            from_location_uri: Location URI of the calling function
            
        Returns:
            List of call relationships
        """
        relationships = []
        
        class CallVisitor(ast.NodeVisitor):
            def __init__(self, parent):
                self.parent = parent
                self.calls = []
            
            def visit_Call(self, node):
                # Extract function name being called
                func_name = None
                confidence = 0.0
                
                if isinstance(node.func, ast.Name):
                    # Direct function call: func()
                    func_name = node.func.id
                    confidence = 0.9
                elif isinstance(node.func, ast.Attribute):
                    # Method call: obj.method()
                    func_name = node.func.attr
                    confidence = 0.7
                
                if func_name:
                    self.calls.append((func_name, node.lineno, confidence))
                
                self.generic_visit(node)
        
        visitor = CallVisitor(self)
        visitor.visit(func_node)
        
        # Convert found calls to relationships
        for func_name, line_no, confidence in visitor.calls:
            # Check if this function exists in our symbol index
            if func_name in self.symbols_by_name:
                # Create relationships to all matching symbols
                for target_symbol in self.symbols_by_name[func_name]:
                    if target_symbol["kind"] == "function":
                        relationships.append(CallRelationship(
                            from_location_uri=from_location_uri,
                            to_function_name=func_name,
                            line_number=line_no,
                            confidence=confidence
                        ))
            else:
                # Still record the call even if we can't resolve the target
                relationships.append(CallRelationship(
                    from_location_uri=from_location_uri,
                    to_function_name=func_name,
                    line_number=line_no,
                    confidence=confidence * 0.5  # Lower confidence for unresolved calls
                ))
        
        return relationships
    
    def _detect_calls_with_regex(self, file_path: str) -> List[CallRelationship]:
        """
        Detect function calls using regex patterns (fallback for non-Python files).
        
        Args:
            file_path: Absolute path to the file
            
        Returns:
            List of detected call relationships
        """
        relationships = []
        
        # Common patterns for function calls in various languages
        patterns = [
            # Function calls: func() or func(args)
            (r'\b(\w+)\s*\(', 0.6),
            # Method calls: obj.method() or obj->method()
            (r'(?:\.|->)\s*(\w+)\s*\(', 0.5),
            # JavaScript/TypeScript: function calls with await
            (r'await\s+(\w+)\s*\(', 0.7),
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get functions defined in this file
            file_functions = self.symbols_by_file.get(file_path, [])
            
            # For each function in the file
            for func_symbol in file_functions:
                if func_symbol["kind"] != "function":
                    continue
                
                func_line = self._extract_line_number(func_symbol["location_uri"])
                if not func_line:
                    continue
                
                # Analyze a window of lines around the function
                lines = content.split('\n')
                start_line = max(0, func_line - 1)
                
                # Simple heuristic: analyze next 50 lines or until we hit another function
                end_line = min(len(lines), func_line + 50)
                
                for i in range(start_line, end_line):
                    line = lines[i]
                    line_no = i + 1
                    
                    # Check each pattern
                    for pattern, confidence in patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            func_name = match.group(1)
                            
                            # Skip some common false positives
                            if func_name in ['if', 'while', 'for', 'switch', 'catch', 'return']:
                                continue
                            
                            relationships.append(CallRelationship(
                                from_location_uri=func_symbol["location_uri"],
                                to_function_name=func_name,
                                line_number=line_no,
                                confidence=confidence
                            ))
        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        
        return relationships
    
    def detect_all_calls(self, directory: str, extensions: Optional[List[str]] = None) -> List[CallRelationship]:
        """
        Detect all function calls in a directory.
        
        Args:
            directory: Path to the directory to analyze
            extensions: List of file extensions to include
            
        Returns:
            List of all detected call relationships
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.go']
        
        all_relationships = []
        directory_path = Path(directory)
        
        # Process each file
        for ext in extensions:
            for file_path in directory_path.rglob(f"*{ext}"):
                if file_path.is_file():
                    relationships = self.detect_calls_in_file(str(file_path))
                    all_relationships.extend(relationships)
        
        return all_relationships
    
    def resolve_call_targets(self, relationships: List[CallRelationship]) -> List[Tuple[str, str, int]]:
        """
        Resolve function names to location URIs for creating CALLS relationships.
        
        Args:
            relationships: List of detected call relationships
            
        Returns:
            List of tuples (from_uri, to_uri, line_number) ready for storage
        """
        resolved = []
        
        for rel in relationships:
            # Find target symbols
            target_symbols = self.symbols_by_name.get(rel.to_function_name, [])
            
            # For each potential target
            for target in target_symbols:
                if target["kind"] == "function":
                    # Use confidence threshold
                    if rel.confidence >= 0.5:
                        resolved.append((
                            rel.from_location_uri,
                            target["location_uri"],
                            rel.line_number
                        ))
        
        # Remove duplicates
        resolved = list(set(resolved))
        
        return resolved


def main():
    """Example usage of CallDetector."""
    print("Import this module and use with symbol data:")
    print("  from call_detector import CallDetector")
    print("  detector = CallDetector(symbols)")
    print("  relationships = detector.detect_all_calls('.')")


if __name__ == "__main__":
    main()