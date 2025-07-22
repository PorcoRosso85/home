"""
FTS/VSS (Full-Text Search / Vector Similarity Search) with KuzuDB

This package provides full-text search and vector similarity search functionality using KuzuDB.
For the complete public API, import from the mod module:

    from fts_kuzu.mod import VSSService, VectorSearchResult, FTSSearchResult
"""

# Re-export everything from mod.py for backward compatibility
try:
    from .mod import (
        # Service class
        VSSService,
        # Legacy type definitions
        VectorSearchError,
        VectorSearchResult,
        VectorIndexResult,
        # New domain types
        SearchResult,
        FTSSearchResult,
        IndexResult,
        FTSError,
        FTSErrorType,
        # Version
        __version__,
    )
except ImportError:
    # Fallback for direct file execution
    from mod import (
        VSSService,
        VectorSearchError,
        VectorSearchResult,
        VectorIndexResult,
        SearchResult,
        FTSSearchResult,
        IndexResult,
        FTSError,
        FTSErrorType,
        __version__,
    )

__all__ = [
    # Service class
    "VSSService",
    # Legacy type definitions
    "VectorSearchError",
    "VectorSearchResult",
    "VectorIndexResult",
    # New domain types
    "SearchResult",
    "FTSSearchResult",
    "IndexResult",
    "FTSError",
    "FTSErrorType",
    # Version
    "__version__",
]