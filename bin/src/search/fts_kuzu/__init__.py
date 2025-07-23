"""
FTS (Full-Text Search) with KuzuDB

This package provides full-text search functionality using KuzuDB.
For the complete public API, import from the mod module:

    from fts_kuzu.mod import create_fts_connection, index_fts_documents, search_fts_documents
"""

# Re-export everything from mod.py for backward compatibility
try:
    from .mod import (
        FTSError,
        FTSErrorType,
        FTSSearchResult,
        IndexResult,
        # Function-first API
        create_fts_service,
        create_fts_connection,
        index_fts_documents,
        search_fts_documents,
        # Version
        __version__,
    )
except ImportError:
    # Fallback for direct file execution
    from mod import (
        FTSError,
        FTSErrorType,
        FTSSearchResult,
        IndexResult,
        # Function-first API
        create_fts_service,
        create_fts_connection,
        index_fts_documents,
        search_fts_documents,
        __version__,
    )

__all__ = [
    # Function-first API
    "create_fts_service",
    "create_fts_connection",
    "index_fts_documents",
    "search_fts_documents",
    # FTS types
    "FTSSearchResult",
    "IndexResult",
    "FTSError",
    "FTSErrorType",
    # Version
    "__version__",
]
