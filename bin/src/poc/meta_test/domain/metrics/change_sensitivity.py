"""Metric 4: Change sensitivity - fails when requirements change."""

from typing import Any, Union

from ...infrastructure.errors import ValidationError
from .base import BaseMetric, MetricInput, MetricResult


class ChangeSensitivityMetric(BaseMetric):
    """Measures if tests properly fail when requirements change."""

    @property
    def name(self) -> str:
        return "change_sensitivity"

    @property
    def description(self) -> str:
        return "Change sensitivity - fails when requirements change"

    def validate_input(self, input_data: MetricInput) -> bool:
        """Check if we have test mutation data."""
        return bool(
            input_data.requirement_id and
            input_data.requirement_data and
            input_data.test_data
        )

    def _simulate_requirement_changes(self,
                                    requirement_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate simulated requirement changes."""
        changes = []

        # Change thresholds
        thresholds = requirement_data.get("thresholds", {})
        for field, config in thresholds.items():
            if isinstance(config, dict):
                if "min" in config:
                    # Change minimum value
                    new_config = config.copy()
                    new_config["min"] = config["min"] * 1.1  # 10% increase
                    changes.append({
                        "type": "threshold_change",
                        "field": field,
                        "change": "min",
                        "old_value": config["min"],
                        "new_value": new_config["min"]
                    })

                if "max" in config:
                    # Change maximum value
                    new_config = config.copy()
                    new_config["max"] = config["max"] * 0.9  # 10% decrease
                    changes.append({
                        "type": "threshold_change",
                        "field": field,
                        "change": "max",
                        "old_value": config["max"],
                        "new_value": new_config["max"]
                    })

        # Change business rules
        rules = requirement_data.get("business_rules", [])
        for i, rule in enumerate(rules):
            if isinstance(rule, dict) and "condition" in rule:
                # Invert condition
                changes.append({
                    "type": "rule_change",
                    "rule_index": i,
                    "change": "condition_inverted",
                    "old_value": rule["condition"],
                    "new_value": f"NOT({rule['condition']})"
                })

        return changes

    def _check_test_sensitivity(self,
                              changes: list[dict[str, Any]],
                              test_data: dict[str, Any]) -> dict[str, bool]:
        """Check if tests are sensitive to changes."""
        sensitivity = {}

        # Get mutation test results if available
        mutation_results = test_data.get("mutation_results", {})

        for change in changes:
            change_key = f"{change['type']}_{change.get('field', change.get('rule_index', 'unknown'))}"

            # Check if this change was tested
            if change_key in mutation_results:
                # Test should fail when requirement changes
                sensitivity[change_key] = mutation_results[change_key].get("test_failed", False)
            else:
                # Assume not sensitive if no mutation test exists
                sensitivity[change_key] = False

        return sensitivity

    def calculate(self, input_data: MetricInput) -> Union[MetricResult, ValidationError]:
        """Calculate change sensitivity score."""
        if not self.validate_input(input_data):
            return ValidationError(
                type="ValidationError",
                message="Invalid input data for change sensitivity metric",
                field="input_data",
                value=str(input_data),
                constraint="Must have requirement_id, requirement_data, and test_data",
                suggestion="Ensure all required fields are provided with valid data"
            )

        # Generate potential requirement changes
        changes = self._simulate_requirement_changes(input_data.requirement_data)

        if not changes:
            # No changes to test
            return MetricResult(
                metric_name=self.name,
                requirement_id=input_data.requirement_id,
                score=1.0,  # Perfect score if no changes possible
                details={
                    "change_count": 0,
                    "sensitive_count": 0,
                    "sensitivity_details": {},
                },
                suggestions=[]
            )

        # Check test sensitivity
        sensitivity = self._check_test_sensitivity(changes, input_data.test_data)

        # Calculate score
        sensitive_count = sum(1 for sensitive in sensitivity.values() if sensitive)
        total_count = len(sensitivity)
        score = sensitive_count / total_count if total_count > 0 else 0.0

        # Generate suggestions
        suggestions: list[str] = []
        for change_key, sensitive in sensitivity.items():
            if not sensitive:
                suggestions.append(
                    f"Test is not sensitive to change: {change_key}. "
                    "Add assertions to detect this requirement change."
                )

        return MetricResult(
            metric_name=self.name,
            requirement_id=input_data.requirement_id,
            score=score,
            details={
                "change_count": total_count,
                "sensitive_count": sensitive_count,
                "sensitivity_details": sensitivity,
            },
            suggestions=suggestions
        )
