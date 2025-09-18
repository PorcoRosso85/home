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
    embedder_type: Optional[str] = None,
    implementation: Optional[Literal["sentence_transformer", "seed", "semantic_seed"]] = None,
    **kwargs
) -> Union[Embedder, EmbeddingError]:
    """
    Factory function to create embedder instances
    
    Args:
        model_name: Name of the model to use
        embedder_type: Type of embedder (alias for implementation)
        implementation: Type of implementation
        **kwargs: Additional implementation-specific arguments
        
    Returns:
        Either an embedder function or an error
    """
    # Support both embedder_type and implementation parameters
    impl_type = embedder_type or implementation or "sentence_transformer"
    
    # Handle invalid embedder type according to test expectations
    if embedder_type and embedder_type not in ["sentence_transformer", "seed", "semantic_seed"]:
        return {
            "ok": False,
            "error": f"Unknown embedder type: {embedder_type}",
            "details": {"supported": ["sentence_transformer", "seed", "semantic_seed"]}
        }
    
    if impl_type == "sentence_transformer":
        from .sentence_transformer import create_sentence_transformer_embedder
        return create_sentence_transformer_embedder(model_name, **kwargs)
    elif impl_type == "seed":
        from .seed_embedder import create_seed_embedder
        return create_seed_embedder(model_name=model_name, **kwargs)
    elif impl_type == "semantic_seed":
        from .seed_embedder import create_semantic_seed_embedder
        return create_semantic_seed_embedder(model_name=model_name, **kwargs)
    else:
        return {
            "ok": False,
            "error": f"Unknown implementation: {impl_type}",
            "details": {"supported": ["sentence_transformer", "seed", "semantic_seed"]}
        }