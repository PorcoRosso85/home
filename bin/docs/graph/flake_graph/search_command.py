"""Search command functionality for finding flakes by description and path.

This module implements search functionality that allows users to find relevant flakes
using natural language queries. It supports:

- Case-insensitive search
- Partial matching
- Path pattern matching
- VSS similarity ranking when available
- JSON output format

Business Value:
- Enables developers to quickly find relevant flakes using natural language
- Reduces time spent manually browsing directories
- Improves discoverability of existing flake solutions
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from .scanner import scan_flake_description, scan_readme_content
from .vss_adapter import search_similar_flakes


def search_flakes(
    query: str,
    search_path: str,
    use_vss: bool = False,
    db_path: str = "vss.db",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search for flakes matching the query in path and description.
    
    Args:
        query: Search query text
        search_path: Path to search for flakes
        use_vss: Whether to use VSS for similarity ranking
        db_path: Path to VSS database
        limit: Maximum number of results to return
        
    Returns:
        List of matching flakes with metadata
    """
    target_path = Path(search_path)
    if not target_path.exists():
        return []
    
    # Collect all flakes
    flakes = []
    for flake_path in target_path.rglob("flake.nix"):
        flake_dir = flake_path.parent
        description = scan_flake_description(flake_path)
        readme_content = scan_readme_content(flake_dir)
        
        flake_info = {
            "path": str(flake_dir),
            "description": description or "",
            "readme_content": readme_content or "",
            "flake_path": str(flake_path)
        }
        flakes.append(flake_info)
    
    if not flakes:
        return []
    
    # If VSS is enabled, use similarity search
    if use_vss:
        return _search_with_vss(query, flakes, db_path, limit)
    else:
        return _search_with_text_matching(query, flakes, limit)


def _search_with_vss(
    query: str,
    flakes: List[Dict[str, Any]],
    db_path: str,
    limit: int
) -> List[Dict[str, Any]]:
    """Search using VSS similarity ranking."""
    # Convert flakes to VSS document format
    vss_documents = []
    flake_map = {}
    
    for flake in flakes:
        # Create document ID from path
        relative_path = str(Path(flake["path"]).name)
        doc_id = relative_path
        
        # Combine description and readme for content
        content_parts = []
        if flake["description"]:
            content_parts.append(flake["description"])
        if flake["readme_content"]:
            content_parts.append(flake["readme_content"])
        
        doc = {
            "id": doc_id,
            "content": " ".join(content_parts)
        }
        vss_documents.append(doc)
        flake_map[doc_id] = flake
    
    # Perform VSS search
    vss_result = search_similar_flakes(
        query=query,
        flakes=vss_documents,
        db_path=db_path,
        limit=limit
    )
    
    # Handle VSS errors by falling back to text matching
    if isinstance(vss_result, dict) and "error_type" in vss_result:
        return _search_with_text_matching(query, flakes, limit)
    
    # Convert VSS results back to flake format
    results = []
    if isinstance(vss_result, dict) and "results" in vss_result:
        for vss_match in vss_result["results"]:
            flake_id = vss_match["id"]
            if flake_id in flake_map:
                flake = flake_map[flake_id].copy()
                flake["vss_score"] = vss_match["score"]
                results.append(flake)
    
    return results


def _search_with_text_matching(
    query: str,
    flakes: List[Dict[str, Any]],
    limit: int
) -> List[Dict[str, Any]]:
    """Search using simple text matching."""
    query_lower = query.lower()
    matches = []
    
    for flake in flakes:
        # Check description match
        description_match = False
        if flake["description"]:
            description_match = query_lower in flake["description"].lower()
        
        # Check README content match
        readme_match = False
        if flake["readme_content"]:
            readme_match = query_lower in flake["readme_content"].lower()
        
        # Check path match
        path_match = query_lower in flake["path"].lower()
        
        # If any match found, calculate relevance score
        if description_match or readme_match or path_match:
            score = 0.0
            
            # Higher score for description matches
            if description_match:
                score += 0.5
            
            # Medium score for readme matches  
            if readme_match:
                score += 0.3
            
            # Lower score for path matches
            if path_match:
                score += 0.2
            
            flake_copy = flake.copy()
            flake_copy["text_score"] = score
            matches.append(flake_copy)
    
    # Sort by score descending
    matches.sort(key=lambda x: x["text_score"], reverse=True)
    
    return matches[:limit]


def format_search_results(
    results: List[Dict[str, Any]],
    output_json: bool = False
) -> str:
    """Format search results for output.
    
    Args:
        results: List of search results
        output_json: Whether to output in JSON format
        
    Returns:
        Formatted output string
    """
    if output_json:
        # Convert Path objects to strings for JSON serialization
        json_results = []
        for result in results:
            json_result = {}
            for key, value in result.items():
                if isinstance(value, Path):
                    json_result[key] = str(value)
                else:
                    json_result[key] = value
            json_results.append(json_result)
        
        return json.dumps(json_results, indent=2)
    
    else:
        if not results:
            return "No flakes found matching the query."
        
        output_lines = [f"Found {len(results)} matching flakes:\n"]
        
        for result in results:
            output_lines.append(f"Path: {result['path']}")
            
            if result.get("description"):
                output_lines.append(f"  Description: {result['description']}")
            
            # Show score if available
            if "vss_score" in result:
                output_lines.append(f"  VSS Score: {result['vss_score']:.3f}")
            elif "text_score" in result:
                output_lines.append(f"  Relevance: {result['text_score']:.3f}")
            
            output_lines.append("")  # Empty line between results
        
        return "\n".join(output_lines)