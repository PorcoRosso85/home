"""Dual KuzuDB repository implementation.

This module provides the infrastructure implementation of the IDualKuzuRepository
interface, wrapping the DualKuzuDB functionality.
"""

from typing import Dict, Any, List, Optional

from graph_docs.application.interfaces.repository import IDualKuzuRepository
from graph_docs.domain.entities import QueryResult, DualQueryResult
from graph_docs.mod import DualKuzuDB


class DualKuzuRepository(IDualKuzuRepository):
    """Repository implementation for dual KuzuDB operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__()
        self._dual_db: Optional[DualKuzuDB] = None
    
    def connect(self) -> Dict[str, Any]:
        """Connect to both databases.
        
        Returns:
            Success or error result dictionary
        """
        if not self.db1_path or not self.db2_path:
            return {
                "error": "Database paths not set",
                "details": "Call set_database_paths() before connecting"
            }
        
        # Create DualKuzuDB instance
        self._dual_db = DualKuzuDB(self.db1_path, self.db2_path)
        
        # Connect to databases
        result = self._dual_db.connect()
        return result
    
    def disconnect(self) -> None:
        """Disconnect from both databases."""
        if self._dual_db:
            self._dual_db.disconnect()
            self._dual_db = None
    
    def query_single(self, db_name: str, query: str) -> QueryResult:
        """Execute query on a single database.
        
        Args:
            db_name: "db1" or "db2"
            query: Cypher query to execute
            
        Returns:
            QueryResult object
        """
        if not self._dual_db:
            return QueryResult(
                source=db_name,
                columns=[],
                rows=[],
                error="Not connected to databases"
            )
        
        return self._dual_db.query_single(db_name, query)
    
    def query_both(self, query: str) -> DualQueryResult:
        """Execute same query on both databases.
        
        Args:
            query: Cypher query to execute
            
        Returns:
            DualQueryResult object
        """
        if not self._dual_db:
            return DualQueryResult(
                db1_result=QueryResult(
                    source="db1",
                    columns=[],
                    rows=[],
                    error="Not connected to databases"
                ),
                db2_result=QueryResult(
                    source="db2",
                    columns=[],
                    rows=[],
                    error="Not connected to databases"
                )
            )
        
        return self._dual_db.query_both(query)
    
    def query_parallel(self, db1_query: str, db2_query: str) -> DualQueryResult:
        """Execute different queries on each database.
        
        Args:
            db1_query: Query for DB1
            db2_query: Query for DB2
            
        Returns:
            DualQueryResult object
        """
        if not self._dual_db:
            return DualQueryResult(
                db1_result=QueryResult(
                    source="db1",
                    columns=[],
                    rows=[],
                    error="Not connected to databases"
                ),
                db2_result=QueryResult(
                    source="db2",
                    columns=[],
                    rows=[],
                    error="Not connected to databases"
                )
            )
        
        return self._dual_db.query_parallel(db1_query, db2_query)
    
    def init_local_db(self, local_path: str) -> Dict[str, Any]:
        """Initialize a local database.
        
        Args:
            local_path: Path for local database
            
        Returns:
            Success or error result dictionary
        """
        if not self._dual_db:
            # Create DualKuzuDB instance if not already created
            if not self.db1_path or not self.db2_path:
                # Use dummy paths if not set, as we only need local DB
                self._dual_db = DualKuzuDB(":memory:", ":memory:", local_path)
            else:
                self._dual_db = DualKuzuDB(self.db1_path, self.db2_path, local_path)
        
        result = self._dual_db.init_local_db(local_path)
        return result
    
    def create_relation(self, from_id: Any, from_type: str, to_id: Any, 
                       to_type: str, rel_type: str = "OWNS") -> QueryResult:
        """Create a relation in the local database.
        
        Args:
            from_id: Source node ID
            from_type: Source node type
            to_id: Target node ID
            to_type: Target node type
            rel_type: Relation type
            
        Returns:
            QueryResult object
        """
        if not self._dual_db:
            return QueryResult(
                source="local",
                columns=[],
                rows=[],
                error="DualKuzuDB not initialized"
            )
        
        return self._dual_db.create_relation(from_id, from_type, to_id, to_type, rel_type)
    
    def create_relations(self, relations_list: List[Dict[str, Any]]) -> QueryResult:
        """Create multiple relations in the local database.
        
        Args:
            relations_list: List of relation definitions
            
        Returns:
            QueryResult object
        """
        if not self._dual_db:
            return QueryResult(
                source="local",
                columns=[],
                rows=[],
                error="DualKuzuDB not initialized"
            )
        
        return self._dual_db.create_relations(relations_list)
    
    def copy_from(self, target_name: str, table_name: str, csv_path: str) -> QueryResult:
        """Import CSV data into a table.
        
        Args:
            target_name: "db1", "db2", or "local"
            table_name: Target table name
            csv_path: Path to CSV file
            
        Returns:
            QueryResult object
        """
        if not self._dual_db:
            return QueryResult(
                source=target_name,
                columns=[],
                rows=[],
                error="DualKuzuDB not initialized"
            )
        
        return self._dual_db.copy_from(target_name, table_name, csv_path)