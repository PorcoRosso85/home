"""Test KuzuDB persistence and COPY FROM/TO functionality."""

import tempfile
import os
from pathlib import Path
from graph_docs.pyright_analyzer import PyrightAnalyzer
from graph_docs.kuzu_storage import KuzuStorage


def test_kuzu_persistence_and_copy():
    """Test persisting to file and copying data between databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python file
        test_file = Path(tmpdir) / "example.py"
        test_file.write_text("""
def hello(name: str) -> str:
    return f"Hello, {name}!"

# Type error
result: int = hello("world")
""")
        
        # 1. Analyze and store in persistent DB
        print("1. Creating persistent KuzuDB...")
        db_path = os.path.join(tmpdir, "analysis.kuzu")
        storage1 = KuzuStorage(db_path)
        
        analyzer = PyrightAnalyzer(tmpdir)
        results = analyzer.analyze()
        storage1.store_analysis(results)
        
        # Query from persistent DB
        files1 = storage1.query_files_with_errors()
        print(f"   Files with errors in persistent DB: {len(files1)}")
        
        # 2. Export to CSV using COPY TO
        print("\n2. Exporting to CSV...")
        csv_dir = Path(tmpdir) / "export"
        csv_dir.mkdir()
        
        # Export Files table
        storage1.conn.execute(f"""
            COPY (MATCH (f:File) RETURN f.*) 
            TO '{csv_dir}/files.csv' (header=true)
        """)
        
        # Export Diagnostics table
        storage1.conn.execute(f"""
            COPY (MATCH (d:Diagnostic) RETURN d.*) 
            TO '{csv_dir}/diagnostics.csv' (header=true)
        """)
        
        print(f"   Exported to {csv_dir}")
        
        # 3. Create new in-memory DB and import from CSV
        print("\n3. Creating in-memory DB and importing from CSV...")
        storage2 = KuzuStorage(":memory:")
        
        # Import using COPY FROM
        storage2.conn.execute(f"""
            COPY File FROM '{csv_dir}/files.csv' (header=true)
        """)
        
        storage2.conn.execute(f"""
            COPY Diagnostic FROM '{csv_dir}/diagnostics.csv' (header=true)
        """)
        
        # Query from in-memory DB
        files2 = storage2.query_files_with_errors()
        print(f"   Files with errors in in-memory DB: {len(files2)}")
        
        # 4. Verify data consistency
        print("\n4. Verifying data consistency...")
        assert len(files1) == len(files2), "File count mismatch"
        assert files1[0][0] == files2[0][0], "File path mismatch"
        assert files1[0][1] == files2[0][1], "Error count mismatch"
        
        print("   ✅ Data successfully migrated from persistent to in-memory DB!")
        
        # 5. Test direct DB copy (attach and copy)
        print("\n5. Testing direct DB copy using ATTACH...")
        storage3 = KuzuStorage(":memory:")
        
        # Attach the persistent DB
        storage3.conn.execute(f"""
            ATTACH DATABASE '{db_path}' AS source_db
        """)
        
        # Copy data using cross-database query
        storage3.conn.execute("""
            CREATE (f:File {path: n.path, errors: n.errors, warnings: n.warnings, analyzed_at: n.analyzed_at})
            FROM source_db.File n
        """)
        
        files3 = storage3.query_files_with_errors()
        print(f"   Files with errors after ATTACH copy: {len(files3)}")
        
        assert len(files1) == len(files3), "ATTACH copy file count mismatch"
        
        print("\n✅ All persistence tests passed!")


def test_parquet_export():
    """Test exporting File and Diagnostic tables to Parquet format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
def add(a: int, b: int) -> int:
    return a + b

