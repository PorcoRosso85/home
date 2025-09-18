"""Factory for creating embedding functions.

This module provides functions to create embedding services,
following the layered architecture principle where application
layer manages the creation of infrastructure components.
"""

from typing import List, Callable
from log_py import log


def create_default_embedding_function() -> Callable[[str], List[float]]:
    """Create the default embedding function using vss_kuzu.
    
    This function is in the application layer and can import from vss_kuzu.application.
    
    Returns:
        A function that takes text and returns embedding vector.
    """
    try:
        # This import is allowed here as we're in the application layer
        from vss_kuzu.application import create_embedding_service
        return create_embedding_service()
    except ImportError as e:
        log("error", {
            "message": "Failed to import embedding service",
            "component": "flake_graph.embedding_factory",
            "operation": "create_default_embedding_function",
            "error": str(e)
        })
        raise
    except Exception as e:
        log("error", {
            "message": "Failed to create embedding service",
            "component": "flake_graph.embedding_factory",
            "operation": "create_default_embedding_function",
            "error": str(e)
        })
        raise


def create_mock_embedding_function(dimension: int = 384) -> Callable[[str], List[float]]:
    """Create a mock embedding function for testing.
    
    Args:
        dimension: Size of the embedding vector to return
        
    Returns:
        A function that returns fixed-size vectors for any input
    """
    def mock_embedding(text: str) -> List[float]:
        # Simple hash-based generation for reproducible results
        hash_value = hash(text) % 1000 / 1000
        return [hash_value + i * 0.001 for i in range(dimension)]
    
    return mock_embedding