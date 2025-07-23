"""
FTS (Full-Text Search) with KuzuDB - Public API

This module provides the public interface for the FTS-KuzuDB library.
All public classes, functions, and types should be imported from this module.
"""

# Import from new modular architecture
try:
    # New function-first architecture imports
    from .application import (
        create_fts_service,
        create_fts_connection,
        index_fts_documents,
        search_fts_documents,
    )
    from .domain import (
        FTSError,
        FTSErrorType,
        FTSSearchResult,
        IndexResult,
    )
    from .infrastructure import (
        DatabaseConfig,
        check_fts_extension,
        close_connection,
        count_documents,
        create_fts_index,
        create_kuzu_connection,
        create_kuzu_database,
        initialize_fts_schema,
        install_fts_extension,
    )

except ImportError:
    # Handle import errors gracefully
    pass


# Version information
__version__ = "0.2.0"  # Updated for FTS support

# Public API - everything that external users should import
__all__ = [
    # Main service classes (for backward compatibility)
    # Note: FTSService removed from exports to encourage function-first API usage
    # The class-based approach is deprecated in favor of composable functions
    # New function-first API
    "create_fts_service",
    "create_fts_connection",
    "index_fts_documents",
    "search_fts_documents",
    # Domain data classes
    "FTSSearchResult",
    "IndexResult",
    "FTSError",
    "FTSErrorType",
    # Infrastructure functions
    "DatabaseConfig",
    "create_kuzu_database",
    "create_kuzu_connection",
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

## Primary API - Function-First Approach

Note: The class-based FTSService is deprecated. Use the function-first API for better composability and testability.

Example usage:
    from fts_kuzu import create_fts_service, DatabaseConfig

    # Create FTS service using function-first approach
    config = DatabaseConfig(in_memory=True)
    fts_funcs = create_fts_service()
    
    # Create connection
    conn_result = fts_funcs["create_connection"](config)
    if not conn_result["ok"]:
        raise Exception(conn_result["error"])
    conn = conn_result["value"]

    # Index documents
    documents = [
        {"id": "doc1", "title": "Authentication Guide", "content": "How to implement user authentication"},
        {"id": "doc2", "title": "Login System", "content": "Building a secure login system"},
    ]
    result = fts_funcs["index_documents"](documents, conn)

    # Search documents
    search_result = fts_funcs["search_documents"]("authentication", conn, limit=10)
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
