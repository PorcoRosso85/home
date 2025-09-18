"""
Domain logic for CallRelationship entity.

This module provides factory functions for creating CallRelationship instances with proper validation.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class CallRelationship:
    """Represents a function call relationship between two code locations."""
    
    from_location_uri: str
    to_location_uri: str
    line_number: Optional[int] = None


def create_call_relationship(
    from_location_uri: str,
    to_location_uri: str,
    line_number: Optional[int] = None,
) -> CallRelationship:
    """
    Factory function to create a CallRelationship instance with validation.
    
    Args:
        from_location_uri: The URI of the calling location
        to_location_uri: The URI of the called location
        line_number: Optional line number where the call occurs
        
    Returns:
        A validated CallRelationship instance
        
    Raises:
        ValueError: If either location_uri is empty or if line_number is invalid
    """
    # Validate from_location_uri
    if not from_location_uri:
        raise ValueError("from_location_uri cannot be empty")
    
    # Validate to_location_uri
    if not to_location_uri:
        raise ValueError("to_location_uri cannot be empty")
    
    # Validate line_number if provided
    if line_number is not None:
        if not isinstance(line_number, int):
            raise ValueError(f"line_number must be an integer, got {type(line_number).__name__}")
        if line_number < 0:
            raise ValueError(f"line_number must be non-negative, got {line_number}")
    
    # Self-recursion is allowed (from_uri == to_uri)
    
    return CallRelationship(
        from_location_uri=from_location_uri,
        to_location_uri=to_location_uri,
        line_number=line_number,
    )