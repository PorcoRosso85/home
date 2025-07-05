#!/usr/bin/env python3
"""
KuzuDB LocationURI query tool using requirement/graph infrastructure
"""

import json
import sys
import os
from pathlib import Path
import tempfile

# Add requirement/graph to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "requirement" / "graph"))

try:
    from infrastructure.database_factory import DatabaseFactory
    from infrastructure.kuzu_repository import KuzuRepository
    import kuzu
except ImportError as e:
    # Fallback for testing without full KuzuDB
    # Global storage for mock database
    _mock_databases = {}
    
    class MockDatabase:
        def __init__(self, path):
            self.path = path
            # Use persistent storage per database path
            if path not in _mock_databases:
                _mock_databases[path] = []
            self._data = _mock_databases[path]
        
        def get_connection(self):
            return MockConnection(self.path, self._data)
    
    class MockConnection:
        def __init__(self, path, data):
            self.path = path
            self._data = data
        
        def execute(self, query):
            class Result:
                def __init__(self, data):
                    self._data = data
                    self._index = 0
                
                def has_next(self):
                    return self._index < len(self._data)
                
                def get_next(self):
                    if self.has_next():
                        result = self._data[self._index]
                        self._index += 1
                        return result
                    return None
            
            if "CREATE NODE TABLE" in query:
                return Result([])
            elif "CREATE (:LocationURI" in query:
                # Extract id from query
                import re
                match = re.search(r'id:\s*"([^"]+)"', query)
                if match:
                    uri = match.group(1)
                    # Avoid duplicates
                    if not any(item["uri"] == uri for item in self._data):
                        self._data.append({"uri": uri})
                return Result([])
            elif "MATCH (l:LocationURI)" in query:
                # Sort for ORDER BY
                sorted_data = sorted(self._data, key=lambda x: x["uri"])
                return Result([[item["uri"]] for item in sorted_data])
            else:
                return Result([])
        
        def close(self):
            pass
    
    DatabaseFactory = None
    kuzu = None


def create_test_database(db_path: str):
    """Create and setup test database with DDL schema"""
    if DatabaseFactory and kuzu:
        # Use real KuzuDB
        db_factory = DatabaseFactory()
        db = db_factory.create_database(db_path)
        conn = db.get_connection()
        
        try:
            # Check if table exists
            conn.execute("MATCH (l:LocationURI) RETURN COUNT(*)")
        except:
            # Create DDL schema
            conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
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
            conn.execute("""
                CREATE REL TABLE LOCATES (
                    FROM LocationURI TO RequirementEntity,
                    entity_type STRING DEFAULT 'requirement',
                    current BOOLEAN DEFAULT false
                )
            """)
        return db
    else:
        # Use mock for testing
        return MockDatabase(db_path)


def query_location_uris(db_path: str = None) -> list[dict]:
    """
    Query all LocationURI nodes from KuzuDB
    """
    if db_path is None:
        # Default path
        db_path = str(Path.home() / "bin" / "src" / "requirement" / "graph" / "rgl_db")
    
    db_path = Path(db_path)
    
    if not db_path.parent.exists():
        raise FileNotFoundError(f"Database directory not found: {db_path.parent}")
    
    # Create or connect to database
    db = create_test_database(str(db_path))
    
    if hasattr(db, 'get_connection'):
        conn = db.get_connection()
    else:
        conn = db
    
    # Execute DQL query
    result = conn.execute("MATCH (l:LocationURI) RETURN l.id AS uri ORDER BY l.id")
    
    # Collect results
    uris = []
    while result.has_next():
        row = result.get_next()
        if row:
            uris.append({"uri": row[0]})
    
    if hasattr(conn, 'close'):
        conn.close()
    
    return uris


def insert_location_uri(db_path: str, uri: str):
    """Insert a LocationURI for testing"""
    db = create_test_database(db_path)
    
    if hasattr(db, 'get_connection'):
        conn = db.get_connection()
    else:
        conn = db
    
    conn.execute(f'CREATE (:LocationURI {{id: "{uri}"}})')
    
    if hasattr(conn, 'close'):
        conn.close()

def main():
    """CLI entry point"""
    # Parse arguments
    db_path = None
    if len(sys.argv) > 1:
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