"""
Test for search_requirements template
"""
from application.templates import process_search_template


def test_search_template_validation():
    """Test input validation"""
    # Test missing query
    result = process_search_template({}, None)
    assert result["status"] == "error"
    assert result["error"]["type"] == "InvalidInputError"
    
    # Test invalid limit
    result = process_search_template({"query": "test", "limit": -1}, None)
    assert result["status"] == "error"
    assert result["error"]["type"] == "InvalidInputError"
    
    # Test no search service
    result = process_search_template({"query": "test"}, lambda: None)
    assert result["status"] == "error"
    assert result["error"]["type"] == "ServiceNotAvailable"


def test_search_template_with_mock_adapter():
    """Test with a mock search adapter"""
    class MockSearchAdapter:
        def search_hybrid(self, query, k=10):
            return [
                {
                    "id": "req_001",
                    "title": "Test Requirement",
                    "content": "This is a test requirement",
                    "score": 0.95,
                    "source": "hybrid"
                }
            ]
    
    result = process_search_template(
        {"query": "test requirement", "limit": 5},
        lambda: MockSearchAdapter()
    )
    
    assert result["status"] == "success"
    assert result["query"] == "test requirement"
    assert result["count"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == "req_001"
    assert result["results"][0]["score"] == 0.95


def test_search_template_with_error():
    """Test error handling"""
    class ErrorSearchAdapter:
        def search_hybrid(self, query, k=10):
            return [{"error": {"type": "SearchError", "message": "Search failed"}}]
    
    result = process_search_template(
        {"query": "test"},
        lambda: ErrorSearchAdapter()
    )
    
    assert result["status"] == "error"
    assert result["error"]["type"] == "SearchError"


if __name__ == "__main__":
    test_search_template_validation()
    test_search_template_with_mock_adapter()
    test_search_template_with_error()
    print("All tests passed!")