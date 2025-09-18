"""Tests for KuzuRepository implementation."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List

from graph_docs.application.interfaces.repository import (
    GraphRepository,
    FileInfo,
    DiagnosticInfo,
    ExportResult,
    ImportResult,
    ErrorResult
)
from graph_docs.infrastructure.kuzu.kuzu_repository import KuzuRepository


class TestKuzuRepository:
    """Test suite for KuzuRepository."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Provide a temporary database path."""
        temp_dir = tempfile.mkdtemp()
        yield f"{temp_dir}/test.db"
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_db_path):
        """Create a KuzuRepository instance."""
        repo = KuzuRepository(temp_db_path)
        yield repo
        repo.close()
    
    def test_implements_graph_repository_interface(self):
        """Test that KuzuRepository implements GraphRepository interface."""
        assert issubclass(KuzuRepository, GraphRepository)
    
    def test_can_create_in_memory_repository(self):
        """Test creating an in-memory repository."""
        repo = KuzuRepository(":memory:")
        assert repo is not None
        repo.close()
    
    def test_can_create_file_repository(self, temp_db_path):
        """Test creating a file-based repository."""
        repo = KuzuRepository(temp_db_path)
        assert repo is not None
        repo.close()
        assert Path(temp_db_path).exists()
    
    def test_store_file_info(self, repository: GraphRepository):
        """Test storing file information."""
        file_info: FileInfo = {
            "path": "/test/file.py",
            "errors": 2,
            "warnings": 1
        }
        
        # Should not raise any exception
        repository.store_file(file_info)
    
    def test_store_diagnostic_info(self, repository: GraphRepository):
        """Test storing diagnostic information."""
        diagnostic: DiagnosticInfo = {
            "id": "test_diag_1",
            "severity": "error",
            "message": "Test error message",
            "line": 10,
            "col": 5,
            "file_path": "/test/file.py"
        }
        
        # Should not raise any exception
        repository.store_diagnostic(diagnostic)
    
    def test_create_file_diagnostic_relationship(self, repository: GraphRepository):
        """Test creating relationship between file and diagnostic."""
        # First store file and diagnostic
        file_info: FileInfo = {
            "path": "/test/file.py",
            "errors": 1,
            "warnings": 0
        }
        repository.store_file(file_info)
        
        diagnostic: DiagnosticInfo = {
            "id": "test_diag_1",
            "severity": "error",
            "message": "Test error",
            "line": 10,
            "col": 5,
            "file_path": "/test/file.py"
        }
        repository.store_diagnostic(diagnostic)
        
        # Create relationship
        repository.create_file_diagnostic_relationship("/test/file.py", "test_diag_1")
    
    def test_query_files_with_errors(self, repository: GraphRepository):
        """Test querying files with errors."""
        # Store files with different error counts
        files = [
            {"path": "/test/file1.py", "errors": 2, "warnings": 0},
            {"path": "/test/file2.py", "errors": 0, "warnings": 1},
            {"path": "/test/file3.py", "errors": 5, "warnings": 2}
        ]
        
        for file_info in files:
            repository.store_file(file_info)
        
        # Query files with errors
        result = repository.query_files_with_errors()
        
        # Should return only files with errors > 0, sorted by error count descending
        assert len(result) == 2
        assert result[0]["path"] == "/test/file3.py"
        assert result[0]["errors"] == 5
        assert result[1]["path"] == "/test/file1.py"
        assert result[1]["errors"] == 2
    
    def test_export_to_parquet_success(self, repository: GraphRepository):
        """Test successful export to Parquet files."""
        # Store some data
        file_info: FileInfo = {
            "path": "/test/file.py",
            "errors": 1,
            "warnings": 0
        }
        repository.store_file(file_info)
        
        diagnostic: DiagnosticInfo = {
            "id": "test_diag_1",
            "severity": "error",
            "message": "Test error",
            "line": 10,
            "col": 5,
            "file_path": "/test/file.py"
        }
        repository.store_diagnostic(diagnostic)
        
        # Export to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            result = repository.export_to_parquet(temp_dir)
            
            assert result["ok"] is True
            assert "files_path" in result
            assert "diagnostics_path" in result
            assert Path(result["files_path"]).exists()
            assert Path(result["diagnostics_path"]).exists()
    
    def test_export_to_parquet_creates_directory(self, repository: GraphRepository):
        """Test that export creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = f"{temp_dir}/new_dir"
            result = repository.export_to_parquet(output_dir)
            
            assert result["ok"] is True
            assert Path(output_dir).exists()
    
    def test_import_from_parquet_success(self, repository: GraphRepository):
        """Test successful import from Parquet files."""
        # First, create another repository with data and export it
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source repository
            source_repo = KuzuRepository(":memory:")
            
            # Add data to source
            file_info: FileInfo = {
                "path": "/test/file.py",
                "errors": 1,
                "warnings": 0
            }
            source_repo.store_file(file_info)
            
            diagnostic: DiagnosticInfo = {
                "id": "test_diag_1",
                "severity": "error",
                "message": "Test error",
                "line": 10,
                "col": 5,
                "file_path": "/test/file.py"
            }
            source_repo.store_diagnostic(diagnostic)
            
            # Export from source
            export_result = source_repo.export_to_parquet(temp_dir)
            assert export_result["ok"] is True
            source_repo.close()
            
            # Import into target repository
            import_result = repository.import_from_parquet(temp_dir)
            
            assert import_result["ok"] is True
            assert import_result["files_count"] == 1
            assert import_result["diagnostics_count"] == 1
    
    def test_import_from_parquet_missing_directory(self, repository: GraphRepository):
        """Test import from non-existent directory."""
        result = repository.import_from_parquet("/non/existent/directory")
        
        assert result["ok"] is False
        assert "error" in result
        assert "does not exist" in result["error"]
    
    def test_import_from_parquet_missing_files(self, repository: GraphRepository):
        """Test import when Parquet files are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory exists but no Parquet files
            result = repository.import_from_parquet(temp_dir)
            
            assert result["ok"] is False
            assert "error" in result
            assert "not found" in result["error"]
    
    def test_full_workflow(self, repository: GraphRepository):
        """Test complete workflow: store, query, export, import."""
        # Store multiple files and diagnostics
        files = [
            {"path": "/test/file1.py", "errors": 2, "warnings": 1},
            {"path": "/test/file2.py", "errors": 0, "warnings": 3},
            {"path": "/test/file3.py", "errors": 1, "warnings": 0}
        ]
        
        for file_info in files:
            repository.store_file(file_info)
        
        diagnostics = [
            {
                "id": "diag1",
                "severity": "error",
                "message": "Error 1",
                "line": 10,
                "col": 5,
                "file_path": "/test/file1.py"
            },
            {
                "id": "diag2",
                "severity": "error",
                "message": "Error 2",
                "line": 20,
                "col": 10,
                "file_path": "/test/file1.py"
            },
            {
                "id": "diag3",
                "severity": "warning",
                "message": "Warning 1",
                "line": 15,
                "col": 3,
                "file_path": "/test/file1.py"
            }
        ]
        
        for diagnostic in diagnostics:
            repository.store_diagnostic(diagnostic)
            repository.create_file_diagnostic_relationship(
                diagnostic["file_path"],
                diagnostic["id"]
            )
        
        # Query files with errors
        error_files = repository.query_files_with_errors()
        assert len(error_files) == 2
        
        # Export and verify
        with tempfile.TemporaryDirectory() as temp_dir:
            export_result = repository.export_to_parquet(temp_dir)
            assert export_result["ok"] is True
            
            # Create new repository and import
            new_repo = KuzuRepository(":memory:")
            import_result = new_repo.import_from_parquet(temp_dir)
            
            assert import_result["ok"] is True
            assert import_result["files_count"] == 3
            assert import_result["diagnostics_count"] == 3
            
            # Verify imported data
            imported_error_files = new_repo.query_files_with_errors()
            assert len(imported_error_files) == 2
            
            new_repo.close()