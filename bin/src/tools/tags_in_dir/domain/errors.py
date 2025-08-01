"""Error types and utilities following the error-as-value pattern."""

from typing import TypedDict, Any, Optional, Dict


class ErrorDict(TypedDict):
    """Standard error dictionary structure."""
    error: str
    message: str
    details: Optional[Dict[str, Any]]


def create_error(error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> ErrorDict:
    """Create a standardized error dictionary."""
    return ErrorDict(error=error_code, message=message, details=details)


def is_error(result: Any) -> bool:
    """Check if a result is an error dictionary."""
    return (
        isinstance(result, dict) and
        'error' in result and
        'message' in result and
        isinstance(result.get('error'), str) and
        isinstance(result.get('message'), str)
    )