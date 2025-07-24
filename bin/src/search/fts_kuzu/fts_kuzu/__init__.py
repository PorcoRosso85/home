"""
FTS KuzuDB Package

Full-Text Search implementation with KuzuDB
"""

# Unified API
from .application import create_fts, FTS

# Protocols and types
from .protocols import SearchSystem, FTSAlgebra
from .common_types import SearchResults, IndexResult, SearchResultItem, SearchConfig

# Function-first API
from .application import (
    create_fts_service,
    create_fts_connection,
    index_fts_documents,
    search_fts_documents,
    ApplicationConfig,
)

# Domain
from .domain import (
    FTSError,
    FTSErrorType,
    FTSSearchResult,
    create_highlight_info,
)

# Infrastructure
from .infrastructure import (
    DatabaseConfig,
    create_kuzu_database,
    create_kuzu_connection,
    check_fts_extension,
    install_fts_extension,
    initialize_fts_schema,
    create_fts_index,
    drop_fts_index,
    list_fts_indexes,
    get_fts_index_info,
    query_fts_index,
    count_documents,
    close_connection,
)

# Version
from .mod import __version__

__all__ = [
    # Unified API (Recommended)
    "create_fts",
    "FTS",  # Deprecated: for backward compatibility
    
    # Protocols and types
    "FTSAlgebra",  # New: Protocol-based interface
    "SearchSystem",
    "SearchResults",
    "IndexResult",
    "SearchResultItem",
    "SearchConfig",
    
    # Function-first API
    "create_fts_service",
    "create_fts_connection",
    "index_fts_documents",
    "search_fts_documents",
    "ApplicationConfig",
    
    # Domain
    "FTSError",
    "FTSErrorType",
    "FTSSearchResult",
    "create_highlight_info",
    
    # Infrastructure
    "DatabaseConfig",
    "create_kuzu_database",
    "create_kuzu_connection",
    "check_fts_extension",
    "install_fts_extension",
    "initialize_fts_schema",
    "create_fts_index",
    "drop_fts_index",
    "list_fts_indexes",
    "get_fts_index_info",
    "query_fts_index",
    "count_documents",
    "close_connection",
    
    # Version
    "__version__",
]