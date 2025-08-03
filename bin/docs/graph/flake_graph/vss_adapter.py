"""VSS adapter for flake exploration with KuzuDB persistence."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from vss_kuzu import create_vss
from .kuzu_adapter import KuzuAdapter


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
    
    # Index documents if any
    if documents_to_index:
        try:
            # Index documents in VSS
            index_result = vss.index(documents_to_index)
            
            if index_result.get("ok"):
                stats["indexed"] = len(documents_to_index)
                
                # Get embeddings from VSS and persist to KuzuDB
                # Note: This assumes VSS exposes embeddings after indexing
                # In practice, you might need to extract embeddings differently
                timestamp = datetime.now()
                
                for doc in documents_to_index:
                    flake = flake_map[doc["id"]]
                    flake_path = str(flake["path"])
                    
                    # For now, we'll create a placeholder embedding
                    # In a real implementation, you'd extract the actual embedding from VSS
                    embedding = [0.0] * 384  # Placeholder 384-dim embedding
                    
                    # Update flake with embedding
                    kuzu.update_flake(
                        path=flake_path,
                        vss_embedding=embedding,
                        vss_analyzed_at=timestamp
                    )
            else:
                stats["errors"] = len(documents_to_index)
                
        except Exception as e:
            print(f"Error during indexing: {e}")
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
    vss = create_vss(db_path=vss_db_path)
    kuzu = KuzuAdapter(db_path=kuzu_db_path)
    
    # If using cached embeddings, load flakes from KuzuDB
    if use_cached_embeddings:
        flakes_with_embeddings = kuzu.list_flakes()
        
        # Convert to VSS document format
        documents = []
        for flake in flakes_with_embeddings:
            if flake.get("vss_embedding"):
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