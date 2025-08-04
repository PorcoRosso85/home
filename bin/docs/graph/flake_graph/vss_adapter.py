"""VSS adapter for flake exploration with KuzuDB persistence."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json

from vss_kuzu import create_vss
from .kuzu_adapter import KuzuAdapter
from log_py import log


def create_flake_document(flake_info: Dict[str, Any], base_path: Path = None) -> Dict[str, str]:
    """Convert flake info to VSS document format.
    
    Args:
        flake_info: Dictionary with path, description, and optional readme_content
        base_path: Optional base path to compute relative paths from
    
    Returns:
        Dictionary with id and content fields for VSS
    """
    # Extract relative path from full path
    path = flake_info["path"]
    if isinstance(path, Path):
        if base_path:
            # Use parent directory as ID when base_path is provided
            try:
                relative_path = str(path.relative_to(base_path).parent)
            except ValueError:
                # If path is not relative to base_path, use the parent directory name
                relative_path = str(path.parent.name)
        else:
            # Get the relative path starting from 'src' if present
            path_parts = path.parts
            if "src" in path_parts:
                src_index = path_parts.index("src")
                relative_path = "/".join(path_parts[src_index + 1:])
            else:
                relative_path = path.name
    else:
        relative_path = str(path)
    
    # Combine description and readme content
    content_parts = []
    if flake_info.get("description"):
        content_parts.append(flake_info["description"])
    if flake_info.get("readme_content"):
        content_parts.append(flake_info["readme_content"])
    
    return {
        "id": relative_path,
        "content": " ".join(content_parts)
    }


def search_similar_flakes(
    query: str,
    flakes: List[Dict[str, str]],
    db_path: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Search for similar flakes using VSS."""
    # Use actual VSS
    vss = create_vss(db_path=db_path)
    
    # Handle case where VSS is not available (returns dict with 'type' key on error)
    if isinstance(vss, dict) and 'type' in vss:
        log("error", {
            "message": f"VSS initialization failed: {vss.get('message', 'Unknown error')}",
            "component": "flake_graph.vss_adapter",
            "operation": "search_similar_flakes",
            "error": vss.get('type', 'VSSInitializationError'),
            "details": vss.get('details', {})
        })
        # Return error result following error handling convention
        return []
    
    # Index all flakes
    vss.index(flakes)
    
    # Search
    results = vss.search(query, limit=limit)
    
    # Format results
    return [
        {
            "id": result["id"],
            "content": result["content"],
            "score": result["score"]
        }
        for result in results["results"]
    ]




def index_flakes_with_persistence(
    flakes: List[Dict[str, Any]],
    vss_db_path: str,
    kuzu_db_path: str,
    force_reindex: bool = False
) -> Dict[str, Any]:
    """Index flakes with VSS and persist embeddings to KuzuDB.
    
    Args:
        flakes: List of flake information dictionaries
        vss_db_path: Path to VSS database
        kuzu_db_path: Path to KuzuDB database
        force_reindex: If True, reindex all flakes regardless of existing embeddings
        
    Returns:
        Dictionary with indexing results and statistics
    """
    # Initialize adapters
    vss = create_vss(db_path=vss_db_path)
    
    # Handle VSS initialization failure
    if isinstance(vss, dict) and 'type' in vss:
        return {
            "ok": False,
            "stats": {
                "total_flakes": len(flakes),
                "indexed": 0,
                "skipped": 0,
                "errors": len(flakes),
                "new_embeddings": 0,
                "updated_embeddings": 0
            },
            "message": f"VSS initialization failed: {vss.get('message', 'Unknown error')}"
        }
    
    kuzu = KuzuAdapter(db_path=kuzu_db_path)
    
    # Statistics
    stats = {
        "total_flakes": len(flakes),
        "indexed": 0,
        "skipped": 0,
        "errors": 0,
        "new_embeddings": 0,
        "updated_embeddings": 0
    }
    
    # Prepare documents for indexing
    documents_to_index = []
    flake_map = {}  # Map document ID to flake info
    needs_update = {}  # Track which flakes need embedding updates
    
    for flake in flakes:
        flake_path = str(flake["path"])
        
        # Check if flake exists in KuzuDB
        existing_flake = kuzu.read_flake(flake_path)
        
        # Determine if we need to index this flake
        needs_indexing = (
            force_reindex or 
            existing_flake is None or 
            existing_flake.get("vss_embedding") is None
        )
        
        if needs_indexing:
            # Create document for VSS indexing
            doc = create_flake_document(flake)
            documents_to_index.append(doc)
            flake_map[doc["id"]] = flake
            needs_update[doc["id"]] = existing_flake is None
            
            # Create or update flake in KuzuDB (without embedding yet)
            if existing_flake is None:
                kuzu.create_flake(
                    path=flake_path,
                    description=flake.get("description", ""),
                    language=flake.get("language", "nix")
                )
                stats["new_embeddings"] += 1
            else:
                stats["updated_embeddings"] += 1
        else:
            stats["skipped"] += 1
    
    # Index documents and extract embeddings if any
    if documents_to_index:
        try:
            # First, generate embeddings by indexing documents
            index_result = vss.index(documents_to_index)
            
            if index_result.get("ok"):
                stats["indexed"] = len(documents_to_index)
                
                # Extract embeddings using the internal embedding function
                # This is a direct approach to get embeddings
                from vss_kuzu.application import create_embedding_service
                embedding_func = create_embedding_service()
                timestamp = datetime.now()
                
                for doc in documents_to_index:
                    flake = flake_map[doc["id"]]
                    flake_path = str(flake["path"])
                    
                    try:
                        # Generate embedding for the content
                        embedding = embedding_func(doc["content"])
                        
                        # Update flake with embedding
                        kuzu.update_flake(
                            path=flake_path,
                            vss_embedding=embedding,
                            vss_analyzed_at=timestamp
                        )
                    except Exception as e:
                        log("error", {
                            "message": "Failed to generate embedding",
                            "component": "flake_graph.vss_adapter",
                            "operation": "index_flakes_with_persistence",
                            "flake_path": flake_path,
                            "error": str(e)
                        })
                        stats["errors"] += 1
                        stats["indexed"] -= 1
            else:
                stats["errors"] = len(documents_to_index)
                
        except Exception as e:
            log("error", {
                "message": "Error during indexing",
                "component": "flake_graph.vss_adapter",
                "operation": "index_flakes_with_persistence",
                "error": str(e),
                "documents_count": len(documents_to_index)
            })
            stats["errors"] = len(documents_to_index)
    
    # Close connections
    kuzu.close()
    
    return {
        "ok": stats["errors"] == 0,
        "stats": stats,
        "message": f"Indexed {stats['indexed']} flakes, skipped {stats['skipped']}, errors: {stats['errors']}"
    }


