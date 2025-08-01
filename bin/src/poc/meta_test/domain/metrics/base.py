"""Base metric interface and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Union

from ...infrastructure.errors import ValidationError


@dataclass
class MetricInput:
    """Input data for metric calculation."""
    requirement_id: str
    requirement_data: dict[str, Any]
    test_data: dict[str, Any] | None = None
    runtime_data: dict[str, Any] | None = None


@dataclass
class MetricResult:
    """Result of metric calculation."""
    metric_name: str
    requirement_id: str
    score: float  # 0.0 to 1.0
    details: dict[str, Any]
    suggestions: list[str]


class BaseMetric(ABC):
    """Base interface for all metrics."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Metric name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Metric description."""
        pass

    @abstractmethod
    def calculate(self, input_data: MetricInput) -> Union[MetricResult, ValidationError]:
        """Calculate the metric score."""
        pass

    @abstractmethod
    def validate_input(self, input_data: MetricInput) -> bool:
        """Validate if input data is sufficient for calculation."""
        pass