# Type error
result: str = add(1, 2)
""")
        
        # Analyze and store in DB
        print("1. Analyzing code and storing in KuzuDB...")
        db_path = os.path.join(tmpdir, "test.kuzu")
        storage = KuzuStorage(db_path)
        
        analyzer = PyrightAnalyzer(tmpdir)
        results = analyzer.analyze()
        storage.store_analysis(results)
        
        # Export to Parquet
        print("\n2. Exporting to Parquet format...")
        parquet_dir = Path(tmpdir) / "parquet_export"
        storage.export_to_parquet(str(parquet_dir))
        
        # Verify files were created
        files_parquet = parquet_dir / "files.parquet"
        diagnostics_parquet = parquet_dir / "diagnostics.parquet"
        
        assert files_parquet.exists(), f"Files parquet not created at {files_parquet}"
        assert diagnostics_parquet.exists(), f"Diagnostics parquet not created at {diagnostics_parquet}"
        
        # Check file sizes
        files_size = files_parquet.stat().st_size
        diag_size = diagnostics_parquet.stat().st_size
        
        print(f"\n3. Verifying Parquet files:")
        print(f"   - Files parquet: {files_size} bytes")
        print(f"   - Diagnostics parquet: {diag_size} bytes")
        
        assert files_size > 0, "Files parquet is empty"
        assert diag_size > 0, "Diagnostics parquet is empty"
        
        print("\n✅ Parquet export test passed!")


def test_parquet_import():
    """Test importing File and Diagnostic tables from Parquet format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python files with various issues
        test_file1 = Path(tmpdir) / "module1.py"
        test_file1.write_text("""
def multiply(x: int, y: int) -> int:
    return x * y

# Type error: expecting int, got str
result1: int = multiply("hello", 5)

# Another type error
result2: str = multiply(3, 4)
""")
        
        test_file2 = Path(tmpdir) / "module2.py"
        test_file2.write_text("""
from typing import List

def process_items(items: List[str]) -> int:
    return len(items)

# Type error: passing int instead of List[str]
count = process_items(42)
""")
        
        # 1. Analyze and store in original DB
        print("1. Analyzing code and storing in original KuzuDB...")
        original_db_path = os.path.join(tmpdir, "original.kuzu")
        original_storage = KuzuStorage(original_db_path)
        
        analyzer = PyrightAnalyzer(tmpdir)
        results = analyzer.analyze()
        original_storage.store_analysis(results)
        
        # Query original data for comparison
        original_files = original_storage.query_files_with_errors()
        print(f"   Original DB - Files with errors: {len(original_files)}")
        for file_path, errors in original_files:
            print(f"     - {Path(file_path).name}: {errors} errors")
        
        # Get all diagnostics from original DB
        original_diagnostics = original_storage.conn.execute("""
            MATCH (d:Diagnostic)
            RETURN d.id as id, d.severity as severity, d.message as message, 
                   d.line as line, d.column as column
            ORDER BY d.id
        """)
        original_diag_list = []
        while original_diagnostics.has_next():
            original_diag_list.append(original_diagnostics.get_next())
        print(f"   Original DB - Total diagnostics: {len(original_diag_list)}")
        
        # 2. Export to Parquet
        print("\n2. Exporting to Parquet format...")
        parquet_dir = Path(tmpdir) / "parquet_data"
        original_storage.export_to_parquet(str(parquet_dir))
        
        # 3. Create new in-memory DB and import from Parquet
        print("\n3. Creating new in-memory DB and importing from Parquet...")
        new_storage = KuzuStorage(":memory:")
        new_storage.import_from_parquet(str(parquet_dir))
        
        # 4. Query imported data
        imported_files = new_storage.query_files_with_errors()
        print(f"   Imported DB - Files with errors: {len(imported_files)}")
        for file_path, errors in imported_files:
            print(f"     - {Path(file_path).name}: {errors} errors")
        
        # Get all diagnostics from imported DB
        imported_diagnostics = new_storage.conn.execute("""
            MATCH (d:Diagnostic)
            RETURN d.id as id, d.severity as severity, d.message as message, 
                   d.line as line, d.column as column
            ORDER BY d.id
        """)
        imported_diag_list = []
        while imported_diagnostics.has_next():
            imported_diag_list.append(imported_diagnostics.get_next())
        print(f"   Imported DB - Total diagnostics: {len(imported_diag_list)}")
        
        # 5. Verify data consistency
        print("\n4. Verifying data consistency...")
        
        # Check file count
        assert len(original_files) == len(imported_files), \
            f"File count mismatch: original={len(original_files)}, imported={len(imported_files)}"
        
        # Check file details
        for orig, imp in zip(sorted(original_files), sorted(imported_files)):
            assert orig[0] == imp[0], f"File path mismatch: {orig[0]} != {imp[0]}"
            assert orig[1] == imp[1], f"Error count mismatch for {orig[0]}: {orig[1]} != {imp[1]}"
        
        # Check diagnostic count
        assert len(original_diag_list) == len(imported_diag_list), \
            f"Diagnostic count mismatch: original={len(original_diag_list)}, imported={len(imported_diag_list)}"
        
        # Check diagnostic details
        for orig, imp in zip(original_diag_list, imported_diag_list):
            assert orig[0] == imp[0], f"Diagnostic ID mismatch: {orig[0]} != {imp[0]}"
            assert orig[1] == imp[1], f"Severity mismatch: {orig[1]} != {imp[1]}"
            assert orig[2] == imp[2], f"Message mismatch: {orig[2]} != {imp[2]}"
            assert orig[3] == imp[3], f"Line mismatch: {orig[3]} != {imp[3]}"
            assert orig[4] == imp[4], f"Column mismatch: {orig[4]} != {imp[4]}"
        
        print("   ✅ All data successfully imported and verified!")
        
        # 6. Test error handling - missing files
        print("\n5. Testing error handling...")
        missing_dir = Path(tmpdir) / "missing_dir"
        try:
            new_storage2 = KuzuStorage(":memory:")
            new_storage2.import_from_parquet(str(missing_dir))
            assert False, "Should have raised ValueError for missing directory"
        except ValueError as e:
            print(f"   ✅ Correctly raised ValueError: {e}")
        
        # Test missing parquet files
        incomplete_dir = Path(tmpdir) / "incomplete"
        incomplete_dir.mkdir()
        (incomplete_dir / "files.parquet").touch()  # Create empty file
        try:
            new_storage3 = KuzuStorage(":memory:")
            new_storage3.import_from_parquet(str(incomplete_dir))
            assert False, "Should have raised FileNotFoundError for missing diagnostics.parquet"
        except FileNotFoundError as e:
            print(f"   ✅ Correctly raised FileNotFoundError: {e}")
        
        print("\n✅ Parquet import test passed!")


if __name__ == "__main__":
    test_kuzu_persistence_and_copy()
    print("\n" + "="*50 + "\n")
    test_parquet_export()
    print("\n" + "="*50 + "\n")
    test_parquet_import()