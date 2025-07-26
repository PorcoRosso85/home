#!/usr/bin/env python3
"""Verify KuzuDB installation and configuration"""

import sys

try:
    import kuzu
    print("✅ KuzuDB Python module imported successfully")
    print(f"   Version: {kuzu.__version__ if hasattr(kuzu, '__version__') else 'Unknown'}")
    
    # Try to create a test database
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # Create a simple test table
        conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))")
        conn.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        
        # Query the data
        result = conn.execute("MATCH (p:Person) RETURN p.name, p.age")
        while result.has_next():
            row = result.get_next()
            print(f"✅ Query successful: {row}")
        
        print("✅ KuzuDB is fully functional!")
        
except ImportError as e:
    print(f"❌ Failed to import kuzu: {e}")
    print("   Run 'nix develop' to enter the development shell")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing KuzuDB: {e}")
    sys.exit(1)