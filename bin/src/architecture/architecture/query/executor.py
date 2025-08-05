"""Query executor for DQL queries."""

from pathlib import Path
from typing import List, Dict, Any
from architecture.db import KuzuConnectionManager


class QueryExecutor:
    """Executes DQL queries against KuzuDB."""
    
    def __init__(self, connection_manager: KuzuConnectionManager):
        """Initialize query executor.
        
        Args:
            connection_manager: Database connection manager
        """
        self.connection_manager = connection_manager
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a DQL query and return results.
        
        Args:
            query: Cypher query to execute
            
        Returns:
            List of result rows as dictionaries
        """
        conn = self.connection_manager.get_connection()
        result = conn.execute(query)
        
        # Get column names from the result
        columns = result.get_column_names()
        
        # Convert results to list of dictionaries
        rows = []
        while result.has_next():
            row_data = result.get_next()
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = row_data[i]
            rows.append(row_dict)
        
        return rows
    
    def execute_query_from_file(self, query_path: Path) -> List[Dict[str, Any]]:
        """Execute a DQL query from a file.
        
        Args:
            query_path: Path to file containing Cypher query
            
        Returns:
            List of result rows as dictionaries
        """
        with open(query_path, 'r') as f:
            query_content = f.read()
        
        # Remove comments and empty lines
        lines = []
        for line in query_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                lines.append(line)
        
        query = ' '.join(lines)
        return self.execute_query(query)