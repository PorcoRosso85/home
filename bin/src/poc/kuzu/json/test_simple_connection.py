"""Simple test without JSON extension"""
import tempfile
import shutil

def test_simple_connection():
    """Test basic KuzuDB connection without JSON extension"""
    import kuzu
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create database
        db = kuzu.Database(f"{temp_dir}/test.db")
        conn = kuzu.Connection(db)
        
        # Create simple table
        conn.execute("CREATE NODE TABLE Person(name STRING, PRIMARY KEY(name))")
        
        # Insert data
        conn.execute("CREATE (:Person {name: 'Alice'})")
        
        # Query data
        result = conn.execute("MATCH (p:Person) RETURN p.name")
        
        # Get results without pyarrow
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 'Alice'
        print("✓ Basic connection works without JSON extension")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_simple_connection()