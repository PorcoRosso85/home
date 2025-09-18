"""
Standalone Embedding Repository - Works without asvs_reference dependency
Implements full embedding functionality with pluggable storage backends
Follows functional programming style
"""
from typing import List, Dict, Any, Union, Optional, Callable
import json
import math
from datetime import datetime
from embed_pkg.types import (
    ReferenceDict, SaveResult, FindResult, SearchResult, SearchMatch,
    EmbeddingRepository, DatabaseError, ValidationError, ModelError,
    ReferenceWithEmbedding
)
from embed_pkg.embeddings.base import create_embedder, Embedder
from embed_pkg.embeddings.seed_embedder import create_seed_embedder, create_semantic_seed_embedder


def create_embedding_repository_standalone(
    storage_backend: Optional[Dict[str, Any]] = None,
    use_seed_embedder: bool = False,
    embedder: Optional[Embedder] = None,
    custom_embedder: Optional[Callable] = None,
    model_name: str = "all-MiniLM-L6-v2",
    seed: int = 42,
    dimensions: int = 384,
    **kwargs
) -> EmbeddingRepository:
    """
    Create a standalone embedding repository with pluggable storage
    
    Args:
        storage_backend: Optional dict for storage (default: creates new dict)
        use_seed_embedder: Use seed-based embedder instead of ML model
        embedder: Optional custom embedder function (legacy parameter)
        custom_embedder: Optional custom embedder function
        model_name: Embedding model name (if not using seed/custom embedder)
        seed: Seed for deterministic embeddings
        dimensions: Embedding dimensions
        **kwargs: Additional arguments
        
    Returns:
        Repository functions dictionary with embedding support
    """
    # Initialize storage
    storage = storage_backend if storage_backend is not None else {}
    
    # Initialize embedder
    embedder_instance = None
    embedder_error = None
    
    # Support both embedder and custom_embedder parameters
    if custom_embedder is not None:
        embedder_instance = custom_embedder
    elif embedder is not None:
        embedder_instance = embedder
    elif use_seed_embedder:
        # Use semantic seed embedder for better test results
        embedder_result = create_semantic_seed_embedder(seed=seed, dimensions=dimensions)
        if callable(embedder_result):
            embedder_instance = embedder_result
        else:
            embedder_error = embedder_result
    else:
        # Try to create ML embedder
        embedder_result = create_embedder(model_name, "sentence_transformer")
        if callable(embedder_result):
            embedder_instance = embedder_result
        else:
            embedder_error = embedder_result
    
    def validate_reference(reference: Dict[str, Any]) -> Optional[ValidationError]:
        """Validate reference structure"""
        required_fields = ["uri", "title", "entity_type"]
        for field in required_fields:
            if field not in reference:
                return {
                    "type": "validation_error",
                    "message": f"Missing required field: {field}",
                    "field": field,
                    "value": None
                }
        
        if not isinstance(reference["uri"], str) or not reference["uri"]:
            return {
                "type": "validation_error",
                "message": "URI must be a non-empty string",
                "field": "uri",
                "value": reference["uri"]
            }
        
        return None
    
    def save_with_embedding(reference: ReferenceDict) -> SaveResult:
        """Save reference with its text embedding"""
        # Validate reference
        validation_error = validate_reference(reference)
        if validation_error:
            return {
                "success": False,
                "reference": None,
                "error": validation_error["message"]
            }
        
        # Check if embedder is available
        if embedder_error:
            return {
                "success": False,
                "reference": None,
                "error": f"Embedder not available: {embedder_error.get('message', 'Unknown error')}"
            }
        
        if not embedder_instance:
            return {
                "success": False,
                "reference": None,
                "error": "No embedder configured"
            }
        
        # Generate embedding text
        text_parts = []
        if reference.get("title"):
            text_parts.append(reference["title"])
        if reference.get("description"):
            text_parts.append(reference["description"])
        
        if text_parts:
            embedding_text = " ".join(text_parts)
            
            # Generate embedding
            embedding_result = embedder_instance([embedding_text])
            
            if not embedding_result["ok"]:
                # For encoding errors, save without embedding
                if embedding_result.get("error_type") == "EncodingError":
                    # Save reference without embedding
                    storage[reference["uri"]] = {
                        **reference,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    return {
                        "success": True,
                        "reference": reference,
                        "error": None
                    }
                
                # Handle both 'message' and 'error' fields for error description
                error_msg = embedding_result.get('error') or embedding_result.get('message', 'Unknown error')
                return {
                    "success": False,
                    "reference": None,
                    "error": error_msg
                }
            
            # Store reference with embedding
            enriched_reference = {
                **reference,
                "embedding": embedding_result["embeddings"][0],
                "embedding_model": embedding_result["model_name"],
                "embedding_dimensions": embedding_result["dimensions"],
                "embedding_updated_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        else:
            # No text to embed
            enriched_reference = {
                **reference,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Store in backend
        storage[reference["uri"]] = enriched_reference
        
        return {
            "success": True,
            "reference": reference,
            "error": None
        }
    
    def find_with_embedding(uri: str) -> FindResult:
        """Find reference with its embedding"""
        if uri not in storage:
            return None
        
        stored_ref = storage[uri]
        
        # Build result with core fields
        result: ReferenceWithEmbedding = {
            "uri": stored_ref["uri"],
            "title": stored_ref["title"],
            "entity_type": stored_ref["entity_type"]
        }
        
        # Add optional fields if present
        if "description" in stored_ref:
            result["description"] = stored_ref["description"]
        if "tags" in stored_ref:
            result["tags"] = stored_ref["tags"]
        if "metadata" in stored_ref:
            result["metadata"] = stored_ref["metadata"]
        
        # Add embedding if present
        if "embedding" in stored_ref:
            result["embedding"] = stored_ref["embedding"]
        
        return result
    
    def find_similar_by_text(text: str, limit: int = 10) -> SearchResult:
        """Find similar references using text similarity"""
        # Validate limit
        if limit < 0:
            # Return empty list for invalid limit (following test expectations)
            return []
        
        if limit == 0:
            return []
        
        if not embedder_instance:
            return []
        
        # Generate embedding for search text
        embedding_result = embedder_instance([text])
        
        if not embedding_result["ok"]:
            return []
        
        query_embedding = embedding_result["embeddings"][0]
        
        # Calculate similarities for all references with embeddings
        similarities = []
        
        for uri, ref in storage.items():
            if "embedding" in ref:
                similarity = cosine_similarity(query_embedding, ref["embedding"])
                
                match: SearchMatch = {
                    "uri": ref["uri"],
                    "title": ref["title"],
                    "entity_type": ref["entity_type"],
                    "similarity_score": similarity
                }
                
                # Add optional fields
                if "description" in ref:
                    match["description"] = ref["description"]
                if "tags" in ref:
                    match["tags"] = ref["tags"]
                if "metadata" in ref:
                    match["metadata"] = ref["metadata"]
                
                similarities.append(match)
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top results
        return similarities[:limit]
    
    def find_similar_by_embedding(embedding: List[float], limit: int = 10) -> SearchResult:
        """Find similar references using direct embedding comparison"""
        # Validate limit
        if limit < 0:
            return []
        
        if limit == 0:
            return []
        
        # Calculate similarities for all references with embeddings
        similarities = []
        
        for uri, ref in storage.items():
            if "embedding" in ref:
                similarity = cosine_similarity(embedding, ref["embedding"])
                
                match: SearchMatch = {
                    "uri": ref["uri"],
                    "title": ref["title"],
                    "entity_type": ref["entity_type"],
                    "similarity_score": similarity
                }
                
                # Add optional fields
                if "description" in ref:
                    match["description"] = ref["description"]
                if "tags" in ref:
                    match["tags"] = ref["tags"]
                if "metadata" in ref:
                    match["metadata"] = ref["metadata"]
                
                similarities.append(match)
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top results
        return similarities[:limit]
    
    def update_all_embeddings() -> Dict[str, Any]:
        """Update embeddings for all references without embeddings"""
        if not embedder_instance:
            return {
                "total": 0,
                "updated": 0,
                "failed": 0,
                "updated_count": 0,
                "error_count": 0,
                "errors": ["No embedder configured"]
            }
        
        total_count = len(storage)
        updated_count = 0
        error_count = 0
        errors = []
        
        for uri, ref in storage.items():
            if "embedding" not in ref:
                # Generate embedding text
                text_parts = []
                if ref.get("title"):
                    text_parts.append(ref["title"])
                if ref.get("description"):
                    text_parts.append(ref["description"])
                
                if text_parts:
                    embedding_text = " ".join(text_parts)
                    
                    # Generate embedding
                    embedding_result = embedder_instance([embedding_text])
                    
                    if embedding_result["ok"]:
                        # Update reference with embedding
                        ref["embedding"] = embedding_result["embeddings"][0]
                        ref["embedding_model"] = embedding_result["model_name"]
                        ref["embedding_dimensions"] = embedding_result["dimensions"]
                        ref["embedding_updated_at"] = datetime.now().isoformat()
                        ref["updated_at"] = datetime.now().isoformat()
                        updated_count += 1
                    else:
                        error_count += 1
                        error_msg = embedding_result.get('error') or embedding_result.get('message', 'Unknown error')
                        errors.append(f"{uri}: {error_msg}")
        
        result = {
            "total": total_count,
            "updated": updated_count,
            "failed": error_count,
            # Keep legacy fields for backward compatibility
            "updated_count": updated_count,
            "error_count": error_count
        }
        
        if errors:
            result["errors"] = errors
        
        return result
    
    # Return repository interface
    return {
        "save_with_embedding": save_with_embedding,
        "find_with_embedding": find_with_embedding,
        "find_similar_by_text": find_similar_by_text,
        "find_similar_by_embedding": find_similar_by_embedding,
        "update_all_embeddings": update_all_embeddings
    }


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    if len(vec1) != len(vec2):
        return 0.0
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate magnitudes
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    
    # Avoid division by zero
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    # Calculate cosine similarity
    return dot_product / (mag1 * mag2)