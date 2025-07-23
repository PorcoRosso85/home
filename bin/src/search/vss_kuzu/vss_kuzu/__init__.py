"""
VSS (Vector Similarity Search) with KuzuDB - Public API

This module provides the public interface for the VSS-KuzuDB library.
All public classes, functions, and types should be imported from this module.
"""

from typing import List, Dict, Any, TypedDict, Optional

# Import only what's needed for the public API
from .application import create_vss

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
    
    # Unified API (Recommended)
    "create_vss",
    
    # Version
    "__version__",
]

# Module metadata
__doc__ = """
VSS-KuzuDB: Vector Similarity Search with KuzuDB

A library for performing vector similarity search using KuzuDB's VECTOR extension.
Supports Japanese text embeddings using the ruri-v3-30m model.

## Usage

    from vss_kuzu import create_vss
    
    # Create VSS instance
    vss = create_vss(in_memory=True)
    
    # Index documents
    documents = [
        {"id": "doc1", "content": "ユーザー認証機能を実装する"},
        {"id": "doc2", "content": "ログインシステムを構築する"},
    ]
    vss.index(documents)
    
    # Search similar documents
    results = vss.search("認証システム", limit=5)

## Type Definitions

The module exports TypedDict classes for type-safe interactions:
- VectorSearchError: Error information with ok=False, error message, and details
- VectorSearchResult: Successful search results with ok=True, results list, and metadata
- VectorIndexResult: Indexing operation result with status and performance metrics
"""