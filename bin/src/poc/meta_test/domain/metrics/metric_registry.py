"""Registry for all metric functions following functional style."""

from typing import NamedTuple

from domain.metrics.existence_functional import (
    calculate_existence_metric,
    get_metric_info as get_existence_info,
    validate_input as validate_existence_input
)
from domain.metrics.reachability_functional import (
    calculate_reachability_metric,
    get_metric_info as get_reachability_info,
    validate_input as validate_reachability_input
)
from domain.metrics.boundary_coverage_functional import (
    calculate_boundary_coverage_metric,
    get_metric_info as get_boundary_coverage_info,
    validate_input as validate_boundary_coverage_input
)
from domain.metrics.change_sensitivity_functional import (
    calculate_change_sensitivity_metric,
    get_metric_info as get_change_sensitivity_info,
    validate_input as validate_change_sensitivity_input
)
from domain.metrics.semantic_alignment_functional import (
    calculate_semantic_alignment_metric,
    get_metric_info as get_semantic_alignment_info,
    validate_input as validate_semantic_alignment_input
)
from domain.metrics.runtime_correlation_functional import (
    calculate_runtime_correlation_metric,
    get_metric_info as get_runtime_correlation_info,
    validate_input as validate_runtime_correlation_input
)
from domain.metrics.value_probability_functional import (
    calculate_value_probability_metric,
    get_metric_info as get_value_probability_info,
    validate_input as validate_value_probability_input
)
from domain.metrics.protocols import MetricProtocol, MetricInfoProtocol, ValidationProtocol


class MetricBundle(NamedTuple):
    """Bundle of functions for a single metric."""
    name: str
    calculate: MetricProtocol
    get_info: MetricInfoProtocol
    validate: ValidationProtocol


# Registry of all available metrics
METRIC_REGISTRY: dict[str, MetricBundle] = {
    "existence": MetricBundle(
        name="existence",
        calculate=calculate_existence_metric,
        get_info=get_existence_info,
        validate=validate_existence_input
    ),
    "reachability": MetricBundle(
        name="reachability",
        calculate=calculate_reachability_metric,
        get_info=get_reachability_info,
        validate=validate_reachability_input
    ),
    "boundary_coverage": MetricBundle(
        name="boundary_coverage",
        calculate=calculate_boundary_coverage_metric,
        get_info=get_boundary_coverage_info,
        validate=validate_boundary_coverage_input
    ),
    "change_sensitivity": MetricBundle(
        name="change_sensitivity",
        calculate=calculate_change_sensitivity_metric,
        get_info=get_change_sensitivity_info,
        validate=validate_change_sensitivity_input
    ),
    "semantic_alignment": MetricBundle(
        name="semantic_alignment",
        calculate=calculate_semantic_alignment_metric,
        get_info=get_semantic_alignment_info,
        validate=validate_semantic_alignment_input
    ),
    "runtime_correlation": MetricBundle(
        name="runtime_correlation",
        calculate=calculate_runtime_correlation_metric,
        get_info=get_runtime_correlation_info,
        validate=validate_runtime_correlation_input
    ),
    "value_probability": MetricBundle(
        name="value_probability",
        calculate=calculate_value_probability_metric,
        get_info=get_value_probability_info,
        validate=validate_value_probability_input
    ),
}


def get_all_metric_functions() -> list[MetricProtocol]:
    """Get all metric calculation functions."""
    return [bundle.calculate for bundle in METRIC_REGISTRY.values()]


def get_metric_by_name(name: str) -> MetricBundle | None:
    """Get metric bundle by name."""
    return METRIC_REGISTRY.get(name)