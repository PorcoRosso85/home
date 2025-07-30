#!/usr/bin/env python3
"""
Cypher query collection for code analysis using KuzuDB.

This module provides a collection of useful Cypher queries for analyzing
code structure and relationships stored in KuzuDB.
"""

from typing import List, Dict, Any, Optional
from kuzu_storage import KuzuStorage


class CodeAnalyzer:
    """Code analysis queries for symbols stored in KuzuDB."""

    def __init__(self, storage: KuzuStorage):
        """
        Initialize code analyzer with a KuzuDB storage instance.

        Args:
            storage: KuzuStorage instance with symbols and relationships
        """
        self.storage = storage

    def find_all_functions_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Find all functions in a specific file.

        Args:
            file_path: Path to the file (absolute or relative)

        Returns:
            List of function symbols with their properties
        """
        import os
        abs_path = os.path.abspath(file_path)
        file_uri_pattern = f"file://{abs_path}#"
        
        query = """
        MATCH (s:Symbol)
        WHERE s.location_uri STARTS WITH $pattern
          AND s.kind = 'function'
        RETURN s.name AS function_name,
               s.location_uri AS location,
               s.signature AS signature,
               s.scope AS scope
        ORDER BY s.location_uri
        """
        
        results = self.storage.execute_cypher(query, {"pattern": file_uri_pattern})
        return [
            {
                "function_name": row[0],
                "location": row[1],
                "signature": row[2],
                "scope": row[3]
            }
            for row in results
        ]

    def find_most_called_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find the most frequently called functions in the codebase.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of functions with their call counts
        """
        query = """
        MATCH (s:Symbol)<-[c:CALLS]-()
        WHERE s.kind = 'function'
        WITH s, COUNT(c) AS call_count
        RETURN s.name AS function_name,
               s.location_uri AS location,
               call_count
        ORDER BY call_count DESC
        LIMIT $limit
        """
        
        results = self.storage.execute_cypher(query, {"limit": limit})
        return [
            {
                "function_name": row[0],
                "location": row[1],
                "call_count": row[2]
            }
            for row in results
        ]

    def find_dead_code(self) -> List[Dict[str, Any]]:
        """
        Find functions with no callers (potential dead code).

        Note: This may include entry points (like main()) and test functions.

        Returns:
            List of functions that are never called
        """
        query = """
        MATCH (s:Symbol)
        WHERE s.kind = 'function'
          AND NOT EXISTS {
              MATCH (s)<-[:CALLS]-()
          }
          AND s.name != 'main'
          AND NOT s.name STARTS WITH 'test_'
        RETURN s.name AS function_name,
               s.location_uri AS location,
               s.scope AS scope
        ORDER BY s.location_uri
        """
        
        results = self.storage.execute_cypher(query)
        return [
            {
                "function_name": row[0],
                "location": row[1],
                "scope": row[2]
            }
            for row in results
        ]

    def find_circular_dependencies(self, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Find circular dependencies (functions that call each other in a cycle).

        Args:
            max_depth: Maximum cycle length to detect

        Returns:
            List of circular dependency cycles
        """
        cycles = []
        
        # Check for cycles of different lengths
        for depth in range(2, min(max_depth + 1, 6)):
            if depth == 2:
                # Direct mutual recursion
                query = """
                MATCH (a:Symbol)-[:CALLS]->(b:Symbol)-[:CALLS]->(a)
                WHERE a.kind = 'function' AND b.kind = 'function'
                  AND a.location_uri < b.location_uri
                RETURN a.name AS func1, b.name AS func2,
                       a.location_uri AS loc1, b.location_uri AS loc2
                """
                results = self.storage.execute_cypher(query)
                for row in results:
                    cycles.append({
                        "cycle_length": 2,
                        "functions": [row[0], row[1]],
                        "locations": [row[2], row[3]]
                    })
            
            elif depth == 3:
                # Three-way cycle
                query = """
                MATCH (a:Symbol)-[:CALLS]->(b:Symbol)-[:CALLS]->(c:Symbol)-[:CALLS]->(a)
                WHERE a.kind = 'function' AND b.kind = 'function' AND c.kind = 'function'
                  AND a.location_uri < b.location_uri
                  AND a.location_uri < c.location_uri
                RETURN a.name AS func1, b.name AS func2, c.name AS func3,
                       a.location_uri AS loc1, b.location_uri AS loc2, c.location_uri AS loc3
                """
                results = self.storage.execute_cypher(query)
                for row in results:
                    cycles.append({
                        "cycle_length": 3,
                        "functions": [row[0], row[1], row[2]],
                        "locations": [row[3], row[4], row[5]]
                    })
        
        return cycles

    def get_function_call_hierarchy(self, function_name: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get the call hierarchy for a specific function (both callers and callees).

        Args:
            function_name: Name of the function to analyze
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary with 'callers' and 'callees' hierarchies
        """
        # Find the function
        symbols = self.storage.find_symbols_by_name(function_name)
        if not symbols:
            return {"error": f"Function '{function_name}' not found"}
        
        # Use the first matching function
        function_uri = symbols[0]["location_uri"]
        
        # Get direct callers
        query_callers = """
        MATCH (caller:Symbol)-[:CALLS]->(target:Symbol {location_uri: $uri})
        RETURN caller.name AS name, caller.location_uri AS location
        """
        
        callers_results = self.storage.execute_cypher(
            query_callers, {"uri": function_uri}
        )
        callers = [
            {"name": row[0], "location": row[1]}
            for row in callers_results
        ]
        
        # Get direct callees
        query_callees = """
        MATCH (target:Symbol {location_uri: $uri})-[:CALLS]->(callee:Symbol)
        RETURN callee.name AS name, callee.location_uri AS location
        """
        
        callees_results = self.storage.execute_cypher(
            query_callees, {"uri": function_uri}
        )
        callees = [
            {"name": row[0], "location": row[1]}
            for row in callees_results
        ]
        
        return {
            "function": {
                "name": function_name,
                "location": function_uri
            },
            "callers": callers,
            "callees": callees
        }

    def find_entry_points(self) -> List[Dict[str, Any]]:
        """
        Find potential entry points (functions that are never called).

        This includes main functions, test functions, and other top-level functions.

        Returns:
            List of potential entry point functions
        """
        query = """
        MATCH (s:Symbol)
        WHERE s.kind = 'function'
          AND NOT EXISTS {
              MATCH (s)<-[:CALLS]-()
          }
        RETURN s.name AS function_name,
               s.location_uri AS location,
               CASE
                   WHEN s.name = 'main' THEN 'main'
                   WHEN s.name STARTS WITH 'test_' THEN 'test'
                   WHEN s.name STARTS WITH '_' THEN 'private'
                   ELSE 'public'
               END AS entry_type
        ORDER BY entry_type, s.name
        """
        
        results = self.storage.execute_cypher(query)
        return [
            {
                "function_name": row[0],
                "location": row[1],
                "entry_type": row[2]
            }
            for row in results
        ]

    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Get dependencies between files based on function calls.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary with files this file depends on and files that depend on it
        """
        import os
        abs_path = os.path.abspath(file_path)
        file_uri_pattern = f"file://{abs_path}#"
        
        # Files this file depends on (calls functions from)
        query_deps_on = """
        MATCH (from:Symbol)-[:CALLS]->(to:Symbol)
        WHERE from.location_uri STARTS WITH $pattern
          AND NOT to.location_uri STARTS WITH $pattern
        WITH DISTINCT SUBSTRING(to.location_uri, 7, INDEXOF(to.location_uri, '#') - 7) AS dep_file
        RETURN dep_file
        ORDER BY dep_file
        """
        
        deps_on_results = self.storage.execute_cypher(
            query_deps_on, {"pattern": file_uri_pattern}
        )
        depends_on = [row[0] for row in deps_on_results]
        
        # Files that depend on this file (call functions from this file)
        query_dep_by = """
        MATCH (from:Symbol)-[:CALLS]->(to:Symbol)
        WHERE to.location_uri STARTS WITH $pattern
          AND NOT from.location_uri STARTS WITH $pattern
        WITH DISTINCT SUBSTRING(from.location_uri, 7, INDEXOF(from.location_uri, '#') - 7) AS dep_file
        RETURN dep_file
        ORDER BY dep_file
        """
        
        dep_by_results = self.storage.execute_cypher(
            query_dep_by, {"pattern": file_uri_pattern}
        )
        depended_by = [row[0] for row in dep_by_results]
        
        return {
            "file": abs_path,
            "depends_on": depends_on,
            "depended_by": depended_by
        }

    def get_complexity_metrics(self) -> Dict[str, Any]:
        """
        Get complexity metrics for the codebase.

        Returns:
            Dictionary with various complexity metrics
        """
        # Get basic statistics
        stats = self.storage.get_statistics()
        
        # Functions with most outgoing calls (high coupling)
        query_high_coupling = """
        MATCH (s:Symbol)-[c:CALLS]->()
        WHERE s.kind = 'function'
        WITH s, COUNT(c) AS out_calls
        RETURN s.name AS function_name, out_calls
        ORDER BY out_calls DESC
        LIMIT 10
        """
        
        high_coupling_results = self.storage.execute_cypher(query_high_coupling)
        high_coupling = [
            {"function": row[0], "outgoing_calls": row[1]}
            for row in high_coupling_results
        ]
        
        # Average calls per function
        query_avg_calls = """
        MATCH (s:Symbol)
        WHERE s.kind = 'function'
        OPTIONAL MATCH (s)-[c:CALLS]->()
        WITH s, COUNT(c) AS out_calls
        RETURN AVG(out_calls) AS avg_outgoing_calls
        """
        
        avg_results = self.storage.execute_cypher(query_avg_calls)
        avg_calls = avg_results[0][0] if avg_results else 0
        
        return {
            "total_symbols": stats["total_symbols"],
            "total_relationships": stats["total_relationships"],
            "symbols_by_kind": stats["symbols_by_kind"],
            "functions_with_highest_coupling": high_coupling,
            "average_outgoing_calls_per_function": round(avg_calls, 2)
        }


def main():
    """Example usage of analysis queries."""
    # This would be used with an actual KuzuStorage instance
    print("Import this module and use with a KuzuStorage instance:")
    print("  from analysis_queries import CodeAnalyzer")
    print("  analyzer = CodeAnalyzer(storage)")
    print("  dead_code = analyzer.find_dead_code()")


if __name__ == "__main__":
    main()