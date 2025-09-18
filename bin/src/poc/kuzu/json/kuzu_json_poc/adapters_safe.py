"""Safe adapters using subprocess for pytest compatibility"""
import tempfile
import shutil
import os
import sys
from typing import Union, Dict, Any, Callable
from .types import ErrorDict
from .subprocess_wrapper import KuzuJSONSubprocess


def is_pytest_running() -> bool:
    """Check if running under pytest"""
    return 'pytest' in sys.modules


def with_temp_database_safe(operation: Callable[[Any], Union[Any, ErrorDict]]) -> Union[Any, ErrorDict]:
    """Execute an operation with a temporary database using subprocess if in pytest"""
    temp_dir = tempfile.mkdtemp(prefix="kuzu_json_")
    try:
        db_path = f"{temp_dir}/test.db"
        
        if is_pytest_running():
            # Use subprocess wrapper in pytest environment
            wrapper = KuzuJSONSubprocess(db_path)
            return operation(wrapper)
        else:
            # Use direct connection outside pytest
            import kuzu
            db = kuzu.Database(db_path)
            conn = kuzu.Connection(db)
            
            # Setup JSON extension
            try:
                conn.execute("INSTALL json;")
                conn.execute("LOAD EXTENSION json;")
            except:
                pass  # Already installed
            
            return operation(conn)
            
    except Exception as e:
        return {"error": "Database operation failed", "details": str(e), "traceback": None}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_document_node_safe(conn: Any, doc_id: str, doc_type: str, description: Dict[str, Any]) -> Union[Dict[str, str], ErrorDict]:
    """Create a Document node with JSON data"""
    try:
        # Create table if needed
        if hasattr(conn, 'execute_many'):
            # Subprocess wrapper
            results = conn.execute_many([
                """CREATE NODE TABLE IF NOT EXISTS Document(
                    id STRING,
                    type STRING,
                    description JSON,
                    PRIMARY KEY(id)
                )""",
                f"""CREATE (:Document {{
                    id: '{doc_id}',
                    type: '{doc_type}',
                    description: to_json(map({repr(list(description.keys()))}, {repr([str(v) for v in description.values()])}))
                }})"""
            ])
            
            if all(r.get("success", False) for r in results):
                return {"id": doc_id, "status": "created"}
            else:
                errors = [r.get("error") for r in results if not r.get("success")]
                return {"error": "Failed to create document", "details": "; ".join(errors), "traceback": None}
        else:
            # Direct connection
            conn.execute("""CREATE NODE TABLE IF NOT EXISTS Document(
                id STRING,
                type STRING,
                description JSON,
                PRIMARY KEY(id)
            )""")
            
            # Create JSON from dict
            keys = list(description.keys())
            values = [str(v) for v in description.values()]  # Convert all values to strings
            conn.execute(f"""CREATE (:Document {{
                id: '{doc_id}',
                type: '{doc_type}',
                description: to_json(map({repr(keys)}, {repr(values)}))
            }})""")
            
            return {"id": doc_id, "status": "created"}
            
    except Exception as e:
        return {"error": "Failed to create document node", "details": str(e), "traceback": None}


def query_json_field_safe(conn: Any, doc_id: str, json_path: str) -> Union[str, ErrorDict]:
    """Query a specific field from JSON data"""
    try:
        query = f"""
            MATCH (d:Document)
            WHERE d.id = '{doc_id}'
            RETURN json_extract(d.description, '{json_path}') as value
        """
        
        if hasattr(conn, 'execute'):
            # Both wrapper and direct connection have execute
            result = conn.execute(query)
            
            if isinstance(result, list) and len(result) > 0:
                # Subprocess wrapper returns list of rows
                return result[0][0].strip('"')  # Remove JSON quotes
            elif hasattr(result, 'has_next'):
                # Direct connection returns cursor
                if result.has_next():
                    row = result.get_next()
                    return str(row[0]).strip('"')
                    
        return {"error": "Document not found", "details": f"No document with id: {doc_id}", "traceback": None}
        
    except Exception as e:
        return {"error": "Query failed", "details": str(e), "traceback": None}