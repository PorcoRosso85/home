"""
Domain logic for Symbol entity.

This module provides factory functions for creating Symbol instances with proper validation.
"""

from typing import Optional
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from tags_in_dir import Symbol


def create_symbol(
    name: str,
    kind: str,
    location_uri: str,
    scope: Optional[str] = None,
    signature: Optional[str] = None,
) -> Symbol:
    """
    Factory function to create a Symbol instance with validation.
    
    Args:
        name: The symbol name
        kind: The type of symbol (e.g., 'function', 'class')
        location_uri: The URI pointing to the symbol location
        scope: Optional scope information
        signature: Optional signature information
        
    Returns:
        A validated Symbol instance
        
    Raises:
        ValueError: If the location_uri is invalid
    """
    # Validate location_uri format
    if not location_uri:
        raise ValueError("location_uri cannot be empty")
    
    if not location_uri.startswith("file://"):
        raise ValueError(f"location_uri must start with 'file://': {location_uri}")
    
    # Check for line number
    if "#L" not in location_uri:
        raise ValueError(f"location_uri must contain line number (#L<number>): {location_uri}")
    
    # Extract and validate line number
    try:
        line_part = location_uri.split("#L")[1]
        if not line_part:  # Handle "#L" with no number
            raise ValueError(f"Invalid line number format in location_uri: {location_uri}")
        line_num = int(line_part)
        if line_num < 0:
            raise ValueError(f"Line number must be non-negative: {line_num}")
    except (IndexError, ValueError) as e:
        if "Line number must be non-negative" in str(e):
            raise  # Re-raise the negative number error as-is
        raise ValueError(f"Invalid line number format in location_uri: {location_uri}") from e
    
    return Symbol(
        name=name,
        kind=kind,
        location_uri=location_uri,
        scope=scope,
        signature=signature,
    )