#!/usr/bin/env python3
"""
Demo script for standalone embedding repository
Shows usage without asvs_reference dependency
"""
from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone as create_embedding_repository_standalone
from embed_pkg.types import ReferenceDict


def main():
    print("=== Standalone Embedding Repository Demo ===\n")
    
    # Create repository with seed embedder (no ML dependencies)
    print("1. Creating repository with seed embedder...")
    repo = create_embedding_repository_standalone(
        use_seed_embedder=True,
        seed=42,
        dimensions=384
    )
    print("✓ Repository created\n")
    
    # Sample references
    references = [
        {
            "uri": "req:auth:001",
            "title": "User Authentication Required",
            "description": "All users must authenticate with username and password before accessing protected resources",
            "entity_type": "requirement"
        },
        {
            "uri": "req:auth:002",
            "title": "Multi-Factor Authentication",
            "description": "High-privilege users must use MFA with TOTP or hardware tokens",
            "entity_type": "requirement"
        },
        {
            "uri": "req:sec:001",
            "title": "Encryption at Rest",
            "description": "All sensitive data must be encrypted using AES-256 when stored",
            "entity_type": "requirement"
        },
        {
            "uri": "req:perf:001",
            "title": "Response Time Requirement",
            "description": "API endpoints must respond within 200ms for 95% of requests",
            "entity_type": "requirement"
        }
    ]
    
    # Save references with embeddings
    print("2. Saving references with embeddings...")
    for ref in references:
        result = repo["save_with_embedding"](ref)
        if result["success"]:
            print(f"   ✓ Saved: {ref['uri']} - {ref['title']}")
        else:
            print(f"   ✗ Failed: {ref['uri']} - {result['error']}")
    print()
    
    # Find a specific reference
    print("3. Finding reference with embedding...")
    found = repo["find_with_embedding"]("req:auth:001")
    if found:
        print(f"   ✓ Found: {found['uri']} - {found['title']}")
        print(f"   Embedding dimensions: {len(found.get('embedding', []))}")
    print()
    
    # Semantic search
    print("4. Semantic search for similar references...")
    search_queries = [
        "user login and authentication process",
        "data security and encryption",
        "system performance requirements"
    ]
    
    for query in search_queries:
        print(f"\n   Query: '{query}'")
        results = repo["find_similar_by_text"](query, limit=2)
        for i, match in enumerate(results, 1):
            print(f"   {i}. {match['uri']} - {match['title']}")
            print(f"      Similarity: {match['similarity_score']:.3f}")
    
    # Direct embedding search
    print("\n5. Direct embedding similarity search...")
    # Get embedding from first reference
    ref_embedding = repo["find_with_embedding"]("req:auth:001")["embedding"]
    similar = repo["find_similar_by_embedding"](ref_embedding, limit=3)
    print(f"   References similar to 'req:auth:001':")
    for match in similar:
        print(f"   - {match['uri']}: {match['similarity_score']:.3f}")
    
    # Using custom storage backend
    print("\n6. Using custom storage backend...")
    custom_storage = {}
    repo2 = create_embedding_repository_standalone(
        storage_backend=custom_storage,
        use_seed_embedder=True
    )
    
    test_ref = {
        "uri": "test:001",
        "title": "Test Reference",
        "entity_type": "test"
    }
    repo2["save_with_embedding"](test_ref)
    print(f"   ✓ Saved to custom storage")
    print(f"   Storage contains: {list(custom_storage.keys())}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()