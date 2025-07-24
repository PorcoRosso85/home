"""
Integration test for search_requirements template with template_processor
"""
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from requirement.graph.application.template_processor import process_template


def test_search_template_integration():
    """Test search template through template processor"""
    # Mock repository (not used for search)
    mock_repository = {}
    
    # Mock search factory
    class MockSearchAdapter:
        def search_hybrid(self, query, k=10):
            if "architecture" in query.lower():
                return [
                    {
                        "id": "req_arch_001",
                        "title": "System Architecture Requirements",
                        "content": "Define the overall system architecture and components",
                        "score": 0.92,
                        "source": "hybrid"
                    },
                    {
                        "id": "req_arch_002", 
                        "title": "Microservices Architecture",
                        "content": "Implement microservices pattern for scalability",
                        "score": 0.85,
                        "source": "hybrid"
                    }
                ]
            return []
    
    def mock_search_factory():
        return MockSearchAdapter()
    
    # Test successful search
    result = process_template(
        {
            "template": "search_requirements",
            "parameters": {
                "query": "architecture requirements",
                "limit": 5
            }
        },
        mock_repository,
        mock_search_factory
    )
    
    assert result["status"] == "success"
    assert result["query"] == "architecture requirements"
    assert result["count"] == 2
    assert len(result["results"]) == 2
    assert result["results"][0]["id"] == "req_arch_001"
    assert result["results"][0]["score"] == 0.92
    
    # Test with no search factory
    result = process_template(
        {
            "template": "search_requirements",
            "parameters": {
                "query": "test"
            }
        },
        mock_repository,
        None
    )
    
    assert result["status"] == "error"
    assert result["error"]["type"] == "ServiceNotAvailable"
    
    # Test with invalid input
    result = process_template(
        {
            "template": "search_requirements",
            "parameters": {}
        },
        mock_repository,
        mock_search_factory
    )
    
    assert result["status"] == "error"
    assert result["error"]["type"] == "InvalidInputError"
    
    print("All integration tests passed!")


if __name__ == "__main__":
    test_search_template_integration()