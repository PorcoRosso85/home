"""graph_docs_pyright - Pyright-based code analysis with KuzuDB storage.

This package provides code analysis using Pyright Language Server Protocol
and stores the results in KuzuDB for graph-based querying.
"""

__version__ = "0.1.0"

# Define explicit exports
__all__ = [
    "PyrightAnalyzer",
    "KuzuStorage",
]

# Re-export main components - delayed import to avoid circular dependencies
def __getattr__(name):
    if name == "PyrightAnalyzer":
        from .pyright_analyzer import PyrightAnalyzer
        return PyrightAnalyzer
    elif name == "KuzuStorage":
        from .kuzu_storage import KuzuStorage
        return KuzuStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")