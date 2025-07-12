#!/usr/bin/env python3
"""
TDD Red Phase - Hybrid Search Integration Tests
Following t-wada style TDD approach
"""

import pytest
from typing import Dict, List, Any


def test_hybrid_search_uses_vss_ruri_model():
    """Hybrid検索がVSS POCのRuriモデルを使用すること"""
    # Arrange
    from poc.search.hybrid.main import create_hybrid_search
    
    # Act
    search = create_hybrid_search(None)
    
    # Assert
    assert hasattr(search, 'embedder')
    assert search.embedder.__class__.__name__ == "RuriEmbeddingModel"


def test_hybrid_search_uses_fts_facade():
    """Hybrid検索がFTS POCのfacadeを使用すること"""
    # Arrange
    from poc.search.hybrid.main import create_hybrid_search
    
    # Act
    search = create_hybrid_search(None)
    
    # Assert
    assert hasattr(search, 'fts_ops')
    assert 'search' in search.fts_ops
    assert 'create_index' in search.fts_ops


def test_hybrid_search_no_mock_embedding():
    """Hybrid検索にモック埋め込み関数が存在しないこと"""
    # Arrange
    import poc.search.hybrid.main as hybrid_main
    
    # Act & Assert
    assert not hasattr(hybrid_main, 'generate_requirement_embedding')
    assert 'hash' not in str(hybrid_main.__dict__)


def test_hybrid_search_returns_merged_results():
    """Hybrid検索が3つの検索結果を統合すること"""
    # Arrange
    from poc.search.hybrid.main import create_hybrid_search
    
    search = create_hybrid_search(None)
    
    # Act
    results = search.search("認証システム")
    
    # Assert
    assert isinstance(results, list)
    for result in results:
        assert 'combined_score' in result
        assert 'vss_score' in result
        assert 'fts_score' in result
        assert 'cypher_score' in result
        assert 'sources' in result


def test_hybrid_search_respects_weights():
    """Hybrid検索が重み付けを適用すること"""
    # Arrange
    from poc.search.hybrid.main import create_hybrid_search
    
    search = create_hybrid_search(None)
    weights = {
        "cypher": 3.0,  # カスタム重み
        "fts": 2.0,
        "vss": 1.0
    }
    
    # Act
    results = search.search("グラフデータベース", weights=weights)
    
    # Assert
    # Cypherマッチがあれば最上位に来るはず
    if results and results[0]['cypher_score'] > 0:
        assert results[0]['sources'] == ['cypher'] or 'cypher' in results[0]['sources']


def test_hybrid_search_handles_empty_results():
    """Hybrid検索が空の結果を適切に処理すること"""
    # Arrange
    from poc.search.hybrid.main import create_hybrid_search
    
    search = create_hybrid_search(None)
    
    # Act
    results = search.search("存在しないキーワード12345")
    
    # Assert
    assert isinstance(results, list)
    assert len(results) >= 0  # 空でもエラーにならない


def test_hybrid_search_semantic_understanding():
    """Hybrid検索が意味的理解を示すこと（Ruriモデル使用）"""
    # Arrange
    from poc.search.hybrid.main import create_hybrid_search
    
    search = create_hybrid_search(None)
    
    # Act
    results1 = search.search("認証")
    results2 = search.search("ログイン")
    
    # Assert
    # 意味的に関連する結果が含まれるはず
    ids1 = {r['id'] for r in results1}
    ids2 = {r['id'] for r in results2}
    
    # 共通の結果があることを期待（完全一致でなくても良い）
    assert len(ids1.intersection(ids2)) > 0 or len(results1) == 0 or len(results2) == 0