"""
Sentence Transformer embeddings implementation
Functional wrapper around sentence-transformers library
"""
from typing import List, Union, Optional, Dict, Any
from .base import EmbeddingSuccess, EmbeddingError, EmbeddingResult, Embedder


def create_sentence_transformer_embedder(
    model_name: str,
    device: Optional[str] = None,
    cache_folder: Optional[str] = None,
    **kwargs
) -> Union[Embedder, EmbeddingError]:
    """
    Create a sentence transformer embedder function
    
    Args:
        model_name: HuggingFace model name
        device: Device to use (cpu, cuda, etc)
        cache_folder: Local cache directory
        **kwargs: Additional model parameters
        
    Returns:
        Either an embedder function or an error
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return {
            "ok": False,
            "error_type": "ModelLoadError",
            "message": "sentence-transformers not installed",
            "details": {"install": "pip install sentence-transformers"}
        }
    
    # Try to load the model
    try:
        model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_folder,
            **kwargs
        )
        dimensions = model.get_sentence_embedding_dimension()
    except Exception as e:
        return {
            "ok": False,
            "error_type": "ModelLoadError",
            "message": f"Failed to load model {model_name}",
            "details": {"error": str(e), "model_name": model_name}
        }
    
    def embed_texts(texts: List[str]) -> EmbeddingResult:
        """
        Embed a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Embedding result with embeddings or error
        """
        # Validate input
        if not texts:
            return {
                "ok": False,
                "error_type": "ValidationError",
                "message": "Empty text list provided",
                "details": {"texts_count": 0}
            }
        
        if not all(isinstance(text, str) for text in texts):
            return {
                "ok": False,
                "error_type": "ValidationError",
                "message": "All texts must be strings",
                "details": {
                    "invalid_types": [
                        type(t).__name__ for t in texts if not isinstance(t, str)
                    ]
                }
            }
        
        # Perform embedding
        try:
            embeddings = model.encode(texts, convert_to_numpy=True)
            return {
                "ok": True,
                "embeddings": embeddings.tolist(),
                "model_name": model_name,
                "dimensions": dimensions
            }
        except Exception as e:
            return {
                "ok": False,
                "error_type": "EncodingError",
                "message": "Failed to encode texts",
                "details": {
                    "error": str(e),
                    "texts_count": len(texts),
                    "model_name": model_name
                }
            }
    
    return embed_texts