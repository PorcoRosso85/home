#!/usr/bin/env python3
"""
KuzuDB storage backend for tags_in_dir.

This module provides storage functionality for Symbol nodes and CALLS relationships
using KuzuDB graph database.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import kuzu

from tags_in_dir import Symbol


@dataclass
class KuzuStorage:
    """Storage backend for symbols using KuzuDB."""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize KuzuDB storage.

        Args:
            db_path: Path to the database file. Defaults to ":memory:" for in-memory database.
        """
        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Initialize the database schema."""
        # Create Symbol node table
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Symbol(
                location_uri STRING PRIMARY KEY,
                name STRING,
                kind STRING,
                scope STRING,
                signature STRING
            )
        """)

        # Create CALLS relationship table
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS CALLS(
                FROM Symbol TO Symbol,
                line_number INT64
            )
        """)

    def store_symbol(self, symbol: Symbol) -> bool:
        """
        Store a single symbol in the database.

        Args:
            symbol: Symbol object to store

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Prepare values, handling None values
            params = {
                "location_uri": symbol.location_uri,
                "name": symbol.name,
                "kind": symbol.kind,
                "scope": symbol.scope if symbol.scope else "",
                "signature": symbol.signature if symbol.signature else ""
            }

            # Use MERGE to handle duplicates gracefully
            self.conn.execute("""
                MERGE (s:Symbol {location_uri: $location_uri})
                SET s.name = $name,
                    s.kind = $kind,
                    s.scope = $scope,
                    s.signature = $signature
            """, params)

            return True
        except Exception as e:
            print(f"Error storing symbol: {e}")
            return False

    def store_symbols(self, symbols: List[Symbol]) -> int:
        """
        Store multiple symbols in the database.

        Args:
            symbols: List of Symbol objects to store

        Returns:
            Number of symbols successfully stored
        """
        stored_count = 0
        for symbol in symbols:
            if self.store_symbol(symbol):
                stored_count += 1
        return stored_count

    def create_calls_relationship(
        self, from_location_uri: str, to_location_uri: str, line_number: Optional[int] = None
    ) -> bool:
        """
        Create a CALLS relationship between two symbols.

        Args:
            from_location_uri: Location URI of the calling symbol
            to_location_uri: Location URI of the called symbol
            line_number: Optional line number where the call occurs

        Returns:
            True if relationship created successfully, False otherwise
        """
        try:
            params = {
                "from_uri": from_location_uri,
                "to_uri": to_location_uri,
                "line_number": line_number if line_number else 0
            }

            # Create the relationship
            self.conn.execute("""
                MATCH (from:Symbol {location_uri: $from_uri})
                MATCH (to:Symbol {location_uri: $to_uri})
                MERGE (from)-[c:CALLS]->(to)
                SET c.line_number = $line_number
            """, params)

            return True
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return False

    def find_symbols_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Find all symbols in a specific file.

        Args:
            file_path: Path to the file (can be relative or absolute)

        Returns:
            List of symbol dictionaries
        """
        # Convert to absolute path and create file URI pattern
        abs_path = os.path.abspath(file_path)
        file_uri_pattern = f"file://{abs_path}#%"

        result = self.conn.execute("""
            MATCH (s:Symbol)
            WHERE s.location_uri STARTS WITH $pattern
            RETURN s.location_uri, s.name, s.kind, s.scope, s.signature
            ORDER BY s.location_uri
        """, {"pattern": file_uri_pattern[:-1]})  # Remove % for STARTS WITH

        symbols = []
        while result.has_next():
            row = result.get_next()
            symbols.append({
                "location_uri": row[0],
                "name": row[1],
                "kind": row[2],
                "scope": row[3],
                "signature": row[4]
            })

        return symbols

    def find_symbols_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Find symbols by name.

        Args:
            name: Symbol name to search for

        Returns:
            List of symbol dictionaries
        """
        result = self.conn.execute("""
            MATCH (s:Symbol)
            WHERE s.name = $name
            RETURN s.location_uri, s.name, s.kind, s.scope, s.signature
            ORDER BY s.location_uri
        """, {"name": name})

        symbols = []
        while result.has_next():
            row = result.get_next()
            symbols.append({
                "location_uri": row[0],
                "name": row[1],
                "kind": row[2],
                "scope": row[3],
                "signature": row[4]
            })

        return symbols

    def find_symbols_by_kind(self, kind: str) -> List[Dict[str, Any]]:
        """
        Find all symbols of a specific kind.

        Args:
            kind: Symbol kind (e.g., 'function', 'class')

        Returns:
            List of symbol dictionaries
        """
        result = self.conn.execute("""
            MATCH (s:Symbol)
            WHERE s.kind = $kind
            RETURN s.location_uri, s.name, s.kind, s.scope, s.signature
            ORDER BY s.name
        """, {"kind": kind})

        symbols = []
        while result.has_next():
            row = result.get_next()
            symbols.append({
                "location_uri": row[0],
                "name": row[1],
                "kind": row[2],
                "scope": row[3],
                "signature": row[4]
            })

        return symbols

    def find_symbol_calls(self, location_uri: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Find all symbols that call or are called by a specific symbol.

        Args:
            location_uri: Location URI of the symbol

        Returns:
            Tuple of (symbols_called_by_this, symbols_calling_this)
        """
        # Find symbols called by this symbol
        called_result = self.conn.execute("""
            MATCH (from:Symbol {location_uri: $uri})-[c:CALLS]->(to:Symbol)
            RETURN to.location_uri, to.name, to.kind, c.line_number
            ORDER BY c.line_number
        """, {"uri": location_uri})

        called_by_this = []
        while called_result.has_next():
            row = called_result.get_next()
            called_by_this.append({
                "location_uri": row[0],
                "name": row[1],
                "kind": row[2],
                "line_number": row[3]
            })

        # Find symbols that call this symbol
        callers_result = self.conn.execute("""
            MATCH (from:Symbol)-[c:CALLS]->(to:Symbol {location_uri: $uri})
            RETURN from.location_uri, from.name, from.kind, c.line_number
            ORDER BY from.location_uri
        """, {"uri": location_uri})

        calling_this = []
        while callers_result.has_next():
            row = callers_result.get_next()
            calling_this.append({
                "location_uri": row[0],
                "name": row[1],
                "kind": row[2],
                "line_number": row[3]
            })

        return called_by_this, calling_this

    def execute_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[List[Any]]:
        """
        Execute a raw Cypher query.

        Args:
            query: Cypher query string
            params: Optional parameters for the query

        Returns:
            List of result rows
        """
        result = self.conn.execute(query, params or {})
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        return rows

    def get_statistics(self) -> Dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with symbol and relationship counts
        """
        # Count symbols
        symbol_count_result = self.conn.execute("MATCH (s:Symbol) RETURN COUNT(s)")
        symbol_count = symbol_count_result.get_next()[0] if symbol_count_result.has_next() else 0

        # Count relationships
        rel_count_result = self.conn.execute("MATCH ()-[c:CALLS]->() RETURN COUNT(c)")
        rel_count = rel_count_result.get_next()[0] if rel_count_result.has_next() else 0

        # Count by kind
        kind_counts = {}
        kind_result = self.conn.execute("""
            MATCH (s:Symbol)
            RETURN s.kind, COUNT(s)
            ORDER BY COUNT(s) DESC
        """)
        
        while kind_result.has_next():
            row = kind_result.get_next()
            kind_counts[row[0]] = row[1]

        return {
            "total_symbols": symbol_count,
            "total_relationships": rel_count,
            "symbols_by_kind": kind_counts
        }

    def close(self):
        """Close the database connection."""
        # KuzuDB handles connection cleanup automatically
        pass


def main():
    """Example usage of KuzuStorage."""
    # This is just for demonstration
    storage = KuzuStorage()
    
    # Create some example symbols
    symbols = [
        Symbol(
            name="hello_world",
            kind="function",
            location_uri="file:///home/user/main.py#L10"
        ),
        Symbol(
            name="greet",
            kind="function", 
            location_uri="file:///home/user/main.py#L20"
        )
    ]
    
    # Store symbols
    count = storage.store_symbols(symbols)
    print(f"Stored {count} symbols")
    
    # Create a relationship
    storage.create_calls_relationship(
        "file:///home/user/main.py#L10",
        "file:///home/user/main.py#L20",
        line_number=12
    )
    
    # Query example
    results = storage.execute_cypher(
        "MATCH (s:Symbol) WHERE s.location_uri CONTAINS 'main.py' RETURN s"
    )
    print(f"Found {len(results)} symbols in main.py")
    
    # Get statistics
    stats = storage.get_statistics()
    print(f"Database statistics: {stats}")


if __name__ == "__main__":
    main()