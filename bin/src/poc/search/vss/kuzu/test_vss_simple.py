#!/usr/bin/env python3
"""Simple tests for VSS with mocked connection"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_mock import MockConnection
from main import create_embedder, create_vector_search
from vss_types import IndexSuccess, SearchSuccess, EmbeddingSuccess


def test_basic_functionality():
    """Test basic VSS functionality with mocked connection."""
    # Create mock connection
    conn = MockConnection()
    
    # Create embedder
    embedder = create_embedder('all-MiniLM-L6-v2')
    
    # Create vector search operations
    search_ops = create_vector_search(conn, embedder)
    
    # Test 1: Install extension
    print("Test 1: Install extension...")
    result = search_ops['install_extension']()
    assert result['ok'] is True
    assert 'ready' in result['message']
    print("✓ Install extension passed")
    
    # Test 2: Generate embedding
    print("\nTest 2: Generate embedding...")
    result = search_ops['generate_embedding']('test text')
    assert result['ok'] is True
    assert 'embedding' in result
    assert len(result['embedding']) == 384  # all-MiniLM-L6-v2 dimension
    print("✓ Generate embedding passed")
    
    # Test 3: Empty query validation
    print("\nTest 3: Empty query validation...")
    result = search_ops['search']('', 5)
    assert result['ok'] is False
    assert 'empty query' in result['error'].lower()
    print("✓ Empty query validation passed")
    
    # Test 4: Search with results
    print("\nTest 4: Search with results...")
    # Set mock results - VSS returns (node, distance) tuples
    conn.set_results([[
        [{'id': '1', 'title': 'Test Doc', 'content': 'Test content'}, 0.2]
    ]])
    result = search_ops['search']('test query', 5)
    assert result['ok'] is True
    assert len(result['results']) == 1
    assert result['results'][0]['score'] == 0.8  # 1 - distance
    print("✓ Search with results passed")
    
    # Test 5: Check index exists
    print("\nTest 5: Check index exists...")
    result = search_ops['check_index_exists']()
    assert result['ok'] is True
    assert 'exists' in result
    print("✓ Check index exists passed")
    
    # Test 6: Index document
    print("\nTest 6: Index document...")
    result = search_ops['index_document']({
        'path': '/test/readme.md',
        'content': 'Test content',
        'purpose': 'Testing'
    })
    assert result['ok'] is True
    print("✓ Index document passed")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_basic_functionality()