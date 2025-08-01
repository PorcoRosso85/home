"""Analyzer service - Application layer for graph and code analysis.

This service orchestrates the analysis of dual KuzuDB databases and 
optionally integrates with Pyright for code analysis.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

from graph_docs.domain.entities import QueryResult, DualQueryResult
from graph_docs.application.interfaces.repository import IDualKuzuRepository
from graph_docs.pyright_analyzer import PyrightAnalyzer


@dataclass
class AnalysisRequest:
    """Request object for analysis operations."""
    db1_path: str
    db2_path: str
    query: Optional[str] = None
    target_db: Optional[str] = None  # "db1", "db2", or None for both
    db1_query: Optional[str] = None  # For parallel queries
    db2_query: Optional[str] = None  # For parallel queries
    enable_pyright: bool = False
    workspace_path: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of an analysis operation."""
    ok: bool
    single_result: Optional[QueryResult] = None
    dual_result: Optional[DualQueryResult] = None
    error: Optional[str] = None


@dataclass
class DualDBAnalysisResult:
    """Result combining database query and Pyright analysis."""
    ok: bool
    query_result: AnalysisResult
    pyright_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalysisError(Exception):
    """Custom exception for analysis errors."""
    pass


class AnalyzerService:
    """Application service for analyzing graph databases and code."""
    
    def __init__(self, repository: IDualKuzuRepository):
        """Initialize the analyzer service.
        
        Args:
            repository: Repository interface for dual KuzuDB operations
        """
        self.repository = repository
    
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform analysis based on the request.
        
        Args:
            request: Analysis request containing query and target information
            
        Returns:
            AnalysisResult with query results or error information
        """
        if self.repository is None:
            return AnalysisResult(
                ok=False,
                error="Repository not initialized"
            )
        
        # Validate target_db
        if request.target_db and request.target_db not in ["db1", "db2"]:
            return AnalysisResult(
                ok=False,
                error=f"Invalid target_db: {request.target_db}. Must be 'db1', 'db2', or None"
            )
        
        # Set database paths
        self.repository.db1_path = Path(request.db1_path)
        self.repository.db2_path = Path(request.db2_path)
        
        # Connect to databases
        connect_result = self.repository.connect()
        if "error" in connect_result:
            return AnalysisResult(
                ok=False,
                error=f"{connect_result['error']}: {connect_result.get('details', '')}"
            )
        
        try:
            # Execute query based on target
            if request.target_db:
                # Single database query
                result = self.repository.query_single(request.target_db, request.query)
                return AnalysisResult(
                    ok=result.error is None,
                    single_result=result,
                    error=f"Query failed: {result.error}" if result.error else None
                )
            else:
                # Query both databases
                result = self.repository.query_both(request.query)
                has_error = (
                    (result.db1_result and result.db1_result.error) or
                    (result.db2_result and result.db2_result.error)
                )
                
                error_msg = None
                if has_error:
                    errors = []
                    if result.db1_result and result.db1_result.error:
                        errors.append(f"DB1: {result.db1_result.error}")
                    if result.db2_result and result.db2_result.error:
                        errors.append(f"DB2: {result.db2_result.error}")
                    error_msg = "Query failed - " + "; ".join(errors)
                
                return AnalysisResult(
                    ok=not has_error,
                    dual_result=result,
                    error=error_msg
                )
        finally:
            # Always disconnect
            self.repository.disconnect()
    
    def analyze_parallel(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform parallel analysis with different queries for each database.
        
        Args:
            request: Analysis request containing separate queries for each database
            
        Returns:
            AnalysisResult with dual query results
        """
        if self.repository is None:
            return AnalysisResult(
                ok=False,
                error="Repository not initialized"
            )
        
        # Validate parallel queries
        if not request.db1_query or not request.db2_query:
            return AnalysisResult(
                ok=False,
                error="Both db1_query and db2_query must be provided for parallel analysis"
            )
        
        # Set database paths
        self.repository.db1_path = Path(request.db1_path)
        self.repository.db2_path = Path(request.db2_path)
        
        # Connect to databases
        connect_result = self.repository.connect()
        if "error" in connect_result:
            return AnalysisResult(
                ok=False,
                error=f"{connect_result['error']}: {connect_result.get('details', '')}"
            )
        
        try:
            # Execute parallel queries
            result = self.repository.query_parallel(request.db1_query, request.db2_query)
            
            has_error = (
                (result.db1_result and result.db1_result.error) or
                (result.db2_result and result.db2_result.error)
            )
            
            error_msg = None
            if has_error:
                errors = []
                if result.db1_result and result.db1_result.error:
                    errors.append(f"DB1: {result.db1_result.error}")
                if result.db2_result and result.db2_result.error:
                    errors.append(f"DB2: {result.db2_result.error}")
                error_msg = "Parallel query failed - " + "; ".join(errors)
            
            return AnalysisResult(
                ok=not has_error,
                dual_result=result,
                error=error_msg
            )
        finally:
            # Always disconnect
            self.repository.disconnect()
    
    def analyze_with_pyright(self, request: AnalysisRequest) -> DualDBAnalysisResult:
        """Perform analysis with optional Pyright code analysis.
        
        Args:
            request: Analysis request with Pyright configuration
            
        Returns:
            Combined result with database query and Pyright analysis
        """
        # First perform database analysis
        query_result = self.analyze(request)
        
        # If Pyright is not enabled or workspace not provided, return query result only
        if not request.enable_pyright or not request.workspace_path:
            return DualDBAnalysisResult(
                ok=query_result.ok,
                query_result=query_result,
                pyright_result=None,
                error=query_result.error
            )
        
        # Perform Pyright analysis
        try:
            analyzer = PyrightAnalyzer(request.workspace_path)
            pyright_result = analyzer.analyze()
            
            # Check if Pyright analysis failed
            if not pyright_result.get("ok", False):
                error_msg = query_result.error or ""
                if error_msg:
                    error_msg += "; "
                error_msg += f"Pyright analysis failed: {pyright_result.get('error', 'Unknown error')}"
                
                return DualDBAnalysisResult(
                    ok=False,
                    query_result=query_result,
                    pyright_result=pyright_result,
                    error=error_msg
                )
            
            return DualDBAnalysisResult(
                ok=query_result.ok and pyright_result.get("ok", False),
                query_result=query_result,
                pyright_result=pyright_result,
                error=query_result.error
            )
            
        except Exception as e:
            error_msg = query_result.error or ""
            if error_msg:
                error_msg += "; "
            error_msg += f"Pyright analysis error: {str(e)}"
            
            return DualDBAnalysisResult(
                ok=False,
                query_result=query_result,
                pyright_result=None,
                error=error_msg
            )
    
    def get_database_info(self, db1_path: str, db2_path: str) -> Dict[str, Any]:
        """Get information about both databases.
        
        Args:
            db1_path: Path to first database
            db2_path: Path to second database
            
        Returns:
            Dictionary with database information
        """
        if self.repository is None:
            return {
                "ok": False,
                "error": "Repository not initialized"
            }
        
        # Set database paths
        self.repository.db1_path = Path(db1_path)
        self.repository.db2_path = Path(db2_path)
        
        # Connect to databases
        connect_result = self.repository.connect()
        if "error" in connect_result:
            return {
                "ok": False,
                "error": f"{connect_result['error']}: {connect_result.get('details', '')}"
            }
        
        try:
            # Get table information from both databases
            db1_tables = self.repository.query_single("db1", "CALL show_tables() RETURN *;")
            db2_tables = self.repository.query_single("db2", "CALL show_tables() RETURN *;")
            
            return {
                "ok": True,
                "db1_tables": db1_tables,
                "db2_tables": db2_tables,
                "db1_path": db1_path,
                "db2_path": db2_path
            }
        except Exception as e:
            return {
                "ok": False,
                "error": f"Failed to get database info: {str(e)}"
            }
        finally:
            self.repository.disconnect()
    
    def create_local_database(self, local_path: str) -> Dict[str, Any]:
        """Create and initialize a local database.
        
        Args:
            local_path: Path for the local database
            
        Returns:
            Dictionary with operation result
        """
        if self.repository is None:
            return {
                "ok": False,
                "error": "Repository not initialized"
            }
        
        result = self.repository.init_local_db(local_path)
        
        if "error" in result:
            return {
                "ok": False,
                "error": result["error"],
                "details": result.get("details")
            }
        
        return {
            "ok": True,
            "message": result.get("message", "Local database initialized")
        }
    
    def create_relations(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create relations in the local database.
        
        Args:
            relations: List of relation definitions
            
        Returns:
            Dictionary with operation result
        """
        if self.repository is None:
            return {
                "ok": False,
                "error": "Repository not initialized"
            }
        
        result = self.repository.create_relations(relations)
        
        if result.error:
            return {
                "ok": False,
                "error": result.error,
                "result": result
            }
        
        return {
            "ok": True,
            "result": result
        }
    
    def import_csv_data(self, target: str, table_name: str, csv_path: str) -> Dict[str, Any]:
        """Import CSV data into a database table.
        
        Args:
            target: Target database ("db1", "db2", or "local")
            table_name: Name of the table to import into
            csv_path: Path to the CSV file
            
        Returns:
            Dictionary with operation result
        """
        if self.repository is None:
            return {
                "ok": False,
                "error": "Repository not initialized"
            }
        
        result = self.repository.copy_from(target, table_name, csv_path)
        
        if result.error:
            return {
                "ok": False,
                "error": result.error,
                "result": result
            }
        
        return {
            "ok": True,
            "result": result
        }