"""KuzuDB storage for Pyright analysis results.

This module provides a compatibility layer that uses the repository pattern.
"""

from typing import Dict, Any, List, Union

from graph_docs.infrastructure.kuzu.kuzu_repository import KuzuRepository
from graph_docs.application.interfaces.repository import (
    GraphRepository,
    FileInfo,
    DiagnosticInfo,
    ExportResult,
    ImportResult,
    ErrorResult
)


# Re-export types for backward compatibility
ExportSuccess = ExportResult
ImportSuccess = ImportResult


class KuzuStorage:
    """Store Pyright analysis results in KuzuDB.
    
    This class provides backward compatibility while using the repository pattern internally.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self._repository: GraphRepository = KuzuRepository(db_path)
        
    def store_analysis(self, results: Dict[str, Any]):
        """Store Pyright analysis results."""
        # Process each file
        for file_info in results.get("files", []):
            file_data: FileInfo = {
                "path": file_info["path"],
                "errors": file_info["errors"],
                "warnings": file_info["warnings"]
            }
            self._repository.store_file(file_data)
            
        # Process diagnostics
        for i, diag in enumerate(results.get("diagnostics", [])):
            diag_id = f"{diag['file']}:{diag['range']['start']['line']}:{i}"
            
            # Insert diagnostic
            diagnostic_data: DiagnosticInfo = {
                "id": diag_id,
                "severity": diag.get("severity", "error"),
                "message": diag.get("message", ""),
                "line": diag["range"]["start"]["line"],
                "col": diag["range"]["start"]["character"],
                "file_path": diag["file"]
            }
            self._repository.store_diagnostic(diagnostic_data)
            
            # Create relationship
            self._repository.create_file_diagnostic_relationship(diag["file"], diag_id)
            
    def query_files_with_errors(self) -> List[Dict[str, Any]]:
        """Query files that have errors."""
        file_infos = self._repository.query_files_with_errors()
        # Convert FileInfo objects to the expected format
        return [{"path": f["path"], "errors": f["errors"]} for f in file_infos]
    
    def export_to_parquet(self, output_dir: str) -> Union[ExportSuccess, ErrorResult]:
        """Export File and Diagnostic tables to Parquet files.
        
        Args:
            output_dir: Directory path to save the Parquet files
            
        Returns:
            Union[ExportSuccess, ErrorResult]: Result of the export operation
        """
        return self._repository.export_to_parquet(output_dir)
    
    def import_from_parquet(self, input_dir: str) -> Union[ImportSuccess, ErrorResult]:
        """Import File and Diagnostic tables from Parquet files.
        
        Args:
            input_dir: Directory path containing the Parquet files (files.parquet and diagnostics.parquet)
            
        Returns:
            Union[ImportSuccess, ErrorResult]: Result of the import operation
        """
        return self._repository.import_from_parquet(input_dir)