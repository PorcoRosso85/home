#!/usr/bin/env python3
"""Apply migration to remove Responsibility table."""

from pathlib import Path
from architecture.db import KuzuConnectionManager

def main():
    # Connect to database
    db_path = Path("./data/kuzu.db")
    conn_manager = KuzuConnectionManager(db_path=db_path)
    conn = conn_manager.get_connection()
    
    # Check current tables
    print("=== Current tables before migration ===")
    result = conn.execute("CALL show_tables() RETURN *")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[1]} ({row[2]})")
    
    # Apply migration statements one by one
    print("\n=== Applying migration 003_remove_responsibility.cypher ===")
    
    # Step 1: Delete HAS_RESPONSIBILITY relationships
    try:
        print("1. Deleting HAS_RESPONSIBILITY relationships...")
        conn.execute("MATCH ()-[r:HAS_RESPONSIBILITY]->() DELETE r")
        print("   ✓ Success")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 2: Drop HAS_RESPONSIBILITY table
    try:
        print("2. Dropping HAS_RESPONSIBILITY table...")
        conn.execute("DROP TABLE HAS_RESPONSIBILITY CASCADE")
        print("   ✓ Success")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 3: Drop Responsibility table
    try:
        print("3. Dropping Responsibility table...")
        conn.execute("DROP TABLE Responsibility CASCADE")
        print("   ✓ Success")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Verify results
    print("\n=== Tables after migration ===")
    result = conn.execute("CALL show_tables() RETURN *")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[1]} ({row[2]})")
    
    print("\n✅ Migration completed!")

if __name__ == "__main__":
    main()