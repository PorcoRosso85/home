"""KuzuDB implementation of GraphRepository."""

import kuzu
from pathlib import Path
from typing import List, Union
from datetime import datetime

from graph_docs.application.interfaces.repository import (
    GraphRepository,
    FileInfo,
    DiagnosticInfo,
    ExportResult,
    ImportResult,
    ErrorResult
)


class KuzuRepository(GraphRepository):
    """KuzuDB implementation of the GraphRepository interface."""
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize KuzuDB repository.
        
        Args:
            db_path: Path to the database file, or ":memory:" for in-memory database
        """
        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._create_schema()
    
    def _create_schema(self):
        """Create KuzuDB schema for storing analysis results."""
        # File node - represents analyzed Python files
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS File(
                path STRING PRIMARY KEY,
                errors INT64,
                warnings INT64,
                analyzed_at TIMESTAMP
            )
        """)
        
        # Diagnostic node - represents errors/warnings
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Diagnostic(
                id STRING PRIMARY KEY,
                severity STRING,
                message STRING,
                line INT64,
                col INT64
            )
        """)
        
        # Relationship: File has diagnostics
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_DIAGNOSTIC(
                FROM File TO Diagnostic
            )
        """)
    
    def store_file(self, file_info: FileInfo) -> None:
        """Store file analysis information.
        
        Args:
            file_info: Information about the analyzed file
        """
        # Get current timestamp
        current_time = datetime.now().isoformat()
        
        self.conn.execute("""
            CREATE (f:File {
                path: $path,
                errors: $errors,
                warnings: $warnings,
                analyzed_at: timestamp($analyzed_at)
            })
        """, {
            "path": file_info["path"],
            "errors": file_info["errors"],
            "warnings": file_info["warnings"],
            "analyzed_at": current_time
        })
    
    def store_diagnostic(self, diagnostic: DiagnosticInfo) -> None:
        """Store diagnostic information.
        
        Args:
            diagnostic: Diagnostic information (error/warning)
        """
        self.conn.execute("""
            CREATE (d:Diagnostic {
                id: $id,
                severity: $severity,
                message: $message,
                line: $line,
                col: $col
            })
        """, {
            "id": diagnostic["id"],
            "severity": diagnostic["severity"],
            "message": diagnostic["message"],
            "line": diagnostic["line"],
            "col": diagnostic["col"]
        })
    
    def create_file_diagnostic_relationship(self, file_path: str, diagnostic_id: str) -> None:
        """Create relationship between file and diagnostic.
        
        Args:
            file_path: Path of the file
            diagnostic_id: ID of the diagnostic
        """
        self.conn.execute("""
            MATCH (f:File {path: $file_path})
            MATCH (d:Diagnostic {id: $diagnostic_id})
            CREATE (f)-[:HAS_DIAGNOSTIC]->(d)
        """, {
            "file_path": file_path,
            "diagnostic_id": diagnostic_id
        })
    
    def query_files_with_errors(self) -> List[FileInfo]:
        """Query files that have errors.
        
        Returns:
            List of files with error counts
        """
        result = self.conn.execute("""
            MATCH (f:File)
            WHERE f.errors > 0
            RETURN f.path as path, f.errors as errors, f.warnings as warnings
            ORDER BY f.errors DESC
        """)
        
        files = []
        while result.has_next():
            row = result.get_next()
            files.append({
                "path": row[0],
                "errors": row[1],
                "warnings": row[2]
            })
        return files
    
    def export_to_parquet(self, output_dir: str) -> Union[ExportResult, ErrorResult]:
        """Export data to Parquet files.
        
        Args:
            output_dir: Directory path to save the Parquet files
            
        Returns:
            Result of the export operation
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Export File table to Parquet
            files_output = output_path / "files.parquet"
            self.conn.execute(f"""
                COPY (MATCH (f:File) RETURN f.*) TO '{files_output}'
            """)
            
            # Export Diagnostic table to Parquet
            diagnostics_output = output_path / "diagnostics.parquet"
            self.conn.execute(f"""
                COPY (MATCH (d:Diagnostic) RETURN d.*) TO '{diagnostics_output}'
            """)
            
            return ExportResult(
                ok=True,
                files_path=str(files_output),
                diagnostics_path=str(diagnostics_output)
            )
        except Exception as e:
            return ErrorResult(
                ok=False,
                error=str(e)
            )
    
    def import_from_parquet(self, input_dir: str) -> Union[ImportResult, ErrorResult]:
        """Import data from Parquet files.
        
        Args:
            input_dir: Directory path containing the Parquet files
            
        Returns:
            Result of the import operation
        """
        try:
            # Validate input directory
            input_path = Path(input_dir)
            if not input_path.exists():
                return ErrorResult(
                    ok=False,
                    error=f"Input directory does not exist: {input_dir}"
                )
            
            # Check for required Parquet files
            files_parquet = input_path / "files.parquet"
            diagnostics_parquet = input_path / "diagnostics.parquet"
            
            if not files_parquet.exists():
                return ErrorResult(
                    ok=False,
                    error=f"files.parquet not found in {input_dir}"
                )
            if not diagnostics_parquet.exists():
                return ErrorResult(
                    ok=False,
                    error=f"diagnostics.parquet not found in {input_dir}"
                )
            
            # Import File table from Parquet
            self.conn.execute(f"""
                COPY File FROM '{files_parquet}'
            """)
            
            # Import Diagnostic table from Parquet
            self.conn.execute(f"""
                COPY Diagnostic FROM '{diagnostics_parquet}'
            """)
            
            # Get counts for the success result
            file_count_result = self.conn.execute("MATCH (f:File) RETURN COUNT(f) as count")
            file_count = file_count_result.get_next()[0] if file_count_result.has_next() else 0
            
            diag_count_result = self.conn.execute("MATCH (d:Diagnostic) RETURN COUNT(d) as count")
            diag_count = diag_count_result.get_next()[0] if diag_count_result.has_next() else 0
            
            return ImportResult(
                ok=True,
                files_count=file_count,
                diagnostics_count=diag_count
            )
        except Exception as e:
            return ErrorResult(
                ok=False,
                error=str(e)
            )
    
    def close(self) -> None:
        """Close any open connections or resources."""
        # KuzuDB connections are automatically closed when the object is destroyed
        # This method is here to satisfy the interface
        pass