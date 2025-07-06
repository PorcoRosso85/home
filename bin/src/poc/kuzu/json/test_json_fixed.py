"""Fixed JSON extension test based on requirement graph approach"""
import tempfile
import shutil
import sys
import importlib
import pytest

@pytest.fixture
def kuzu_connection():
    """Create a KuzuDB connection with proper setup"""
    # Reload kuzu module like requirement graph does
    if 'kuzu' in sys.modules:
        importlib.reload(sys.modules['kuzu'])
    
    import kuzu
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create database and connection
        db = kuzu.Database(f"{temp_dir}/test.db")
        conn = kuzu.Connection(db)
        
        # Setup JSON extension
        conn.execute("INSTALL json;")
        conn.execute("LOAD EXTENSION json;")
        
        yield conn
        
    finally:
        shutil.rmtree(temp_dir)


def test_json_extension_with_fixed_approach(kuzu_connection):
    """Test JSON extension with fixed approach"""
    conn = kuzu_connection
    
    # Create table with JSON column
    conn.execute("CREATE NODE TABLE TestJson(id INT64, data JSON, PRIMARY KEY(id))")
    
    # Insert JSON data - use proper JSON object, not string
    conn.execute("CREATE (:TestJson {id: 1, data: to_json(map(['name'], ['test']))})")
    
    # Query with json_extract
    result = conn.execute("MATCH (t:TestJson) WHERE t.id = 1 RETURN json_extract(t.data, '$.name') as name")
    
    assert result.has_next()
    row = result.get_next()
    # JSON strings are returned with quotes
    assert row[0] == '"test"' or row[0] == 'test'
    print("✓ JSON extension works with fixed approach")


def test_create_document_node(kuzu_connection):
    """Test creating document node like in POC"""
    conn = kuzu_connection
    
    # Create Document table
    conn.execute("""
        CREATE NODE TABLE Document(
            id STRING,
            type STRING,
            description JSON,
            PRIMARY KEY(id)
        )
    """)
    
    # Insert document - use map function to create JSON
    conn.execute("""
        CREATE (:Document {
            id: 'doc1',
            type: 'test',
            description: to_json(map(['title', 'content'], ['Test Document', 'Sample content']))
        })
    """)
    
    # Query document
    result = conn.execute("""
        MATCH (d:Document)
        WHERE d.id = 'doc1'
        RETURN json_extract(d.description, '$.title') as title
    """)
    
    assert result.has_next()
    row = result.get_next()
    print(f"DEBUG2: row[0] = {row[0]}, type = {type(row[0])}")
    # JSON strings are returned with quotes
    assert row[0] == '"Test Document"' or row[0] == 'Test Document'
    print("✓ Document node with JSON works")


if __name__ == "__main__":
    # Run without pytest for debugging
    import kuzu
    temp_dir = tempfile.mkdtemp()
    try:
        db = kuzu.Database(f"{temp_dir}/test.db")
        conn = kuzu.Connection(db)
        conn.execute("INSTALL json;")
        conn.execute("LOAD EXTENSION json;")
        
        # Run tests manually
        test_json_extension_with_fixed_approach(conn)
        test_create_document_node(conn)
        
    finally:
        shutil.rmtree(temp_dir)