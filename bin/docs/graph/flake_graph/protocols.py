"""Protocol definitions for dependency injection in flake_graph.

This module defines protocols (interfaces) to enable proper layered architecture
and dependency injection, avoiding direct imports from application layer.
"""

from typing import Protocol, List, runtime_checkable


@runtime_checkable
class EmbeddingFunction(Protocol):
    """Protocol for embedding generation functions.
    
    This protocol allows infrastructure layer (VSSAdapter) to accept
    embedding functions from application layer without direct import.
    """
    
    def __call__(self, text: str) -> List[float]:
        """Generate embedding vector from text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        ...