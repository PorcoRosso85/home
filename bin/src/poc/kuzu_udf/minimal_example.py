"""Minimal KuzuDB UDF Example

最小限のKuzuDB UDF実装例
"""

import re
import kuzu


def main():
    # In-memory database
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Create schema
    conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
    
    # Insert data
    conn.execute("CREATE (:LocationURI {id: 'req://system/auth'})")
    conn.execute("CREATE (:LocationURI {id: 'file:///src/main.py'})")
    conn.execute("CREATE (:LocationURI {id: 'test://unit/login'})")
    
    # Register UDF
    def extract_scheme(uri: str) -> str:
        """Extract scheme from URI"""
        match = re.match(r'^([^:]+)://', uri)
        return match.group(1) if match else ""
    
    conn.create_function("extract_scheme", extract_scheme)
    
    # Use UDF in query
    result = conn.execute("""
        MATCH (n:LocationURI)
        WHERE extract_scheme(n.id) = 'req'
        RETURN n.id
    """)
    
    print("Requirements nodes:")
    for row in result:
        print(f"  - {row['n.id']}")


if __name__ == "__main__":
    main()