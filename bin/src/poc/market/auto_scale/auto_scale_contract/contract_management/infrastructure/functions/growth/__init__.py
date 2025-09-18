"""Growth analysis functions for auto-scale market system."""

from .metrics import (
    calculate_k_factor,
    calculate_network_value,
    calculate_growth_rate,
    MetricsData,
    MetricsSuccess,
    MetricsError,
    MetricsResult
)

__all__ = [
    # From metrics
    "calculate_k_factor",
    "calculate_network_value",
    "calculate_growth_rate",
    "MetricsData",
    "MetricsSuccess",
    "MetricsError",
    "MetricsResult"
]