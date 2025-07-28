"""
Test embedding functionality with seed data - RED phase
Tests core embedding behavior without external dependencies
"""
import pytest
from typing import List, Dict, Any
from embed_pkg.types import ReferenceDict, EmbeddingResult, SaveResult, FindResult, SearchResult


def test_create_standalone_embedding_repository():
    """Test creating a standalone embedding repository without asvs_reference"""
    from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone
    
    # Create repository without base repository
    repo = create_embedding_repository_standalone()
    
    # Verify interface
    assert "save_with_embedding" in repo
    assert "find_with_embedding" in repo
    assert "find_similar_by_text" in repo
    assert "find_similar_by_embedding" in repo
    assert "update_all_embeddings" in repo


def test_save_reference_with_embedding_using_seeds():
    """Test saving reference with embedding using seed data"""
    from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone
    
    # Seed data
    reference: ReferenceDict = {
        "uri": "req:auth:001",
        "title": "User Authentication",
        "description": "Users must authenticate before accessing protected resources",
        "entity_type": "requirement"
    }
    
    # Create repository with seed embedder
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    
    # Save reference
    result: SaveResult = repo["save_with_embedding"](reference)
    
    # Verify
    assert result["success"] is True
    assert result["reference"] == reference
    assert result.get("error") is None


def test_find_reference_with_embedding():
    """Test finding reference returns embedding data"""
    from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone
    
    # Setup
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    reference: ReferenceDict = {
        "uri": "req:test:001",
        "title": "Test Requirement",
        "entity_type": "requirement"
    }
    repo["save_with_embedding"](reference)
    
    # Find
    result: FindResult = repo["find_with_embedding"]("req:test:001")
    
    # Verify
    assert result is not None
    assert result["uri"] == "req:test:001"
    assert "embedding" in result
    assert isinstance(result["embedding"], list)
    assert len(result["embedding"]) > 0


def test_find_similar_by_text_with_seeds():
    """Test semantic search using seed embeddings"""
    from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone
    
    # Setup with multiple references
    repo = create_embedding_repository_standalone(use_seed_embedder=True)
    
    seed_references = [
        {
            "uri": "req:auth:001",
            "title": "User Authentication",
            "description": "Users must log in with username and password",
            "entity_type": "requirement"
        },
        {
            "uri": "req:auth:002",
            "title": "Password Security",
            "description": "Passwords must be hashed and salted",
            "entity_type": "requirement"
        },
        {
            "uri": "req:perf:001",
            "title": "Response Time",
            "description": "System must respond within 200ms",
            "entity_type": "requirement"
        }
    ]
    
    for ref in seed_references:
        repo["save_with_embedding"](ref)
    
    # Search
    results: SearchResult = repo["find_similar_by_text"]("user login process", limit=2)
    
    # Verify
    assert len(results) == 2
    assert all("similarity_score" in r for r in results)
    assert all(0 <= r["similarity_score"] <= 1 for r in results)
    # Auth-related should rank higher
    assert any(r["uri"].startswith("req:auth") for r in results)


def test_seed_embedder_deterministic():
    """Test that seed embedder produces deterministic embeddings"""
    from embed_pkg.embeddings.seed_embedder import create_seed_embedder
    
    embedder = create_seed_embedder(seed=42)
    
    text = "This is a test text"
    
    # Generate embeddings multiple times
    result1 = embedder(text)
    result2 = embedder(text)
    
    # Should be deterministic
    assert result1["ok"] is True
    assert result2["ok"] is True
    assert result1["embedding"] == result2["embedding"]


def test_seed_embedder_different_texts():
    """Test that seed embedder produces different embeddings for different texts"""
    from embed_pkg.embeddings.seed_embedder import create_seed_embedder
    
    embedder = create_seed_embedder(seed=42, dimensions=128)
    
    # Different texts
    result1 = embedder("authentication and security")
    result2 = embedder("performance and response time")
    
    # Should produce different embeddings
    assert result1["ok"] is True
    assert result2["ok"] is True
    assert result1["embedding"] != result2["embedding"]
    
    # But same dimension
    assert len(result1["embedding"]) == 128
    assert len(result2["embedding"]) == 128


def test_repository_with_custom_storage():
    """Test repository with in-memory storage instead of database"""
    from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone
    
    # Create with in-memory storage
    storage: Dict[str, Any] = {}
    repo = create_embedding_repository_standalone(
        use_seed_embedder=True,
        storage_backend=storage
    )
    
    # Save reference
    reference: ReferenceDict = {
        "uri": "req:mem:001",
        "title": "Memory Test",
        "entity_type": "requirement"
    }
    repo["save_with_embedding"](reference)
    
    # Verify it's in storage
    assert "req:mem:001" in storage
    assert "embedding" in storage["req:mem:001"]