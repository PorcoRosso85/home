"""Test repository pattern implementation independently."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_docs.infrastructure.kuzu.kuzu_repository import KuzuRepository
from graph_docs.kuzu_storage import KuzuStorage
from graph_docs.application.interfaces.repository import FileInfo, DiagnosticInfo

def test_repository_pattern():
    """Test the repository pattern implementation."""
    print("Testing Repository Pattern Implementation\n")
    
    # Test 1: Direct repository usage
    print("1. Testing KuzuRepository directly...")
    repo = KuzuRepository(":memory:")
    
    # Store a file
    file_info: FileInfo = {
        "path": "/test/example.py",
        "errors": 2,
        "warnings": 1
    }
    repo.store_file(file_info)
    print("   ✅ Stored file information")
    
    # Store a diagnostic
    diagnostic: DiagnosticInfo = {
        "id": "test_diag_1",
        "severity": "error",
        "message": "Test error message",
        "line": 10,
        "col": 5,
        "file_path": "/test/example.py"
    }
    repo.store_diagnostic(diagnostic)
    print("   ✅ Stored diagnostic information")
    
    # Create relationship
    repo.create_file_diagnostic_relationship("/test/example.py", "test_diag_1")
    print("   ✅ Created file-diagnostic relationship")
    
    # Query files with errors
    error_files = repo.query_files_with_errors()
    print(f"   ✅ Found {len(error_files)} files with errors")
    
    repo.close()
    
    # Test 2: KuzuStorage compatibility layer
    print("\n2. Testing KuzuStorage compatibility layer...")
    storage = KuzuStorage(":memory:")
    
    # Simulate Pyright analysis results
    results = {
        "files": [
            {"path": "/app/main.py", "errors": 1, "warnings": 0},
            {"path": "/app/utils.py", "errors": 0, "warnings": 2}
        ],
        "diagnostics": [
            {
                "file": "/app/main.py",
                "severity": "error",
                "message": "Type mismatch",
                "range": {
                    "start": {"line": 5, "character": 10}
                }
            }
        ]
    }
    
    storage.store_analysis(results)
    print("   ✅ Stored analysis results through compatibility layer")
    
    # Query through compatibility layer
    files_with_errors = storage.query_files_with_errors()
    print(f"   ✅ Found {len(files_with_errors)} files with errors through compatibility layer")
    
    # Test the returned format
    if files_with_errors:
        first_file = files_with_errors[0]
        assert "path" in first_file, "Missing 'path' key in result"
        assert "errors" in first_file, "Missing 'errors' key in result"
        print(f"   ✅ Result format is correct: {first_file}")
    
    print("\n✅ All repository pattern tests passed!")

if __name__ == "__main__":
    test_repository_pattern()