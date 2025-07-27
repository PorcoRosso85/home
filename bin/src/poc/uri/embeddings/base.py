"""
Base embeddings protocol - Functional style without classes
Defines the contract for text embedding functions
"""
from typing import TypedDict, List, Union, Literal, Callable, Optional, Dict, Any


class EmbeddingSuccess(TypedDict):
    """Successful embedding result"""
    ok: Literal[True]
    embeddings: List[List[float]]
    model_name: str
    dimensions: int


class EmbeddingError(TypedDict):
    """Embedding operation error"""
    ok: Literal[False]
    error_type: Literal["ModelLoadError", "EncodingError", "ValidationError"]
    message: str
    details: Optional[Dict[str, Any]]


EmbeddingResult = Union[EmbeddingSuccess, EmbeddingError]

# Type alias for embedder function
Embedder = Callable[[List[str]], EmbeddingResult]


def create_embedder(
    model_name: str,
    implementation: Literal["sentence_transformer"],
    **kwargs
) -> Union[Embedder, EmbeddingError]:
    """
    Factory function to create embedder instances
    
    Args:
        model_name: Name of the model to use
        implementation: Type of implementation
        **kwargs: Additional implementation-specific arguments
        
    Returns:
        Either an embedder function or an error
    """
    if implementation == "sentence_transformer":
        from .sentence_transformer import create_sentence_transformer_embedder
        return create_sentence_transformer_embedder(model_name, **kwargs)
    else:
        return {
            "ok": False,
            "error_type": "ValidationError",
            "message": f"Unknown implementation: {implementation}",
            "details": {"supported": ["sentence_transformer"]}
        }