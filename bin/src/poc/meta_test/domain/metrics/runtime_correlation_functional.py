"""Metric 6: Runtime correlation - functional implementation."""

from typing import Union

import numpy as np

from ...infrastructure.errors import ValidationError
from .base import MetricInput, MetricResult


def get_metric_info() -> dict[str, str]:
    """Get metric metadata."""
    return {
        "name": "runtime_correlation",
        "description": "Runtime correlation - correlation between test success and operational metrics"
    }


def validate_input(input_data: MetricInput) -> bool:
    """Check if we have runtime data."""
    return bool(
        input_data.requirement_id and
        input_data.runtime_data and
        input_data.runtime_data.get("test_history") and
        input_data.runtime_data.get("operational_metrics")
    )


def _calculate_correlation(test_results: list[bool],
                          metric_values: list[float]) -> tuple[float, float]:
    """Calculate Pearson correlation coefficient and p-value."""
    if len(test_results) != len(metric_values) or len(test_results) < 3:
        return 0.0, 1.0  # No correlation, high p-value

    # Convert test results to numeric (1 for pass, 0 for fail)
    x = np.array([1.0 if result else 0.0 for result in test_results])
    y = np.array(metric_values)

    # Calculate correlation
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0, 1.0  # No variance, no correlation

    correlation = np.corrcoef(x, y)[0, 1]

    # Simple p-value estimation (would use scipy.stats in real implementation)
    n = len(x)
    t_stat = correlation * np.sqrt(n - 2) / np.sqrt(1 - correlation**2)
    # Rough p-value approximation
    p_value = 2 * (1 - min(0.99, abs(t_stat) / 10))

    return float(correlation), float(p_value)


def _analyze_operational_impact(test_history: list[dict],
                               operational_metrics: dict[str, list[float]]) -> dict[str, dict]:
    """Analyze correlation between test results and each operational metric."""
    correlations = {}

    # Extract test results
    test_results = [entry.get("passed", False) for entry in test_history]
    timestamps = [entry.get("timestamp", i) for i, entry in enumerate(test_history)]

    # Analyze each operational metric
    for metric_name, metric_values in operational_metrics.items():
        if len(metric_values) != len(test_results):
            continue

        correlation, p_value = _calculate_correlation(test_results, metric_values)

        # Determine correlation strength
        abs_corr = abs(correlation)
        if abs_corr > 0.7:
            strength = "strong"
        elif abs_corr > 0.4:
            strength = "moderate"
        elif abs_corr > 0.2:
            strength = "weak"
        else:
            strength = "negligible"

        correlations[metric_name] = {
            "correlation": correlation,
            "p_value": p_value,
            "strength": strength,
            "significant": p_value < 0.05,
            "direction": "positive" if correlation > 0 else "negative"
        }

    return correlations


def calculate_runtime_correlation_metric(input_data: MetricInput) -> Union[MetricResult, ValidationError]:
    """Calculate runtime correlation score."""
    if not validate_input(input_data):
        return ValidationError(
            type="ValidationError",
            message="Invalid input data for runtime correlation metric",
            field="runtime_data",
            value=str(input_data.runtime_data) if input_data.runtime_data else "None",
            constraint="runtime_data must contain 'test_history' and 'operational_metrics'",
            suggestion="Ensure runtime_data contains both test_history and operational_metrics fields"
        )

    test_history = input_data.runtime_data.get("test_history", [])
    operational_metrics = input_data.runtime_data.get("operational_metrics", {})

    metric_info = get_metric_info()

    if not test_history or not operational_metrics:
        return MetricResult(
            metric_name=metric_info["name"],
            requirement_id=input_data.requirement_id,
            score=0.0,
            details={
                "data_points": 0,
                "correlations": {},
                "message": "Insufficient runtime data"
            },
            suggestions=["Collect more runtime data to calculate correlations."]
        )

    # Analyze correlations
    correlations = _analyze_operational_impact(test_history, operational_metrics)

    # Calculate score based on significant correlations
    significant_correlations = [
        abs(c["correlation"])
        for c in correlations.values()
        if c["significant"]
    ]

    if significant_correlations:
        # Score based on strongest significant correlation
        score = max(significant_correlations)
    else:
        # No significant correlations found
        score = 0.0

    # Generate suggestions
    suggestions: list[str] = []

    if score < 0.3:
        suggestions.append(
            "Test results show weak correlation with operational metrics. "
            "Consider if the test is measuring the right aspects."
        )

    # Identify metrics with unexpected correlations
    for metric_name, corr_data in correlations.items():
        if corr_data["significant"]:
            if corr_data["direction"] == "negative" and corr_data["correlation"] < -0.5:
                suggestions.append(
                    f"Strong negative correlation with {metric_name}. "
                    f"Test failures might be associated with better {metric_name}."
                )

    # Suggest metrics that should be monitored
    uncorrelated_metrics = [
        name for name, corr in correlations.items()
        if corr["strength"] == "negligible"
    ]
    if uncorrelated_metrics and len(uncorrelated_metrics) < 3:
        suggestions.append(
            f"Consider monitoring impact on: {', '.join(uncorrelated_metrics)}"
        )

    return MetricResult(
        metric_name=metric_info["name"],
        requirement_id=input_data.requirement_id,
        score=score,
        details={
            "data_points": len(test_history),
            "correlations": correlations,
            "significant_count": len(significant_correlations),
            "strongest_correlation": max(
                correlations.items(),
                key=lambda x: abs(x[1]["correlation"])
            )[0] if correlations else None,
        },
        suggestions=suggestions
    )