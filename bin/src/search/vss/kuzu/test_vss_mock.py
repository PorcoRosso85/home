#!/usr/bin/env python3
"""
Test VSS service with mocked dependencies
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

# Mock the entire POC dependencies before importing
import sys
sys.modules['numpy'] = Mock()
sys.modules['kuzu'] = Mock()

# Now we can import our service
from vss_service import VSSService


def test_vss_service_with_mock():
    """Test VSS service functionality with mocked dependencies"""
    
    # Create service with mocked components
    service = VSSService()
    
    # Mock the lazy-loaded components
    mock_embedding_service = Mock()
    mock_kuzu_db = Mock()
    
    # Configure mocks
    mock_embedding_result = Mock()
    mock_embedding_result.embeddings = [0.1] * 256
    mock_embedding_service.embed_query.return_value = mock_embedding_result
    
    # Mock KuzuDB search results
    mock_kuzu_db.search_similar.return_value = [
        ("ユーザー認証機能を実装する", 0.05),
        ("ログインシステムを構築する", 0.15),
        ("データベースを設計する", 0.85)
    ]
    
    # Inject mocks
    service._embedding_service = mock_embedding_service
    service._kuzu_db = mock_kuzu_db
    service.dimension = 256
    
    # Test search
    search_input = {
        "query": "認証システム",
        "limit": 3
    }
    
    result = service.search(search_input)
    
    # Verify result structure
    assert "results" in result
    assert "metadata" in result
    assert len(result["results"]) == 3
    
    # Check first result
    first = result["results"][0]
    assert first["id"] == "doc_0"
    assert first["content"] == "ユーザー認証機能を実装する"
    assert first["score"] == 0.95  # 1 - 0.05
    assert first["distance"] == 0.05
    
    # Check metadata
    assert result["metadata"]["model"] == "ruri-v3-30m"
    assert result["metadata"]["dimension"] == 256
    assert result["metadata"]["total_results"] == 3
    assert "query_time_ms" in result["metadata"]
    
    print("✓ Search returns correct format")
    
    # Test with threshold
    search_with_threshold = {
        "query": "認証システム",
        "limit": 10,
        "threshold": 0.9
    }
    
    result = service.search(search_with_threshold)
    # Check that all results meet threshold
    for r in result["results"]:
        assert r["score"] >= 0.9
    print("✓ Threshold filtering works")
    
    # Test with pre-computed vector
    search_with_vector = {
        "query": "dummy",
        "query_vector": [0.2] * 256,
        "limit": 2
    }
    
    result = service.search(search_with_vector)
    assert len(result["results"]) > 0
    # Should not call embed_query when vector is provided
    # Check it wasn't called for this search (would be 3 if it was)
    assert mock_embedding_service.embed_query.call_count < 3
    print("✓ Pre-computed vector search works")
    
    print("\nAll mock tests passed!")


if __name__ == "__main__":
    test_vss_service_with_mock()