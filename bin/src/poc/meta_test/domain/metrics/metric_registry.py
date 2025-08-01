"""Registry for all metric functions following functional style."""

from typing import NamedTuple

from domain.metrics.existence_functional import (
    calculate_existence_metric,
    get_metric_info as get_existence_info,
    validate_input as validate_existence_input
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
    # Other metrics would be added here after conversion
}


def get_all_metric_functions() -> list[MetricProtocol]:
    """Get all metric calculation functions."""
    return [bundle.calculate for bundle in METRIC_REGISTRY.values()]


def get_metric_by_name(name: str) -> MetricBundle | None:
    """Get metric bundle by name."""
    return METRIC_REGISTRY.get(name)