"""VSS adapter for flake exploration."""

from pathlib import Path
from typing import Dict, Any, List

from vss_kuzu import create_vss


def create_flake_document(flake_info: Dict[str, Any]) -> Dict[str, str]:
    """Convert flake info to VSS document format."""
    # Extract relative path from full path
    path = flake_info["path"]
    if isinstance(path, Path):
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