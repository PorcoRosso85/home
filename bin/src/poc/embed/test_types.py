"""
Test for type definitions - RED phase
Ensures type contracts are properly defined
"""
import pytest
from typing import TYPE_CHECKING

def test_reference_dict_structure():
    """Test that ReferenceDict has required fields"""
    from embed_pkg.types import ReferenceDict
    
    # Test creating a valid reference
    reference: ReferenceDict = {
        "uri": "req:test:001",
        "title": "Test Requirement",
        "entity_type": "requirement"
    }
    
    # Optional fields
    reference_with_optional: ReferenceDict = {
        "uri": "req:test:002", 
        "title": "Test with Description",
        "description": "A detailed description",
        "entity_type": "requirement"
    }
    
    assert reference["uri"] == "req:test:001"
    assert reference_with_optional.get("description") == "A detailed description"


def test_embedding_result_structure():
    """Test that EmbeddingResult has proper success/error structure"""
    from embed_pkg.types import EmbeddingSuccess, EmbeddingError
    
    # Success case
    success: EmbeddingSuccess = {
        "ok": True,
        "embedding": [0.1, 0.2, 0.3],
        "text": "sample text",
        "model": "test-model"
    }
    
    # Error case
    error: EmbeddingError = {
        "ok": False,
        "error": "Model loading failed",
        "details": {"model": "test-model", "reason": "not found"}
    }
    
    assert success["ok"] is True
    assert len(success["embedding"]) == 3
    assert error["ok"] is False
    assert "error" in error


def test_repository_result_types():
    """Test repository operation result types"""
    from embed_pkg.types import SaveResult, FindResult, SearchResult
    
    # Save success
    save_success: SaveResult = {
        "success": True,
        "reference": {
            "uri": "req:test:001",
            "title": "Saved Reference",
            "entity_type": "requirement"
        }
    }
    
    # Find result (can be None)
    find_result: FindResult = {
        "uri": "req:test:001",
        "title": "Found Reference", 
        "entity_type": "requirement",
        "embedding": [0.1, 0.2, 0.3]
    }
    
    # Search results
    search_results: SearchResult = [
        {
            "uri": "req:test:001",
            "title": "Match 1",
            "entity_type": "requirement", 
            "similarity_score": 0.95
        },
        {
            "uri": "req:test:002",
            "title": "Match 2",
            "entity_type": "requirement",
            "similarity_score": 0.87
        }
    ]
    
    assert save_success["success"] is True
    assert find_result is not None and "embedding" in find_result
    assert len(search_results) == 2
    assert all("similarity_score" in r for r in search_results)


def test_error_types():
    """Test common error type definitions"""
    from embed_pkg.types import DatabaseError, ValidationError, ModelError
    
    db_error: DatabaseError = {
        "type": "database_error",
        "message": "Connection failed",
        "details": {"db_path": "/tmp/test.db"}
    }
    
    validation_error: ValidationError = {
        "type": "validation_error", 
        "message": "Invalid URI format",
        "field": "uri",
        "value": "invalid-uri"
    }
    
    model_error: ModelError = {
        "type": "model_error",
        "message": "Model loading failed",
        "model_name": "test-model",
        "details": {"reason": "file not found"}
    }
    
    assert db_error["type"] == "database_error"
    assert validation_error["field"] == "uri"
    assert model_error["model_name"] == "test-model"