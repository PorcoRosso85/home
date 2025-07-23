"""
FTS (Full-Text Search) with KuzuDB

This package provides full-text search functionality using KuzuDB.
For the complete public API, import from the mod module:

    from fts_kuzu.mod import FTSService, FTSSearchResult
"""

# Re-export everything from mod.py for backward compatibility
try:
    from .mod import (
        FTSError,
        FTSErrorType,
        FTSSearchResult,
        FTSService,
        IndexResult,
        # Version
        __version__,
    )
except ImportError:
    # Fallback for direct file execution
    from mod import (
        FTSError,
        FTSErrorType,
        FTSSearchResult,
        FTSService,
        IndexResult,
        __version__,
    )

__all__ = [
    # Service class
    "FTSService",
    # FTS types
    "FTSSearchResult",
    "IndexResult",
    "FTSError",
    "FTSErrorType",
    # Version
    "__version__",
]
