#!/usr/bin/env python3
"""
Lightweight KuzuDB LocationURI query tool
Leverages existing requirement/graph infrastructure
"""

import json
import sys
import os
from pathlib import Path

# Add requirement/graph to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "requirement" / "graph"))

try:
    from infrastructure.database_factory import DatabaseFactory
except ImportError:
    print("Error: Could not import from requirement/graph. Ensure it exists.", file=sys.stderr)
    sys.exit(1)

def query_location_uris(db_path: str = None) -> list[dict]:
    """Query all LocationURI nodes from KuzuDB"""
    if db_path is None:
        # Default path
        db_path = str(Path.home() / "bin" / "src" / "requirement" / "graph" / "rgl_db")
    
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Use existing infrastructure
        db_factory = DatabaseFactory()
        db = db_factory.create_database(db_path)
        conn = db.get_connection()
        
        # Execute query
        result = conn.execute("MATCH (l:LocationURI) RETURN l.id AS uri")
        
        # Collect results
        uris = []
        while result.has_next():
            row = result.get_next()
            uris.append({"uri": row[0]})
        
        return uris
        
    except Exception as e:
        print(f"Error querying database: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # Parse arguments
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Query and output
    uris = query_location_uris(db_path)
    print(json.dumps(uris))

if __name__ == "__main__":
    main()