"""
FTS (Full-Text Search) with KuzuDB - Public API

This module provides the public interface for the FTS-KuzuDB library.
All public classes, functions, and types should be imported from this module.
"""

# Import from new modular architecture
try:
    # New function-first architecture imports
    from .application import (
        FTSService,
        VSSService,
        create_embedding_service,
        create_fts_service,
        create_vss_service,
    )
    from .domain import (
        FTSError,
        FTSErrorType,
        FTSSearchResult,
        IndexResult,
        # Data classes
        SearchResult,
        # Pure functions
        calculate_cosine_similarity,
        cosine_distance_to_similarity,
        find_semantically_similar_documents,
        group_documents_by_topic_similarity,
        select_top_k_results,
        sort_results_by_similarity,
        validate_embedding_dimension,
    )
    from .infrastructure import (
        DatabaseConfig,
        check_fts_extension,
        check_vector_extension,
        close_connection,
        count_documents,
        create_fts_index,
        create_kuzu_connection,
        create_kuzu_database,
        initialize_fts_schema,
        initialize_vector_schema,
        insert_documents_with_embeddings,
        install_fts_extension,
        search_similar_vectors,
    )

except ImportError:
    # Fallback to old implementation for compatibility
    try:
        from .vss_service import (
            VectorIndexResult,
            VectorSearchError,
            VectorSearchResult,
            VSSService,
        )
    except ImportError:
        # Fallback for direct execution
        import sys

        sys.path.insert(0, ".")
        from vss_service import (
            VectorIndexResult,
            VectorSearchError,
            VectorSearchResult,
            VSSService,
        )

# Import type definitions from old implementation for compatibility
try:
    from .vss_service import (
        VectorIndexResult,
        VectorSearchError,
        VectorSearchResult,
    )
except ImportError:
    # Define types if not available
    from typing import Any, TypedDict

    class VectorSearchError(TypedDict):
        """エラー情報を表す型"""

        ok: bool
        error: str
        details: dict[str, Any]

    class VectorSearchResult(TypedDict):
        """検索成功時の結果型"""

        ok: bool
        results: list[dict[str, Any]]
        metadata: dict[str, Any]

    class VectorIndexResult(TypedDict):
        """インデックス操作の結果型"""

        ok: bool
        status: str
        indexed_count: int
        index_time_ms: float
        error: str | None


# Version information
__version__ = "0.2.0"  # Updated for FTS support

# Public API - everything that external users should import
__all__ = [
    # Main service classes
    "FTSService",  # Primary FTS service
    "VSSService",  # Legacy VSS service (for compatibility)
    # Type definitions (compatible with old API)
    "VectorSearchError",
    "VectorSearchResult",
    "VectorIndexResult",
    # New function-first API
    "create_fts_service",
    "create_vss_service",
    "create_embedding_service",
    # Domain data classes
    "SearchResult",
    "FTSSearchResult",
    "IndexResult",
    "FTSError",
    "FTSErrorType",
    # Domain pure functions
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
    "check_fts_extension",
    "install_fts_extension",
    "initialize_fts_schema",
    "create_fts_index",
    "count_documents",
    "close_connection",
    # Version
    "__version__",
]

# Module metadata
__doc__ = """
FTS-KuzuDB: Full-Text Search with KuzuDB

A library for performing full-text search using KuzuDB's FTS extension.
Supports keyword search, BM25 scoring, phrase search, and highlighting.

## Primary API - Full-Text Search

Example usage:
    from fts_kuzu import FTSService

    # Create FTS service instance
    service = FTSService(in_memory=True)

    # Index documents
    documents = [
        {"id": "doc1", "title": "Authentication Guide", "content": "How to implement user authentication"},
        {"id": "doc2", "title": "Login System", "content": "Building a secure login system"},
    ]
    result = service.index_documents(documents)

    # Search documents
    search_result = service.search({"query": "authentication", "limit": 10})
    if search_result["ok"]:
        for doc in search_result["results"]:
            print(f"{doc['id']}: {doc['content']} (score: {doc['score']})")
            print(f"  Highlights: {doc['highlights']}")

## Function-First API

Example usage:
    from fts_kuzu import (
        create_fts_service,
        create_kuzu_database,
        create_kuzu_connection,
        check_fts_extension,
        # ... other functions
    )

    # Create FTS service with dependency injection
    fts_funcs = create_fts_service(
        create_db_func=create_kuzu_database,
        create_conn_func=create_kuzu_connection,
        check_fts_func=check_fts_extension,
        # ... other dependencies
    )

    # Use the functions
    result = fts_funcs["index_documents"](documents, config)
"""
