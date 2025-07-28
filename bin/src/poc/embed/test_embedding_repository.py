"""
Test file for embedding repository - RED phase
Tests verify embedding functionality for references
Following testing.md conventions: test behavior, not implementation
"""
import pytest
from typing import Dict, Any, List, Union
from unittest.mock import MagicMock, patch
from embed_pkg.embedding_repository import create_embedding_repository


def test_save_reference_with_embedding_success():
    """Test that a reference can be saved with its text embedding"""
    # Arrange
    repository = create_embedding_repository()
    reference = {
        "uri": "req.security.auth.001",
        "title": "User Authentication Required",
        "description": "All API endpoints must implement authentication",
        "entity_type": "requirement"
    }
    
    # Act
    result = repository["save_with_embedding"](reference)
    
    # Assert
    assert result == reference  # Should return the saved reference
    
    # Verify embedding was stored
    stored = repository["find_with_embedding"](reference["uri"])
    assert stored["uri"] == reference["uri"]
    assert "embedding" in stored
    assert isinstance(stored["embedding"], list)
    assert len(stored["embedding"]) > 0


def test_save_reference_with_embedding_handles_model_error():
    """Test that model loading errors are properly handled"""
    # Arrange
    repository = create_embedding_repository(
        model_name="non-existent-model"
    )
    reference = {
        "uri": "req.test.001",
        "title": "Test Requirement",
        "description": "Test description",
        "entity_type": "requirement"
    }
    
    # Act
    result = repository["save_with_embedding"](reference)
    
    # Assert
    assert result["type"] == "DatabaseError"
    assert "embedding" in result["message"].lower()
    assert result["details"]["cause"] == "ModelLoadError"


def test_find_similar_references_by_text():
    """Test finding similar references using text similarity"""
    # Arrange
    repository = create_embedding_repository()
    
    # Save some references with embeddings
    refs = [
        {
            "uri": "req.auth.001",
            "title": "Authentication Required",
            "description": "Users must authenticate before accessing resources",
            "entity_type": "requirement"
        },
        {
            "uri": "req.auth.002", 
            "title": "Password Policy",
            "description": "Passwords must be at least 12 characters long",
            "entity_type": "requirement"
        },
        {
            "uri": "req.logging.001",
            "title": "Audit Logging",
            "description": "All authentication attempts must be logged",
            "entity_type": "requirement"
        }
    ]
    
    for ref in refs:
        repository["save_with_embedding"](ref)
    
    # Act
    similar = repository["find_similar_by_text"](
        "user login and authentication",
        limit=2
    )
    
    # Assert
    assert len(similar) == 2
    assert similar[0]["uri"] in ["req.auth.001", "req.auth.002"]
    assert all("similarity_score" in item for item in similar)
    assert all(0 <= item["similarity_score"] <= 1 for item in similar)


def test_find_similar_references_with_empty_database():
    """Test finding similar references when database is empty"""
    # Arrange
    repository = create_embedding_repository()
    
    # Act
    similar = repository["find_similar_by_text"]("authentication")
    
    # Assert
    assert similar == []


def test_update_embeddings_for_existing_references():
    """Test updating embeddings for references without embeddings"""
    # Arrange
    repository = create_embedding_repository()
    
    # Simulate existing references without embeddings
    references = [
        {
            "uri": "req.old.001",
            "title": "Legacy Requirement 1",
            "description": "Old requirement without embedding",
            "entity_type": "requirement"
        },
        {
            "uri": "req.old.002",
            "title": "Legacy Requirement 2", 
            "description": "Another old requirement",
            "entity_type": "requirement"
        }
    ]
    
    # Save without embeddings (simulating legacy data)
    for ref in references:
        repository["save"](ref)  # Use base save, not save_with_embedding
    
    # Act
    result = repository["update_all_embeddings"]()
    
    # Assert
    assert result["updated_count"] == 2
    assert result["error_count"] == 0
    
    # Verify embeddings were added
    for ref in references:
        stored = repository["find_with_embedding"](ref["uri"])
        assert "embedding" in stored


def test_embedding_generation_with_encoding_error():
    """Test handling of text encoding errors during embedding generation"""
    # Arrange
    repository = create_embedding_repository()
    reference = {
        "uri": "req.unicode.001",
        "title": "Unicode Test \ud800",  # Invalid unicode surrogate
        "description": "Test with problematic characters",
        "entity_type": "requirement"
    }
    
    # Act
    result = repository["save_with_embedding"](reference)
    
    # Assert - Should handle gracefully, possibly skip embedding
    # Either saved without embedding or returned error
    if isinstance(result, dict) and result.get("type") == "DatabaseError":
        # Database error is acceptable for invalid unicode
        assert "cast" in result["message"].lower() or "encoding" in result["message"].lower()
    else:
        # Saved successfully
        assert result["uri"] == reference["uri"]
        # Check if embedding was skipped
        stored = repository["find"](reference["uri"])
        assert stored["uri"] == reference["uri"]


def test_find_similar_with_invalid_limit():
    """Test that invalid limit values are handled properly"""
    # Arrange
    repository = create_embedding_repository()
    
    # Act & Assert
    # Negative limit
    result = repository["find_similar_by_text"]("test", limit=-1)
    assert isinstance(result, dict) and result["type"] == "ValidationError"
    assert result["field"] == "limit"
    
    # Zero limit
    result = repository["find_similar_by_text"]("test", limit=0)
    assert result == []
    
    # Very large limit (should work but return available results)
    result = repository["find_similar_by_text"]("test", limit=1000)
    assert isinstance(result, list)


def test_repository_initialization_with_custom_embedder():
    """Test repository can be initialized with custom embedding function"""
    # Arrange
    custom_embedder = MagicMock()
    custom_embedder.return_value = {
        "ok": True,
        "embeddings": [[0.1, 0.2, 0.3]],
        "model_name": "custom-model",
        "dimensions": 3
    }
    
    # Act
    repository = create_embedding_repository(embedder=custom_embedder)
    reference = {
        "uri": "req.custom.001",
        "title": "Test with custom embedder",
        "description": "Testing custom embedding function",
        "entity_type": "requirement"
    }
    result = repository["save_with_embedding"](reference)
    
    # Assert
    assert result == reference
    custom_embedder.assert_called_once()
    call_args = custom_embedder.call_args[0][0]
    assert isinstance(call_args, list)
    assert len(call_args) == 1
    assert reference["title"] in call_args[0] or reference["description"] in call_args[0]


def test_database_schema_includes_embedding_support():
    """Test that database schema properly supports embedding storage"""
    # Arrange
    repository = create_embedding_repository()
    
    # Act - Execute a query to check schema
    result = repository["execute"]("""
        MATCH (r:ReferenceEntity)
        RETURN r LIMIT 1
    """)
    
    # This test will fail in RED phase since schema doesn't exist yet
    # In GREEN phase, we'll need to ensure the schema supports:
    # - embedding property (LIST of DOUBLE)
    # - embedding_model property (STRING)
    # - embedding_updated_at property (TIMESTAMP)
    assert result["status"] == "success"


