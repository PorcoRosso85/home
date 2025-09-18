"""
Embeddings module - Functional text embedding abstractions
Following functional design patterns without classes
"""
from typing import Union

from .base import (
    EmbeddingSuccess,
    EmbeddingError,
    EmbeddingResult,
    create_embedder,
)
from .sentence_transformer import (
    create_sentence_transformer_embedder,
)
from .seed_embedder import (
    create_seed_embedder,
    create_semantic_seed_embedder,
)

__all__ = [
    # Types
    "EmbeddingSuccess",
    "EmbeddingError",
    "EmbeddingResult",
    # Base factory
    "create_embedder",
    # Implementations
    "create_sentence_transformer_embedder",
    "create_seed_embedder",
    "create_semantic_seed_embedder",
]