"""Metric 3: Boundary value coverage - testing thresholds."""

from typing import Any, Union

from ...infrastructure.errors import ValidationError
from .base import BaseMetric, MetricInput, MetricResult


class BoundaryCoverageMetric(BaseMetric):
    """Measures if tests cover boundary values and edge cases."""

    @property
    def name(self) -> str:
        return "boundary_coverage"

    @property
    def description(self) -> str:
        return "Boundary value coverage - testing thresholds"

    def validate_input(self, input_data: MetricInput) -> bool:
        """Check if we have test case data."""
        return bool(
            input_data.requirement_id and
            input_data.requirement_data and
            input_data.test_data
        )

    def _extract_boundaries(self, requirement_data: dict[str, Any]) -> list[tuple[str, Any, Any]]:
        """Extract boundary values from requirement."""
        boundaries = []

        # Look for threshold values in requirement
        thresholds = requirement_data.get("thresholds", {})
        for field, config in thresholds.items():
            if isinstance(config, dict):
                min_val = config.get("min")
                max_val = config.get("max")
                if min_val is not None:
                    boundaries.append((field, "min", min_val))
                if max_val is not None:
                    boundaries.append((field, "max", max_val))

        # Look for numeric constraints
        constraints = requirement_data.get("constraints", {})
        for field, value in constraints.items():
            if isinstance(value, (int, float)):
                boundaries.append((field, "exact", value))

        return boundaries

    def _check_boundary_coverage(self,
                               boundaries: list[tuple[str, Any, Any]],
                               test_cases: list[dict[str, Any]]) -> dict[str, bool]:
        """Check which boundaries are covered by tests."""
        coverage = {}

        for field, boundary_type, value in boundaries:
            key = f"{field}_{boundary_type}_{value}"
            covered = False

            for test_case in test_cases:
                test_values = test_case.get("input_values", {})

                if boundary_type == "min":
                    # Check for values at, below, and just above minimum
                    if field in test_values:
                        test_val = test_values[field]
                        if test_val in [value, value - 1, value + 1]:
                            covered = True
                            break

                elif boundary_type == "max":
                    # Check for values at, above, and just below maximum
                    if field in test_values:
                        test_val = test_values[field]
                        if test_val in [value, value + 1, value - 1]:
                            covered = True
                            break

                elif boundary_type == "exact":
                    # Check for exact value and neighbors
                    if field in test_values:
                        test_val = test_values[field]
                        if abs(test_val - value) <= 1:
                            covered = True
                            break

            coverage[key] = covered

        return coverage

    def calculate(self, input_data: MetricInput) -> Union[MetricResult, ValidationError]:
        """Calculate boundary coverage score."""
        if not self.validate_input(input_data):
            return ValidationError(
                type="ValidationError",
                message="Invalid input data for boundary coverage metric",
                field="input_data",
                value=str(input_data),
                constraint="Must have requirement_id, requirement_data, and test_data",
                suggestion="Ensure input_data contains all required fields"
            )

        # Extract boundaries from requirement
        boundaries = self._extract_boundaries(input_data.requirement_data)

        if not boundaries:
            # No boundaries to test
            return MetricResult(
                metric_name=self.name,
                requirement_id=input_data.requirement_id,
                score=1.0,  # Perfect score if no boundaries exist
                details={
                    "boundary_count": 0,
                    "covered_count": 0,
                    "coverage_details": {},
                },
                suggestions=[]
            )

        # Check coverage
        test_cases = input_data.test_data.get("test_cases", [])
        coverage = self._check_boundary_coverage(boundaries, test_cases)

        # Calculate score
        covered_count = sum(1 for covered in coverage.values() if covered)
        total_count = len(coverage)
        score = covered_count / total_count if total_count > 0 else 0.0

        # Generate suggestions
        suggestions: list[str] = []
        for boundary_key, covered in coverage.items():
            if not covered:
                suggestions.append(f"Add test case for boundary: {boundary_key}")

        return MetricResult(
            metric_name=self.name,
            requirement_id=input_data.requirement_id,
            score=score,
            details={
                "boundary_count": total_count,
                "covered_count": covered_count,
                "coverage_details": coverage,
            },
            suggestions=suggestions
        )
