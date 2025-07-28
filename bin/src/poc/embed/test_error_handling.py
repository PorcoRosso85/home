"""
Test error handling patterns - advanced error cases
"""
import pytest
from embed_pkg.types import is_embedding_error, is_error_result, ErrorResult
from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone


def test_embedder_initialization_error():
    """Test handling embedder initialization failures"""
    from embed_pkg.embeddings.base import create_embedder
    
    # Try to create with invalid embedder type
    result = create_embedder("invalid-model", embedder_type="invalid-type")
    
    assert is_embedding_error(result)
    assert result["ok"] is False
    assert "error" in result
    assert "Unknown embedder type" in result["error"]


def test_repository_with_failing_embedder():
    """Test repository behavior when embedder fails"""
    # Create a mock failing embedder
    def failing_embedder(text):
        return {
            "ok": False,
            "error": "Mock embedder failure",
            "details": {"reason": "test"}
        }
    
    repo = create_embedding_repository_standalone(
        custom_embedder=failing_embedder
    )
    
    reference = {
        "uri": "req:fail:001",
        "title": "Test",
        "entity_type": "requirement"
    }
    
    result = repo["save_with_embedding"](reference)
    
    # Should handle embedder failure gracefully
    assert result["success"] is False
    assert "error" in result
    assert "Mock embedder failure" in result["error"]


def test_invalid_reference_validation():
    """Test validation of invalid reference data"""
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    
    # Missing required field
    invalid_ref = {
        "title": "Missing URI",
        "entity_type": "requirement"
    }
    
    result = repo["save_with_embedding"](invalid_ref)
    
    assert result["success"] is False
    assert "error" in result
    assert "uri" in result["error"].lower()


def test_empty_text_embedding():
    """Test handling of empty text for embedding"""
    from embed_pkg.embeddings.seed_embedder import create_seed_embedder
    
    embedder = create_seed_embedder()
    
    # Empty string
    result = embedder("")
    assert result["ok"] is True  # Should handle gracefully
    assert len(result["embedding"]) > 0
    
    # Whitespace only
    result = embedder("   ")
    assert result["ok"] is True
    assert len(result["embedding"]) > 0


def test_unicode_text_handling():
    """Test handling of various Unicode texts"""
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    
    unicode_refs = [
        {
            "uri": "req:unicode:001",
            "title": "日本語のテスト",
            "description": "これはテストです",
            "entity_type": "requirement"
        },
        {
            "uri": "req:unicode:002", 
            "title": "Emoji test 🚀💻🔒",
            "description": "Testing with emojis",
            "entity_type": "requirement"
        },
        {
            "uri": "req:unicode:003",
            "title": "Mixed языки test",
            "description": "Mixing multiple scripts",
            "entity_type": "requirement"
        }
    ]
    
    for ref in unicode_refs:
        result = repo["save_with_embedding"](ref)
        assert result["success"] is True
    
    # Search with Unicode
    results = repo["find_similar_by_text"]("テスト", limit=3)
    assert len(results) > 0


def test_error_type_guards():
    """Test type guard functions for error narrowing"""
    from embed_pkg.types import is_embedding_error, is_error_result
    
    # Embedding error
    emb_error = {"ok": False, "error": "test"}
    assert is_embedding_error(emb_error) is True
    
    emb_success = {"ok": True, "embedding": [0.1], "text": "test", "model": "test"}
    assert is_embedding_error(emb_success) is False
    
    # General error
    db_error: ErrorResult = {
        "type": "database_error",
        "message": "Connection failed"
    }
    assert is_error_result(db_error) is True
    
    non_error = {"data": "value"}
    assert is_error_result(non_error) is False


def test_batch_update_error_handling():
    """Test error handling in batch operations"""
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    
    # Add mix of valid and problematic references
    refs = [
        {"uri": "req:batch:001", "title": "Normal", "entity_type": "requirement"},
        {"uri": "req:batch:002", "title": "", "entity_type": "requirement"},  # Empty title
        {"uri": "req:batch:003", "title": "Another", "entity_type": "requirement"},
    ]
    
    for ref in refs:
        repo["save_with_embedding"](ref)
    
    # Update all embeddings
    result = repo["update_all_embeddings"]()
    
    # Should complete despite individual failures
    assert "total" in result
    assert "updated" in result
    assert "failed" in result
    assert result["total"] == 3


def test_similarity_search_edge_cases():
    """Test edge cases in similarity search"""
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    
    # Empty repository search
    results = repo["find_similar_by_text"]("test", limit=5)
    assert results == []
    
    # Add one reference
    repo["save_with_embedding"]({
        "uri": "req:single:001",
        "title": "Single Reference",
        "entity_type": "requirement"
    })
    
    # Search with limit higher than available
    results = repo["find_similar_by_text"]("test", limit=10)
    assert len(results) == 1
    
    # Search with limit 0
    results = repo["find_similar_by_text"]("test", limit=0)
    assert results == []