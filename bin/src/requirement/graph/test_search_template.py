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


# REMOVED: Mock test violates "Refactoring Wall" principle
# This test has been replaced with test_search_template_integration_real.py
# which uses actual database and search service instead of mocks


# REMOVED: Mock test violates "Refactoring Wall" principle
# Error handling is tested in test_search_template_integration_real.py
# using real error scenarios instead of mocked errors


if __name__ == "__main__":
    test_search_template_validation()
    test_search_template_with_mock_adapter()
    test_search_template_with_error()
    print("All tests passed!")