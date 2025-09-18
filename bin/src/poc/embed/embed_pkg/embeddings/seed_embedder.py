"""
Seed-based embedder - Generates deterministic embeddings using hash functions
No ML dependencies, purely algorithmic approach
"""
import hashlib
from typing import List, Union
from .base import EmbeddingResult, EmbeddingSuccess, EmbeddingError, Embedder


def create_seed_embedder(
    seed: int = 42,
    dimensions: int = 384,
    model_name: str = "seed-embedder"
) -> Union[Embedder, EmbeddingError]:
    """
    Create a seed-based embedder that generates deterministic embeddings
    
    Args:
        seed: Random seed for deterministic behavior
        dimensions: Number of dimensions for embeddings
        model_name: Name identifier for this embedder
        
    Returns:
        Either an embedder function or an error
    """
    if dimensions <= 0:
        return {
            "ok": False,
            "error_type": "ValidationError",
            "message": f"Invalid dimensions: {dimensions}. Must be positive.",
            "details": {"dimensions": dimensions}
        }
    
    def embed_texts(texts: List[str]) -> EmbeddingResult:
        """
        Generate embeddings for a list of texts using hash-based approach
        
        Args:
            texts: List of strings to embed
            
        Returns:
            EmbeddingResult with deterministic embeddings
        """
        try:
            if not texts:
                return {
                    "ok": False,
                    "error_type": "ValidationError",
                    "message": "Empty text list provided",
                    "details": {"text_count": 0}
                }
            
            embeddings = []
            
            for text in texts:
                # Create a unique hash for each text combined with seed
                text_seed = f"{seed}:{text}"
                
                # Generate multiple hash values to fill dimensions
                embedding = []
                for dim_idx in range(dimensions):
                    # Create unique hash for each dimension
                    dim_text = f"{text_seed}:dim{dim_idx}"
                    hash_obj = hashlib.sha256(dim_text.encode('utf-8'))
                    hash_bytes = hash_obj.digest()
                    
                    # Convert first 8 bytes to float in range [-1, 1]
                    # Use first 8 bytes as uint64, normalize to [-1, 1]
                    value = int.from_bytes(hash_bytes[:8], byteorder='big')
                    normalized = (value / (2**64 - 1)) * 2 - 1
                    embedding.append(normalized)
                
                embeddings.append(embedding)
            
            return {
                "ok": True,
                "embeddings": embeddings,
                "model_name": f"{model_name}-{seed}",
                "dimensions": dimensions
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error_type": "EncodingError",
                "message": f"Failed to generate embeddings: {str(e)}",
                "details": {"exception_type": type(e).__name__}
            }
    
    # Create a wrapper that supports both single text and list interfaces
    def embed_wrapper(text_or_texts):
        """Wrapper that accepts either a single text or list of texts"""
        if isinstance(text_or_texts, str):
            # Single text mode - return single embedding format
            result = embed_texts([text_or_texts])
            if result["ok"]:
                return {
                    "ok": True,
                    "embedding": result["embeddings"][0],
                    "text": text_or_texts,
                    "model": result["model_name"]
                }
            else:
                return result
        else:
            # List mode - return standard format
            return embed_texts(text_or_texts)
    
    return embed_wrapper


def create_semantic_seed_embedder(
    seed: int = 42,
    dimensions: int = 384,
    model_name: str = "semantic-seed-embedder"
) -> Union[Embedder, EmbeddingError]:
    """
    Create a seed-based embedder with pseudo-semantic features
    Generates embeddings that have some semantic properties without ML
    
    Args:
        seed: Random seed for deterministic behavior
        dimensions: Number of dimensions for embeddings
        model_name: Name identifier for this embedder
        
    Returns:
        Either an embedder function or an error
    """
    if dimensions <= 0:
        return {
            "ok": False,
            "error_type": "ValidationError",
            "message": f"Invalid dimensions: {dimensions}. Must be positive.",
            "details": {"dimensions": dimensions}
        }
    
    def embed_texts(texts: List[str]) -> EmbeddingResult:
        """
        Generate pseudo-semantic embeddings using text features
        
        Args:
            texts: List of strings to embed
            
        Returns:
            EmbeddingResult with deterministic embeddings
        """
        try:
            if not texts:
                return {
                    "ok": False,
                    "error_type": "ValidationError",
                    "message": "Empty text list provided",
                    "details": {"text_count": 0}
                }
            
            embeddings = []
            
            for text in texts:
                # Extract simple features
                text_lower = text.lower()
                word_count = len(text.split())
                char_count = len(text)
                unique_chars = len(set(text_lower))
                
                # Create base features
                features = [
                    word_count / 100.0,  # Normalized word count
                    char_count / 1000.0,  # Normalized char count
                    unique_chars / 100.0,  # Normalized unique chars
                    len([c for c in text if c.isupper()]) / (char_count + 1),  # Uppercase ratio
                    len([c for c in text if c.isdigit()]) / (char_count + 1),  # Digit ratio
                    text.count(' ') / (char_count + 1),  # Space ratio
                    text.count('.') / (word_count + 1),  # Sentence approximation
                    text.count(',') / (word_count + 1),  # Comma density
                ]
                
                # Generate remaining dimensions using hash-based approach
                embedding = []
                for dim_idx in range(dimensions):
                    if dim_idx < len(features):
                        # Use extracted features for first dimensions
                        value = features[dim_idx]
                        # Clip to [-1, 1] range
                        value = max(-1.0, min(1.0, value))
                    else:
                        # Use hash-based approach for remaining dimensions
                        # Include features in hash for semantic consistency
                        feature_str = ':'.join(map(str, features))
                        dim_text = f"{seed}:{text}:{feature_str}:dim{dim_idx}"
                        hash_obj = hashlib.sha256(dim_text.encode('utf-8'))
                        hash_bytes = hash_obj.digest()
                        
                        # Convert to float in range [-1, 1]
                        value = int.from_bytes(hash_bytes[:8], byteorder='big')
                        value = (value / (2**64 - 1)) * 2 - 1
                    
                    embedding.append(value)
                
                embeddings.append(embedding)
            
            return {
                "ok": True,
                "embeddings": embeddings,
                "model_name": f"{model_name}-{seed}",
                "dimensions": dimensions
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error_type": "EncodingError",
                "message": f"Failed to generate embeddings: {str(e)}",
                "details": {"exception_type": type(e).__name__}
            }
    
    # Create a wrapper that supports both single text and list interfaces
    def embed_wrapper(text_or_texts):
        """Wrapper that accepts either a single text or list of texts"""
        if isinstance(text_or_texts, str):
            # Single text mode - return single embedding format
            result = embed_texts([text_or_texts])
            if result["ok"]:
                return {
                    "ok": True,
                    "embedding": result["embeddings"][0],
                    "text": text_or_texts,
                    "model": result["model_name"]
                }
            else:
                return result
        else:
            # List mode - return standard format
            return embed_texts(text_or_texts)
    
    return embed_wrapper