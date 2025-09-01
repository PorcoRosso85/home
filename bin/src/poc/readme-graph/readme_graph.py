#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import kuzu
except ImportError:
    print("Error: kuzu module not found. Please run:")
    print("  nix develop")
    print("or")
    print("  nix shell .#default")
    sys.exit(1)


def init_db(db_path: str = "./readme.db") -> None:
    """Initialize database with minimal schema."""
    if Path(db_path).exists():
        print(f"Database {db_path} already exists")
        return
    
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Create minimal schema - only what's needed now
    conn.execute("""
        CREATE NODE TABLE Module(
            path STRING PRIMARY KEY,
            purpose STRING,
            type STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE DEPENDS_ON(FROM Module TO Module)
    """)
    
    print(f"Initialized {db_path}")


def add_module(path: str, purpose: str, module_type: str, db_path: str = "./readme.db") -> None:
    """Add module to graph."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Check if module exists
    result = conn.execute(
        f"MATCH (m:Module {{path: '{path}'}}) RETURN count(m) as count"
    )
    
    if result.has_next() and result.get_next()[0] > 0:
        print(f"Module {path} already exists")
        return
    
    # Add module
    conn.execute(
        f"""
        CREATE (m:Module {{
            path: '{path}',
            purpose: '{purpose}',
            type: '{module_type}'
        }})
        """
    )
    
    print(f"Added module: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python readme_graph.py <command> [args]")
        print("Commands:")
        print("  init                          - Initialize database")
        print("  add <path> <purpose> <type>   - Add module")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        init_db()
    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: python readme_graph.py add <path> <purpose> <type>")
            sys.exit(1)
        add_module(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)