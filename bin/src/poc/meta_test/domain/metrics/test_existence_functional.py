"""Test functional existence metric implementation."""

from domain.metrics.base import MetricInput
from domain.metrics.existence_functional import calculate_existence_metric, get_metric_info, validate_input


def test_metric_info():
    """Test metric info retrieval."""
    info = get_metric_info()
    assert info["name"] == "existence"
    assert "Test existence rate" in info["description"]


def test_validate_input():
    """Test input validation."""
    # Valid input
    valid_input = MetricInput(
        requirement_id="req-1",
        requirement_data={"title": "Test requirement"},
        test_data={"test_count": 1}
    )
    assert validate_input(valid_input) is True
    
    # Invalid input - missing requirement_id
    invalid_input = MetricInput(
        requirement_id="",
        requirement_data={"title": "Test requirement"},
        test_data=None
    )
    assert validate_input(invalid_input) is False


def test_calculate_with_tests():
    """Test calculation when tests exist."""
    input_data = MetricInput(
        requirement_id="req-1",
        requirement_data={"title": "Test requirement"},
        test_data={"test_count": 3}
    )
    
    result = calculate_existence_metric(input_data)
    assert hasattr(result, "score")
    assert result.score == 1.0
    assert result.details["has_tests"] is True
    assert result.details["test_count"] == 3
    assert len(result.suggestions) == 0


def test_calculate_without_tests():
    """Test calculation when no tests exist."""
    input_data = MetricInput(
        requirement_id="req-2",
        requirement_data={"title": "Test requirement"},
        test_data={"test_count": 0}
    )
    
    result = calculate_existence_metric(input_data)
    assert hasattr(result, "score")
    assert result.score == 0.0
    assert result.details["has_tests"] is False
    assert len(result.suggestions) == 1
    assert "No tests found" in result.suggestions[0]


if __name__ == "__main__":
    test_metric_info()
    test_validate_input()
    test_calculate_with_tests()
    test_calculate_without_tests()
    # print("All tests passed!")