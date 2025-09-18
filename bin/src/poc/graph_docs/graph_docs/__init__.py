"""graph_docs - Dual KuzuDB Query Interface Package

This package provides a CLI interface for querying two KuzuDB databases simultaneously,
enabling comparison and analysis across multiple graph databases.
"""

# Re-export main components from submodules
from .mod import (
    DualKuzuDB,
    QueryResult,
    DualQueryResult,
)

from .cli_display import (
    section_title,
    query_result,
    combined_results,
    database_info,
    dual_query_info,
    json_output,
    error,
    newline,
    info,
    table,
)

__version__ = "0.1.0"

# Define explicit exports
__all__ = [
    "DualKuzuDB",
    "QueryResult", 
    "DualQueryResult",
    "section_title",
    "query_result",
    "combined_results",
    "database_info",
    "dual_query_info",
    "json_output",
    "error",
    "newline",
    "info",
    "table",
]