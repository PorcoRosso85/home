"""KuzuDB storage for Pyright analysis results."""

import kuzu
from pathlib import Path
from typing import Dict, Any, List


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