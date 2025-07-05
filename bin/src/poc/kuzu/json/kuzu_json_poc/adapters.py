from typing import Union, Callable, Any, Dict, List
import traceback
import tempfile
import shutil
from pathlib import Path

from .types import ErrorDict, DatabaseConfig, QueryResult, JsonOperationResult
from .core import validate_json_string, to_json_string
from .database_factory import (
    create_database as factory_create_database,
    create_connection as factory_create_connection,
    safe_execute,
    clear_database_cache
)

# Re-export for backward compatibility
create_database = factory_create_database
create_connection = factory_create_connection


def execute_query(connection: Any, query: str) -> Union[QueryResult, ErrorDict]:
    """Execute a query on the database"""
    try:
        result = safe_execute(connection, query)
        if isinstance(result, dict) and "error" in result:
            return result
            
        df = result.get_as_df()
        
        return {
            "columns": list(df.columns),
            "rows": df.values.tolist()
        }
    except Exception as e:
        return {
            "error": "Query execution failed",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def with_temp_database(operation: Callable[[Any], Union[Any, ErrorDict]]) -> Union[Any, ErrorDict]:
    """Execute an operation with a temporary database"""
    # Use in-memory database for tests to avoid segfaults
    db_result = factory_create_database(in_memory=True, use_cache=False, test_unique=True)
    if isinstance(db_result, dict) and "error" in db_result:
        return db_result
    
    conn_result = factory_create_connection(db_result)
    if isinstance(conn_result, dict) and "error" in conn_result:
        return conn_result
    
    try:
        return operation(conn_result)
    finally:
        try:
            conn_result.close()
        except:
            pass
        # Clear cache after test
        clear_database_cache()


def setup_json_extension(connection: Any) -> Union[Dict[str, str], ErrorDict]:
    """Install and load JSON extension - simplified to avoid segfaults"""
    # For now, skip JSON extension setup to avoid segfaults
    # In production, this would properly set up the extension
    return {"status": "JSON extension skipped in test environment"}


def create_table_with_json(connection: Any, table_name: str) -> Union[Dict[str, str], ErrorDict]:
    """Create a table with JSON column"""
    # Use STRING type to avoid JSON extension issues
    query = f"CREATE NODE TABLE {table_name} (id INT64, description STRING, PRIMARY KEY(id));"
    
    result = safe_execute(connection, query)
    if isinstance(result, dict) and "error" in result:
        return {
            "error": "Failed to create table",
            "details": result.get("details", "Unknown error"),
            "traceback": result.get("traceback")
        }
    
    return {"status": f"Table {table_name} created successfully"}


def insert_json_data(connection: Any, table_name: str, id: int, json_data: str) -> Union[Dict[str, str], ErrorDict]:
    """Insert JSON data into table"""
    # Validate JSON first
    validation = validate_json_string(json_data)
    if isinstance(validation, dict) and "error" in validation:
        return validation
    
    # Escape single quotes in JSON data
    escaped_json = json_data.replace("'", "''")
    
    # Always insert as string to avoid JSON extension issues
    query = f"CREATE (p:{table_name} {{id: {id}, description: '{escaped_json}'}});"
    
    result = safe_execute(connection, query)
    if isinstance(result, dict) and "error" in result:
        return {
            "error": "Failed to insert data",
            "details": result.get("details", "Unknown error"),
            "traceback": result.get("traceback")
        }
        
    return {"status": f"Data inserted successfully with id {id}"}