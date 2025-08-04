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


class VSSAdapter:
    """Class-based interface for VSS functionality with KuzuDB persistence.
    
    This class provides an object-oriented interface to the VSS adapter functions,
    supporting embedding persistence and incremental indexing for performance optimization.
    """
    
    def __init__(
        self, 
        kuzu_adapter: KuzuAdapter,
        vss_db_path: str = None,
        model_version: str = "1.0.0",
        load_existing: bool = False
    ):
        """Initialize VSS adapter with KuzuDB integration.
        
        Args:
            kuzu_adapter: KuzuAdapter instance for database operations
            vss_db_path: Path to VSS database (optional, uses temp if not provided)
            model_version: Version of the embedding model
            load_existing: If True, load existing embeddings from KuzuDB
        """
        self.kuzu_adapter = kuzu_adapter
        self.vss_db_path = vss_db_path or "/tmp/vss_adapter.kuzu"
        self.model_version = model_version
        self.embeddings = {}
        self._vss_instance = None
        self._embedding_func = None
        
        if load_existing:
            self.load_all_embeddings()
    
    def _get_embedding_func(self):
        """Get or create embedding function."""
        if not self._embedding_func:
            from vss_kuzu.application import create_embedding_service
            self._embedding_func = create_embedding_service()
        return self._embedding_func
    
    def _get_vss_instance(self):
        """Get or create VSS instance."""
        if not self._vss_instance:
            self._vss_instance = create_vss(db_path=self.vss_db_path)
            # Check if VSS initialization failed
            if isinstance(self._vss_instance, dict) and 'type' in self._vss_instance:
                log("error", {
                    "message": f"VSS initialization failed: {self._vss_instance.get('message', 'Unknown error')}",
                    "component": "flake_graph.VSSAdapter",
                    "operation": "__init__",
                    "error": self._vss_instance.get('type', 'VSSInitializationError')
                })
                self._vss_instance = None
        return self._vss_instance
    
    def index_flakes(self, flakes: List[Dict[str, Any]]) -> None:
        """Generate and store embeddings for flakes.
        
        Args:
            flakes: List of flake dictionaries with path, description, etc.
        """
        embedding_func = self._get_embedding_func()
        
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
                embedding_data = {
                    "embedding_vector": embedding_vector,
                    "embedding_model": "cl-nagoya/ruri-v3-30m",  # Using the actual model from vss_kuzu
                    "model_version": self.model_version,
                    "created_at": datetime.now().isoformat(),
                    "content_hash": content_hash
                }
                
                # Cache in memory
                self.embeddings[flake_id] = embedding_vector
                
                # Persist to KuzuDB
                self.kuzu_adapter.store_embedding(flake_id, embedding_data)
                
            except Exception as e:
                log("error", {
                    "message": f"Failed to generate embedding for {flake_id}",
                    "component": "flake_graph.VSSAdapter",
                    "operation": "index_flakes",
                    "error": str(e),
                    "flake_id": flake_id
                })
    
    def index_flakes_with_persistence(
        self,
        flakes: List[Dict[str, Any]],
        base_path: Path = None
    ) -> Dict[str, Any]:
        """Index flakes and persist embeddings to KuzuDB.
        
        This is an alias for index_flakes that returns statistics.
        
        Args:
            flakes: List of flake information dictionaries
            base_path: Base path for computing relative paths
            
        Returns:
            Dictionary with indexing statistics
        """
        start_count = len(self.embeddings)
        self.index_flakes(flakes)
        end_count = len(self.embeddings)
        
        return {
            "indexed": end_count - start_count,
            "total": end_count,
            "model_version": self.model_version
        }
    
    def load_all_embeddings(self) -> None:
        """Load all embeddings from KuzuDB into memory."""
        try:
            stored_embeddings = self.kuzu_adapter.get_all_embeddings()
            for flake_id, emb_data in stored_embeddings.items():
                if "embedding_vector" in emb_data:
                    self.embeddings[flake_id] = emb_data["embedding_vector"]
            
            log("info", {
                "message": f"Loaded {len(self.embeddings)} embeddings from KuzuDB",
                "component": "flake_graph.VSSAdapter",
                "operation": "load_all_embeddings"
            })
            
        except Exception as e:
            log("error", {
                "message": "Failed to load embeddings from KuzuDB",
                "component": "flake_graph.VSSAdapter", 
                "operation": "load_all_embeddings",
                "error": str(e)
            })
    
    def has_cached_embeddings(self) -> bool:
        """Check if embeddings are loaded in memory."""
        return len(self.embeddings) > 0
    
    def get_embedding_count(self) -> int:
        """Get number of loaded embeddings."""
        return len(self.embeddings)
    
    def get_all_embedding_vectors(self) -> Dict[str, List[float]]:
        """Get all embedding vectors."""
        return self.embeddings.copy()
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar flakes using embeddings.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of search results with similarity scores
        """
        # If we have cached embeddings, use direct similarity computation
        if self.embeddings:
            embedding_func = self._get_embedding_func()
            
            try:
                # Generate query embedding
                query_embedding = embedding_func(query)
                
                # Compute similarities
                results = []
                for flake_id, flake_embedding in self.embeddings.items():
                    score = compute_cosine_similarity(query_embedding, flake_embedding)
                    results.append({
                        "id": flake_id,
                        "similarity": score
                    })
                
                # Sort by score and limit
                results.sort(key=lambda x: x["similarity"], reverse=True)
                return results[:limit]
                
            except Exception as e:
                log("error", {
                    "message": "Failed to search with cached embeddings",
                    "component": "flake_graph.VSSAdapter",
                    "operation": "search",
                    "error": str(e)
                })
        
        # Fallback to VSS instance
        vss = self._get_vss_instance()
        if not vss:
            return []
        
        # Index documents if needed
        if not self.has_cached_embeddings():
            flakes = self.kuzu_adapter.list_flakes()
            documents = []
            for flake in flakes:
                doc = create_flake_document(flake)
                documents.append(doc)
            
            if documents:
                vss.index(documents)
        
        # Perform search
        results = vss.search(query, limit=limit)
        return results.get("results", [])
    
    def update_embeddings(self, flakes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update only changed embeddings.
        
        Args:
            flakes: List of flake information dictionaries
            
        Returns:
            Statistics about the update operation
        """
        stats = {"unchanged": 0, "updated": 0, "new": 0, "total_processed": 0}
        
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
            existing = self.kuzu_adapter.get_embedding(flake_id)
            
            if existing:
                if existing.get("content_hash") == current_hash:
                    stats["unchanged"] += 1
                else:
                    # Re-generate embedding
                    self.index_flakes([flake])
                    stats["updated"] += 1
                    stats["total_processed"] += 1
            else:
                # New flake
                self.index_flakes([flake])
                stats["new"] += 1
                stats["total_processed"] += 1
        
        return stats
    
    def check_embedding_compatibility(self) -> Dict[str, Any]:
        """Check model version compatibility of stored embeddings."""
        all_embeddings = self.kuzu_adapter.get_all_embeddings()
        current_version_count = 0
        outdated_version_count = 0
        outdated_embeddings = []
        
        for flake_id, emb_data in all_embeddings.items():
            if emb_data.get("model_version") == self.model_version:
                current_version_count += 1
            else:
                outdated_version_count += 1
                outdated_embeddings.append(flake_id)
        
        return {
            "total_embeddings": len(all_embeddings),
            "current_version_count": current_version_count,
            "outdated_version_count": outdated_version_count,
            "outdated_embeddings": outdated_embeddings
        }
    
    def get_embeddings_needing_update(self) -> List[Dict[str, str]]:
        """Get list of embeddings that need regeneration."""
        report = self.check_embedding_compatibility()
        needs_update = []
        
        for flake_id in report["outdated_embeddings"]:
            needs_update.append({
                "flake_id": flake_id,
                "reason": "model_version_mismatch"
            })
        
        return needs_update