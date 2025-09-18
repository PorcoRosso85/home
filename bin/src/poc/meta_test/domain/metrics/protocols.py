"""Protocol definitions for metrics following functional style."""

from typing import Protocol, Union

from domain.metrics.base import MetricInput, MetricResult
from infrastructure.errors import ValidationError


class MetricProtocol(Protocol):
    """Protocol for metric calculation functions."""
    
    def __call__(self, input_data: MetricInput) -> Union[MetricResult, ValidationError]:
        """Calculate metric score."""
        ...


class MetricInfoProtocol(Protocol):
    """Protocol for metric info functions."""
    
    def __call__(self) -> dict[str, str]:
        """Return metric metadata."""
        ...


class ValidationProtocol(Protocol):
    """Protocol for validation functions."""
    
    def __call__(self, input_data: MetricInput) -> bool:
        """Validate input data."""
        ...