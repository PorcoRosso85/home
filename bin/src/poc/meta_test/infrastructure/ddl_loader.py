"""
DDL Loader - Handles DDL-specific file loading and execution

This implementation handles multi-statement DDL files with special
parsing for Cypher DDL statements.
"""

from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import re

from .errors import FileOperationError, ValidationError, NotFoundError

from .logger import get_logger
from .graph_adapter import GraphAdapter

logger = get_logger(__name__)


class DDLLoader:
    """DDL loader that wraps query_loader for multi-statement handling."""
    
    def __init__(self, graph_adapter: GraphAdapter, base_dir: Optional[str] = None):
        """
        Initialize DDL loader with graph adapter.
        
        Args:
            graph_adapter: GraphAdapter instance for executing DDL
            base_dir: Base directory for DDL files (default: current directory)
        """
        self.graph = graph_adapter
        self.base_dir = base_dir or str(Path.cwd())
        
    def load_ddl(self, ddl_name: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Load and execute a DDL file.
        
        Args:
            ddl_name: Name of DDL file (without .cypher extension)
            
        Returns:
            Tuple of (success: bool, results: List[Dict])
        """
        logger.info(f"Loading DDL file", name=ddl_name)
        
        # Look for DDL file in various locations
        file_paths = [
            Path(self.base_dir) / f"{ddl_name}.cypher",
            Path(self.base_dir) / "ddl" / f"{ddl_name}.cypher",
        ]
        
        for file_path in file_paths:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Parse and execute statements
                    return self._execute_ddl_content(content, ddl_name)
                except Exception as e:
                    error = FileOperationError(
                        type="FileOperationError",
                        message=f"Failed to read DDL file: {str(e)}",
                        operation="read",
                        file_path=str(file_path),
                        permission_issue=True,
                        exists=True
                    )
                    return False, [error]
        
        # File not found
        error = NotFoundError(
            type="NotFoundError",
            message=f"DDL file '{ddl_name}' not found",
            resource_type="ddl",
            resource_id=ddl_name,
            search_locations=[str(p) for p in file_paths]
        )
        logger.error(f"Failed to load DDL file", name=ddl_name, error=error.get("message"))
        return False, [error]
        
    def _execute_ddl_content(self, content: str, source_name: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Parse and execute DDL content as multiple statements.
        
        Args:
            content: DDL file content
            source_name: Name of source file for logging
            
        Returns:
            Tuple of (all_success: bool, results: List[Dict])
        """
        statements = self._parse_statements(content)
        results = []
        all_success = True
        
        logger.info(f"Executing DDL statements", 
                   source=source_name, 
                   count=len(statements))
        
        for i, statement in enumerate(statements):
            if not statement.strip():
                continue
                
            try:
                result = self.graph.execute_cypher(statement)
                results.append({
                    "statement_index": i,
                    "success": True,
                    "result": result
                })
                logger.debug(f"Statement executed successfully", index=i)
                
            except Exception as e:
                all_success = False
                error_result = ValidationError(
                    type="ValidationError",
                    message=f"Statement {i} failed: {str(e)}",
                    field="statement",
                    value=statement[:100] + "..." if len(statement) > 100 else statement,
                    constraint="Valid DDL statement",
                    suggestion="Check DDL syntax"
                )
                results.append({
                    "statement_index": i,
                    "success": False,
                    "error": error_result
                })
                logger.error(f"Statement failed", index=i, error=str(e))
                
        return all_success, results
        
    def _parse_statements(self, content: str) -> List[str]:
        """
        Parse DDL content into individual statements.
        
        Handles:
        - Comments (// and --)
        - Multi-line statements
        - Quoted strings containing semicolons
        
        Args:
            content: Raw DDL content
            
        Returns:
            List of individual DDL statements
        """
        # Remove single-line comments
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove // comments
            if '//' in line:
                line = line[:line.index('//')]
            # Remove -- comments  
            if '--' in line:
                line = line[:line.index('--')]
            cleaned_lines.append(line)
            
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Split by semicolon, but not within quotes
        statements = []
        current_statement = []
        in_quotes = False
        quote_char = None
        
        for char in cleaned_content:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == ';' and not in_quotes:
                statement = ''.join(current_statement).strip()
                if statement:
                    statements.append(statement)
                current_statement = []
                continue
                
            current_statement.append(char)
            
        # Don't forget the last statement if no trailing semicolon
        final_statement = ''.join(current_statement).strip()
        if final_statement:
            statements.append(final_statement)
            
        return statements
        
    def load_directory(self, directory: str, pattern: str = "*.cypher") -> Tuple[bool, Dict[str, List[Dict[str, Any]]]]:
        """
        Load all DDL files from a directory.
        
        Args:
            directory: Directory path containing DDL files
            pattern: File pattern to match (default: *.cypher)
            
        Returns:
            Tuple of (all_success: bool, results: Dict[filename, List[Dict]])
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            error = FileOperationError(
                type="FileOperationError",
                message=f"Directory not found: {directory}",
                operation="read",
                file_path=str(directory),
                permission_issue=False,
                exists=False
            )
            return False, {"error": [error]}
            
        results = {}
        all_success = True
        
        # Get all matching files
        files = sorted(dir_path.glob(pattern))
        logger.info(f"Loading DDL files from directory", 
                   path=str(directory), 
                   count=len(files))
        
        for file_path in files:
            # Use file stem (name without extension) as query name
            ddl_name = file_path.stem
            success, file_results = self.load_ddl(ddl_name)
            
            results[file_path.name] = file_results
            if not success:
                all_success = False
                
        return all_success, results


# Convenience function to match the original API
def load_ddl_file(graph_adapter: GraphAdapter, file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Load a single DDL file (convenience function).
    
    Args:
        graph_adapter: GraphAdapter instance
        file_path: Path to DDL file
        
    Returns:
        Tuple of (success: bool, results: List[Dict])
    """
    path = Path(file_path)
    loader = DDLLoader(graph_adapter, base_dir=str(path.parent))
    return loader.load_ddl(path.stem)