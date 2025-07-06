"""Test JSON extension with persistent database approach"""
import pytest
import tempfile
import shutil
import os
import subprocess
import sys


class JSONDatabaseWrapper:
    """Wrapper to execute JSON operations via subprocess"""
    def __init__(self, db_path):
        self.db_path = db_path
        
    def execute(self, query):
        """Execute query in subprocess to avoid segfault"""
        code = f'''
import kuzu
import json

db = kuzu.Database({repr(self.db_path)})
conn = kuzu.Connection(db)

try:
    # First time setup - install JSON extension
    try:
        conn.execute("INSTALL json;")
        conn.execute("LOAD EXTENSION json;")
    except:
        pass  # Already installed
    
    # Execute the query
    result = conn.execute({repr(query)})
    
    # Handle different query types
    if "CREATE NODE TABLE" in {repr(query)} or "CREATE (" in {repr(query)}:
        print(json.dumps({{"success": True, "type": "ddl"}}))
    else:
        # Query with results
        rows = []
        while result.has_next():
            row = result.get_next()
            rows.append([str(val) for val in row])
        print(json.dumps({{"success": True, "rows": rows}}))
        
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
'''
        
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            env={**os.environ, 'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', '')}
        )
        
        if result.returncode != 0:
            raise Exception(f"Subprocess failed: {result.stderr}")
        
        import json
        return json.loads(result.stdout.strip())


@pytest.fixture(scope="function")
def json_db():
    """Create a persistent database for JSON testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/test.db"
    wrapper = JSONDatabaseWrapper(db_path)
    
    yield wrapper
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_json_with_persistent_db(json_db):
    """Test JSON operations with persistent database"""
    # Create table
    result = json_db.execute(
        "CREATE NODE TABLE TestJson(id INT64, data JSON, PRIMARY KEY(id))"
    )
    assert result["success"]
    
    # Insert data
    result = json_db.execute(
        "CREATE (:TestJson {id: 1, data: to_json(map(['name', 'value'], ['test', 'data']))})"
    )
    assert result["success"]
    
    # Query data
    result = json_db.execute(
        "MATCH (t:TestJson) WHERE t.id = 1 RETURN json_extract(t.data, '$.name') as name"
    )
    assert result["success"]
    assert len(result["rows"]) == 1
    assert '"test"' in result["rows"][0][0]
    
    print("✓ JSON operations work with persistent database approach")


def test_json_complex_operations(json_db):
    """Test more complex JSON operations"""
    # Create table
    json_db.execute(
        "CREATE NODE TABLE Document(id STRING, content JSON, PRIMARY KEY(id))"
    )
    
    # Insert multiple documents
    for i in range(3):
        json_db.execute(f"""
            CREATE (:Document {{
                id: 'doc{i}',
                content: to_json(map(['title', 'index'], ['Document {i}', '{i}']))
            }})
        """)
    
    # Query all documents
    result = json_db.execute("""
        MATCH (d:Document) 
        RETURN d.id, json_extract(d.content, '$.title') as title
        ORDER BY d.id
    """)
    
    assert result["success"]
    assert len(result["rows"]) == 3
    assert '"Document 0"' in result["rows"][0][1]
    
    print("✓ Complex JSON operations work correctly")


if __name__ == "__main__":
    # Test directly
    temp_dir = tempfile.mkdtemp()
    try:
        wrapper = JSONDatabaseWrapper(f"{temp_dir}/test.db")
        
        # Run tests
        print("Testing persistent database approach...")
        
        # Create table
        result = wrapper.execute(
            "CREATE NODE TABLE TestJson(id INT64, data JSON, PRIMARY KEY(id))"
        )
        print(f"Create table: {result}")
        
        # Insert data
        result = wrapper.execute(
            "CREATE (:TestJson {id: 1, data: to_json(map(['test'], ['value']))})"
        )
        print(f"Insert data: {result}")
        
        # Query
        result = wrapper.execute(
            "MATCH (t:TestJson) RETURN json_extract(t.data, '$.test')"
        )
        print(f"Query result: {result}")
        
    finally:
        shutil.rmtree(temp_dir)