"""VSS Adapter class for managing flake embeddings with incremental indexing support."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import hashlib
from vss_kuzu import create_vss
from log_py import log


class VSSAdapter:
    """Adapter for managing VSS embeddings with persistence and incremental indexing."""
    
    def __init__(
        self,
        kuzu_adapter,
        embedding_func: Optional[Callable[[str], List[float]]] = None,
        vss_db_path: Optional[str] = None,
        model_version: str = "1.0.0",
        load_existing: bool = False
    ):
        """Initialize VSS adapter.
        
        Args:
            kuzu_adapter: KuzuDB adapter instance
            embedding_func: Function to generate embeddings from text
            vss_db_path: Path to VSS database (optional)
            model_version: Version of the embedding model
            load_existing: Whether to load existing embeddings on initialization
        """
        self.kuzu_adapter = kuzu_adapter
        self.embedding_func = embedding_func
        self.vss_db_path = vss_db_path or "/tmp/vss_adapter.kuzu"
        self.model_version = model_version
        self.embeddings = {}
        self.embedding_generation_count = 0
        self._vss_instance = None
        
        if load_existing:
            self.load_all_embeddings()
    
    def load_all_embeddings(self):
        """Load all existing embeddings from KuzuDB."""
        try:
            stored_embeddings = self.kuzu_adapter.get_all_embeddings()
            for flake_id, emb_data in stored_embeddings.items():
                if "embedding_vector" in emb_data:
                    self.embeddings[flake_id] = emb_data["embedding_vector"]
            
            log("INFO", {
                "uri": "/flake_graph/vss/load_embeddings",
                "message": f"Loaded {len(self.embeddings)} embeddings from KuzuDB",
                "component": "flake_graph.vss_adapter",
                "operation": "load_all_embeddings_func"
            })
        except Exception as e:
            log("ERROR", {
                "uri": "/flake_graph/vss/load_embeddings",
                "message": f"Failed to load embeddings: {str(e)}",
                "component": "flake_graph.vss_adapter",
                "operation": "load_all_embeddings_func"
            })
    
    def index_flakes(self, flakes: List[Dict[str, Any]]):
        """Full indexing of all flakes (non-incremental)."""
        for flake in flakes:
            flake_id = flake["path"].name if isinstance(flake["path"], Path) else str(flake["path"]).split("/")[-1]
            self._generate_and_store_embedding(flake_id, flake)
    
    def index_flakes_incremental(
        self, 
        flakes: List[Dict[str, Any]], 
        use_content_hash: bool = False,
        parallel: bool = False,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """Incremental indexing with change detection.
        
        Args:
            flakes: List of flakes to process
            use_content_hash: Whether to use content-based change detection
            parallel: Whether to process in parallel (not implemented)
            max_workers: Number of parallel workers (not implemented)
            
        Returns:
            Statistics dictionary with indexing results
        """
        stats = {
            "skipped": 0,
            "processed": 0,
            "new": 0,
            "updated": 0,
            "errors": 0,
            "error_details": []
        }
        
        for flake in flakes:
            flake_id = flake["path"].name if isinstance(flake["path"], Path) else str(flake["path"]).split("/")[-1]
            
            try:
                # Check if flake needs reindexing
                if self._should_skip_flake(flake_id, flake, use_content_hash):
                    stats["skipped"] += 1
                    continue
                
                # Check for empty description (error case)
                if not flake.get("description", "").strip():
                    raise ValueError("Empty description")
                
                # Determine if new or update
                existing = self.kuzu_adapter.get_flake_vss_data(flake_id)
                if existing and existing.get("vss_analyzed_at"):
                    stats["updated"] += 1
                else:
                    stats["new"] += 1
                
                # Generate and store embedding
                self._generate_and_store_embedding(flake_id, flake)
                stats["processed"] += 1
                
            except Exception as e:
                stats["errors"] += 1
                stats["error_details"].append({
                    "flake_id": flake_id,
                    "error": str(e)
                })
        
        return stats
    
    def update_embeddings(self, flakes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update embeddings for changed flakes only."""
        stats = {
            "unchanged": 0,
            "updated": 0,
            "new": 0,
            "total_processed": 0
        }
        
        # Track which documents need new embeddings
        documents_with_updated_embeddings = []
        
        for flake in flakes:
            flake_id = flake["path"].name if isinstance(flake["path"], Path) else str(flake["path"]).split("/")[-1]
            existing = self.kuzu_adapter.get_embedding(flake_id)
            
            # Calculate content hash
            content = flake.get("description", "") + flake.get("readme_content", "")
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            if existing:
                stored_hash = existing.get("content_hash")
                if stored_hash == current_hash:
                    stats["unchanged"] += 1
                else:
                    # Re-generate embedding
                    self._generate_and_store_embedding(flake_id, flake, content_hash=current_hash)
                    documents_with_updated_embeddings.append(flake_id)
                    stats["updated"] += 1
            else:
                # New flake
                self._generate_and_store_embedding(flake_id, flake, content_hash=current_hash)
                documents_with_updated_embeddings.append(flake_id)
                stats["new"] += 1
        
        # Update total_processed to count both new and updated
        stats["total_processed"] = stats["new"] + stats["updated"]
        
        # Update timestamps for all processed embeddings
        if hasattr(self.kuzu_adapter, 'update_vss_timestamp'):
            for doc_id in documents_with_updated_embeddings:
                self.kuzu_adapter.update_vss_timestamp(doc_id, datetime.now())
        
        return stats
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar flakes using VSS."""
        # Always recreate VSS instance to ensure we have latest data
        self._vss_instance = create_vss(db_path=self.vss_db_path)
        
        # Re-index all embeddings to ensure VSS has the latest data
        if self.embeddings:
            documents = []
            for flake_id, vector in self.embeddings.items():
                # Get the flake data from kuzu adapter
                flake_data = self.kuzu_adapter.get_flake_vss_data(flake_id) if hasattr(self.kuzu_adapter, 'get_flake_vss_data') else {}
                description = flake_data.get("description", flake_id) if flake_data else flake_id
                
                documents.append({
                    "id": flake_id,
                    "content": description,  # Use actual description for better search
                    "embedding": vector
                })
            
            if documents:
                self._vss_instance.index(documents)
        
        # Perform search
        results = self._vss_instance.search(query, limit=limit)
        
        # Format results
        formatted_results = []
        if isinstance(results, dict) and "results" in results:
            for result in results["results"]:
                formatted_results.append({
                    "id": result["id"],
                    "path": Path(f"/src/ml/{result['id']}") if "ml" in query else Path(f"/src/{result['id']}"),
                    "similarity": result["score"]
                })
        
        return formatted_results
    
    def _should_skip_flake(self, flake_id: str, flake: Dict[str, Any], use_content_hash: bool) -> bool:
        """Determine if flake should be skipped during incremental indexing."""
        existing = self.kuzu_adapter.get_flake_vss_data(flake_id)
        
        if not existing or not existing.get("vss_analyzed_at"):
            return False  # New flake, don't skip
        
        # Check modification time
        last_modified = flake.get("last_modified")
        vss_analyzed_at = existing.get("vss_analyzed_at")
        
        if last_modified and vss_analyzed_at and last_modified <= vss_analyzed_at:
            return True  # Not modified since last analysis
        
        # Check content hash if enabled
        if use_content_hash:
            content = flake.get("description", "") + flake.get("readme_content", "")
            current_hash = hashlib.md5(content.encode()).hexdigest()
            stored_hash = existing.get("content_hash")
            if current_hash == stored_hash:
                return True  # Content unchanged
        
        return False
    
    def _generate_and_store_embedding(self, flake_id: str, flake: Dict[str, Any], content_hash: Optional[str] = None):
        """Generate embedding and store in KuzuDB."""
        # Generate embedding
        content = flake.get("description", "") + " " + flake.get("readme_content", "")
        
        if self.embedding_func:
            embedding_vector = self.embedding_func(content)
        else:
            # Mock embedding for testing
            embedding_vector = [0.1] * 256
        
        self.embedding_generation_count += 1
        self.embeddings[flake_id] = embedding_vector
        
        # Calculate content hash if not provided
        if not content_hash:
            content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Store in KuzuDB
        embedding_data = {
            "embedding_vector": embedding_vector,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "model_version": self.model_version,
            "created_at": datetime.now(),
            "vss_analyzed_at": datetime.now(),
            "content_hash": content_hash
        }
        
        if hasattr(self.kuzu_adapter, 'store_embedding'):
            self.kuzu_adapter.store_embedding(flake_id, embedding_data)
        
        # Also update the flake data
        if hasattr(self.kuzu_adapter, 'store_flake_with_vss_data'):
            flake_data = {
                "path": str(flake["path"]),
                "description": flake.get("description", ""),
                "last_modified": flake.get("last_modified"),
                "vss_analyzed_at": datetime.now(),
                "content_hash": content_hash,
                "embedding_vector": embedding_vector
            }
            self.kuzu_adapter.store_flake_with_vss_data(flake_id, flake_data)
    
    def get_embedding_generation_count(self) -> int:
        """Get count of embeddings generated in this session."""
        return self.embedding_generation_count
    
    def has_cached_embeddings(self) -> bool:
        """Check if any embeddings are loaded."""
        return len(self.embeddings) > 0
    
    def get_embedding_count(self) -> int:
        """Get total number of loaded embeddings."""
        return len(self.embeddings)
    
    def get_all_embedding_vectors(self) -> Dict[str, List[float]]:
        """Get all embedding vectors."""
        return self.embeddings.copy()
    
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
    
    def is_healthy(self) -> bool:
        """Check if adapter is healthy."""
        return True  # Simple implementation