"""
VSS (Vector Similarity Search) with KuzuDB - Public API

This module provides the public interface for the VSS-KuzuDB library.
All public classes, functions, and types should be imported from this module.
"""

# Import from new modular architecture
try:
    # New function-first architecture
    from application import VSSService as NewVSSService, create_vss_service, create_embedding_service
    from domain import (
        SearchResult,
        calculate_cosine_similarity,
        cosine_distance_to_similarity,
        sort_results_by_similarity,
        select_top_k_results,
        find_semantically_similar_documents,
        validate_embedding_dimension,
        group_documents_by_topic_similarity,
    )
    from infrastructure import (
        DatabaseConfig,
        create_kuzu_database,
        create_kuzu_connection,
        check_vector_extension,
        initialize_vector_schema,
        insert_documents_with_embeddings,
        search_similar_vectors,
        count_documents,
        close_connection,
    )
    
    # Use new implementation as default
    VSSService = NewVSSService
    
except ImportError:
    # Fallback to old implementation for compatibility
    try:
        from vss_service import (
            VSSService,
            VectorSearchError,
            VectorSearchResult,
            VectorIndexResult,
        )
    except ImportError:
        # Fallback for direct execution
        import sys
        sys.path.insert(0, '.')
        from vss_service import (
            VSSService,
            VectorSearchError,
            VectorSearchResult,
            VectorIndexResult,
        )

# Import type definitions from old implementation for compatibility
try:
    from vss_service import (
        VectorSearchError,
        VectorSearchResult,
        VectorIndexResult,
    )
except ImportError:
    # Define types if not available
    from typing import TypedDict, List, Dict, Any, Optional
    
    class VectorSearchError(TypedDict):
        """エラー情報を表す型"""
        ok: bool
        error: str
        details: Dict[str, Any]
    
    class VectorSearchResult(TypedDict):
        """検索成功時の結果型"""
        ok: bool
        results: List[Dict[str, Any]]
        metadata: Dict[str, Any]
    
    class VectorIndexResult(TypedDict):
        """インデックス操作の結果型"""
        ok: bool
        status: str
        indexed_count: int
        index_time_ms: float
        error: Optional[str]

# Version information
__version__ = "0.1.0"

# Public API - everything that external users should import
__all__ = [
    # Main service class (compatible with old API)
    "VSSService",
    
    # Type definitions (compatible with old API)
    "VectorSearchError",
    "VectorSearchResult",
    "VectorIndexResult",
    
    # New function-first API
    "create_vss_service",
    "create_embedding_service",
    
    # Domain functions
    "SearchResult",
    "calculate_cosine_similarity",
    "cosine_distance_to_similarity",
    "sort_results_by_similarity",
    "select_top_k_results",
    "find_semantically_similar_documents",
    "validate_embedding_dimension",
    "group_documents_by_topic_similarity",
    
    # Infrastructure functions
    "DatabaseConfig",
    "create_kuzu_database",
    "create_kuzu_connection",
    "check_vector_extension",
    "initialize_vector_schema",
    "insert_documents_with_embeddings",
    "search_similar_vectors",
    "count_documents",
    "close_connection",
    
    # Version
    "__version__",
]

# Module metadata
__doc__ = """
VSS-KuzuDB: Vector Similarity Search with KuzuDB

A library for performing vector similarity search using KuzuDB's VECTOR extension.
Supports Japanese text embeddings using the ruri-v3-30m model.

## Object-Oriented API (Compatible with existing code)

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

## Function-First API (New architecture)

Example usage:
    from vss_kuzu import (
        create_vss_service,
        create_embedding_service,
        create_kuzu_database,
        create_kuzu_connection,
        # ... other functions
    )
    
    # Create services with dependency injection
    embedding_func = create_embedding_service()
    vss_funcs = create_vss_service(
        create_db_func=create_kuzu_database,
        # ... other dependencies
    )
    
    # Use the functions
    result = vss_funcs["index_documents"](documents, config)
"""