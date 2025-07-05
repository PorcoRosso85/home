#!/usr/bin/env python3
"""
Real KuzuDB LocationURI query tool
Implements actual database connection and DQL execution
"""

import json
import sys
from pathlib import Path

try:
    import kuzu
except ImportError:
    print("Error: kuzu package not installed. Install with: pip install kuzu", file=sys.stderr)
    sys.exit(1)


def create_database_if_not_exists(db_path: str) -> kuzu.Database:
    """Create database and apply DDL schema if needed"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Check if LocationURI table exists
    try:
        conn.execute("MATCH (l:LocationURI) RETURN COUNT(*)")
    except:
        # Table doesn't exist, create it following DDL schema
        print("Creating LocationURI table...", file=sys.stderr)
        conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
        
        # Also create RequirementEntity for relationships
        conn.execute("""
            CREATE NODE TABLE RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                priority UINT8 DEFAULT 1,
                requirement_type STRING DEFAULT 'functional',
                status STRING DEFAULT 'proposed'
            )
        """)
        
        # Create LOCATES relationship
        conn.execute("""
            CREATE REL TABLE LOCATES (
                FROM LocationURI TO RequirementEntity,
                entity_type STRING DEFAULT 'requirement',
                current BOOLEAN DEFAULT false
            )
        """)
    
    conn.close()
    return db


def query_location_uris(db_path: str = None) -> list[dict]:
    """Query all LocationURI nodes from KuzuDB using DQL"""
    if db_path is None:
        # Default path following requirement/graph convention
        db_path = str(Path.home() / "bin" / "src" / "requirement" / "graph" / "rgl_db")
    
    if not Path(db_path).parent.exists():
        raise FileNotFoundError(f"Database directory not found: {Path(db_path).parent}")
    
    try:
        # Connect to database
        db = create_database_if_not_exists(db_path)
        conn = kuzu.Connection(db)
        
        # Execute DQL query
        result = conn.execute("MATCH (l:LocationURI) RETURN l.id AS uri ORDER BY l.id")
        
        # Collect results
        uris = []
        while result.has_next():
            row = result.get_next()
            uris.append({"uri": row[0]})
        
        conn.close()
        return uris
        
    except Exception as e:
        raise RuntimeError(f"Database query failed: {e}")


def insert_test_data(db_path: str, cypher_file: str = None):
    """Insert test data from cypher file (for testing)"""
    if cypher_file is None:
        cypher_file = "test_data_setup.cypher"
    
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Read and execute cypher statements
    with open(cypher_file, 'r') as f:
        statements = f.read().split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    conn.execute(stmt)
                except Exception as e:
                    print(f"Error executing: {stmt[:50]}... - {e}", file=sys.stderr)
    
    conn.close()


def main():
    """CLI entry point"""
    # Parse arguments
    db_path = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup-test-data":
            # Special mode for setting up test data
            db_path = sys.argv[2] if len(sys.argv) > 2 else "./test.db"
            insert_test_data(db_path)
            print("Test data inserted successfully")
            return 0
        else:
            db_path = sys.argv[1]
    
    try:
        # Query and output
        uris = query_location_uris(db_path)
        print(json.dumps(uris))
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error querying database: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())