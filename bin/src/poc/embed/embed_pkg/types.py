"""
Type definitions for embedding repository
Defines contracts for data structures without external dependencies
"""
from typing import TypedDict, List, Optional, Dict, Any, Union, Literal


# Base reference types (matching asvs_reference structure)
class ReferenceDict(TypedDict, total=False):
    """Reference entity structure"""
    uri: str  # Required
    title: str  # Required
    entity_type: str  # Required
    description: Optional[str]
    tags: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]


# Embedding-specific types
class EmbeddingSuccess(TypedDict):
    """Successful embedding generation result"""
    ok: Literal[True]
    embedding: List[float]
    text: str
    model: str


class EmbeddingError(TypedDict):
    """Failed embedding generation result"""
    ok: Literal[False]
    error: str
    details: Optional[Dict[str, Any]]


# Union type for embedding results
EmbeddingResult = Union[EmbeddingSuccess, EmbeddingError]


# Repository operation results
class SaveResult(TypedDict):
    """Result of save operation"""
    success: bool
    reference: Optional[ReferenceDict]
    error: Optional[str]


class ReferenceWithEmbedding(ReferenceDict):
    """Reference with embedding data"""
    embedding: List[float]


# Find can return None or reference with embedding
FindResult = Optional[ReferenceWithEmbedding]


class SearchMatch(ReferenceDict):
    """Search result with similarity score"""
    similarity_score: float


# Search returns list of matches
SearchResult = List[SearchMatch]


# Error types (following error-as-value pattern)
class DatabaseError(TypedDict):
    """Database operation error"""
    type: Literal["database_error"]
    message: str
    details: Optional[Dict[str, Any]]


class ValidationError(TypedDict):
    """Input validation error"""
    type: Literal["validation_error"]
    message: str
    field: str
    value: Any


class ModelError(TypedDict):
    """Model-related error"""
    type: Literal["model_error"]
    message: str
    model_name: str
    details: Optional[Dict[str, Any]]


# Generic error type
ErrorResult = Union[DatabaseError, ValidationError, ModelError]


# Repository interface types
class EmbeddingRepository(TypedDict):
    """Embedding repository interface"""
    save_with_embedding: Any  # Callable[[ReferenceDict], SaveResult]
    find_with_embedding: Any  # Callable[[str], FindResult]
    find_similar_by_text: Any  # Callable[[str, int], SearchResult]
    find_similar_by_embedding: Any  # Callable[[List[float], int], SearchResult]
    update_all_embeddings: Any  # Callable[[], Dict[str, Any]]


# Type guards for narrowing
def is_embedding_success(result: EmbeddingResult) -> bool:
    """Type guard for embedding success"""
    return result.get("ok", False) is True


def is_embedding_error(result: EmbeddingResult) -> bool:
    """Type guard for embedding error"""
    return result.get("ok", True) is False


def is_error_result(result: Dict[str, Any]) -> bool:
    """Type guard for error results"""
    return "type" in result and result["type"] in ["database_error", "validation_error", "model_error"]