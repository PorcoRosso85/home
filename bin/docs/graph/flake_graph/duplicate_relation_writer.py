"""Duplicate relation writer functionality for persisting duplicate relationships as graph edges."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from log_py import log

from .kuzu_adapter_functional import (
    create_connection, 
    KuzuConnection,
    OperationSuccessDict,
    QueryErrorDict,
    ValidationErrorDict
)


class DuplicateRelationWriter:
    """Writer class for persisting duplicate detection results as graph relationships."""
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize the duplicate relation writer with KuzuDB connection.
        
        Args:
            db_path: Path to the KuzuDB database directory
        """
        self.db_path = Path(db_path)
        
    def _create_connection(self) -> Union[KuzuConnection, Dict[str, Any]]:
        """Create a KuzuDB connection."""
        result = create_connection(self.db_path)
        if result.get('ok', False):
            return result['connection']
        else:
            return result
    
    def _ensure_relationship_table(self, connection: KuzuConnection) -> Dict[str, Any]:
        """Ensure DUPLICATES_WITH relationship table exists."""
        try:
            # Create DUPLICATES_WITH relationship table if it doesn't exist
            connection['conn'].execute("""
                CREATE REL TABLE IF NOT EXISTS DUPLICATES_WITH (
                    FROM Flake TO Flake,
                    similarity_score FLOAT,
                    group_id STRING,
                    detected_at STRING,
                    detection_method STRING DEFAULT 'vss_similarity'
                )
            """)
            
            return {
                "ok": True,
                "message": "DUPLICATES_WITH relationship table ensured"
            }
            
        except Exception as e:
            log("ERROR", {
                "uri": "/duplicate_relation_writer/ensure_relationship_table",
                "message": "Failed to create DUPLICATES_WITH table",
                "error": str(e)
            })
            return {
                "ok": False,
                "error_type": "schema_error",
                "message": f"Failed to ensure relationship table: {str(e)}",
                "details": {"exception": str(e)}
            }
    
    def _create_flake_nodes(self, connection: KuzuConnection, flakes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure all flake nodes exist before creating relationships."""
        try:
            created_count = 0
            
            for flake in flakes:
                # Create flake node if it doesn't exist (MERGE-like operation)
                path = str(flake["path"])
                description = flake.get("description", "")
                
                connection['conn'].execute("""
                    MERGE (f:Flake {path: $path})
                    ON CREATE SET f.description = $description
                """, {
                    'path': path,
                    'description': description
                })
                created_count += 1
                
            return {
                "ok": True,
                "nodes_ensured": created_count,
                "message": f"Ensured {created_count} flake nodes exist"
            }
            
        except Exception as e:
            log("ERROR", {
                "uri": "/duplicate_relation_writer/create_flake_nodes",
                "message": "Failed to ensure flake nodes",
                "error": str(e)
            })
            return {
                "ok": False,
                "error_type": "query_error",
                "message": f"Failed to ensure flake nodes: {str(e)}",
                "details": {"exception": str(e)}
            }
    
    def _create_duplicate_edges(self, connection: KuzuConnection, duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create DUPLICATES_WITH edges for duplicate groups."""
        try:
            total_edges_created = 0
            edges_created_details = []
            
            for group_idx, group in enumerate(duplicate_groups):
                flakes = group["flakes"]
                similarity_score = group.get("similarity_score", 0.0)
                group_id = f"dup_group_{group_idx}"
                detected_at = datetime.now().isoformat() + "Z"
                
                # Create bidirectional edges between all pairs in the group (complete graph)
                for i, flake1 in enumerate(flakes):
                    for j, flake2 in enumerate(flakes):
                        if i != j:  # No self-loops
                            path1 = str(flake1["path"])
                            path2 = str(flake2["path"])
                            
                            # Create the relationship
                            connection['conn'].execute("""
                                MATCH (f1:Flake {path: $path1}), (f2:Flake {path: $path2})
                                CREATE (f1)-[r:DUPLICATES_WITH {
                                    similarity_score: $similarity_score,
                                    group_id: $group_id,
                                    detected_at: $detected_at,
                                    detection_method: 'vss_similarity'
                                }]->(f2)
                            """, {
                                'path1': path1,
                                'path2': path2,
                                'similarity_score': similarity_score,
                                'group_id': group_id,
                                'detected_at': detected_at
                            })
                            
                            total_edges_created += 1
                            
                            # Record edge details
                            edges_created_details.append({
                                "source_path": path1,
                                "target_path": path2,
                                "relationship_type": "DUPLICATES_WITH",
                                "similarity_score": similarity_score,
                                "group_id": group_id,
                                "detected_at": detected_at,
                                "detection_method": "vss_similarity"
                            })
            
            return {
                "ok": True,
                "edges_created": total_edges_created,
                "edges_created_details": edges_created_details,
                "message": f"Created {total_edges_created} DUPLICATES_WITH relationships"
            }
            
        except Exception as e:
            log("ERROR", {
                "uri": "/duplicate_relation_writer/create_duplicate_edges",
                "message": "Failed to create duplicate edges",
                "error": str(e)
            })
            return {
                "ok": False,
                "error_type": "query_error", 
                "message": f"Failed to create duplicate edges: {str(e)}",
                "details": {"exception": str(e)}
            }
    
    def persist_duplicate_relationships(self, duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Persist duplicate relationships to the graph database.
        
        Args:
            duplicate_groups: List of duplicate groups from duplicate_detector
            
        Returns:
            Dictionary with success/failure information and edge details
        """
        # Input validation
        if not duplicate_groups:
            return {
                "ok": False,
                "error_type": "validation_error",
                "message": "No groups provided",
                "edges_created": 0
            }
        
        # Validate each group
        for group in duplicate_groups:
            if not group.get("flakes") or len(group["flakes"]) < 2:
                return {
                    "ok": False,
                    "error_type": "validation_error", 
                    "message": "Invalid group data",
                    "edges_created": 0
                }
            
            # Check for invalid flake data
            for flake in group["flakes"]:
                if not flake.get("path") or not flake.get("description"):
                    return {
                        "ok": False,
                        "error_type": "validation_error",
                        "message": "Invalid flake data",
                        "edges_created": 0
                    }
            
            # Check similarity score
            if group.get("similarity_score", 0) < 0:
                return {
                    "ok": False,
                    "error_type": "validation_error",
                    "message": "Invalid similarity score", 
                    "edges_created": 0
                }
        
        # Create connection
        connection = self._create_connection()
        if not isinstance(connection, dict) or 'conn' not in connection:
            return {
                "ok": False,
                "error_type": "connection_error",
                "message": "Failed to create database connection",
                "edges_created": 0
            }
        
        try:
            # Ensure relationship table exists
            table_result = self._ensure_relationship_table(connection)
            if not table_result.get("ok", False):
                return {
                    "ok": False,
                    "error_type": "schema_error",
                    "message": table_result.get("message", "Failed to ensure relationship table"),
                    "edges_created": 0
                }
            
            # Collect all unique flakes from all groups
            all_flakes = []
            for group in duplicate_groups:
                all_flakes.extend(group["flakes"])
            
            # Remove duplicates while preserving order
            seen_paths = set()
            unique_flakes = []
            for flake in all_flakes:
                path = str(flake["path"])
                if path not in seen_paths:
                    seen_paths.add(path)
                    unique_flakes.append(flake)
            
            # Ensure flake nodes exist
            nodes_result = self._create_flake_nodes(connection, unique_flakes)
            if not nodes_result.get("ok", False):
                return {
                    "ok": False,
                    "error_type": "node_creation_error",
                    "message": nodes_result.get("message", "Failed to create flake nodes"),
                    "edges_created": 0
                }
            
            # Create duplicate edges
            edges_result = self._create_duplicate_edges(connection, duplicate_groups)
            if not edges_result.get("ok", False):
                return {
                    "ok": False,
                    "error_type": "edge_creation_error", 
                    "message": edges_result.get("message", "Failed to create edges"),
                    "edges_created": 0
                }
            
            log("INFO", {
                "uri": "/duplicate_relation_writer/persist_duplicate_relationships",
                "message": "Successfully persisted duplicate relationships",
                "groups_processed": len(duplicate_groups),
                "edges_created": edges_result["edges_created"]
            })
            
            return {
                "ok": True,
                "edges_created": edges_result["edges_created"],
                "groups_processed": len(duplicate_groups),
                "edges_created_details": edges_result["edges_created_details"],
                "message": f"Successfully created {edges_result['edges_created']} DUPLICATES_WITH relationships"
            }
            
        except Exception as e:
            log("ERROR", {
                "uri": "/duplicate_relation_writer/persist_duplicate_relationships",
                "message": "Unexpected error during relationship persistence",
                "error": str(e)
            })
            return {
                "ok": False,
                "error_type": "unexpected_error",
                "message": f"Unexpected error: {str(e)}",
                "edges_created": 0
            }


# Functional interface for backward compatibility and easier testing
def persist_duplicate_relationships(duplicate_groups: List[Dict[str, Any]], db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Functional interface for persisting duplicate relationships.
    
    Args:
        duplicate_groups: List of duplicate groups from duplicate_detector
        db_path: Optional database path (uses temporary database if None)
        
    Returns:
        Dictionary with success/failure information and edge details
    """
    # Use a temporary database if no path provided
    if db_path is None:
        import tempfile
        tmpdir = tempfile.mkdtemp()
        db_path = Path(tmpdir) / "duplicate_relations.kuzu"
    
    writer = DuplicateRelationWriter(db_path)
    return writer.persist_duplicate_relationships(duplicate_groups)