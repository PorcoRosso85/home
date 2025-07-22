"""
VSS (Vector Similarity Search) with KuzuDB - Public API

This module provides the public interface for the VSS-KuzuDB library.
All public classes, functions, and types should be imported from this module.
"""

from vss_service import (
    VSSService,
    VectorSearchError,
    VectorSearchResult,
    VectorIndexResult,
)

# Version information
__version__ = "0.1.0"

# Public API - everything that external users should import
__all__ = [
    # Main service class
    "VSSService",
    
    # Type definitions
    "VectorSearchError",
    "VectorSearchResult",
    "VectorIndexResult",
    
    # Version
    "__version__",
]

# Module metadata
__doc__ = """
VSS-KuzuDB: Vector Similarity Search with KuzuDB

A library for performing vector similarity search using KuzuDB's VECTOR extension.
Supports Japanese text embeddings using the ruri-v3-30m model.

Example usage:
    from vss_kuzu import VSSService, VectorSearchResult
    
    # Create service instance
    service = VSSService(in_memory=True)
    
    # Index documents
    documents = [
        {"id": "doc1", "content": "ユーザー認証機能を実装する"},
        {"id": "doc2", "content": "ログインシステムを構築する"},
    ]
    result = service.index_documents(documents)
    
    # Search similar documents
    search_result: VectorSearchResult = service.search({"query": "認証システム", "limit": 5})
    if search_result["ok"]:
        for doc in search_result["results"]:
            print(f"{doc['id']}: {doc['content']} (score: {doc['score']})")
"""