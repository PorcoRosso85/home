#!/usr/bin/env python3
"""
Minimal versioning integration test that can run without nix
"""

import tempfile
import os
import sys
import json

# Add parent directories to path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

# Test environment setup
os.environ['RGL_SKIP_SCHEMA_CHECK'] = 'true'

def test_versioning_through_api():
    """Test versioning through the API without full main.py"""
    from requirement.graph.infrastructure.database_factory import create_database, create_connection
    from requirement.graph.infrastructure.ddl_schema_manager import DDLSchemaManager
    from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
    from requirement.graph.infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
    from requirement.graph.infrastructure.query_validator import QueryValidator
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"
        os.environ["RGL_DB_PATH"] = db_path
        
        print("=== Setting up test environment ===")
        
        # Create database and apply schema
        db = create_database(path=db_path)
        conn = create_connection(db)
        
        manager = DDLSchemaManager(conn)
        schema_path = Path(current_dir) / "ddl" / "migrations" / "3.2.0_current.cypher"
        
        success, results = manager.apply_schema(str(schema_path))
        if not success:
            print("Failed to apply schema!")
            return False
        print(f"Schema applied: {len(results)} statements")
        
        # Create repository and versioned executor
        repo = create_kuzu_repository(db_path)
        versioned_executor = create_versioned_cypher_executor(repo)
        validator = QueryValidator()
        
        print("\n=== Testing versioned CREATE ===")
        
        # Test 1: Create versioned requirement
        create_request = {
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'REQ-001',
                title: 'ユーザー認証機能',
                description: '安全なログイン機能を提供'
            })
            """
        }
        
        # Validate query first
        is_valid, error = validator.validate(create_request["query"])
        if not is_valid:
            print(f"Query validation failed: {error}")
            return False
        
        result = versioned_executor["execute"](create_request)
        print(f"Create result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("status") != "success":
            print(f"Create failed: {result}")
            return False
        
        # Check if versioning worked
        data = result.get("data", [])
        metadata = result.get("metadata", {})
        
        print(f"\nData: {data}")
        print(f"Metadata: {metadata}")
        
        # For versioned create, we expect the data to contain version info
        if data and len(data) > 0 and len(data[0]) >= 3:
            print(f"Version number: {data[0][2]}")  # Third element should be version
            if data[0][2] != 1:
                print("ERROR: Expected version 1 for new requirement")
                return False
        else:
            print("ERROR: No version data returned")
            return False
        
        print("\n=== Testing versioned UPDATE ===")
        
        # Test 2: Update versioned requirement
        update_request = {
            "type": "cypher",
            "query": """
            MATCH (r:RequirementEntity {id: 'REQ-001'})
            SET r.description = '二要素認証を含む安全なログイン機能'
            RETURN r
            """,
            "metadata": {
                "author": "security_team",
                "reason": "セキュリティ要件の強化"
            }
        }
        
        # Validate and execute update
        is_valid, error = validator.validate(update_request["query"])
        if not is_valid:
            print(f"Update query validation failed: {error}")
            return False
        
        result = versioned_executor["execute"](update_request)
        print(f"\nUpdate result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("status") != "success":
            print(f"Update failed: {result}")
            return False
        
        # Check version incremented
        data = result.get("data", [])
        metadata = result.get("metadata", {})
        
        print(f"\nUpdate data: {data}")
        print(f"Update metadata: {metadata}")
        
        # Check from metadata
        if metadata.get("version") == 2 and metadata.get("previous_version") == 1:
            print(f"Version correctly incremented to 2")
        else:
            print("ERROR: Version not incremented properly")
            print(f"Expected version=2, previous_version=1")
            print(f"Got: version={metadata.get('version')}, previous_version={metadata.get('previous_version')}")
            return False
        
        print("\n=== All tests passed! ===")
        return True

if __name__ == "__main__":
    print("Running minimal versioning integration test...")
    success = test_versioning_through_api()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)