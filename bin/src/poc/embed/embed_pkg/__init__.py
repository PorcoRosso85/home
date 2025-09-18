"""
Embed package - Embedding functionality for semantic search
"""
from .embedding_repository_standalone import create_embedding_repository_standalone
from .embeddings.base import create_embedder
from .types import (
    ReferenceDict, SaveResult, FindResult, SearchResult,
    EmbeddingResult, EmbeddingRepository
)

# Export main functions with simpler names
create_embedding_repository = create_embedding_repository_standalone

__all__ = [
    'create_embedding_repository',
    'create_embedding_repository_standalone',
    'create_embedder',
    'ReferenceDict',
    'SaveResult',
    'FindResult',
    'SearchResult',
    'EmbeddingResult',
    'EmbeddingRepository',
]