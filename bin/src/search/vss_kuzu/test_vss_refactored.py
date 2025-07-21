#!/usr/bin/env python3
"""
Test refactored VSS service with persistence layer
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Mock dependencies before importing
import sys
sys.modules['numpy'] = Mock()
sys.modules['kuzu'] = Mock()

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from search.vss.kuzu.vss_service import VSSService


def test_vss_with_persistence_layer():
    """Test VSS service using persistence layer"""
    
    # Mock the persistence layer
    with patch('search.vss.kuzu.vss_service.create_database') as mock_create_db, \
         patch('search.vss.kuzu.vss_service.create_connection') as mock_create_conn:
        
        # Create service
        service = VSSService(in_memory=True)
        
        # Mock database and connection
        mock_db = Mock()
        mock_create_db.return_value = mock_db
        
        mock_conn = Mock()
        mock_create_conn.return_value = mock_conn
        
        # Mock embedding service
        mock_embedding_service = Mock()
        mock_embedding_result = Mock()
        mock_embedding_result.embeddings = [0.1] * 256
        mock_embedding_service.embed_query.return_value = mock_embedding_result
        mock_embedding_service.embed_documents.return_value = [mock_embedding_result]
        
        service._embedding_service = mock_embedding_service
        
        # Test 1: Schema validation
        print("Test 1: Schema validation")
        valid_input = {"query": "test", "limit": 5}
        service.validate_input(valid_input)
        print("✓ Valid input passes validation")
        
        try:
            invalid_input = {"limit": 5}  # Missing query
            service.validate_input(invalid_input)
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✓ Invalid input is rejected")
        
        # Test 2: Document indexing
        print("\nTest 2: Document indexing")
        documents = [
            {"id": "1", "content": "Test document"}
        ]
        
        result = service.index_documents(documents)
        assert result["status"] == "success"
        assert result["indexed_count"] == 1
        
        # Verify CREATE was called
        create_calls = [call for call in mock_conn.execute.call_args_list 
                       if 'CREATE' in str(call)]
        assert len(create_calls) >= 1
        print("✓ Documents indexed successfully")
        
        # Test 3: Vector search
        print("\nTest 3: Vector search")
        
        # Reset mock for search test
        mock_conn.reset_mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.has_next.side_effect = [True, True, False]
        mock_result.get_next.side_effect = [
            [{"content": "Document 1", "id": 1}, 0.1],
            [{"content": "Document 2", "id": 2}, 0.2]
        ]
        
        # Configure execute to return different results based on query
        def execute_side_effect(query, params=None):
            if "QUERY_VECTOR_INDEX" in query:
                return mock_result
            return Mock()  # Default mock for other queries
        
        mock_conn.execute.side_effect = execute_side_effect
        
        search_input = {
            "query": "test query",
            "limit": 5
        }
        
        result = service.search(search_input)
        
        # Verify result structure
        assert "results" in result
        assert "metadata" in result
        assert len(result["results"]) == 2
        assert result["results"][0]["score"] == 0.9  # 1 - 0.1
        assert result["metadata"]["model"] == "ruri-v3-30m"
        assert result["metadata"]["dimension"] == 256
        print("✓ Search returns correct format")
        
        # Test 4: Search with threshold
        print("\nTest 4: Search with threshold")
        
        # Reset mock for threshold test
        mock_result2 = Mock()
        mock_result2.has_next.side_effect = [True, True, False]
        mock_result2.get_next.side_effect = [
            [{"content": "Document 1", "id": 1}, 0.1],
            [{"content": "Document 2", "id": 2}, 0.2]
        ]
        
        def execute_side_effect2(query, params=None):
            if "QUERY_VECTOR_INDEX" in query:
                return mock_result2
            return Mock()
        
        mock_conn.execute.side_effect = execute_side_effect2
        
        search_with_threshold = {
            "query": "test",
            "threshold": 0.85
        }
        
        result = service.search(search_with_threshold)
        # Only first result should pass threshold (0.9 > 0.85)
        assert all(r["score"] >= 0.85 for r in result["results"])
        print("✓ Threshold filtering works")
        
        print("\nAll tests passed!")


if __name__ == "__main__":
    test_vss_with_persistence_layer()