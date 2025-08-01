"""Test functional reachability metric implementation."""

from domain.metrics.base import MetricInput
from domain.metrics.reachability_functional import calculate_reachability_metric, get_metric_info, validate_input


def test_metric_info():
    """Test metric info retrieval."""
    info = get_metric_info()
    assert info["name"] == "reachability"
    assert "executable without circular references" in info["description"]


def test_validate_input():
    """Test input validation."""
    # Valid input
    valid_input = MetricInput(
        requirement_id="req-1",
        requirement_data={"title": "Test requirement"},
        test_data={"test_id": "test-1", "dependencies": {}}
    )
    assert validate_input(valid_input) is True
    
    # Invalid input - missing test_data
    invalid_input = MetricInput(
        requirement_id="req-1",
        requirement_data={"title": "Test requirement"},
        test_data=None
    )
    assert validate_input(invalid_input) is False


def test_calculate_without_circular_deps():
    """Test calculation when no circular dependencies exist."""
    input_data = MetricInput(
        requirement_id="req-1",
        requirement_data={"title": "Test requirement"},
        test_data={
            "test_id": "test-1",
            "dependencies": {
                "test-1": ["test-2", "test-3"],
                "test-2": ["test-4"],
                "test-3": [],
                "test-4": []
            }
        }
    )
    
    result = calculate_reachability_metric(input_data)
    assert hasattr(result, "score")
    assert result.score == 1.0
    assert result.details["has_circular_dependencies"] is False
    assert len(result.suggestions) == 0


def test_calculate_with_circular_deps():
    """Test calculation when circular dependencies exist."""
    input_data = MetricInput(
        requirement_id="req-2",
        requirement_data={"title": "Test requirement"},
        test_data={
            "test_id": "test-1",
            "dependencies": {
                "test-1": ["test-2"],
                "test-2": ["test-3"],
                "test-3": ["test-1"]  # Circular dependency
            }
        }
    )
    
    result = calculate_reachability_metric(input_data)
    assert hasattr(result, "score")
    assert result.score == 0.0
    assert result.details["has_circular_dependencies"] is True
    assert len(result.suggestions) == 1
    assert "Circular dependency detected" in result.suggestions[0]


def test_calculate_with_self_reference():
    """Test calculation when a test depends on itself."""
    input_data = MetricInput(
        requirement_id="req-3",
        requirement_data={"title": "Test requirement"},
        test_data={
            "test_id": "test-1",
            "dependencies": {
                "test-1": ["test-1"]  # Self-reference
            }
        }
    )
    
    result = calculate_reachability_metric(input_data)
    assert hasattr(result, "score")
    assert result.score == 0.0
    assert result.details["has_circular_dependencies"] is True


def test_calculate_invalid_input():
    """Test calculation with invalid input returns ValidationError."""
    input_data = MetricInput(
        requirement_id="",
        requirement_data=None,
        test_data=None
    )
    
    result = calculate_reachability_metric(input_data)
    assert isinstance(result, dict)
    assert result["type"] == "ValidationError"
    assert "Invalid input data" in result["message"]


if __name__ == "__main__":
    test_metric_info()
    test_validate_input()
    test_calculate_without_circular_deps()
    test_calculate_with_circular_deps()
    test_calculate_with_self_reference()
    test_calculate_invalid_input()
    print("All tests passed!")