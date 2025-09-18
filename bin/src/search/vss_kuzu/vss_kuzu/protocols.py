#!/usr/bin/env python3
"""
Protocol definitions for VSS operations

This module defines the algebraic interface for vector similarity search operations
using Python's Protocol feature for structural subtyping.
"""

from typing import Protocol, List, Dict, Any, runtime_checkable


@runtime_checkable
class VSSAlgebra(Protocol):
    """
    VSS操作の代数的インターフェース
    
    This protocol defines the minimal interface for vector similarity search.
    Any class implementing these methods can be used as a VSS service.
    """
    
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        ドキュメントをインデックスに追加
        
        Args:
            documents: List of documents with 'id' and 'content' fields
            
        Returns:
            Result dictionary with 'ok', 'indexed_count', etc.
        """
        ...
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        類似ドキュメントを検索
        
        Args:
            query: Search query text
            limit: Maximum number of results
            **kwargs: Additional parameters (efs, etc.)
            
        Returns:
            Result dictionary with 'ok', 'results', 'metadata'
        """
        ...


@runtime_checkable
class SearchResult(Protocol):
    """検索結果の構造を定義するProtocol"""
    ok: bool
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@runtime_checkable  
class IndexResult(Protocol):
    """インデックス結果の構造を定義するProtocol"""
    ok: bool
    indexed_count: int
    index_time_ms: float
    status: str


@runtime_checkable
class ErrorResult(Protocol):
    """エラー結果の構造を定義するProtocol"""
    ok: bool
    error: str
    details: Dict[str, Any]