"""VSS adapter for flake exploration with KuzuDB persistence.

This module provides Vector Similarity Search (VSS) functionality for flake exploration
using a functional approach with TypedDict for state management. It follows the layered 
architecture principle by accepting embedding functions via dependency injection, avoiding 
direct imports from the application layer.

Usage:
    from flake_graph.embedding_factory import create_default_embedding_function
    from flake_graph.vss_adapter import create_vss_state, index_flakes_func, search_func
    from flake_graph.kuzu_adapter import KuzuAdapter
    
    # Create dependencies
    kuzu_adapter = KuzuAdapter(db_path="path/to/db")
    embedding_func = create_default_embedding_function()
    
    # Create VSS state with dependency injection
    vss_state = create_vss_state(
        kuzu_adapter=kuzu_adapter,
        embedding_func=embedding_func
    )
    
    # Use the functional interface
    updated_state = index_flakes_func(vss_state, flakes)
    results, final_state = search_func(updated_state, "query text")
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, TypedDict, Union
from datetime import datetime
import hashlib
import json

from vss_kuzu import create_vss
from .kuzu_adapter import KuzuAdapter
from log_py import log


# TypedDict definitions for data structures
class EmbeddingData(TypedDict):
    """Structure for storing embedding information."""
    embedding_vector: List[float]
    embedding_model: str
    model_version: str
    created_at: str
    content_hash: str


# Error type definitions following error handling convention
class VSSInitializationError(TypedDict):
    """Error when VSS initialization fails."""
    error_type: str  # Always "vss_initialization_error"
    message: str
    details: Dict[str, Any]


class EmbeddingGenerationError(TypedDict):
    """Error when embedding generation fails."""
    error_type: str  # Always "embedding_generation_error"
    message: str
    flake_id: str
    details: Dict[str, Any]


class SearchError(TypedDict):
    """Error when search operation fails."""
    error_type: str  # Always "search_error"
    message: str
    query: str
    details: Dict[str, Any]


class IndexingError(TypedDict):
    """Error when indexing operation fails."""
    error_type: str  # Always "indexing_error"
    message: str
    document_count: int
    details: Dict[str, Any]


# Success type definitions
class SearchResult(TypedDict):
    """Successful search result."""
    id: str
    content: str
    score: float
    path: Optional[str]
    description: Optional[str]
    language: Optional[str]
    vss_analyzed_at: Optional[str]


class SearchSuccess(TypedDict):
    """Successful search operation."""
    results: List[SearchResult]
    total_found: int


class IndexingStats(TypedDict):
    """Statistics for indexing operations."""
    documents_processed: int
    documents_indexed: int
    documents_failed: int
    time_elapsed: float


class IndexingSuccess(TypedDict):
    """Successful indexing operation."""
    indexed: int
    total: int
    model_version: str
    stats: IndexingStats


class VSSState(TypedDict):
    """State structure for VSS adapter functionality."""
    kuzu_adapter: KuzuAdapter
    vss_db_path: str
    model_version: str
    embeddings: Dict[str, List[float]]
    vss_instance: Optional[Any]
    embedding_func: Optional[Callable[[str], List[float]]]


class IndexingStats(TypedDict):
    """Statistics for indexing operations."""
    indexed: int
    total: int
    model_version: str


class UpdateStats(TypedDict):
    """Statistics for update operations."""
    unchanged: int
    updated: int
    new: int
    total_processed: int


class CompatibilityReport(TypedDict):
    """Embedding compatibility report structure."""
    total_embeddings: int
    current_version_count: int
    outdated_version_count: int
    outdated_embeddings: List[str]


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
) -> Union[SearchSuccess, VSSInitializationError, SearchError]:
    """Search for similar flakes using VSS."""
    # Use actual VSS
    vss = create_vss(db_path=db_path)
    
    # Handle case where VSS is not available (returns dict with 'type' key on error)
    if isinstance(vss, dict) and 'type' in vss:
        error: VSSInitializationError = {
            "error_type": "vss_initialization_error",
            "message": f"VSS initialization failed: {vss.get('message', 'Unknown error')}",
            "details": vss
        }
        log("ERROR", {
            "uri": "/flake_graph/vss/search",
            "message": error["message"],
            "component": "flake_graph.vss_adapter",
            "operation": "search_similar_flakes",
            "error": error["error_type"],
            "details": error["details"]
        })
        return error
    
    try:
        # Index all flakes
        vss.index(flakes)
        
        # Search
        results = vss.search(query, limit=limit)
        
        # Format results
        formatted_results = [
            SearchResult(
                id=result["id"],
                content=result["content"],
                score=result["score"],
                path=None,
                description=None,
                language=None,
                vss_analyzed_at=None
            )
            for result in results["results"]
        ]
        
        success: SearchSuccess = {
            "results": formatted_results,
            "total_found": len(formatted_results)
        }
        return success
    except Exception as e:
        error: SearchError = {
            "error_type": "search_error",
            "message": f"Search operation failed: {str(e)}",
            "query": query,
            "details": {"exception": str(e)}
        }
        log("ERROR", {
            "uri": "/flake_graph/vss/search",
            "message": error["message"],
            "component": "flake_graph.vss_adapter",
            "operation": "search_similar_flakes",
            "error": error["error_type"],
            "query": query
        })
        return error




def index_flakes_with_persistence(
    flakes: List[Dict[str, Any]],
    vss_db_path: str,
    kuzu_db_path: str,
    force_reindex: bool = False,
    embedding_func: Optional[Callable[[str], List[float]]] = None
) -> Dict[str, Any]:
    """Index flakes with VSS and persist embeddings to KuzuDB.
    
    Args:
        flakes: List of flake information dictionaries
        vss_db_path: Path to VSS database
        kuzu_db_path: Path to KuzuDB database
        force_reindex: If True, reindex all flakes regardless of existing embeddings
        embedding_func: Optional embedding function for generating vectors
        
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
                
                # Extract embeddings using the provided embedding function
                if not embedding_func:
                    raise ValueError(
                        "embedding_func parameter is required for generating embeddings"
                    )
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
                        log("ERROR", {
                            "uri": "/flake_graph/vss/index",
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
            log("ERROR", {
                "uri": "/flake_graph/vss/index",
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
    use_cached_embeddings: bool = True,
    embedding_func: Optional[Callable[[str], List[float]]] = None
) -> Union[SearchSuccess, VSSInitializationError, SearchError]:
    """Search for similar flakes using VSS with KuzuDB persistence.
    
    Args:
        query: Search query
        vss_db_path: Path to VSS database
        kuzu_db_path: Path to KuzuDB database  
        limit: Maximum number of results
        use_cached_embeddings: If True, use embeddings from KuzuDB when available
        embedding_func: Optional embedding function for generating query vectors
        
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
            if not embedding_func:
                kuzu.close()
                error: SearchError = {
                    "error_type": "search_error",
                    "message": "embedding_func parameter is required for generating query embeddings",
                    "query": query,
                    "details": {"reason": "missing_embedding_func"}
                }
                return error
            
            try:
                # Generate query embedding
                query_embedding = embedding_func(query)
                
                # Compute similarities directly
                results = []
                for flake in embeddings_available:
                    score = compute_cosine_similarity(
                        query_embedding, 
                        flake["vss_embedding"]
                    )
                    results.append(
                        SearchResult(
                            id=flake["path"],
                            content=flake.get("description", ""),
                            score=score,
                            path=flake["path"],
                            description=flake["description"],
                            language=flake.get("language"),
                            vss_analyzed_at=flake.get("vss_analyzed_at")
                        )
                    )
                
                # Sort by score and limit results
                results.sort(key=lambda x: x["score"], reverse=True)
                kuzu.close()
                
                success: SearchSuccess = {
                    "results": results[:limit],
                    "total_found": len(results)
                }
                return success
                
            except Exception as e:
                log("WARN", {
                    "uri": "/flake_graph/vss/search_kuzu",
                    "message": "Failed to use cached embeddings, falling back to VSS",
                    "component": "flake_graph.vss_adapter",
                    "operation": "search_similar_flakes_with_kuzu",
                    "error": str(e)
                })
    
    # Fallback to VSS if cached embeddings not available or failed
    vss = create_vss(db_path=vss_db_path)
    
    # Handle VSS initialization failure
    if isinstance(vss, dict) and 'type' in vss:
        kuzu.close()
        error: VSSInitializationError = {
            "error_type": "vss_initialization_error",
            "message": f"VSS initialization failed: {vss.get('message', 'Unknown error')}",
            "details": vss
        }
        log("ERROR", {
            "uri": "/flake_graph/vss/search_kuzu",
            "message": error["message"],
            "component": "flake_graph.vss_adapter",
            "operation": "search_similar_flakes_with_kuzu"
        })
        return error
    
    try:
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
                enhanced_results.append(
                    SearchResult(
                        id=result["id"],
                        content=result["content"],
                        score=result["score"],
                        path=flake_data["path"],
                        description=flake_data["description"],
                        language=flake_data.get("language"),
                        vss_analyzed_at=flake_data.get("vss_analyzed_at")
                    )
                )
            else:
                enhanced_results.append(
                    SearchResult(
                        id=result["id"],
                        content=result["content"],
                        score=result["score"],
                        path=None,
                        description=None,
                        language=None,
                        vss_analyzed_at=None
                    )
                )
        
        kuzu.close()
        success: SearchSuccess = {
            "results": enhanced_results,
            "total_found": len(enhanced_results)
        }
        return success
    except Exception as e:
        kuzu.close()
        error: SearchError = {
            "error_type": "search_error",
            "message": f"Search operation failed: {str(e)}",
            "query": query,
            "details": {"exception": str(e)}
        }
        log("ERROR", {
            "uri": "/flake_graph/vss/search_kuzu",
            "message": error["message"],
            "component": "flake_graph.vss_adapter",
            "operation": "search_similar_flakes_with_kuzu",
            "error": error["error_type"]
        })
        return error


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


# Functional implementations of VSSAdapter functionality

def create_vss_state(
    kuzu_adapter: KuzuAdapter,
    vss_db_path: str = None,
    model_version: str = "1.0.0",
    load_existing: bool = False,
    embedding_func: Optional[Callable[[str], List[float]]] = None
) -> VSSState:
    """Create initial VSS state.
    
    Args:
        kuzu_adapter: KuzuAdapter instance for database operations
        vss_db_path: Path to VSS database (optional, uses temp if not provided)
        model_version: Version of the embedding model
        load_existing: If True, load existing embeddings from KuzuDB
        embedding_func: Optional embedding function for dependency injection
        
    Returns:
        Initial VSSState dictionary
    """
    state: VSSState = {
        'kuzu_adapter': kuzu_adapter,
        'vss_db_path': vss_db_path or "/tmp/vss_adapter.kuzu",
        'model_version': model_version,
        'embeddings': {},
        'vss_instance': None,
        'embedding_func': embedding_func
    }
    
    if load_existing:
        state = load_all_embeddings_func(state)
    
    return state


def get_embedding_func(state: VSSState) -> Callable[[str], List[float]]:
    """Get embedding function from state.
    
    Args:
        state: Current VSS state
        
    Returns:
        Embedding function
        
    Raises:
        ValueError: If no embedding function is available
    """
    if not state['embedding_func']:
        raise ValueError(
            "No embedding function provided. Please pass embedding_func when creating VSS state."
        )
    return state['embedding_func']


def get_vss_instance(state: VSSState) -> tuple[Optional[Any], VSSState]:
    """Get or create VSS instance.
    
    Args:
        state: Current VSS state
        
    Returns:
        Tuple of (vss_instance, updated_state)
    """
    if state['vss_instance']:
        return state['vss_instance'], state
    
    vss_instance = create_vss(db_path=state['vss_db_path'])
    
    # Check if VSS initialization failed
    if isinstance(vss_instance, dict) and 'type' in vss_instance:
        log("ERROR", {
            "uri": "/flake_graph/vss/init",
            "message": f"VSS initialization failed: {vss_instance.get('message', 'Unknown error')}",
            "component": "flake_graph.vss_adapter",
            "operation": "get_vss_instance",
            "error": vss_instance.get('type', 'VSSInitializationError')
        })
        return None, state
    
    # Update state with instance
    new_state = state.copy()
    new_state['vss_instance'] = vss_instance
    return vss_instance, new_state


def index_flakes_func(state: VSSState, flakes: List[Dict[str, Any]]) -> VSSState:
    """Generate and store embeddings for flakes.
    
    Args:
        state: Current VSS state
        flakes: List of flake dictionaries with path, description, etc.
        
    Returns:
        Updated VSS state with new embeddings
    """
    embedding_func = get_embedding_func(state)
    new_embeddings = state['embeddings'].copy()
    
    for flake in flakes:
        # Extract flake ID from path
        if isinstance(flake.get("path"), Path):
            flake_id = flake["path"].name
        else:
            flake_id = str(flake.get("path", "unknown"))
        
        # Create content for embedding
        content = create_flake_document(flake)["content"]
        
        # Generate embedding
        try:
            embedding_vector = embedding_func(content)
            
            # Create content hash for change detection
            content_hash = hashlib.md5(
                (flake.get("description", "") + flake.get("readme_content", "")).encode()
            ).hexdigest()
            
            # Store embedding data
            embedding_data: EmbeddingData = {
                "embedding_vector": embedding_vector,
                "embedding_model": "cl-nagoya/ruri-v3-30m",  # Using the actual model from vss_kuzu
                "model_version": state['model_version'],
                "created_at": datetime.now().isoformat(),
                "content_hash": content_hash
            }
            
            # Cache in memory
            new_embeddings[flake_id] = embedding_vector
            
            # Persist to KuzuDB
            state['kuzu_adapter'].store_embedding(flake_id, embedding_data)
            
        except Exception as e:
            log("ERROR", {
                "uri": "/flake_graph/vss/index_func",
                "message": f"Failed to generate embedding for {flake_id}",
                "component": "flake_graph.vss_adapter",
                "operation": "index_flakes_func",
                "error": str(e),
                "flake_id": flake_id
            })
    
    # Return updated state
    new_state = state.copy()
    new_state['embeddings'] = new_embeddings
    return new_state


def index_flakes_with_persistence_func(
    state: VSSState,
    flakes: List[Dict[str, Any]],
    base_path: Path = None
) -> tuple[IndexingStats, VSSState]:
    """Index flakes and persist embeddings to KuzuDB.
    
    Args:
        state: Current VSS state
        flakes: List of flake information dictionaries
        base_path: Base path for computing relative paths
        
    Returns:
        Tuple of (indexing statistics, updated state)
    """
    start_count = len(state['embeddings'])
    updated_state = index_flakes_func(state, flakes)
    end_count = len(updated_state['embeddings'])
    
    stats: IndexingStats = {
        "indexed": end_count - start_count,
        "total": end_count,
        "model_version": state['model_version']
    }
    
    return stats, updated_state


def load_all_embeddings_func(state: VSSState) -> VSSState:
    """Load all embeddings from KuzuDB into memory.
    
    Args:
        state: Current VSS state
        
    Returns:
        Updated state with loaded embeddings
    """
    try:
        stored_embeddings = state['kuzu_adapter'].get_all_embeddings()
        new_embeddings = state['embeddings'].copy()
        
        for flake_id, emb_data in stored_embeddings.items():
            if "embedding_vector" in emb_data:
                new_embeddings[flake_id] = emb_data["embedding_vector"]
        
        log("INFO", {
            "uri": "/flake_graph/vss/load_embeddings",
            "message": f"Loaded {len(new_embeddings)} embeddings from KuzuDB",
            "component": "flake_graph.vss_adapter",
            "operation": "load_all_embeddings_func"
        })
        
        # Return updated state
        new_state = state.copy()
        new_state['embeddings'] = new_embeddings
        return new_state
        
    except Exception as e:
        log("ERROR", {
            "uri": "/flake_graph/vss/load_embeddings",
            "message": "Failed to load embeddings from KuzuDB",
            "component": "flake_graph.vss_adapter", 
            "operation": "load_all_embeddings_func",
            "error": str(e)
        })
        return state


def has_cached_embeddings(state: VSSState) -> bool:
    """Check if embeddings are loaded in memory.
    
    Args:
        state: Current VSS state
        
    Returns:
        True if embeddings exist in state
    """
    return len(state['embeddings']) > 0


def get_embedding_count(state: VSSState) -> int:
    """Get number of loaded embeddings.
    
    Args:
        state: Current VSS state
        
    Returns:
        Number of embeddings
    """
    return len(state['embeddings'])


def get_all_embedding_vectors(state: VSSState) -> Dict[str, List[float]]:
    """Get all embedding vectors.
    
    Args:
        state: Current VSS state
        
    Returns:
        Copy of all embeddings
    """
    return state['embeddings'].copy()


def search_func(state: VSSState, query: str, limit: int = 5) -> tuple[Union[SearchSuccess, SearchError], VSSState]:
    """Search for similar flakes using embeddings.
    
    Args:
        state: Current VSS state
        query: Search query text
        limit: Maximum number of results
        
    Returns:
        Tuple of (search results, potentially updated state)
    """
    # If we have cached embeddings, use direct similarity computation
    if state['embeddings']:
        try:
            embedding_func = get_embedding_func(state)
        except ValueError as e:
            error: SearchError = {
                "error_type": "search_error",
                "message": str(e),
                "query": query,
                "details": {"reason": "missing_embedding_func"}
            }
            return error, state
        
        try:
            # Generate query embedding
            query_embedding = embedding_func(query)
            
            # Compute similarities
            results = []
            for flake_id, flake_embedding in state['embeddings'].items():
                score = compute_cosine_similarity(query_embedding, flake_embedding)
                results.append(
                    SearchResult(
                        id=flake_id,
                        content="",
                        score=score,
                        path=None,
                        description=None,
                        language=None,
                        vss_analyzed_at=None
                    )
                )
            
            # Sort by score and limit
            results.sort(key=lambda x: x["score"], reverse=True)
            success: SearchSuccess = {
                "results": results[:limit],
                "total_found": len(results)
            }
            return success, state
            
        except Exception as e:
            error: SearchError = {
                "error_type": "search_error",
                "message": "Failed to search with cached embeddings",
                "query": query,
                "details": {"exception": str(e)}
            }
            log("ERROR", {
                "uri": "/flake_graph/vss/search_func",
                "message": error["message"],
                "component": "flake_graph.vss_adapter",
                "operation": "search_func",
                "error": str(e)
            })
            # Fall through to VSS instance search
    
    # Fallback to VSS instance
    vss, updated_state = get_vss_instance(state)
    if not vss:
        error: VSSInitializationError = {
            "error_type": "vss_initialization_error",
            "message": "Failed to initialize VSS instance",
            "details": {}
        }
        return error, updated_state
    
    try:
        # Index documents if needed
        if not has_cached_embeddings(updated_state):
            flakes = updated_state['kuzu_adapter'].list_flakes()
            documents = []
            for flake in flakes:
                doc = create_flake_document(flake)
                documents.append(doc)
            
            if documents:
                vss.index(documents)
        
        # Perform search
        results = vss.search(query, limit=limit)
        formatted_results = [
            SearchResult(
                id=result["id"],
                content=result.get("content", ""),
                score=result.get("score", 0.0),
                path=None,
                description=None,
                language=None,
                vss_analyzed_at=None
            )
            for result in results.get("results", [])
        ]
        
        success: SearchSuccess = {
            "results": formatted_results,
            "total_found": len(formatted_results)
        }
        return success, updated_state
    except Exception as e:
        error: SearchError = {
            "error_type": "search_error",
            "message": f"VSS search failed: {str(e)}",
            "query": query,
            "details": {"exception": str(e)}
        }
        log("ERROR", {
            "uri": "/flake_graph/vss/search_func",
            "message": error["message"],
            "component": "flake_graph.vss_adapter",
            "operation": "search_func",
            "error": error["error_type"]
        })
        return error, updated_state


def update_embeddings_func(state: VSSState, flakes: List[Dict[str, Any]]) -> tuple[UpdateStats, VSSState]:
    """Update only changed embeddings.
    
    Args:
        state: Current VSS state
        flakes: List of flake information dictionaries
        
    Returns:
        Tuple of (update statistics, updated state)
    """
    stats: UpdateStats = {"unchanged": 0, "updated": 0, "new": 0, "total_processed": 0}
    current_state = state
    
    for flake in flakes:
        # Extract flake ID
        if isinstance(flake.get("path"), Path):
            flake_id = flake["path"].name
        else:
            flake_id = str(flake.get("path", "unknown"))
        
        # Compute content hash
        current_hash = hashlib.md5(
            (flake.get("description", "") + flake.get("readme_content", "")).encode()
        ).hexdigest()
        
        # Check if embedding exists
        existing = state['kuzu_adapter'].get_embedding(flake_id)
        
        if existing:
            if existing.get("content_hash") == current_hash:
                stats["unchanged"] += 1
            else:
                # Re-generate embedding
                current_state = index_flakes_func(current_state, [flake])
                stats["updated"] += 1
                stats["total_processed"] += 1
        else:
            # New flake
            current_state = index_flakes_func(current_state, [flake])
            stats["new"] += 1
            stats["total_processed"] += 1
    
    return stats, current_state


def check_embedding_compatibility_func(state: VSSState) -> CompatibilityReport:
    """Check model version compatibility of stored embeddings.
    
    Args:
        state: Current VSS state
        
    Returns:
        Compatibility report
    """
    all_embeddings = state['kuzu_adapter'].get_all_embeddings()
    current_version_count = 0
    outdated_version_count = 0
    outdated_embeddings = []
    
    for flake_id, emb_data in all_embeddings.items():
        if emb_data.get("model_version") == state['model_version']:
            current_version_count += 1
        else:
            outdated_version_count += 1
            outdated_embeddings.append(flake_id)
    
    report: CompatibilityReport = {
        "total_embeddings": len(all_embeddings),
        "current_version_count": current_version_count,
        "outdated_version_count": outdated_version_count,
        "outdated_embeddings": outdated_embeddings
    }
    
    return report


def get_embeddings_needing_update_func(state: VSSState) -> List[Dict[str, str]]:
    """Get list of embeddings that need regeneration.
    
    Args:
        state: Current VSS state
        
    Returns:
        List of embeddings needing update
    """
    report = check_embedding_compatibility_func(state)
    needs_update = []
    
    for flake_id in report["outdated_embeddings"]:
        needs_update.append({
            "flake_id": flake_id,
            "reason": "model_version_mismatch"
        })
    
    return needs_update


# Compatibility wrapper for backward compatibility
class VSSAdapter:
    """Class-based compatibility wrapper for functional VSS implementation.
    
    This class provides backward compatibility for existing code that uses the
    class-based interface. It wraps the functional implementation, maintaining
    the same API while using the functional approach internally.
    """
    
    def __init__(
        self, 
        kuzu_adapter: KuzuAdapter,
        vss_db_path: str = None,
        model_version: str = "1.0.0",
        load_existing: bool = False,
        embedding_func: Optional[Callable[[str], List[float]]] = None
    ):
        """Initialize VSS adapter wrapper.
        
        Args:
            kuzu_adapter: KuzuAdapter instance for database operations
            vss_db_path: Path to VSS database (optional, uses temp if not provided)
            model_version: Version of the embedding model
            load_existing: If True, load existing embeddings from KuzuDB
            embedding_func: Optional embedding function for dependency injection
        """
        self._state = create_vss_state(
            kuzu_adapter=kuzu_adapter,
            vss_db_path=vss_db_path,
            model_version=model_version,
            load_existing=load_existing,
            embedding_func=embedding_func
        )
        
        # Expose some attributes for compatibility
        self.kuzu_adapter = kuzu_adapter
        self.vss_db_path = self._state['vss_db_path']
        self.model_version = model_version
        self._embedding_func = embedding_func
    
    @property
    def embeddings(self) -> Dict[str, List[float]]:
        """Get embeddings from state."""
        return self._state['embeddings']
    
    def index_flakes(self, flakes: List[Dict[str, Any]]) -> None:
        """Generate and store embeddings for flakes."""
        self._state = index_flakes_func(self._state, flakes)
    
    def index_flakes_with_persistence(
        self,
        flakes: List[Dict[str, Any]],
        base_path: Path = None
    ) -> Dict[str, Any]:
        """Index flakes and persist embeddings to KuzuDB."""
        stats, self._state = index_flakes_with_persistence_func(self._state, flakes, base_path)
        return stats
    
    def load_all_embeddings(self) -> None:
        """Load all embeddings from KuzuDB into memory."""
        self._state = load_all_embeddings_func(self._state)
    
    def has_cached_embeddings(self) -> bool:
        """Check if embeddings are loaded in memory."""
        return has_cached_embeddings(self._state)
    
    def get_embedding_count(self) -> int:
        """Get number of loaded embeddings."""
        return get_embedding_count(self._state)
    
    def get_all_embedding_vectors(self) -> Dict[str, List[float]]:
        """Get all embedding vectors."""
        return get_all_embedding_vectors(self._state)
    
    def search(self, query: str, limit: int = 5) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Search for similar flakes using embeddings.
        
        Returns:
            Either a list of results (for backward compatibility) or an error dict
        """
        result, self._state = search_func(self._state, query, limit)
        
        # Check if it's an error
        if "error_type" in result:
            # Return error as dict for backward compatibility
            return result
        
        # Extract results list for backward compatibility
        return result["results"]
    
    def update_embeddings(self, flakes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update only changed embeddings."""
        stats, self._state = update_embeddings_func(self._state, flakes)
        return stats
    
    def check_embedding_compatibility(self) -> Dict[str, Any]:
        """Check model version compatibility of stored embeddings."""
        return check_embedding_compatibility_func(self._state)
    
    def get_embeddings_needing_update(self) -> List[Dict[str, str]]:
        """Get list of embeddings that need regeneration."""
        return get_embeddings_needing_update_func(self._state)


