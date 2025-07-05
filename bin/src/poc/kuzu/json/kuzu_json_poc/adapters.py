from typing import Union, Callable, Any, Dict, List
import traceback
import tempfile
import shutil
from pathlib import Path

from .types import ErrorDict, DatabaseConfig, QueryResult, JsonOperationResult
from .core import validate_json_string, to_json_string


def create_database(config: DatabaseConfig) -> Union[Any, ErrorDict]:
    """Create a KuzuDB database instance"""
    try:
        import kuzu
        return kuzu.Database(config["path"])
    except Exception as e:
        return {
            "error": "Failed to create database",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def create_connection(database: Any) -> Union[Any, ErrorDict]:
    """Create a connection to KuzuDB database"""
    try:
        import kuzu
        return kuzu.Connection(database)
    except Exception as e:
        return {
            "error": "Failed to create connection",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def execute_query(connection: Any, query: str) -> Union[QueryResult, ErrorDict]:
    """Execute a query on the database"""
    try:
        result = connection.execute(query)
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
    temp_dir = tempfile.mkdtemp()
    try:
        db_result = create_database({"path": temp_dir})
        if isinstance(db_result, dict) and "error" in db_result:
            return db_result
        
        conn_result = create_connection(db_result)
        if isinstance(conn_result, dict) and "error" in conn_result:
            return conn_result
        
        try:
            return operation(conn_result)
        finally:
            conn_result.close()
    finally:
        shutil.rmtree(temp_dir)


def setup_json_extension(connection: Any) -> Union[Dict[str, str], ErrorDict]:
    """Install and load JSON extension"""
    try:
        connection.execute("INSTALL json;")
        connection.execute("LOAD json;")
        return {"status": "JSON extension loaded successfully"}
    except Exception as e:
        return {
            "error": "Failed to setup JSON extension",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def create_table_with_json(connection: Any, table_name: str) -> Union[Dict[str, str], ErrorDict]:
    """Create a table with JSON column"""
    try:
        query = f"CREATE NODE TABLE {table_name} (id INT64, description JSON, primary key(id));"
        connection.execute(query)
        return {"status": f"Table {table_name} created successfully"}
    except Exception as e:
        return {
            "error": "Failed to create table",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def insert_json_data(connection: Any, table_name: str, id: int, json_data: str) -> Union[Dict[str, str], ErrorDict]:
    """Insert JSON data into table"""
    try:
        # Validate JSON first
        validation = validate_json_string(json_data)
        if isinstance(validation, dict) and "error" in validation:
            return validation
        
        query = f"CREATE (p:{table_name} {{id: {id}, description: to_json('{json_data}')}});"
        connection.execute(query)
        return {"status": f"Data inserted successfully with id {id}"}
    except Exception as e:
        return {
            "error": "Failed to insert data",
            "details": str(e),
            "traceback": traceback.format_exc()
        }