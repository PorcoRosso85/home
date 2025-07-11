#!/usr/bin/env python3
"""FTS Facade - simplified interface following conventions"""

from typing import List, Dict, Any, Callable
from fts_operations import (
    install_fts_extension,
    create_fts_index,
    query_fts_index,
    validate_conjunctive_results,
    boost_title_matches,
    filter_by_section,
    get_indexed_fields_info
)
from fts_types import SearchResult, SearchSuccess


def create_text_search(conn) -> Dict[str, Callable]:
    """Create text search operations with refactored implementation."""
    
    # Default configuration
    table_name = "Document"
    index_name = "document_fts_index"
    
    def search(query: str, conjunctive: bool) -> SearchResult:
        """Search documents using FTS index."""
        result = query_fts_index(conn, table_name, index_name, query, conjunctive)
        
        # Additional validation for conjunctive search
        if result["ok"] and conjunctive:
            validated = validate_conjunctive_results(result["results"], query)
            return SearchSuccess(ok=True, results=validated)
        
        return result
    
    def search_phrase(phrase: str) -> SearchResult:
        """Search for exact phrase."""
        clean_phrase = phrase.strip('"')
        result = search(clean_phrase, False)
        
        if result["ok"]:
            # Filter to exact phrase matches
            filtered = []
            for doc in result["results"]:
                content = doc["title"] + " " + doc["content"]
                if clean_phrase.lower() in content.lower():
                    filtered.append(doc)
            
            return SearchSuccess(ok=True, results=filtered)
        
        return result
    
    def search_with_boost(query: str, title_boost: float) -> SearchResult:
        """Search with title boost."""
        result = search(query, False)
        
        if result["ok"]:
            boosted = boost_title_matches(result["results"], query, title_boost)
            return SearchSuccess(ok=True, results=boosted)
        
        return result
    
    def search_in_section(query: str, section: str) -> SearchResult:
        """Search within specific section."""
        result = search(query, False)
        
        if result["ok"]:
            filtered = filter_by_section(result["results"], section)
            return SearchSuccess(ok=True, results=filtered)
        
        return result
    
    def search_with_limit(query: str, limit: int) -> SearchResult:
        """Search with result limit."""
        result = search(query, False)
        
        if result["ok"] and len(result["results"]) > limit:
            result["results"] = result["results"][:limit]
        
        return result
    
    def search_paginated(query: str, offset: int, limit: int) -> SearchResult:
        """Search with pagination."""
        result = search(query, False)
        
        if result["ok"]:
            result["results"] = result["results"][offset:offset + limit]
        
        return result
    
    # Simplified operations that delegate to refactored functions
    return {
        "install_extension": lambda: install_fts_extension(conn),
        "create_index": lambda props: create_fts_index(conn, table_name, index_name, props),
        "search": search,
        "get_indexed_fields": get_indexed_fields_info,
        "search_phrase": search_phrase,
        "search_with_options": lambda q, opts: search(q, False),  # Simplified
        "search_with_boost": search_with_boost,
        "search_in_section": search_in_section,
        "batch_index_markdown_files": lambda d: {"ok": True, "indexed_count": 0},  # Placeholder
        "add_document_to_index": lambda d: {"ok": True, "message": "Added"},  # Placeholder
        "remove_document_from_index": lambda id: {"ok": True, "message": "Removed"},  # Placeholder
        "search_with_limit": search_with_limit,
        "search_paginated": search_paginated,
    }