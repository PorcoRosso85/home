"""Tests for runtime correlation metric functional implementation."""

import pytest

from .base import MetricInput
from .runtime_correlation_functional import (
    get_metric_info,
    validate_input,
    calculate_runtime_correlation_metric
)


class TestRuntimeCorrelationFunctional:
    """Test runtime correlation metric functional implementation."""

    def test_metric_info(self):
        """Test metric info function."""
        info = get_metric_info()
        assert info["name"] == "runtime_correlation"
        assert "correlation between test success and operational metrics" in info["description"]

    def test_validate_input_valid(self):
        """Test input validation with valid data."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Test requirement"},
            runtime_data={
                "test_history": [{"passed": True}],
                "operational_metrics": {"metric": [1]}
            }
        )
        assert validate_input(input_data) is True

    def test_validate_input_missing_runtime_data(self):
        """Test input validation with missing runtime data."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Test requirement"},
            runtime_data=None
        )
        assert validate_input(input_data) is False

    def test_validate_input_missing_test_history(self):
        """Test input validation with missing test history."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Test requirement"},
            runtime_data={"operational_metrics": {"metric": [1]}}
        )
        assert validate_input(input_data) is False

    def test_validate_input_missing_operational_metrics(self):
        """Test input validation with missing operational metrics."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Test requirement"},
            runtime_data={"test_history": [{"passed": True}]}
        )
        assert validate_input(input_data) is False

    def test_valid_correlation(self):
        """Test with valid runtime data showing correlation."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Performance requirement"},
            runtime_data={
                "test_history": [
                    {"passed": True, "timestamp": 1},
                    {"passed": True, "timestamp": 2},
                    {"passed": False, "timestamp": 3},
                    {"passed": True, "timestamp": 4},
                    {"passed": False, "timestamp": 5}
                ],
                "operational_metrics": {
                    "response_time": [100, 120, 300, 110, 280],
                    "error_rate": [0.01, 0.02, 0.15, 0.01, 0.12]
                }
            }
        )

        result = calculate_runtime_correlation_metric(input_data)

        assert result.metric_name == "runtime_correlation"
        assert result.requirement_id == "req_001"
        assert 0.0 <= result.score <= 1.0
        assert "correlations" in result.details
        assert "response_time" in result.details["correlations"]
        assert "error_rate" in result.details["correlations"]

    def test_no_correlation(self):
        """Test with runtime data showing no correlation."""
        input_data = MetricInput(
            requirement_id="req_002",
            requirement_data={"title": "Unrelated requirement"},
            runtime_data={
                "test_history": [
                    {"passed": True, "timestamp": 1},
                    {"passed": False, "timestamp": 2},
                    {"passed": True, "timestamp": 3},
                    {"passed": False, "timestamp": 4}
                ],
                "operational_metrics": {
                    "random_metric": [42, 42, 42, 42]  # No variance
                }
            }
        )

        result = calculate_runtime_correlation_metric(input_data)

        assert result.score == 0.0
        assert result.details["correlations"]["random_metric"]["correlation"] == 0.0

    def test_insufficient_data(self):
        """Test with insufficient runtime data."""
        input_data = MetricInput(
            requirement_id="req_003",
            requirement_data={"title": "New requirement"},
            runtime_data={
                "test_history": [],
                "operational_metrics": {}
            }
        )

        result = calculate_runtime_correlation_metric(input_data)

        # Empty lists/dicts fail validation, so we get a ValidationError
        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert result["field"] == "runtime_data"

    def test_insufficient_data_non_empty(self):
        """Test with non-empty but still insufficient runtime data."""
        input_data = MetricInput(
            requirement_id="req_003b",
            requirement_data={"title": "New requirement"},
            runtime_data={
                "test_history": [{"passed": True}],  # Non-empty to pass validation
                "operational_metrics": {"metric": [1]}  # Non-empty to pass validation
            }
        )

        result = calculate_runtime_correlation_metric(input_data)

        # This should pass validation but return a MetricResult with score 0
        assert hasattr(result, 'score')
        assert result.score == 0.0
        assert result.details["data_points"] == 1

    def test_invalid_input_returns_validation_error(self):
        """Test that invalid input returns ValidationError instead of raising."""
        input_data = MetricInput(
            requirement_id="req_004",
            requirement_data={},
            runtime_data=None
        )

        result = calculate_runtime_correlation_metric(input_data)

        # Check that it returns a ValidationError TypedDict
        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert result["field"] == "runtime_data"
        assert "Invalid input data for runtime correlation metric" in result["message"]
        assert "test_history" in result["constraint"]
        assert "operational_metrics" in result["constraint"]

    def test_missing_test_history_returns_validation_error(self):
        """Test that missing test_history returns ValidationError."""
        input_data = MetricInput(
            requirement_id="req_005",
            requirement_data={},
            runtime_data={
                "operational_metrics": {"cpu": [1, 2, 3]}
            }
        )

        result = calculate_runtime_correlation_metric(input_data)

        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert result["field"] == "runtime_data"

    def test_missing_operational_metrics_returns_validation_error(self):
        """Test that missing operational_metrics returns ValidationError."""
        input_data = MetricInput(
            requirement_id="req_006",
            requirement_data={},
            runtime_data={
                "test_history": [{"passed": True}]
            }
        )

        result = calculate_runtime_correlation_metric(input_data)

        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert result["field"] == "runtime_data"