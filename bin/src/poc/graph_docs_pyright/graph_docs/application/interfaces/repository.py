"""Abstract repository interface for graph_docs."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, TypedDict, Optional
from pathlib import Path

from graph_docs.domain.entities import QueryResult, DualQueryResult


class ExportResult(TypedDict):
    """Result for export operations."""
    ok: bool
    files_path: str
    diagnostics_path: str


class ImportResult(TypedDict):
    """Result for import operations."""
    ok: bool
    files_count: int
    diagnostics_count: int


class ErrorResult(TypedDict):
    """Error result for operations."""
    ok: bool
    error: str


class FileInfo(TypedDict):
    """File information."""
    path: str
    errors: int
    warnings: int


class DiagnosticInfo(TypedDict):
    """Diagnostic information."""
    id: str
    severity: str
    message: str
    line: int
    col: int
    file_path: str


class GraphRepository(ABC):
    """Abstract repository interface for storing and querying analysis results."""
    
    @abstractmethod
    def store_file(self, file_info: FileInfo) -> None:
        """Store file analysis information.
        
        Args:
            file_info: Information about the analyzed file
        """
        pass
    
    @abstractmethod
    def store_diagnostic(self, diagnostic: DiagnosticInfo) -> None:
        """Store diagnostic information.
        
        Args:
            diagnostic: Diagnostic information (error/warning)
        """
        pass
    
    @abstractmethod
    def create_file_diagnostic_relationship(self, file_path: str, diagnostic_id: str) -> None:
        """Create relationship between file and diagnostic.
        
        Args:
            file_path: Path of the file
            diagnostic_id: ID of the diagnostic
        """
        pass
    
    @abstractmethod
    def query_files_with_errors(self) -> List[FileInfo]:
        """Query files that have errors.
        
        Returns:
            List of files with error counts
        """
        pass
    
    @abstractmethod
    def export_to_parquet(self, output_dir: str) -> Union[ExportResult, ErrorResult]:
        """Export data to Parquet files.
        
        Args:
            output_dir: Directory path to save the Parquet files
            
        Returns:
            Result of the export operation
        """
        pass
    
    @abstractmethod
    def import_from_parquet(self, input_dir: str) -> Union[ImportResult, ErrorResult]:
        """Import data from Parquet files.
        
        Args:
            input_dir: Directory path containing the Parquet files
            
        Returns:
            Result of the import operation
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close any open connections or resources."""
        pass


class IDualKuzuRepository(ABC):
    """Interface for dual KuzuDB operations."""
    
    def __init__(self):
        """Initialize repository with database paths."""
        self.db1_path: Optional[Path] = None
        self.db2_path: Optional[Path] = None
    
    @abstractmethod
    def connect(self) -> Dict[str, Any]:
        """Connect to both databases.
        
        Returns:
            Success or error result dictionary
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from both databases."""
        pass
    
    @abstractmethod
    def query_single(self, db_name: str, query: str) -> QueryResult:
        """Execute query on a single database.
        
        Args:
            db_name: "db1" or "db2"
            query: Cypher query to execute
            
        Returns:
            QueryResult object
        """
        pass
    
    @abstractmethod
    def query_both(self, query: str) -> DualQueryResult:
        """Execute same query on both databases.
        
        Args:
            query: Cypher query to execute
            
        Returns:
            DualQueryResult object
        """
        pass
    
    @abstractmethod
    def query_parallel(self, db1_query: str, db2_query: str) -> DualQueryResult:
        """Execute different queries on each database.
        
        Args:
            db1_query: Query for DB1
            db2_query: Query for DB2
            
        Returns:
            DualQueryResult object
        """
        pass
    
    @abstractmethod
    def init_local_db(self, local_path: str) -> Dict[str, Any]:
        """Initialize a local database.
        
        Args:
            local_path: Path for local database
            
        Returns:
            Success or error result dictionary
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def create_relations(self, relations_list: List[Dict[str, Any]]) -> QueryResult:
        """Create multiple relations in the local database.
        
        Args:
            relations_list: List of relation definitions
            
        Returns:
            QueryResult object
        """
        pass
    
    @abstractmethod
    def copy_from(self, target_name: str, table_name: str, csv_path: str) -> QueryResult:
        """Import CSV data into a table.
        
        Args:
            target_name: "db1", "db2", or "local"
            table_name: Target table name
            csv_path: Path to CSV file
            
        Returns:
            QueryResult object
        """
        pass