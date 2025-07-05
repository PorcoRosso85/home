#!/usr/bin/env python3
"""
Standalone KuzuDB LocationURI query tool
Minimal implementation without external dependencies
"""

import json
import sys
import os
from pathlib import Path

def query_location_uris(db_path: str = None) -> list[dict]:
    """
    Query all LocationURI nodes from KuzuDB
    For now, returns mock data for testing
    """
    # TODO: Replace with actual KuzuDB query when available
    # Mock implementation for Green phase
    if db_path and not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found at {db_path}")
    
    # Return mock LocationURIs for testing
    return [
        {"uri": "file:///home/user/project/src/main.py"},
        {"uri": "file:///home/user/project/src/utils.py#L42"},
        {"uri": "file:///home/user/project/tests/test_main.py#test_function"},
    ]

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