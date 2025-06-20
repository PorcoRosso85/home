#!/usr/bin/env python3
"""Simple FTS test for KuzuDB"""

import sys
sys.path.append('/home/nixos/bin/src')
from db.kuzu.connection import get_connection

def main():
    conn = get_connection()
    
    # Install and load FTS
    try:
        conn.execute("INSTALL FTS;")
        conn.execute("LOAD EXTENSION FTS;")
    except:
        pass
    
    # Create index
    try:
        conn.execute("CALL DROP_FTS_INDEX('Document', 'doc_idx');")
    except:
        pass
        
    conn.execute("CALL CREATE_FTS_INDEX('Document', 'doc_idx', ['title', 'content']);")
    print("FTS index created")
    
    # Test query
    query = "neural networks"
    result = conn.execute(f"CALL QUERY_FTS_INDEX('Document', 'doc_idx', '{query}') RETURN *;")
    
    print(f"\nResults for '{query}':")
    while result.has_next():
        row = result.get_next()
        print(f"Row: {row}")

if __name__ == "__main__":
    main()