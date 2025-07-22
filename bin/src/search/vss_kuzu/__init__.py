"""
VSS (Vector Similarity Search) with KuzuDB - JSON Schema based implementation

This package provides vector similarity search functionality using KuzuDB.
For the complete public API, import from the mod module:

    from vss_kuzu.mod import VSSService, VectorSearchResult
"""

# Re-export everything from mod.py for backward compatibility
try:
    from .mod import (
        VSSService,
        VectorSearchError,
        VectorSearchResult,
        VectorIndexResult,
        __version__,
    )
except ImportError:
    # Fallback for direct file execution
    from mod import (
        VSSService,
        VectorSearchError,
        VectorSearchResult,
        VectorIndexResult,
        __version__,
    )

__all__ = [
    "VSSService",
    "VectorSearchError",
    "VectorSearchResult",
    "VectorIndexResult",
    "__version__",
]