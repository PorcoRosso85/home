"""Error handling utilities for the domain layer."""

from typing import Dict, Any, TypedDict


class ErrorDetails(TypedDict):
    """Type definition for error details."""
    code: str
    message: str
    details: Dict[str, Any]


class ErrorDict(TypedDict):
    """Type definition for error dictionary."""
    error: ErrorDetails


def create_error(code: str, message: str, details: Dict[str, Any] = None) -> ErrorDict:
    """
    Create a standardized error dictionary.
    
    Args:
        code: Error code (e.g., "SYMBOL_VALIDATION_ERROR")
        message: Human-readable error message
        details: Additional error details
        
    Returns:
        Error dictionary
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }