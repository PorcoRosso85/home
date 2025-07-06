"""Test JSON extension with controlled fixture"""
import pytest
import tempfile
import shutil
import subprocess
import sys


@pytest.fixture(scope="function")
def json_connection_subprocess():
    """Create a connection with JSON extension in subprocess"""
    def run_query(query):
        code = f'''
import tempfile
import shutil
import kuzu
import json

temp_dir = tempfile.mkdtemp()
try:
    db = kuzu.Database(f"{{temp_dir}}/test.db")
    conn = kuzu.Connection(db)
    
    # Setup JSON extension
    conn.execute("INSTALL json;")
    conn.execute("LOAD EXTENSION json;")
    
    # Create table if needed
    query_str = {repr(query)}
    if "CREATE NODE TABLE" in query_str:
        conn.execute(query_str)
        print(json.dumps({{"success": True, "type": "create"}}))
    elif "CREATE (" in query_str:
        conn.execute(query_str)
        print(json.dumps({{"success": True, "type": "insert"}}))
    else:
        # Query execution
        result = conn.execute(query_str)
        if result.has_next():
            row = result.get_next()
            print(json.dumps({{"success": True, "type": "query", "result": str(row[0])}}))
        else:
            print(json.dumps({{"success": True, "type": "query", "result": None}}))
    
finally:
    shutil.rmtree(temp_dir)
'''
        
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Subprocess failed: {result.stderr}")
        
        import json
        return json.loads(result.stdout.strip())
    
    return run_query


def test_json_via_subprocess(json_connection_subprocess):
    """Test JSON extension through subprocess isolation"""
    # Create table
    result = json_connection_subprocess(
        "CREATE NODE TABLE TestJson(id INT64, data JSON, PRIMARY KEY(id))"
    )
    assert result["success"]
    assert result["type"] == "create"
    
    # Insert data
    result = json_connection_subprocess(
        "CREATE (:TestJson {id: 1, data: to_json(map(['name'], ['test']))})"
    )
    assert result["success"]
    assert result["type"] == "insert"
    
    # Query data
    result = json_connection_subprocess(
        "MATCH (t:TestJson) WHERE t.id = 1 RETURN json_extract(t.data, '$.name')"
    )
    assert result["success"]
    assert result["type"] == "query"
    assert '"test"' in result["result"]
    
    print("✓ JSON operations work via subprocess isolation")


def test_without_json_extension():
    """Test basic operations without JSON extension"""
    import kuzu
    
    temp_dir = tempfile.mkdtemp()
    try:
        db = kuzu.Database(f"{temp_dir}/test.db")
        conn = kuzu.Connection(db)
        
        # Create table without JSON
        conn.execute("CREATE NODE TABLE Person(id INT64, name STRING, PRIMARY KEY(id))")
        conn.execute("CREATE (:Person {id: 1, name: 'Alice'})")
        
        result = conn.execute("MATCH (p:Person) RETURN p.name")
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 'Alice'
        
        print("✓ Basic operations work without JSON extension")
        
    finally:
        shutil.rmtree(temp_dir)