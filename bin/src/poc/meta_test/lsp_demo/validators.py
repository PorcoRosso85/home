"""Input validation module."""
from typing import Union, Any


def validate_input(a: Any, b: Any) -> bool:
    """Validate that inputs are numbers."""
    return isinstance(a, (int, float)) and isinstance(b, (int, float))


def validate_positive(value: Union[int, float]) -> bool:
    """Validate that value is positive."""
    return value > 0


def validate_range(value: Union[int, float], min_val: float, max_val: float) -> bool:
    """Validate that value is within range."""
    return min_val <= value <= max_val