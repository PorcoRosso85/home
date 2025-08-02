"""Duplicate flake detection functionality."""

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
    """Find similar flakes using VSS."""
    if not flakes:
        return []
    
    # Create temporary database for VSS
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "duplicate_detection.kuzu"
        
        # Convert flakes to VSS documents
        documents = []
        flake_map = {}  # Map document ID to original flake
        
        for i, flake in enumerate(flakes):
            doc_id = f"flake_{i}"
            doc = {
                "id": doc_id,
                "content": flake.get("description", "")
            }
            documents.append(doc)
            flake_map[doc_id] = flake
        
        # Build similarity groups
        similar_groups = []
        processed_ids = set()
        
        for doc in documents:
            if doc["id"] in processed_ids:
                continue
            
            # Search for similar flakes
            results = search_similar_flakes(
                query=doc["content"],
                flakes=documents,
                db_path=str(db_path),
                limit=len(documents)
            )
            
            # Group similar flakes
            similar_flakes = []
            total_score = 0.0
            count = 0
            
            for result in results:
                if result["score"] >= similarity_threshold:
                    similar_flakes.append(flake_map[result["id"]])
                    processed_ids.add(result["id"])
                    total_score += result["score"]
                    count += 1
            
            # Add group if it has more than one flake
            if len(similar_flakes) > 1:
                similar_groups.append({
                    "description": similar_flakes[0]["description"],
                    "flakes": similar_flakes,
                    "similarity_score": total_score / count if count > 0 else 0.0
                })
        
        return similar_groups


def detect_and_report_duplicates(
    base_dir: Path,
    flakes: List[Dict[str, Any]],
    use_vss: bool = False
) -> str:
    """
    Detect and generate a report of duplicate flakes.
    
    Args:
        base_dir: Base directory for relative paths
        flakes: List of flake information
        use_vss: Whether to use VSS for similarity detection
    
    Returns:
        Formatted report string
    """
    duplicates = find_duplicate_flakes(flakes, use_vss=use_vss)
    
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