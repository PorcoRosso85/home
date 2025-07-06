"""Test pytest isolation issues with JSON extension"""
import subprocess
import sys
import tempfile
import shutil

def test_subprocess_execution():
    """Test if running in subprocess avoids segfault"""
    code = '''
import tempfile
import shutil
import kuzu

temp_dir = tempfile.mkdtemp()
try:
    db = kuzu.Database(f"{temp_dir}/test.db")
    conn = kuzu.Connection(db)
    
    # Setup JSON extension
    conn.execute("INSTALL json;")
    conn.execute("LOAD EXTENSION json;")
    
    # Create table
    conn.execute("CREATE NODE TABLE Test(id INT64, data JSON, PRIMARY KEY(id))")
    
    # Insert data
    conn.execute("CREATE (:Test {id: 1, data: to_json(map(['key'], ['value']))})")
    
    # Query
    result = conn.execute("MATCH (t:Test) RETURN json_extract(t.data, '$.key')")
    assert result.has_next()
    
    print("SUCCESS: JSON extension works in subprocess")
    
finally:
    shutil.rmtree(temp_dir)
'''
    
    # Run in subprocess
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True,
        text=True
    )
    
    print(f"Subprocess stdout: {result.stdout}")
    print(f"Subprocess stderr: {result.stderr}")
    print(f"Subprocess returncode: {result.returncode}")
    
    assert result.returncode == 0
    assert "SUCCESS" in result.stdout


def test_pytest_marker():
    """Test with pytest marker to check if it affects behavior"""
    import pytest
    
    # This test will be skipped to avoid segfault
    pytest.skip("JSON extension causes segfault in pytest environment")


if __name__ == "__main__":
    # Direct execution test
    print("Testing subprocess execution...")
    test_subprocess_execution()
    print("✓ Subprocess test passed")