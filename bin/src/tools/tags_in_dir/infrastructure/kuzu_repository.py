"""Repository for KuzuDB operations."""

import kuzu
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
from ..domain.symbol import Symbol
from ..domain.call_relationship import CallRelationship
from ..domain.errors import ErrorDict, create_error


class KuzuRepository:
    """Repository for persisting symbols and relationships in KuzuDB."""
    
    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize KuzuDB connection.
        
        Args:
            db_path: Path to database file or ":memory:" for in-memory DB
        """
        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._create_schema()
    
    def _create_schema(self) -> None:
        """Create database schema if not exists."""
        # Create Symbol node table
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Symbol (
                location_uri STRING PRIMARY KEY,
                name STRING,
                kind STRING,
                scope STRING,
                signature STRING
            )
        """)
        
        # Create CALLS relationship table
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS CALLS (
                FROM Symbol TO Symbol,
                line_number INT64
            )
        """)
    
    def store_symbol(self, symbol: Symbol) -> Union[bool, ErrorDict]:
        """
        Store a single symbol in the database.
        
        Args:
            symbol: Symbol to store
            
        Returns:
            True if successful, error dictionary otherwise
        """
        try:
            self.conn.execute(
                """
                MERGE (s:Symbol {location_uri: $location_uri})
                SET s.name = $name,
                    s.kind = $kind,
                    s.scope = $scope,
                    s.signature = $signature
                """,
                {
                    'location_uri': symbol.location_uri,
                    'name': symbol.name,
                    'kind': symbol.kind,
                    'scope': symbol.scope,
                    'signature': symbol.signature
                }
            )
            return True
        except Exception as e:
            return create_error(
                "KUZU_STORE_ERROR",
                f"Failed to store symbol: {str(e)}",
                {"symbol": symbol.to_dict()}
            )
    
    def store_symbols(self, symbols: List[Symbol]) -> Union[int, ErrorDict]:
        """
        Store multiple symbols in the database.
        
        Args:
            symbols: List of symbols to store
            
        Returns:
            Number of symbols stored or error dictionary
        """
        count = 0
        for symbol in symbols:
            result = self.store_symbol(symbol)
            if isinstance(result, dict) and 'error' in result:
                return result
            count += 1
        return count
    
    def store_call_relationship(self, relationship: CallRelationship) -> Union[bool, ErrorDict]:
        """
        Store a call relationship in the database.
        
        Args:
            relationship: CallRelationship to store
            
        Returns:
            True if successful, error dictionary otherwise
        """
        try:
            self.conn.execute(
                """
                MATCH (from:Symbol {location_uri: $from_uri}),
                      (to:Symbol {location_uri: $to_uri})
                MERGE (from)-[c:CALLS]->(to)
                SET c.line_number = $line_number
                """,
                {
                    'from_uri': relationship.from_location_uri,
                    'to_uri': relationship.to_location_uri,
                    'line_number': relationship.line_number
                }
            )
            return True
        except Exception as e:
            return create_error(
                "KUZU_RELATIONSHIP_ERROR",
                f"Failed to store relationship: {str(e)}",
                {
                    "from": relationship.from_location_uri,
                    "to": relationship.to_location_uri
                }
            )
    
    def store_call_relationships(self, relationships: List[CallRelationship]) -> Union[int, ErrorDict]:
        """
        Store multiple call relationships.
        
        Args:
            relationships: List of relationships to store
            
        Returns:
            Number of relationships stored or error dictionary
        """
        count = 0
        for relationship in relationships:
            result = self.store_call_relationship(relationship)
            if isinstance(result, dict) and 'error' in result:
                return result
            count += 1
        return count
    
    def find_symbol_by_uri(self, location_uri: str) -> Union[Optional[Symbol], ErrorDict]:
        """Find a symbol by its location URI."""
        try:
            result = self.conn.execute(
                """
                MATCH (s:Symbol {location_uri: $uri})
                RETURN s.name, s.kind, s.location_uri, s.scope, s.signature
                """,
                {'uri': location_uri}
            )
            
            if result.has_next():
                row = result.get_next()
                return Symbol(
                    name=row[0],
                    kind=row[1],
                    location_uri=row[2],
                    scope=row[3],
                    signature=row[4]
                )
            return None
            
        except Exception as e:
            return create_error(
                "KUZU_QUERY_ERROR",
                f"Failed to find symbol: {str(e)}",
                {"location_uri": location_uri}
            )
    
    def find_symbols_by_name(self, name: str) -> Union[List[Symbol], ErrorDict]:
        """Find all symbols with a given name."""
        try:
            result = self.conn.execute(
                """
                MATCH (s:Symbol)
                WHERE s.name = $name
                RETURN s.name, s.kind, s.location_uri, s.scope, s.signature
                """,
                {'name': name}
            )
            
            symbols = []
            while result.has_next():
                row = result.get_next()
                symbols.append(Symbol(
                    name=row[0],
                    kind=row[1],
                    location_uri=row[2],
                    scope=row[3],
                    signature=row[4]
                ))
            
            return symbols
            
        except Exception as e:
            return create_error(
                "KUZU_QUERY_ERROR",
                f"Failed to find symbols by name: {str(e)}",
                {"name": name}
            )
    
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Union[List[Any], ErrorDict]:
        """
        Execute a raw Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            Query results as list or error dictionary
        """
        try:
            result = self.conn.execute(query, parameters or {})
            
            rows = []
            while result.has_next():
                rows.append(result.get_next())
            
            return rows
            
        except Exception as e:
            return create_error(
                "KUZU_QUERY_ERROR",
                f"Failed to execute Cypher query: {str(e)}",
                {"query": query}
            )
    
    def export_to_parquet(self, output_dir: str) -> Union[Dict[str, str], ErrorDict]:
        """
        Export database contents to Parquet files.
        
        Args:
            output_dir: Directory to save Parquet files
            
        Returns:
            Dictionary of exported file paths or error
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exports = {}
        
        # Export symbols
        symbols_path = output_path / "symbols.parquet"
        try:
            self.conn.execute(f"""
                COPY (MATCH (s:Symbol) RETURN s.*) 
                TO '{symbols_path}'
            """)
            exports['symbols'] = str(symbols_path)
        except Exception as e:
            return create_error(
                "KUZU_EXPORT_ERROR",
                f"Failed to export symbols: {str(e)}",
                {"path": str(symbols_path)}
            )
        
        # Export relationships
        calls_path = output_path / "calls.parquet"
        try:
            self.conn.execute(f"""
                COPY (
                    MATCH (from:Symbol)-[c:CALLS]->(to:Symbol)
                    RETURN from.location_uri AS from_uri, 
                           to.location_uri AS to_uri,
                           c.line_number
                ) TO '{calls_path}'
            """)
            exports['calls'] = str(calls_path)
        except Exception as e:
            return create_error(
                "KUZU_EXPORT_ERROR",
                f"Failed to export calls: {str(e)}",
                {"path": str(calls_path)}
            )
        
        return exports
    
    def close(self) -> None:
        """Close database connection."""
        # KuzuDB connections are automatically closed
        pass