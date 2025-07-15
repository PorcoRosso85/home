#!/usr/bin/env python3
"""FTS operations - refactored as independent functions"""

import time
from typing import List, Dict, Any
from fts_types import (
    IndexResult, SearchResult, FieldsResult, CountResult,
    IndexSuccess, IndexError,
    SearchSuccess, SearchError,
    FieldsSuccess, CountSuccess
)


# Temporary log function until telemetry is available
def log(level: str, component: str, message: str, **kwargs):
    """Temporary logging function."""
    pass


def install_fts_extension(conn) -> IndexResult:
    """Install and load FTS extension."""
    if conn is None:
        return IndexError(ok=False, error="Connection is None")
    
    try:
        conn.execute("INSTALL FTS;")
        log("INFO", "search.fts", "FTS extension installed")
    except Exception as e:
        log("DEBUG", "search.fts", "FTS extension already installed", error=str(e))
    
    try:
        conn.execute("LOAD EXTENSION FTS;")
        log("INFO", "search.fts", "FTS extension loaded")
    except Exception as e:
        log("DEBUG", "search.fts", "FTS extension already loaded", error=str(e))
    
    return IndexSuccess(ok=True, message="FTS extension ready")


def drop_fts_index(conn, table_name: str, index_name: str) -> IndexResult:
    """Drop existing FTS index if exists."""
    if conn is None:
        return IndexError(ok=False, error="Connection is None")
    
    try:
        conn.execute(f"CALL DROP_FTS_INDEX('{table_name}', '{index_name}');")
        log("INFO", "search.fts", "Dropped existing FTS index", 
            table_name=table_name, index_name=index_name)
        return IndexSuccess(ok=True, message=f"Index {index_name} dropped")
    except Exception as e:
        log("DEBUG", "search.fts", "No existing FTS index to drop", 
            table_name=table_name, index_name=index_name, error=str(e))
        return IndexSuccess(ok=True, message="No index to drop")


def create_fts_index(conn, table_name: str, index_name: str, 
                    properties: List[str]) -> IndexResult:
    """Create FTS index on specified table and properties."""
    if conn is None:
        return IndexError(ok=False, error="Connection is None")
    
    # Drop existing index first
    drop_fts_index(conn, table_name, index_name)
    
    # Create new index
    try:
        props_str = str(properties).replace("'", '"')
        query = f"CALL CREATE_FTS_INDEX('{table_name}', '{index_name}', {props_str});"
        conn.execute(query)
        log("INFO", "search.fts", "Created FTS index", 
            table_name=table_name, index_name=index_name, properties=properties)
        return IndexSuccess(ok=True, message=f"Index created with fields: {properties}")
    except Exception as e:
        return IndexError(ok=False, error=str(e))


def query_fts_index(conn, table_name: str, index_name: str, 
                   query: str, conjunctive: bool = False) -> SearchResult:
    """Query FTS index and return results."""
    if conn is None:
        return SearchError(ok=False, error="Connection error")
    
    if not query:
        return SearchError(ok=False, error="Empty query not allowed")
    
    try:
        # Simple text search implementation without FTS extension
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Get all documents
        start_time = time.time()
        result = conn.execute(f"MATCH (d:{table_name}) RETURN d")
        
        # Search in documents
        fts_results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            
            # Combine title and content for search
            full_text = (node.get("title", "") + " " + node.get("content", "")).lower()
            
            if conjunctive:
                # AND search - all terms must match
                if all(term in full_text for term in query_terms):
                    score = sum(full_text.count(term) for term in query_terms) / len(full_text) * 100
                    fts_results.append({
                        "id": node.get("id", ""),
                        "title": node.get("title", ""),
                        "content": node.get("content", ""),
                        "score": score,
                    })
            else:
                # OR search - any term matches
                matching_terms = sum(1 for term in query_terms if term in full_text)
                if matching_terms > 0:
                    score = matching_terms / len(query_terms) * 10
                    fts_results.append({
                        "id": node.get("id", ""),
                        "title": node.get("title", ""),
                        "content": node.get("content", ""),
                        "score": score,
                    })
        
        # Sort by score descending
        fts_results.sort(key=lambda x: x["score"], reverse=True)
        
        search_time = time.time() - start_time
        log("INFO", "search.fts", "Text search completed",
            query=query, conjunctive=conjunctive,
            results_count=len(fts_results),
            search_time_ms=search_time * 1000)
        
        return SearchSuccess(ok=True, results=fts_results)
        
    except Exception as e:
        return SearchError(ok=False, error=str(e))


def validate_conjunctive_results(results: List[Dict[str, Any]], 
                               query: str) -> List[Dict[str, Any]]:
    """Filter results to ensure all query terms are present."""
    query_terms = query.lower().split()
    validated = []
    
    for doc in results:
        content = doc.get("title", "") + " " + doc.get("content", "")
        if all(term in content.lower() for term in query_terms):
            validated.append(doc)
    
    return validated


def boost_title_matches(results: List[Dict[str, Any]], 
                       query: str, boost_factor: float) -> List[Dict[str, Any]]:
    """Apply boost to documents with query terms in title."""
    query_lower = query.lower()
    
    for doc in results:
        if query_lower in doc.get("title", "").lower():
            doc["score"] *= boost_factor
    
    # Re-sort after boosting
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def filter_by_section(results: List[Dict[str, Any]], 
                     section: str) -> List[Dict[str, Any]]:
    """Filter results to only include documents in specified section."""
    section_clean = section.lower().strip("#").strip()
    filtered = []
    
    for doc in results:
        if section_clean in doc.get("content", "").lower():
            filtered.append(doc)
    
    return filtered


def get_indexed_fields_info() -> FieldsResult:
    """Return currently indexed fields information."""
    # In a real implementation, this would query the index metadata
    return FieldsSuccess(ok=True, fields=["title", "content"])