"""DDL Helper functions for KuzuDB operations."""

import re
from typing import Any


def execute_ddl_file(conn: Any, path: str) -> None:
    """Execute DDL file with multiple statements.
    
    Args:
        conn: KuzuDB connection object
        path: Path to DDL file
        
    Features:
    - Split statements by semicolon
    - Remove comments (-- and /* */)
    - Ignore "already exists" errors
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove comments
    content = _remove_comments(content)
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
    
    for statement in statements:
        try:
            conn.execute(statement)
        except Exception as e:
            # Ignore "already exists" errors
            if "already exists" not in str(e).lower():
                raise


def _remove_comments(content: str) -> str:
    """Remove SQL comments from content.
    
    Args:
        content: SQL content with comments
        
    Returns:
        Content with comments removed
    """
    # Remove single-line comments (--)
    content = re.sub(r'--.*?(?=\n|$)', '', content)
    
    # Remove multi-line comments (/* */)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    return content