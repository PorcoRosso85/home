"""Tests for existence metric."""

import pytest

from .base import MetricInput
from .existence import ExistenceMetric


class TestExistenceMetric:
    """Test existence metric calculation."""

    def setup_method(self):
        """Set up test fixture."""
        self.metric = ExistenceMetric()

    def test_metric_properties(self):
        """Test metric name and description."""
        assert self.metric.name == "existence"
        assert "existence rate" in self.metric.description

    def test_requirement_with_tests(self):
        """Test requirement that has tests."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "User login"},
            test_data={"test_count": 3}
        )

        result = self.metric.calculate(input_data)

        assert result.score == 1.0
        assert result.details["has_tests"] is True
        assert result.details["test_count"] == 3
        assert len(result.suggestions) == 0

    def test_requirement_without_tests(self):
        """Test requirement that has no tests."""
        input_data = MetricInput(
            requirement_id="req_002",
            requirement_data={"title": "Password reset"},
            test_data={"test_count": 0}
        )

        result = self.metric.calculate(input_data)

        assert result.score == 0.0
        assert result.details["has_tests"] is False
        assert result.details["test_count"] == 0
        assert len(result.suggestions) > 0
        assert "No tests found" in result.suggestions[0]

    def test_missing_test_data(self):
        """Test requirement with missing test data."""
        input_data = MetricInput(
            requirement_id="req_003",
            requirement_data={"title": "Data export"},
            test_data=None
        )

        result = self.metric.calculate(input_data)

        assert result.score == 0.0
        assert result.details["has_tests"] is False
        assert len(result.suggestions) > 0

    def test_invalid_input(self):
        """Test with invalid input data."""
        input_data = MetricInput(
            requirement_id="",
            requirement_data={},
            test_data=None
        )

        with pytest.raises(ValueError, match="Invalid input data"):
            self.metric.calculate(input_data)
