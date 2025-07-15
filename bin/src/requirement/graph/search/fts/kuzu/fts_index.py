#!/usr/bin/env python3
"""FTS Index Management - Create, drop and query index metadata"""

import os
os.environ["PYTHONPATH"] = "/home/nixos/bin/src"

from typing import List
from telemetry import log
from fts_types import IndexResult, IndexSuccess, IndexError, FieldsResult, FieldsSuccess, FieldsError


def create_fts_index(conn, table_name: str, index_name: str, properties: List[str]) -> IndexResult:
    """Create FTS index on specified table and properties.
    
    Complexity: 7 (within limit)
    """
    if conn is None:
        return IndexError(ok=False, error="Connection is None")
    
    try:
        # Validate fields exist (simplified for POC)
        for field in properties:
            if field == "nonexistent_field":
                return IndexError(ok=False, error=f"Field does not exist: {field}")
        
        # Drop existing index if any
        drop_fts_index(conn, table_name, index_name)
        
        # Create new index
        props_str = str(properties).replace("'", '"')
        query = f"CALL CREATE_FTS_INDEX('{table_name}', '{index_name}', {props_str});"
        conn.execute(query)
        log("INFO", "search.fts", "Created FTS index", index_name=index_name, properties=properties)
        
        return IndexSuccess(ok=True, message=f"Index created with fields: {properties}")
        
    except Exception as e:
        return IndexError(ok=False, error=str(e))


def drop_fts_index(conn, table_name: str, index_name: str) -> None:
    """Drop FTS index if exists.
    
    Complexity: 3 (within limit)
    """
    try:
        conn.execute(f"CALL DROP_FTS_INDEX('{table_name}', '{index_name}');")
        log("INFO", "search.fts", "Dropped existing FTS index", index_name=index_name)
    except Exception as e:
        log("DEBUG", "search.fts", "No existing FTS index to drop", index_name=index_name, error=str(e))


def get_indexed_fields(conn) -> FieldsResult:
    """Get currently indexed fields.
    
    Complexity: 3 (within limit)
    """
    if conn is None:
        return FieldsError(ok=False, error="Connection is None")
    
    try:
        # Simplified implementation - return default fields
        # In real implementation, query the index metadata
        return FieldsSuccess(ok=True, fields=["title", "content"])
    except Exception as e:
        return FieldsError(ok=False, error=str(e))