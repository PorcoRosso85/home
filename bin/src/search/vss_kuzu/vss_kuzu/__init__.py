"""
VSS (Vector Similarity Search) with KuzuDB - Public API

This module provides the public interface for the VSS-KuzuDB library.
All public classes, functions, and types should be imported from this module.
"""

from typing import List, Dict, Any, TypedDict, Optional

# Import from function-first architecture
from .application import create_vss_service, create_embedding_service
from .domain import (
    SearchResult,
    calculate_cosine_similarity,
    cosine_distance_to_similarity,
    sort_results_by_similarity,
    select_top_k_results,
    find_semantically_similar_documents,
    validate_embedding_dimension,
    group_documents_by_topic_similarity,
)
from .infrastructure import (
    DatabaseConfig,
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    count_documents,
    close_connection,
    VSSConfig,
    create_config,
    get_default_config,
)

# Type definitions
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
    # Type definitions
    "VectorSearchError",
    "VectorSearchResult",
    "VectorIndexResult",
    
    # Function-first API
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
    "VSSConfig",
    "create_config",
    "get_default_config",
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

## Function-First API

Example usage:
    from vss_kuzu import (
        create_config,
        create_kuzu_database,
        create_kuzu_connection,
        check_vector_extension,
        initialize_vector_schema,
        insert_documents_with_embeddings,
        search_similar_vectors,
        create_embedding_service,
    )
    
    # Create configuration
    config = create_config(db_path="./my_db", in_memory=False)
    
    # Setup database
    db_config = DatabaseConfig(
        db_path=config.db_path,
        in_memory=config.in_memory,
        embedding_dimension=config.embedding_dimension
    )
    success, database, error = create_kuzu_database(db_config)
    
    # Create embedding service
    embedding_func = create_embedding_service(config.model_name)
    
    # Index documents
    documents = [
        {"id": "doc1", "content": "ユーザー認証機能を実装する"},
        {"id": "doc2", "content": "ログインシステムを構築する"},
    ]
    
    # Generate embeddings and insert
    embeddings = [embedding_func(doc["content"]) for doc in documents]
    docs_with_embeddings = [
        (doc["id"], doc["content"], emb) 
        for doc, emb in zip(documents, embeddings)
    ]
    success, count, error = insert_documents_with_embeddings(connection, docs_with_embeddings)
    
    # Search similar documents
    query_embedding = embedding_func("認証システム")
    success, results, error = search_similar_vectors(
        connection, query_embedding, limit=5
    )
"""