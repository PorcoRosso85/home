"""Minimal test for Pyright analyzer with KuzuDB."""

import tempfile
from pathlib import Path
from graph_docs.pyright_analyzer import PyrightAnalyzer
from graph_docs.kuzu_storage import KuzuStorage


def test_pyright_with_kuzu():
    """Test Pyright analyzer with KuzuDB storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python files
        test_file1 = Path(tmpdir) / "example.py"
        test_file1.write_text("""
def hello(name: str) -> str:
    return f"Hello, {name}!"

# This will cause a type error
result: int = hello("world")
""")
        
        test_file2 = Path(tmpdir) / "clean.py"
        test_file2.write_text("""
def add(a: int, b: int) -> int:
    return a + b

result = add(1, 2)  # No type error
""")
        
        # Run analyzer
        print("Running Pyright analysis...")
        analyzer = PyrightAnalyzer(tmpdir)
        results = analyzer.analyze()
        
        # Check results
        assert "diagnostics" in results
        assert "files" in results
        
        print(f"Found {len(results['diagnostics'])} diagnostics")
        print(f"Analyzed {len(results['files'])} files")
        
        # Store in KuzuDB
        print("\nStoring results in KuzuDB...")
        storage = KuzuStorage()
        storage.store_analysis(results)
        
        # Query results
        files_with_errors = storage.query_files_with_errors()
        print(f"\nFiles with errors: {len(files_with_errors)}")
        for file_info in files_with_errors:
            print(f"- {file_info[0]}: {file_info[1]} errors")
        
        # Verify
        assert len(files_with_errors) >= 1
        assert any("example.py" in str(f[0]) for f in files_with_errors)
        
        print("\n✅ Test passed!")


if __name__ == "__main__":
    test_pyright_with_kuzu()