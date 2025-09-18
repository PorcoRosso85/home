#!/usr/bin/env python3
"""Simple KuzuDB connection test."""

import sys
import tempfile
from pathlib import Path

try:
    # Try to import kuzu
    import kuzu
    print("✓ Successfully imported kuzu module")
    print(f"  KuzuDB version: {kuzu.__version__}")
except ImportError as e:
    print(f"✗ Failed to import kuzu: {e}")
    sys.exit(1)

try:
    # Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n✓ Created temporary directory: {tmpdir}")
        
        # Create database connection
        db = kuzu.Database(tmpdir)
        print("✓ Created KuzuDB database instance")
        
        # Create connection
        conn = kuzu.Connection(db)
        print("✓ Created KuzuDB connection")
        
        # Execute a simple query
        result = conn.execute("RETURN 1 AS test")
        print("✓ Executed test query")
        
        # Get results
        while result.has_next():
            row = result.get_next()
            print(f"✓ Query result: {row}")
        
        print("\n✓ All KuzuDB connection tests passed!")
        
except Exception as e:
    print(f"\n✗ Error during KuzuDB operations: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)