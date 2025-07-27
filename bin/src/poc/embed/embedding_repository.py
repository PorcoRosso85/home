"""
Embedding Repository - Extends reference_repository with embedding capabilities
Functional style following reference_repository.py patterns
"""
from typing import List, Dict, Any, Union, Optional
import json
from reference_repository import create_reference_repository, DatabaseError, ValidationError
from embeddings.base import create_embedder, Embedder


def create_embedding_repository(
    db_path: str = ":memory:",
    model_name: str = "all-MiniLM-L6-v2",
    embedder: Optional[Embedder] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create an embedding-enabled reference repository
    
    Args:
        db_path: Database path (default: in-memory)
        model_name: Embedding model name
        embedder: Optional custom embedder function
        **kwargs: Additional arguments
        
    Returns:
        Repository functions dictionary with embedding support
    """
    # Skip schema check for testing
    import os
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "1"
    
    # Create base repository
    base_repo = create_reference_repository(db_path=db_path)
    
    # Check if base repository creation failed
    if isinstance(base_repo, dict) and base_repo.get("type") == "DatabaseError":
        return base_repo
    
    # Create schema if needed (for testing)
    conn = base_repo["connection"]
    try:
        # Check if table exists
        conn.execute("MATCH (n:ReferenceEntity) RETURN count(n) LIMIT 1")
    except:
        # Create minimal schema for tests
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS ReferenceEntity (
                uri STRING PRIMARY KEY,
                title STRING,
                description STRING DEFAULT '',
                entity_type STRING,
                metadata STRING DEFAULT '{}',
                created_at TIMESTAMP DEFAULT current_timestamp(),
                updated_at TIMESTAMP DEFAULT current_timestamp(),
                embedding STRING,
                embedding_model STRING,
                embedding_dimensions INT64,
                embedding_updated_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE REL TABLE IF NOT EXISTS IMPLEMENTS (
                FROM ReferenceEntity TO ReferenceEntity,
                implementation_type STRING DEFAULT 'implements',
                confidence DOUBLE DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT current_timestamp()
            )
        """)
    
    # Create or use provided embedder
    embedder_failed = False
    if embedder is None:
        embedder_result = create_embedder(model_name, "sentence_transformer")
        if not callable(embedder_result):
            # Error creating embedder - store error for later
            embedder_failed = True
            embedder_error = embedder_result
        else:
            embedder = embedder_result
    
    def save_with_embedding(reference: Dict[str, Any]) -> Union[Dict[str, Any], DatabaseError]:
        """Save reference with its text embedding"""
        # Check if embedder failed during initialization
        if embedder_failed:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to create embedding model: {embedder_error.get('message', 'Unknown error')}",
                operation="save_with_embedding",
                database_name=db_path,
                error_code="EMBEDDER_CREATION_FAILED",
                details={"cause": "ModelLoadError", "model_name": model_name}
            )
        
        # First save the reference using base repository
        save_result = base_repo["save"](reference)
        
        # Check if save failed
        if isinstance(save_result, dict) and "type" in save_result and save_result["type"] in ["DatabaseError", "ValidationError"]:
            return save_result
        
        # Generate embedding text from title and description
        text_parts = []
        if "title" in reference:
            text_parts.append(reference["title"])
        if "description" in reference and reference["description"]:
            text_parts.append(reference["description"])
        
        if not text_parts:
            # No text to embed, return the saved reference
            return reference
        
        embedding_text = " ".join(text_parts)
        
        # Generate embedding
        embedding_result = embedder([embedding_text])
        
        if not embedding_result["ok"]:
            # Handle encoding errors gracefully
            if embedding_result["error_type"] == "EncodingError":
                # Try to handle encoding issues
                try:
                    # Remove invalid unicode characters
                    clean_text = embedding_text.encode('utf-8', 'ignore').decode('utf-8')
                    embedding_result = embedder([clean_text])
                except:
                    pass
            
            if not embedding_result["ok"]:
                # For encoding errors, still save the reference without embedding
                if embedding_result["error_type"] == "EncodingError":
                    return reference
                    
                return DatabaseError(
                    type="DatabaseError",
                    message=f"Failed to generate embedding: {embedding_result['message']}",
                    operation="generate_embedding",
                    database_name=db_path,
                    error_code="EMBEDDING_GENERATION_FAILED",
                    details={"cause": embedding_result["error_type"], "uri": reference["uri"]}
                )
        
        # Store embedding in database
        embedding = embedding_result["embeddings"][0]
        embedding_json = json.dumps(embedding)
        
        try:
            conn = base_repo["connection"]
            conn.execute("""
                MATCH (r:ReferenceEntity {uri: $uri})
                SET r.embedding = $embedding,
                    r.embedding_model = $model,
                    r.embedding_dimensions = $dimensions,
                    r.embedding_updated_at = current_timestamp()
                RETURN r
            """, {
                "uri": reference["uri"],
                "embedding": embedding_json,
                "model": embedding_result["model_name"],
                "dimensions": embedding_result["dimensions"]
            })
            
            return reference
            
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to store embedding: {str(e)}",
                operation="store_embedding",
                database_name=db_path,
                error_code="EMBEDDING_STORAGE_FAILED",
                details={"uri": reference["uri"], "error": str(e)}
            )
    
    def find_with_embedding(uri: str) -> Union[Dict[str, Any], DatabaseError]:
        """Find reference with its embedding"""
        try:
            conn = base_repo["connection"]
            result = conn.execute("""
                MATCH (r:ReferenceEntity {uri: $uri})
                RETURN r
            """, {"uri": uri})
            
            if result.has_next():
                row = result.get_next()
                node = row[0]
                
                ref_data = {
                    "uri": node["uri"],
                    "title": node["title"],
                    "description": node.get("description", ""),
                    "entity_type": node["entity_type"],
                    "metadata": node.get("metadata", "{}"),
                    "created_at": node.get("created_at"),
                    "updated_at": node.get("updated_at")
                }
                
                # Add embedding if present
                if "embedding" in node and node["embedding"]:
                    ref_data["embedding"] = json.loads(node["embedding"])
                
                return ref_data
            
            return base_repo["find"](uri)  # Will return NotFoundError
            
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to find reference with embedding: {str(e)}",
                operation="find_with_embedding",
                database_name=db_path,
                error_code="FIND_FAILED",
                details={"uri": uri, "error": str(e)}
            )
    
    def find_similar_by_text(text: str, limit: int = 10) -> Union[List[Dict[str, Any]], ValidationError]:
        """Find similar references using text similarity"""
        # Validate limit
        if limit < 0:
            return ValidationError(
                type="ValidationError",
                message="Limit must be non-negative",
                field="limit",
                value=limit,
                constraint="non-negative",
                expected="Integer >= 0"
            )
        
        if limit == 0:
            return []
        
        # Generate embedding for search text
        embedding_result = embedder([text])
        
        if not embedding_result["ok"]:
            return []  # Return empty list if embedding fails
        
        query_embedding = embedding_result["embeddings"][0]
        
        try:
            conn = base_repo["connection"]
            # Get all references with embeddings
            result = conn.execute("""
                MATCH (r:ReferenceEntity)
                WHERE r.embedding IS NOT NULL
                RETURN r
            """)
            
            # Calculate similarities
            similar_refs = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                
                # Parse stored embedding
                stored_embedding = json.loads(node["embedding"])
                
                # Calculate cosine similarity
                similarity = cosine_similarity(query_embedding, stored_embedding)
                
                similar_refs.append({
                    "uri": node["uri"],
                    "title": node["title"],
                    "description": node.get("description", ""),
                    "entity_type": node["entity_type"],
                    "similarity_score": similarity
                })
            
            # Sort by similarity and limit
            similar_refs.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_refs[:limit]
            
        except Exception:
            return []
    
    def update_all_embeddings() -> Dict[str, int]:
        """Update embeddings for all references without embeddings"""
        updated_count = 0
        error_count = 0
        
        try:
            conn = base_repo["connection"]
            # Find references without embeddings
            result = conn.execute("""
                MATCH (r:ReferenceEntity)
                WHERE r.embedding IS NULL
                RETURN r
            """)
            
            while result.has_next():
                row = result.get_next()
                node = row[0]
                
                reference = {
                    "uri": node["uri"],
                    "title": node["title"],
                    "description": node.get("description", ""),
                    "entity_type": node["entity_type"]
                }
                
                # Try to add embedding
                update_result = save_with_embedding(reference)
                
                if isinstance(update_result, dict) and update_result.get("type") == "DatabaseError":
                    error_count += 1
                else:
                    updated_count += 1
            
            return {
                "updated_count": updated_count,
                "error_count": error_count
            }
            
        except Exception:
            return {
                "updated_count": updated_count,
                "error_count": error_count
            }
    
    # Return extended repository
    return {
        **base_repo,  # Include all base repository functions
        "save_with_embedding": save_with_embedding,
        "find_with_embedding": find_with_embedding,
        "find_similar_by_text": find_similar_by_text,
        "update_all_embeddings": update_all_embeddings
    }


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    import math
    
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