"""Test JSON extension step by step"""
import tempfile
import shutil
import sys
import importlib

def test_json_extension_steps():
    """Test JSON extension loading in steps"""
    # Reload kuzu module like requirement graph does
    if 'kuzu' in sys.modules:
        importlib.reload(sys.modules['kuzu'])
    
    import kuzu
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        print("1. Creating database...")
        db = kuzu.Database(f"{temp_dir}/test.db")
        conn = kuzu.Connection(db)
        print("✓ Database created")
        
        print("\n2. Installing JSON extension...")
        try:
            conn.execute("INSTALL json;")
            print("✓ JSON extension installed")
        except Exception as e:
            print(f"✗ Failed to install: {e}")
            return
        
        print("\n3. Loading JSON extension...")
        try:
            conn.execute("LOAD EXTENSION json;")
            print("✓ JSON extension loaded")
        except Exception as e:
            print(f"✗ Failed to load: {e}")
            return
        
        print("\n4. Creating table with JSON column...")
        try:
            conn.execute("CREATE NODE TABLE TestJson(id INT64, data JSON, PRIMARY KEY(id))")
            print("✓ Table with JSON column created")
        except Exception as e:
            print(f"✗ Failed to create table: {e}")
            return
        
        print("\n5. Inserting JSON data...")
        try:
            conn.execute("CREATE (:TestJson {id: 1, data: to_json('{\"name\": \"test\"}')})")
            print("✓ JSON data inserted")
        except Exception as e:
            print(f"✗ Failed to insert: {e}")
            return
        
        print("\nAll steps completed successfully!")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_json_extension_steps()