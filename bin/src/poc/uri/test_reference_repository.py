"""
Test ReferenceEntity Repository
Verifies integration with DDL migration and basic CRUD operations
"""
import pytest
from reference_repository import create_reference_repository


def test_repository_creation():
    """Test repository can be created with in-memory database"""
    repo = create_reference_repository(":memory:")
    
    # Should return error because schema not initialized
    assert isinstance(repo, dict)
    assert repo.get("type") == "DatabaseError"
    assert "SCHEMA_NOT_INITIALIZED" in str(repo)


def test_repository_with_schema():
    """Test repository operations with schema initialized"""
    import os
    import kuzu
    
    # Create in-memory database and apply schema
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Apply minimal schema
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM ReferenceEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'implements',
            confidence DOUBLE DEFAULT 1.0,
            created_at TIMESTAMP
        )
    """)
    
    # Skip schema check since we manually created it
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
    
    # Now create repository with the same database
    # Note: In real usage, we'd use the migration script
    repo = create_reference_repository(":memory:")
    
    # Clean up
    del os.environ["URI_SKIP_SCHEMA_CHECK"]
    
    # Should have all functions
    assert "save" in repo
    assert "find" in repo
    assert "find_all" in repo
    assert "add_implementation" in repo
    assert "find_implementations" in repo
    assert "search" in repo
    assert "execute" in repo


def test_crud_operations():
    """Test basic CRUD operations"""
    import os
    import kuzu
    
    # Setup
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Apply schema
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM ReferenceEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'implements',
            confidence DOUBLE DEFAULT 1.0,
            created_at TIMESTAMP
        )
    """)
    
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
    repo = create_reference_repository(existing_db=db)
    del os.environ["URI_SKIP_SCHEMA_CHECK"]
    
    # Test save
    reference = {
        "uri": "iso:9001:2015/clause/4.1",
        "title": "Understanding the organization and its context",
        "description": "The organization shall determine external and internal issues",
        "entity_type": "standard_clause"
    }
    
    result = repo["save"](reference)
    # Check if it's an error
    if isinstance(result, dict) and result.get("type") in ["DatabaseError", "ValidationError"]:
        assert False, f"Save failed: {result}"
    assert result == reference
    
    # Test find
    found = repo["find"]("iso:9001:2015/clause/4.1")
    assert found["uri"] == reference["uri"]
    assert found["title"] == reference["title"]
    
    # Test find_all
    all_refs = repo["find_all"]()
    assert len(all_refs) == 1
    assert all_refs[0]["uri"] == reference["uri"]
    
    # Test update
    reference["title"] = "Updated title"
    result = repo["save"](reference)
    assert result == reference
    
    found = repo["find"]("iso:9001:2015/clause/4.1")
    assert found["title"] == "Updated title"
    
    # Test not found
    not_found = repo["find"]("non-existent")
    assert not_found["type"] == "NotFoundError"


def test_implementation_relationships():
    """Test IMPLEMENTS relationship management"""
    import os
    import kuzu
    
    # Setup
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Apply schema
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM ReferenceEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'implements',
            confidence DOUBLE DEFAULT 1.0,
            created_at TIMESTAMP
        )
    """)
    
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
    repo = create_reference_repository(existing_db=db)
    del os.environ["URI_SKIP_SCHEMA_CHECK"]
    
    # Create two references
    spec = {
        "uri": "iso:9001:2015/clause/4.1",
        "title": "Understanding context",
        "entity_type": "standard_clause"
    }
    
    impl = {
        "uri": "company:acme/proc/context-analysis",
        "title": "Context Analysis Procedure",
        "entity_type": "procedure"
    }
    
    repo["save"](spec)
    repo["save"](impl)
    
    # Add implementation relationship
    result = repo["add_implementation"](
        impl["uri"], 
        spec["uri"],
        "procedural",
        0.95
    )
    assert result.get("success") == True
    
    # Find implementations
    outgoing = repo["find_implementations"](impl["uri"], "outgoing")
    assert len(outgoing) == 1
    assert outgoing[0]["reference"]["uri"] == spec["uri"]
    assert outgoing[0]["relationship"]["confidence"] == 0.95
    
    incoming = repo["find_implementations"](spec["uri"], "incoming")
    assert len(incoming) == 1
    assert incoming[0]["reference"]["uri"] == impl["uri"]
    
    # Test relationship to non-existent reference
    result = repo["add_implementation"](
        impl["uri"],
        "non-existent",
        "procedural"
    )
    assert result["type"] == "NotFoundError"


def test_search_functionality():
    """Test search functionality"""
    import os
    import kuzu
    
    # Setup
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Apply schema
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
    repo = create_reference_repository(existing_db=db)
    del os.environ["URI_SKIP_SCHEMA_CHECK"]
    
    # Create test data
    references = [
        {
            "uri": "iso:9001:2015/clause/4.1",
            "title": "Understanding the organization and its context",
            "description": "Determine external and internal issues",
            "entity_type": "standard_clause"
        },
        {
            "uri": "iso:9001:2015/clause/4.2",
            "title": "Understanding needs and expectations",
            "description": "Determine interested parties and their requirements",
            "entity_type": "standard_clause"
        },
        {
            "uri": "company:acme/proc/context",
            "title": "Context Analysis Procedure",
            "description": "Procedure for analyzing organizational context",
            "entity_type": "procedure"
        }
    ]
    
    for ref in references:
        repo["save"](ref)
    
    # Search by title
    results = repo["search"]("Understanding")
    assert len(results) == 2
    assert all("Understanding" in r["title"] for r in results)
    
    # Search by description
    results = repo["search"]("context")
    assert len(results) == 2
    
    # Search with no results
    results = repo["search"]("nonexistent")
    assert len(results) == 0


def test_validation_errors():
    """Test validation error handling"""
    import os
    import kuzu
    
    # Setup
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Apply schema
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
    repo = create_reference_repository(existing_db=db)
    del os.environ["URI_SKIP_SCHEMA_CHECK"]
    
    # Test missing required field
    invalid_ref = {
        "title": "Missing URI",
        "entity_type": "test"
    }
    
    result = repo["save"](invalid_ref)
    assert result["type"] == "ValidationError"
    assert result["field"] == "uri"
    assert result["constraint"] == "required"


if __name__ == "__main__":
    # Run basic tests
    print("Testing repository creation...")
    test_repository_creation()
    print("✓ Repository creation test passed")
    
    print("\nTesting repository with schema...")
    test_repository_with_schema()
    print("✓ Repository with schema test passed")
    
    print("\nTesting CRUD operations...")
    test_crud_operations()
    print("✓ CRUD operations test passed")
    
    print("\nTesting implementation relationships...")
    test_implementation_relationships()
    print("✓ Implementation relationships test passed")
    
    print("\nTesting search functionality...")
    test_search_functionality()
    print("✓ Search functionality test passed")
    
    print("\nTesting validation errors...")
    test_validation_errors()
    print("✓ Validation errors test passed")
    
    print("\n✅ All tests passed!")