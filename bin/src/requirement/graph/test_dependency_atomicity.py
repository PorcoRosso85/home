"""
Characterization tests for add_dependency function
Captures current behavior before refactoring

CURRENT BEHAVIOR DOCUMENTED:
1. Normal dependency creation works correctly
2. Self-reference prevention works correctly
3. Circular dependency prevention works correctly
4. Duplicate dependencies are handled idempotently (no duplicates created)
5. Race conditions:
   - Concurrent creation of same dependency can create duplicates (BUG)
   - Circular dependency checks work correctly even under concurrency
6. Error handling:
   - Empty IDs are accepted and create dependencies (BUG)
   - Non-existent nodes are accepted and create orphan relationships (BUG)
7. Dependency types and reasons are stored correctly

KNOWN ISSUES TO FIX:
- Race condition allows duplicate dependencies in concurrent scenarios
- No validation of node existence before creating dependencies
- Empty IDs are not rejected
"""
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .infrastructure.kuzu_repository import create_kuzu_repository
from .domain.errors import ValidationError, DatabaseError


@pytest.fixture
def repo():
    """Create an in-memory repository for testing"""
    import os
    # Skip schema check for testing
    os.environ['RGL_SKIP_SCHEMA_CHECK'] = 'true'
    
    result = create_kuzu_repository(":memory:")
    
    # Check if we got an error instead of repository
    if isinstance(result, dict) and result.get("type") in ["DatabaseError", "EnvironmentConfigError"]:
        pytest.fail(f"Failed to create repository: {result.get('message', 'Unknown error')}")
    
    # Initialize schema manually since we're skipping the check
    conn = result["connection"]
    
    # Create RequirementEntity table
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            status STRING,
            original_id STRING,
            version INT64,
            created_at STRING
        )
    """)
    
    # Create LocationURI table
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS LocationURI (
            id STRING PRIMARY KEY
        )
    """)
    
    # Create relationship tables
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS DEPENDS_ON (
            FROM RequirementEntity TO RequirementEntity,
            dependency_type STRING DEFAULT 'depends_on',
            reason STRING DEFAULT ''
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS LOCATES (
            FROM LocationURI TO RequirementEntity,
            entity_type STRING,
            current BOOLEAN,
            version INT64
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS CONTAINS_LOCATION (
            FROM LocationURI TO LocationURI,
            relation_type STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS PREVIOUS_VERSION (
            FROM RequirementEntity TO RequirementEntity
        )
    """)
    
    return result


@pytest.fixture
def sample_requirements(repo):
    """Create sample requirements for testing"""
    req1 = {
        "id": "req_001",
        "title": "Requirement 1",
        "description": "First requirement",
        "status": "active"
    }
    req2 = {
        "id": "req_002", 
        "title": "Requirement 2",
        "description": "Second requirement",
        "status": "active"
    }
    req3 = {
        "id": "req_003",
        "title": "Requirement 3", 
        "description": "Third requirement",
        "status": "active"
    }
    
    repo["save"](req1)
    repo["save"](req2)
    repo["save"](req3)
    
    return {"req1": req1, "req2": req2, "req3": req3}


class TestAddDependencyNormalBehavior:
    """Test normal dependency creation"""
    
    def test_create_simple_dependency(self, repo, sample_requirements):
        """Test creating a simple dependency between two requirements"""
        result = repo["add_dependency"]("req_001", "req_002")
        
        assert result["success"] is True
        assert result["from"] == "req_001"
        assert result["to"] == "req_002"
        
        # Verify dependency exists in database
        deps = repo["find_dependencies"]("req_001")
        assert len(deps) == 1
        assert deps[0]["requirement"]["id"] == "req_002"
    
    def test_create_dependency_with_type(self, repo, sample_requirements):
        """Test creating a dependency with specific type"""
        result = repo["add_dependency"]("req_001", "req_002", "implements")
        
        assert result["success"] is True
        
        # Verify dependency type is stored
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN dep.dependency_type as type
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == "implements"
    
    def test_create_dependency_with_reason(self, repo, sample_requirements):
        """Test creating a dependency with reason"""
        reason = "Required for authentication flow"
        result = repo["add_dependency"]("req_001", "req_002", "depends_on", reason)
        
        assert result["success"] is True
        
        # Verify reason is stored
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN dep.reason as reason
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == reason
    
    def test_create_chain_dependencies(self, repo, sample_requirements):
        """Test creating a chain of dependencies: req1 -> req2 -> req3"""
        result1 = repo["add_dependency"]("req_001", "req_002")
        result2 = repo["add_dependency"]("req_002", "req_003")
        
        assert result1["success"] is True
        assert result2["success"] is True
        
        # Verify chain exists
        deps_1 = repo["find_dependencies"]("req_001", depth=2)
        assert len(deps_1) == 2
        dep_ids = [dep["requirement"]["id"] for dep in deps_1]
        assert "req_002" in dep_ids
        assert "req_003" in dep_ids


class TestSelfReferencePrevention:
    """Test self-reference prevention"""
    
    def test_prevent_self_dependency(self, repo, sample_requirements):
        """Test that self-dependencies are prevented"""
        result = repo["add_dependency"]("req_001", "req_001")
        
        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert "Self dependency not allowed" in result["message"]
        assert result["field"] == "dependency"
        assert result["constraint"] == "no_self_dependency"
    
    def test_self_dependency_with_different_versions(self, repo):
        """Test self-dependency prevention with versioned requirements"""
        req = {
            "id": "req_versioned",
            "title": "Versioned Requirement",
            "description": "Test versioning",
            "status": "active"
        }
        
        # Save twice to create versions
        repo["save"](req)
        req["title"] = "Updated Versioned Requirement"
        repo["save"](req)
        
        # Try to create dependency between versions of same requirement
        result = repo["add_dependency"]("req_versioned", "req_versioned_v2")
        
        # Should succeed as they are different entities in the graph
        assert result["success"] is True


class TestCircularDependencyPrevention:
    """Test circular dependency prevention"""
    
    def test_prevent_direct_circular_dependency(self, repo, sample_requirements):
        """Test prevention of A -> B -> A circular dependency"""
        # Create A -> B
        result1 = repo["add_dependency"]("req_001", "req_002")
        assert result1["success"] is True
        
        # Try to create B -> A (should fail)
        result2 = repo["add_dependency"]("req_002", "req_001")
        
        assert isinstance(result2, dict)
        assert result2["type"] == "ValidationError"
        assert "Circular dependency detected" in result2["message"]
        assert result2["constraint"] == "no_circular_dependency"
    
    def test_prevent_indirect_circular_dependency(self, repo, sample_requirements):
        """Test prevention of A -> B -> C -> A circular dependency"""
        # Create chain A -> B -> C
        repo["add_dependency"]("req_001", "req_002")
        repo["add_dependency"]("req_002", "req_003")
        
        # Try to create C -> A (should fail)
        result = repo["add_dependency"]("req_003", "req_001")
        
        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert "Circular dependency detected" in result["message"]
    
    def test_complex_circular_dependency_prevention(self, repo):
        """Test prevention in complex dependency graphs"""
        # Create more requirements
        for i in range(1, 6):
            repo["save"]({
                "id": f"req_{i:03d}",
                "title": f"Requirement {i}",
                "description": f"Requirement number {i}",
                "status": "active"
            })
        
        # Create complex dependency structure
        # 1 -> 2 -> 3
        #      ↓    ↓
        #      4 -> 5
        repo["add_dependency"]("req_001", "req_002")
        repo["add_dependency"]("req_002", "req_003")
        repo["add_dependency"]("req_002", "req_004")
        repo["add_dependency"]("req_003", "req_005")
        repo["add_dependency"]("req_004", "req_005")
        
        # Try to create 5 -> 1 (should fail due to circular path)
        result = repo["add_dependency"]("req_005", "req_001")
        
        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert "Circular dependency detected" in result["message"]


class TestDuplicateDependencyPrevention:
    """Test duplicate dependency handling"""
    
    def test_duplicate_dependency_is_idempotent(self, repo, sample_requirements):
        """Test that duplicate dependencies are handled idempotently"""
        # Create dependency first time
        result1 = repo["add_dependency"]("req_001", "req_002", "depends_on", "First reason")
        assert result1["success"] is True
        
        # Try to create same dependency again
        result2 = repo["add_dependency"]("req_001", "req_002", "depends_on", "Second reason")
        assert result2["success"] is True
        
        # Verify only one dependency exists
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN count(dep) as count
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == 1
    
    def test_duplicate_with_different_types(self, repo, sample_requirements):
        """Test creating dependencies with different types"""
        # Create dependency with one type
        result1 = repo["add_dependency"]("req_001", "req_002", "depends_on")
        assert result1["success"] is True
        
        # Try with different type - should be idempotent (no new edge created)
        result2 = repo["add_dependency"]("req_001", "req_002", "implements")
        assert result2["success"] is True
        
        # Verify still only one dependency
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN count(dep) as count, collect(dep.dependency_type) as types
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == 1


class TestRaceConditionScenarios:
    """Test race condition scenarios (simulated with threading)"""
    
    def test_concurrent_dependency_creation(self, repo, sample_requirements):
        """Test concurrent creation of same dependency"""
        results = []
        errors = []
        
        def create_dependency():
            try:
                result = repo["add_dependency"]("req_001", "req_002")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads trying to create same dependency
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_dependency)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0
        
        # All results should be successful
        assert all(r["success"] is True for r in results if isinstance(r, dict) and "success" in r)
        
        # Verify only one dependency exists
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN count(dep) as count
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        # Current implementation allows duplicate dependencies in concurrent scenarios
        # This is a characterization test - documenting current behavior
        dep_count = query_result["data"][0][0]
        assert dep_count >= 1  # BUG: Should be exactly 1, but can be more due to race condition
    
    def test_concurrent_circular_dependency_check(self, repo, sample_requirements):
        """Test concurrent creation of circular dependencies"""
        results = []
        
        def create_forward_dependency():
            result = repo["add_dependency"]("req_001", "req_002")
            results.append(("forward", result))
        
        def create_backward_dependency():
            # Small delay to ensure forward dependency is likely created first
            time.sleep(0.01)
            result = repo["add_dependency"]("req_002", "req_001")
            results.append(("backward", result))
        
        # Run both operations concurrently
        thread1 = threading.Thread(target=create_forward_dependency)
        thread2 = threading.Thread(target=create_backward_dependency)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # One should succeed, one should fail with circular dependency error
        forward_results = [r for direction, r in results if direction == "forward"]
        backward_results = [r for direction, r in results if direction == "backward"]
        
        assert len(forward_results) == 1
        assert len(backward_results) == 1
        
        # Forward should succeed
        assert forward_results[0]["success"] is True
        
        # Backward should fail with circular dependency
        assert backward_results[0]["type"] == "ValidationError"
        assert "Circular dependency detected" in backward_results[0]["message"]
    
    def test_concurrent_complex_dependency_creation(self, repo):
        """Test concurrent creation of complex dependency graphs"""
        # Create 10 requirements
        for i in range(10):
            repo["save"]({
                "id": f"req_{i:03d}",
                "title": f"Requirement {i}",
                "description": f"Requirement number {i}",
                "status": "active"
            })
        
        results = []
        
        def create_dependencies(start_idx):
            """Each thread creates dependencies from one requirement to others"""
            for j in range(10):
                if start_idx != j:
                    result = repo["add_dependency"](f"req_{start_idx:03d}", f"req_{j:03d}")
                    results.append((start_idx, j, result))
        
        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(5):  # 5 threads each handling 2 requirements
                futures.append(executor.submit(create_dependencies, i))
            
            # Wait for all to complete
            for future in as_completed(futures):
                future.result()
        
        # Count successful and failed operations
        success_count = sum(1 for _, _, r in results if isinstance(r, dict) and r.get("success") is True)
        validation_errors = [r for _, _, r in results if isinstance(r, dict) and r.get("type") == "ValidationError"]
        
        # Should have some successes and some circular dependency failures
        assert success_count > 0
        assert len(validation_errors) > 0
        
        # All validation errors should be about circular dependencies
        assert all("Circular dependency detected" in e["message"] for e in validation_errors)


class TestErrorConditions:
    """Test error conditions and edge cases"""
    
    def test_dependency_with_nonexistent_source(self, repo):
        """Test creating dependency with non-existent source requirement"""
        # Create only target requirement
        repo["save"]({
            "id": "req_exists",
            "title": "Existing Requirement",
            "description": "This requirement exists",
            "status": "active"
        })
        
        # Try to create dependency from non-existent requirement
        result = repo["add_dependency"]("req_nonexistent", "req_exists")
        
        # Current implementation returns success even when nodes don't exist
        # This is a characterization test - documenting current behavior
        assert result["success"] is True  # BUG: Should fail but doesn't
    
    def test_dependency_with_nonexistent_target(self, repo):
        """Test creating dependency with non-existent target requirement"""
        # Create only source requirement
        repo["save"]({
            "id": "req_exists",
            "title": "Existing Requirement",
            "description": "This requirement exists",
            "status": "active"
        })
        
        # Try to create dependency to non-existent requirement
        result = repo["add_dependency"]("req_exists", "req_nonexistent")
        
        # Current implementation returns success even when nodes don't exist
        # This is a characterization test - documenting current behavior
        assert result["success"] is True  # BUG: Should fail but doesn't
    
    def test_dependency_with_empty_ids(self, repo):
        """Test creating dependency with empty or invalid IDs"""
        # Test with empty strings
        result1 = repo["add_dependency"]("", "req_001")
        # Current implementation returns success even with empty IDs
        # This is a characterization test - documenting current behavior
        assert result1["success"] is True  # BUG: Should fail but doesn't
        
        result2 = repo["add_dependency"]("req_001", "")
        assert result2["success"] is True  # BUG: Should fail but doesn't
    
    def test_dependency_with_special_characters(self, repo):
        """Test creating dependencies with IDs containing special characters"""
        # Create requirements with special characters in IDs
        req1 = {
            "id": "req-with-dash",
            "title": "Requirement with dash",
            "description": "Test special chars",
            "status": "active"
        }
        req2 = {
            "id": "req_with_underscore",
            "title": "Requirement with underscore", 
            "description": "Test special chars",
            "status": "active"
        }
        
        repo["save"](req1)
        repo["save"](req2)
        
        # Should work normally
        result = repo["add_dependency"]("req-with-dash", "req_with_underscore")
        assert result["success"] is True


class TestDependencyTypeAndReason:
    """Test dependency type and reason handling"""
    
    def test_default_dependency_type(self, repo, sample_requirements):
        """Test that default dependency type is 'depends_on'"""
        result = repo["add_dependency"]("req_001", "req_002")
        assert result["success"] is True
        
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN dep.dependency_type as type
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == "depends_on"
    
    def test_empty_reason_handling(self, repo, sample_requirements):
        """Test that empty reason is stored as empty string"""
        result = repo["add_dependency"]("req_001", "req_002", "depends_on", "")
        assert result["success"] is True
        
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN dep.reason as reason
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == ""
    
    def test_long_reason_text(self, repo, sample_requirements):
        """Test handling of long reason text"""
        long_reason = "This is a very long reason " * 50  # ~1350 characters
        result = repo["add_dependency"]("req_001", "req_002", "depends_on", long_reason)
        
        assert result["success"] is True
        
        # Verify full reason is stored
        query_result = repo["execute"]("""
            MATCH (from:RequirementEntity {id: $from_id})-[dep:DEPENDS_ON]->(to:RequirementEntity {id: $to_id})
            RETURN dep.reason as reason
        """, {"from_id": "req_001", "to_id": "req_002"})
        
        assert query_result["data"][0][0] == long_reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])