def search_similar_flakes_with_kuzu(
    query: str,
    vss_db_path: str,
    kuzu_db_path: str,
    limit: int = 5,
    use_cached_embeddings: bool = True
) -> List[Dict[str, Any]]:
    """Search for similar flakes using VSS with KuzuDB persistence.
    
    Args:
        query: Search query
        vss_db_path: Path to VSS database
        kuzu_db_path: Path to KuzuDB database  
        limit: Maximum number of results
        use_cached_embeddings: If True, use embeddings from KuzuDB when available
        
    Returns:
        List of similar flakes with scores
    """
    kuzu = KuzuAdapter(db_path=kuzu_db_path)
    
    # If using cached embeddings, attempt to use KuzuDB-stored embeddings
    if use_cached_embeddings:
        # Get all flakes with embeddings from KuzuDB
        flakes_with_embeddings = kuzu.list_flakes()
        embeddings_available = [f for f in flakes_with_embeddings if f.get("vss_embedding")]
        
        if embeddings_available:
            # Use direct vector similarity computation
            from vss_kuzu.application import create_embedding_service
            
            try:
                # Generate query embedding
                embedding_func = create_embedding_service()
                query_embedding = embedding_func(query)
                
                # Compute similarities directly
                results = []
                for flake in embeddings_available:
                    score = compute_cosine_similarity(
                        query_embedding, 
                        flake["vss_embedding"]
                    )
                    results.append({
                        "id": flake["path"],
                        "content": flake.get("description", ""),
                        "score": score,
                        "path": flake["path"],
                        "description": flake["description"],
                        "language": flake.get("language"),
                        "vss_analyzed_at": flake.get("vss_analyzed_at")
                    })
                
                # Sort by score and limit results
                results.sort(key=lambda x: x["score"], reverse=True)
                kuzu.close()
                return results[:limit]
                
            except Exception as e:
                log("warning", {
                    "message": "Failed to use cached embeddings, falling back to VSS",
                    "component": "flake_graph.vss_adapter",
                    "operation": "search_similar_flakes_with_kuzu",
                    "error": str(e)
                })
    
    # Fallback to VSS if cached embeddings not available or failed
    vss = create_vss(db_path=vss_db_path)
    
    # Handle VSS initialization failure
    if isinstance(vss, dict) and 'type' in vss:
        log("error", {
            "message": f"VSS initialization failed: {vss.get('message', 'Unknown error')}",
            "component": "flake_graph.vss_adapter",
            "operation": "search_similar_flakes_with_kuzu"
        })
        kuzu.close()
        return []
    
    # Get all flakes for indexing
    all_flakes = kuzu.list_flakes()
    
    # Convert to VSS document format
    documents = []
    for flake in all_flakes:
        documents.append({
            "id": flake["path"],
            "content": flake.get("description", "")
        })
    
    # Index documents
    if documents:
        vss.index(documents)
    
    # Search
    results = vss.search(query, limit=limit)
    
    # Enhance results with KuzuDB data
    enhanced_results = []
    for result in results.get("results", []):
        flake_data = kuzu.read_flake(result["id"])
        if flake_data:
            enhanced_results.append({
                "id": result["id"],
                "content": result["content"],
                "score": result["score"],
                "path": flake_data["path"],
                "description": flake_data["description"],
                "language": flake_data.get("language"),
                "vss_analyzed_at": flake_data.get("vss_analyzed_at")
            })
        else:
            enhanced_results.append(result)
    
    kuzu.close()
    return enhanced_results


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    import math
    
    # Compute dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Compute magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    # Compute cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)
    
    # Ensure result is in [0, 1] range (convert from [-1, 1])
    return (similarity + 1) / 2