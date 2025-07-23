#!/usr/bin/env python3
"""
Integration test demonstrating FTS package works correctly
This can be used to verify the package after build fixes
"""

import sys
try:
    from fts_kuzu import create_fts
    print("✓ Successfully imported fts_kuzu.create_fts")
except ImportError as e:
    print(f"✗ Failed to import fts_kuzu: {e}")
    sys.exit(1)

# Test basic functionality
try:
    # Create file-based FTS instance (workaround for connection issue)
    import tempfile
    import os
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_fts.db")
    
    fts = create_fts(db_path=db_path, in_memory=False)
    print(f"✓ Created FTS instance (using {db_path})")
    
    # Test indexing
    documents = [
        {"id": "req001", "content": "User authentication system with OAuth2"},
        {"id": "req002", "content": "Database connection pooling for performance"},
        {"id": "req003", "content": "Authentication via JWT tokens"},
    ]
    
    result = fts.index(documents)
    if result["ok"]:
        print(f"✓ Indexed {result['indexed_count']} documents")
    else:
        print(f"✗ Indexing failed: {result}")
        sys.exit(1)
    
    # Test searching
    search_result = fts.search("authentication", limit=2)
    if search_result["ok"]:
        print(f"✓ Search found {len(search_result['results'])} results")
        for doc in search_result["results"]:
            print(f"  - {doc['id']}: score={doc['score']:.2f}")
    else:
        print(f"✗ Search failed: {search_result}")
        sys.exit(1)
    
    # Close connection
    fts.close()
    print("✓ Closed FTS connection")
    
    # Cleanup temp directory
    import shutil
    shutil.rmtree(temp_dir)
    print(f"✓ Cleaned up temp directory")
    
    print("\n✅ All integration tests passed!")
    
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)