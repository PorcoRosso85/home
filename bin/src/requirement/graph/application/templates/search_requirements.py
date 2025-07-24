"""
Search Requirements Template - semantic search functionality for requirements

This template provides a simple interface for searching requirements using
hybrid search (combining vector similarity and keyword search).
"""
from typing import Dict, Any, List


def search_requirements(query: str, search_adapter, limit: int = 10) -> Dict[str, Any]:
    """
    Search for requirements using hybrid search
    
    Args:
        query: Search query string
        search_adapter: Instance of SearchAdapter
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        Dictionary containing search results or error
    """
    try:
        # Perform hybrid search
        results = search_adapter.search_hybrid(query, k=limit)
        
        # Check for errors in results
        if results and isinstance(results[0], dict) and "error" in results[0]:
            return {
                "status": "error",
                "error": results[0]["error"]
            }
        
        # Format successful results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id", ""),
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "source": result.get("source", "unknown")
            })
        
        return {
            "status": "success",
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "type": "SearchError",
                "message": f"Failed to execute search: {str(e)}"
            }
        }


def process_search_template(input_data: Dict[str, Any], search_factory) -> Dict[str, Any]:
    """
    Process search template input
    
    Args:
        input_data: {"query": "search terms", "limit": 10}
        search_factory: Factory function to create SearchAdapter instance
        
    Returns:
        Search results or error
    """
    # Extract parameters
    query = input_data.get("query", "")
    limit = input_data.get("limit", 10)
    
    # Validate input
    if not query or not isinstance(query, str):
        return {
            "status": "error",
            "error": {
                "type": "InvalidInputError",
                "message": "Query parameter is required and must be a string"
            }
        }
    
    if not isinstance(limit, int) or limit <= 0:
        return {
            "status": "error", 
            "error": {
                "type": "InvalidInputError",
                "message": "Limit parameter must be a positive integer"
            }
        }
    
    # Create search adapter
    search_adapter = search_factory()
    if not search_adapter:
        return {
            "status": "error",
            "error": {
                "type": "ServiceNotAvailable",
                "message": "Search service is not available"
            }
        }
    
    # Execute search
    return search_requirements(query, search_adapter, limit)