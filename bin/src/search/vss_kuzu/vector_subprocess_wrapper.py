#!/usr/bin/env python3
"""
Simplified subprocess wrapper for VECTOR operations
Based on POC implementation but without external dependencies
"""
import subprocess
import sys
import json
import tempfile
from typing import Dict, Any, Optional


def is_pytest_running() -> bool:
    """Check if running under pytest"""
    return 'pytest' in sys.modules


class VectorSubprocessWrapper:
    """Execute VECTOR operations in subprocess to avoid segfaults in pytest"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute_vector_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute VECTOR operation in subprocess"""
        
        # Generate Python code to execute
        code = f'''
import json
import sys

try:
    import kuzu
    
    # Connect to database
    db_path = {repr(self.db_path)}
    if db_path == ":memory:":
        db = kuzu.Database(":memory:")
    else:
        db = kuzu.Database(db_path)
    
    conn = kuzu.Connection(db)
    
    # Load VECTOR extension
    try:
        conn.execute("LOAD EXTENSION VECTOR;")
    except:
        conn.execute("INSTALL VECTOR;")
        conn.execute("LOAD EXTENSION VECTOR;")
    
    # Execute operation
    params = {repr(params)}
    operation = {repr(operation)}
    
    if operation == "check_extension":
        # Just check if extension loads
        result = {{"ok": True, "available": True}}
    
    elif operation == "create_index":
        table_name = params["table_name"]
        index_name = params["index_name"]
        column_name = params["column_name"]
        
        conn.execute(f"CALL CREATE_VECTOR_INDEX('{{table_name}}', '{{index_name}}', '{{column_name}}')")
        result = {{"ok": True}}
    
    elif operation == "query_index":
        table_name = params["table_name"]
        index_name = params["index_name"]
        query_vector = params["query_vector"]
        k = params["k"]
        
        res = conn.execute(f"""
            CALL QUERY_VECTOR_INDEX(
                '{{table_name}}',
                '{{index_name}}',
                $embedding,
                $k
            ) RETURN node, distance
        """, {{"embedding": query_vector, "k": k}})
        
        results = []
        while res.has_next():
            row = res.get_next()
            node = row[0]
            distance = row[1]
            results.append({{
                "id": node.get("id"),
                "content": node.get("content"),
                "distance": float(distance)
            }})
        
        result = {{"ok": True, "results": results}}
    
    else:
        result = {{"ok": False, "error": f"Unknown operation: {{operation}}"}}
    
    print(json.dumps(result))

except Exception as e:
    error_result = {{
        "ok": False,
        "error": str(e),
        "type": type(e).__name__
    }}
    print(json.dumps(error_result))
'''
        
        # Execute in subprocess
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                env=dict(os.environ) if 'os' in globals() else None
            )
            
            if result.returncode != 0:
                return {
                    "ok": False,
                    "error": f"Subprocess failed with code {result.returncode}",
                    "stderr": result.stderr
                }
            
            # Parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return {
                    "ok": False,
                    "error": f"Failed to parse subprocess output: {e}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except Exception as e:
            return {
                "ok": False,
                "error": f"Subprocess execution failed: {e}",
                "type": type(e).__name__
            }