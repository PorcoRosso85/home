"""Metric 1: Test existence rate - percentage of requirements with tests."""


from .base import BaseMetric, MetricInput, MetricResult


class ExistenceMetric(BaseMetric):
    """Measures if requirements have corresponding tests."""

    @property
    def name(self) -> str:
        return "existence"

    @property
    def description(self) -> str:
        return "Test existence rate - percentage of requirements with tests"

    def validate_input(self, input_data: MetricInput) -> bool:
        """Check if we have requirement and test data."""
        return bool(input_data.requirement_id and input_data.requirement_data)

    def calculate(self, input_data: MetricInput) -> MetricResult:
        """Calculate test existence score."""
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data for existence metric")

        # Check if tests exist for this requirement
        has_tests = bool(input_data.test_data and input_data.test_data.get("test_count", 0) > 0)

        # Binary score: 1.0 if tests exist, 0.0 if not
        score = 1.0 if has_tests else 0.0

        # Generate suggestions
        suggestions: list[str] = []
        if score == 0.0:
            suggestions.append(
                f"No tests found for requirement {input_data.requirement_id}. "
                "Create at least one test to verify this requirement."
            )

        return MetricResult(
            metric_name=self.name,
            requirement_id=input_data.requirement_id,
            score=score,
            details={
                "has_tests": has_tests,
                "test_count": input_data.test_data.get("test_count", 0) if input_data.test_data else 0,
            },
            suggestions=suggestions
        )
