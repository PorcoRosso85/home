"""
Symbol Search Module

統一された形式でシンボル探索を行うモジュール
bin/docs/conventions/module_design.md に従った設計

使用例:
    >>> result = search_symbols("./src")
    >>> if result["success"]:
    ...     for symbol in result["data"]:
    ...         print(f"{symbol['name']} at {symbol['path']}:{symbol['line']}")
    ... else:
    ...     print(f"Error: {result['error']}")
"""

from .search import search_symbols
from .types import SearchResult, SymbolDict, SearchSuccessDict, SearchErrorDict

__all__ = [
    "search_symbols",
    "SearchResult", 
    "SymbolDict",
    "SearchSuccessDict",
    "SearchErrorDict",
]