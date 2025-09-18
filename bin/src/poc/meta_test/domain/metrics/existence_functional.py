"""Metric 1: Test existence rate - functional implementation."""

from typing import Union

from infrastructure.errors import ValidationError
from domain.metrics.base import MetricInput, MetricResult


def get_metric_info() -> dict[str, str]:
    """Get metric metadata."""
    return {
        "name": "existence",
        "description": "Test existence rate - percentage of requirements with tests"
    }


def validate_input(input_data: MetricInput) -> bool:
    """Check if we have requirement and test data."""
    return bool(input_data.requirement_id and input_data.requirement_data)


def calculate_existence_metric(input_data: MetricInput) -> Union[MetricResult, ValidationError]:
    """Calculate test existence score."""
    if not validate_input(input_data):
        return ValidationError(
            type="ValidationError",
            message="Invalid input data for existence metric",
            field="input_data",
            value=str(input_data),
            constraint="requirement_id and requirement_data must be provided",
            suggestion="Ensure input contains valid requirement_id and requirement_data"
        )

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

    metric_info = get_metric_info()
    return MetricResult(
        metric_name=metric_info["name"],
        requirement_id=input_data.requirement_id,
        score=score,
        details={
            "has_tests": has_tests,
            "test_count": input_data.test_data.get("test_count", 0) if input_data.test_data else 0,
        },
        suggestions=suggestions
    )