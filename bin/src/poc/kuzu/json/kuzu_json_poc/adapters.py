from typing import Union, Callable, Any, Dict
import tempfile
import shutil
from .types import ErrorDict, QueryResult
from .core import validate_json_string


def create_database(path: str = None, in_memory: bool = False) -> Union[Any, ErrorDict]:
    """Create KuzuDB database"""
    try:
        import kuzu
        return kuzu.Database(":memory:" if in_memory else path)
    except Exception as e:
        return {"error": "Failed to create database", "details": str(e), "traceback": None}


def create_connection(database: Any) -> Any:
    """Create connection"""
    import kuzu
    return kuzu.Connection(database)


def execute_query(connection: Any, query: str) -> Union[QueryResult, ErrorDict]:
    """Execute a query on the database"""
    try:
        result = connection.execute(query)
        df = result.get_as_df()
        return {"columns": list(df.columns), "rows": df.values.tolist()}
    except Exception as e:
        return {"error": "Query execution failed", "details": str(e), "traceback": None}


def with_temp_database(operation: Callable[[Any], Union[Any, ErrorDict]]) -> Union[Any, ErrorDict]:
    """Execute an operation with a temporary database"""
    import kuzu
    temp_dir = tempfile.mkdtemp(prefix="kuzu_json_")
    try:
        db = kuzu.Database(temp_dir)
        conn = kuzu.Connection(db)
        # Always setup JSON extension - no fallback allowed
        setup_result = setup_json_extension(conn)
        if isinstance(setup_result, dict) and "error" in setup_result:
            return setup_result
        return operation(conn)
    except Exception as e:
        return {"error": "Database operation failed", "details": str(e), "traceback": None}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def setup_json_extension(connection: Any) -> Union[Dict[str, str], ErrorDict]:
    """Install and load JSON extension"""
    try:
        connection.execute("INSTALL json;")
        connection.execute("LOAD EXTENSION json;")
        return {"status": "JSON extension loaded"}
    except Exception as e:
        return {"error": "JSON extension setup failed", "details": str(e), "traceback": None}


def create_table_with_json(connection: Any, table_name: str) -> Union[Dict[str, str], ErrorDict]:
    """Create a table with JSON column"""
    try:
        connection.execute(f"CREATE NODE TABLE {table_name} (id INT64, description JSON, PRIMARY KEY(id));")
        return {"status": f"Table {table_name} created successfully"}
    except Exception as e:
        return {"error": "Failed to create table", "details": str(e), "traceback": None}


def insert_json_data(connection: Any, table_name: str, id: int, json_data: str) -> Union[Dict[str, str], ErrorDict]:
    """Insert JSON data into table"""
    validation = validate_json_string(json_data)
    if isinstance(validation, dict) and "error" in validation:
        return validation
    try:
        escaped_json = json_data.replace("'", "''")
        connection.execute(f"CREATE (p:{table_name} {{id: {id}, description: to_json('{escaped_json}')}});")
        return {"status": f"Data inserted successfully with id {id}"}
    except Exception as e:
        return {"error": "Failed to insert data", "details": str(e), "traceback": None}


def query_json_field(connection: Any, table_name: str, json_path: str) -> Union[QueryResult, ErrorDict]:
    """Query JSON field using json_extract"""
    return execute_query(connection, f"MATCH (p:{table_name}) RETURN p.id, json_extract(p.description, '{json_path}') as extracted_value")

def update_json_field(connection: Any, table_name: str, id: int, json_patch: str) -> Union[Dict[str, str], ErrorDict]:
    """Update JSON field using json_merge_patch"""
    validation = validate_json_string(json_patch)
    if isinstance(validation, dict) and "error" in validation:
        return validation
    try:
        escaped = json_patch.replace("'", "''")
        connection.execute(f"MATCH (p:{table_name}) WHERE p.id = {id} SET p.description = json_merge_patch(p.description, to_json('{escaped}'))")
        return {"status": f"JSON field updated for id {id}"}
    except Exception as e:
        return {"error": "Failed to update JSON", "details": str(e), "traceback": None}