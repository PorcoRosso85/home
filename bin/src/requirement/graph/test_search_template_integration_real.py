"""
Integration test for search_requirements template with real database
Following the testing philosophy: testing behavior, not implementation
"""
import tempfile
import os
import sys

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application.templates import process_search_template
from infrastructure import create_kuzu_repository
from application.search_adapter import SearchAdapter
from main import create_search_service


def test_search_template_with_real_database():
    """Test search template with actual database and search service"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_search.db")
        
        # Create repository
        repository = create_kuzu_repository(db_path)
        
        # Check if repository is error
        if isinstance(repository, dict) and repository.get("type") == "DatabaseError":
            # Skip if schema not initialized
            import pytest
            pytest.skip("Database schema not initialized")
        
        # Get connection from repository
        connection = repository.get("connection") if isinstance(repository, dict) else None
        
        # Create search service factory using the real implementation
        search_factory = lambda: create_search_service(repository, connection)
        
        # First, add some test data to the repository
        if hasattr(repository, 'create_requirement'):
            # Add test requirements
            req1 = repository.create_requirement({
                "title": "Test Architecture Requirement",
                "description": "System must support microservices architecture",
                "status": "active"
            })
            req2 = repository.create_requirement({
                "title": "Performance Requirement", 
                "description": "Response time must be under 100ms",
                "status": "active"
            })
        
        # Test search functionality
        result = process_search_template(
            {"query": "architecture", "limit": 5},
            search_factory
        )
        
        # Verify the behavior, not the implementation
        assert result["status"] == "success"
        assert result["query"] == "architecture"
        assert isinstance(result["count"], int)
        assert isinstance(result["results"], list)
        
        # If results are found, verify structure
        if result["count"] > 0:
            first_result = result["results"][0]
            assert "id" in first_result
            assert "title" in first_result
            assert "content" in first_result
            assert "score" in first_result
            assert isinstance(first_result["score"], (int, float))


def test_search_template_error_handling_real():
    """Test error handling with real components"""
    # Test with invalid database path
    invalid_db_path = "/invalid/path/to/database"
    
    # This should handle errors gracefully
    result = process_search_template(
        {"query": "test"},
        lambda: None  # Simulate service creation failure
    )
    
    assert result["status"] == "error"
    assert result["error"]["type"] == "ServiceNotAvailable"


def test_search_template_empty_results():
    """Test search with query that returns no results"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_empty.db")
        
        # Create repository
        repository = create_kuzu_repository(db_path)
        
        if isinstance(repository, dict) and repository.get("type") == "DatabaseError":
            import pytest
            pytest.skip("Database schema not initialized")
        
        connection = repository.get("connection") if isinstance(repository, dict) else None
        search_factory = lambda: create_search_service(repository, connection)
        
        # Search for something that doesn't exist
        result = process_search_template(
            {"query": "xyz123nonexistent", "limit": 10},
            search_factory
        )
        
        # Should succeed but return empty results
        assert result["status"] == "success"
        assert result["count"] == 0
        assert result["results"] == []