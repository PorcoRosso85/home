"""Tests for reachability metric."""


from .base import MetricInput
from .reachability import ReachabilityMetric


class TestReachabilityMetric:
    """Test reachability metric calculation."""

    def setup_method(self):
        """Set up test fixture."""
        self.metric = ReachabilityMetric()

    def test_metric_properties(self):
        """Test metric name and description."""
        assert self.metric.name == "reachability"
        assert "circular references" in self.metric.description

    def test_no_dependencies(self):
        """Test with no dependencies."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Independent test"},
            test_data={
                "test_id": "test_001",
                "dependencies": {}
            }
        )

        result = self.metric.calculate(input_data)

        assert result.score == 1.0
        assert result.details["has_circular_dependencies"] is False
        assert len(result.suggestions) == 0

    def test_linear_dependencies(self):
        """Test with linear dependencies (no cycles)."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Test with deps"},
            test_data={
                "test_id": "test_003",
                "dependencies": {
                    "test_003": ["test_002"],
                    "test_002": ["test_001"],
                    "test_001": []
                }
            }
        )

        result = self.metric.calculate(input_data)

        assert result.score == 1.0
        assert result.details["has_circular_dependencies"] is False

    def test_circular_dependencies(self):
        """Test with circular dependencies."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Test with cycles"},
            test_data={
                "test_id": "test_001",
                "dependencies": {
                    "test_001": ["test_002"],
                    "test_002": ["test_003"],
                    "test_003": ["test_001"]  # Circular!
                }
            }
        )

        result = self.metric.calculate(input_data)

        assert result.score == 0.0
        assert result.details["has_circular_dependencies"] is True
        assert len(result.suggestions) > 0
        assert "Circular dependency" in result.suggestions[0]

    def test_self_dependency(self):
        """Test with self-referential dependency."""
        input_data = MetricInput(
            requirement_id="req_001",
            requirement_data={"title": "Self-referential test"},
            test_data={
                "test_id": "test_001",
                "dependencies": {
                    "test_001": ["test_001"]  # Self-reference!
                }
            }
        )

        result = self.metric.calculate(input_data)

        assert result.score == 0.0
        assert result.details["has_circular_dependencies"] is True
