"""Duplicate flake detection functionality."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile

from flake_graph.vss_adapter import search_similar_flakes, create_flake_document


def find_duplicate_flakes(
    flakes: List[Dict[str, Any]], 
    use_vss: bool = False,
    similarity_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """
    Find duplicate or similar flakes based on their descriptions.
    
    Args:
        flakes: List of flake information dictionaries
        use_vss: Whether to use VSS for similarity detection
        similarity_threshold: Minimum similarity score for VSS matching
    
    Returns:
        List of duplicate groups, each containing:
        - description: The duplicate description
        - flakes: List of flakes with this description
        - similarity_score: (VSS only) Average similarity score
    """
    if use_vss:
        return _find_similar_flakes_with_vss(flakes, similarity_threshold)
    else:
        return _find_exact_duplicates(flakes)


def _find_exact_duplicates(flakes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find flakes with exactly matching descriptions."""
    # Group flakes by description
    description_groups: Dict[str, List[Dict[str, Any]]] = {}
    
    for flake in flakes:
        desc = flake.get("description", "")
        if desc:
            if desc not in description_groups:
                description_groups[desc] = []
            description_groups[desc].append(flake)
    
    # Find duplicates (groups with more than one flake)
    duplicates = []
    for description, flake_list in description_groups.items():
        if len(flake_list) > 1:
            duplicates.append({
                "description": description,
                "flakes": flake_list
            })
    
    return duplicates


def _find_similar_flakes_with_vss(
    flakes: List[Dict[str, Any]], 
    similarity_threshold: float
) -> List[Dict[str, Any]]:
    """Find similar flakes using VSS with complete-linkage clustering."""
    if not flakes:
        return []
    
    # Create temporary database for VSS
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "duplicate_detection.kuzu"
        
        # Convert flakes to VSS documents
        documents = []
        flake_map = {}  # Map document ID to original flake
        
        # Extract base_path if all flakes share a common base
        base_path = None
        if flakes and isinstance(flakes[0].get("path"), Path):
            # Try to find common base path
            all_paths = [f["path"] for f in flakes if isinstance(f.get("path"), Path)]
            if all_paths:
                # Find common parent
                base_path = Path(os.path.commonpath([str(p) for p in all_paths]))
                if base_path.name == "flake.nix":
                    base_path = base_path.parent
        
        for i, flake in enumerate(flakes):
            # Create document using the adapter function for consistency
            doc = create_flake_document(flake, base_path=base_path)
            # Override ID to maintain mapping
            doc["id"] = f"flake_{i}"
            documents.append(doc)
            flake_map[doc["id"]] = flake
        
        # Build pairwise similarity matrix
        similarity_matrix = {}
        
        # Compute all pairwise similarities
        for i, doc in enumerate(documents):
            results = search_similar_flakes(
                query=doc["content"],
                flakes=documents,
                db_path=str(db_path),
                limit=len(documents)
            )
            
            for result in results:
                pair = tuple(sorted([doc["id"], result["id"]]))
                if pair not in similarity_matrix:
                    similarity_matrix[pair] = result["score"]
        
        # Build groups using complete-linkage clustering
        similar_groups = []
        processed_ids = set()
        
        for doc in documents:
            if doc["id"] in processed_ids:
                continue
            
            # Start a new group with current document
            current_group = {doc["id"]}
            processed_ids.add(doc["id"])
            
            # Try to add documents that are similar to ALL in current group
            changed = True
            while changed:
                changed = False
                for other_doc in documents:
                    if other_doc["id"] in current_group or other_doc["id"] in processed_ids:
                        continue
                    
                    # Check if this document is similar to ALL documents in current group
                    min_similarity = 1.0
                    for member_id in current_group:
                        pair = tuple(sorted([member_id, other_doc["id"]]))
                        similarity = similarity_matrix.get(pair, 0.0)
                        min_similarity = min(min_similarity, similarity)
                    
                    # Add only if similar to all members
                    if min_similarity >= similarity_threshold:
                        current_group.add(other_doc["id"])
                        processed_ids.add(other_doc["id"])
                        changed = True
            
            # Add group if it has more than one flake
            if len(current_group) > 1:
                group_flakes = [flake_map[doc_id] for doc_id in current_group]
                
                # Calculate average similarity within group
                total_similarity = 0.0
                pair_count = 0
                group_list = list(current_group)
                for i in range(len(group_list)):
                    for j in range(i + 1, len(group_list)):
                        pair = tuple(sorted([group_list[i], group_list[j]]))
                        total_similarity += similarity_matrix.get(pair, 0.0)
                        pair_count += 1
                
                similar_groups.append({
                    "description": group_flakes[0]["description"],
                    "flakes": group_flakes,
                    "similarity_score": total_similarity / pair_count if pair_count > 0 else 0.0
                })
        
        return similar_groups


def detect_and_report_duplicates(
    base_dir: Path,
    flakes: List[Dict[str, Any]],
    use_vss: bool = False,
    similarity_threshold: float = 0.8
) -> str:
    """
    Detect and generate a report of duplicate flakes.
    
    Args:
        base_dir: Base directory for relative paths
        flakes: List of flake information
        use_vss: Whether to use VSS for similarity detection
        similarity_threshold: Minimum similarity score for VSS matching
    
    Returns:
        Formatted report string
    """
    duplicates = find_duplicate_flakes(flakes, use_vss=use_vss, similarity_threshold=similarity_threshold)
    
    if not duplicates:
        return "No duplicate flakes found."
    
    report_lines = [f"Found {len(duplicates)} duplicate group(s):"]
    
    for i, dup_group in enumerate(duplicates, 1):
        report_lines.append(f"\n{i}. Description: {dup_group['description']}")
        
        if "similarity_score" in dup_group:
            report_lines.append(f"   Similarity Score: {dup_group['similarity_score']:.2f}")
        
        report_lines.append("   Flakes:")
        for flake in dup_group["flakes"]:
            rel_path = flake["path"].relative_to(base_dir) if isinstance(flake["path"], Path) else flake["path"]
            report_lines.append(f"   - {rel_path}")
    
    return "\n".join(report_lines)