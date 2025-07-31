"""KuzuDB storage for Pyright analysis results."""

import kuzu
from pathlib import Path
from typing import Dict, Any, List
import os


class KuzuStorage:
    """Store Pyright analysis results in KuzuDB."""
    
    def __init__(self, db_path: str = ":memory:"):
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
                column INT64
            )
        """)
        
        # Relationship: File has diagnostics
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_DIAGNOSTIC(
                FROM File TO Diagnostic
            )
        """)
        
    def store_analysis(self, results: Dict[str, Any]):
        """Store Pyright analysis results."""
        # Process each file
        for file_info in results.get("files", []):
            file_path = file_info["path"]
            
            # Insert file
            self.conn.execute("""
                CREATE (f:File {
                    path: $path,
                    errors: $errors,
                    warnings: $warnings,
                    analyzed_at: timestamp()
                })
            """, {
                "path": file_path,
                "errors": file_info["errors"],
                "warnings": file_info["warnings"]
            })
            
        # Process diagnostics
        for i, diag in enumerate(results.get("diagnostics", [])):
            diag_id = f"{diag['file']}:{diag['range']['start']['line']}:{i}"
            
            # Insert diagnostic
            self.conn.execute("""
                CREATE (d:Diagnostic {
                    id: $id,
                    severity: $severity,
                    message: $message,
                    line: $line,
                    column: $column
                })
            """, {
                "id": diag_id,
                "severity": diag.get("severity", "error"),
                "message": diag.get("message", ""),
                "line": diag["range"]["start"]["line"],
                "column": diag["range"]["start"]["character"]
            })
            
            # Create relationship
            self.conn.execute("""
                MATCH (f:File {path: $file_path})
                MATCH (d:Diagnostic {id: $diag_id})
                CREATE (f)-[:HAS_DIAGNOSTIC]->(d)
            """, {
                "file_path": diag["file"],
                "diag_id": diag_id
            })
            
    def query_files_with_errors(self) -> List[Dict[str, Any]]:
        """Query files that have errors."""
        result = self.conn.execute("""
            MATCH (f:File)
            WHERE f.errors > 0
            RETURN f.path as path, f.errors as errors
            ORDER BY f.errors DESC
        """)
        
        files = []
        while result.has_next():
            files.append(result.get_next())
        return files
    
    def export_to_parquet(self, output_dir: str):
        """Export File and Diagnostic tables to Parquet files.
        
        Args:
            output_dir: Directory path to save the Parquet files
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export File table to Parquet
        files_output = output_path / "files.parquet"
        self.conn.execute(f"""
            COPY (MATCH (f:File) RETURN f.*) TO '{files_output}' (FORMAT PARQUET)
        """)
        
        # Export Diagnostic table to Parquet
        diagnostics_output = output_path / "diagnostics.parquet"
        self.conn.execute(f"""
            COPY (MATCH (d:Diagnostic) RETURN d.*) TO '{diagnostics_output}' (FORMAT PARQUET)
        """)
        
        print(f"Exported File table to: {files_output}")
        print(f"Exported Diagnostic table to: {diagnostics_output}")
    
    def import_from_parquet(self, input_dir: str):
        """Import File and Diagnostic tables from Parquet files.
        
        Args:
            input_dir: Directory path containing the Parquet files (files.parquet and diagnostics.parquet)
        """
        # Validate input directory
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        # Check for required Parquet files
        files_parquet = input_path / "files.parquet"
        diagnostics_parquet = input_path / "diagnostics.parquet"
        
        if not files_parquet.exists():
            raise FileNotFoundError(f"files.parquet not found in {input_dir}")
        if not diagnostics_parquet.exists():
            raise FileNotFoundError(f"diagnostics.parquet not found in {input_dir}")
        
        # Import File table from Parquet
        self.conn.execute(f"""
            COPY File FROM '{files_parquet}' (FORMAT PARQUET)
        """)
        
        # Import Diagnostic table from Parquet
        self.conn.execute(f"""
            COPY Diagnostic FROM '{diagnostics_parquet}' (FORMAT PARQUET)
        """)
        
        print(f"Imported File table from: {files_parquet}")
        print(f"Imported Diagnostic table from: {diagnostics_parquet}")