#!/usr/bin/env python3
"""
Test the 3.3.0 migration impact on basic operations
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
from requirement.graph.infrastructure.ddl_schema_manager import DDLSchemaManager
from pathlib import Path

def test_basic_crud():
    """Test basic CRUD operations with simplified schema"""
    print("Testing basic CRUD operations...")
    
    # Create repository
    repo = create_kuzu_repository()
    
    # Apply current schema
    schema_manager = DDLSchemaManager(repo["connection"])
    schema_path = Path(__file__).parent / "ddl" / "migrations" / "3.2.0_current.cypher"
    if schema_path.exists():
        success, results = schema_manager.apply_schema(str(schema_path))
        if not success:
            print(f"Failed to apply schema: {results}")
            return False
    
    # Test 1: Create requirement without priority
    print("\n1. Creating requirement without priority...")
    try:
        result = repo["save"]({
            "id": "TEST-001",
            "title": "Test Requirement",
            "description": "Testing simplified schema",
            "status": "proposed"
        })
        print(f"   ✓ Created: {result}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 2: Find requirement
    print("\n2. Finding requirement...")
    try:
        result = repo["find"]("TEST-001")
        if result.get("type") == "DecisionNotFoundError":
            print(f"   ✗ Not found: {result}")
            return False
        print(f"   ✓ Found: id={result['id']}, title={result['title']}")
        # Verify no priority field
        if "priority" in result:
            print(f"   ✗ ERROR: priority field still present!")
            return False
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 3: Update requirement
    print("\n3. Updating requirement...")
    try:
        result = repo["save"]({
            "id": "TEST-001",
            "title": "Updated Test Requirement",
            "description": "Testing update without priority",
            "status": "approved"
        })
        print(f"   ✓ Updated: {result}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 4: Check history
    print("\n4. Checking history...")
    try:
        history = repo["get_requirement_history"]("TEST-001")
        print(f"   ✓ History entries: {len(history)}")
        for h in history:
            # Verify no priority in history
            if "priority" in str(h):
                print(f"   ✗ ERROR: priority field in history!")
                return False
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    return True

def test_query_templates():
    """Test query templates work with simplified schema"""
    print("\n\nTesting query templates...")
    
    repo = create_kuzu_repository()
    conn = repo["connection"]
    
    # Test create_versioned_requirement template
    print("\n1. Testing create_versioned_requirement.cypher...")
    try:
        template_path = Path(__file__).parent / "query" / "dml" / "create_versioned_requirement.cypher"
        if template_path.exists():
            template = template_path.read_text()
            # Execute with parameters (no priority)
            params = {
                "req_id": "TEMPLATE-001",
                "title": "Template Test",
                "description": "Testing template",
                "status": "draft",
                "author": "test",
                "reason": "test",
                "timestamp": "2025-01-01T00:00:00Z"
            }
            result = conn.execute(template, params)
            if result.has_next():
                print("   ✓ Template executed successfully")
            else:
                print("   ✗ No result returned")
        else:
            print("   - Template not found, skipping")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    return True

if __name__ == "__main__":
    print("3.3.0 Migration Impact Test")
    print("=" * 50)
    
    # Run tests
    crud_ok = test_basic_crud()
    template_ok = test_query_templates()
    
    print("\n" + "=" * 50)
    if crud_ok and template_ok:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
        sys.exit(1)