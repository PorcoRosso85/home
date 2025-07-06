"""Subprocess wrapper for KuzuDB JSON operations to avoid segfault"""
import subprocess
import sys
import json
import os
from typing import Any, Dict, List, Union


class KuzuJSONSubprocess:
    """Execute KuzuDB JSON operations in subprocess to avoid pytest segfault"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False
    
    def _execute_in_subprocess(self, operations: List[str]) -> Dict[str, Any]:
        """Execute operations in subprocess"""
        code = f'''
import kuzu
import json
import traceback

db = kuzu.Database({repr(self.db_path)})
conn = kuzu.Connection(db)

results = []

try:
    # Always install and load JSON extension
    try:
        conn.execute("INSTALL json;")
        conn.execute("LOAD EXTENSION json;")
    except:
        pass  # Already installed
    
    # Execute each operation
    for operation in {repr(operations)}:
        try:
            result = conn.execute(operation)
            
            # Check if this is a query with results
            if result.has_next():
                rows = []
                while result.has_next():
                    row = result.get_next()
                    rows.append([str(val) for val in row])
                results.append({{"success": True, "rows": rows}})
            else:
                results.append({{"success": True}})
                
        except Exception as e:
            results.append({{"success": False, "error": str(e)}})
            
    print(json.dumps({{"results": results}}))
    
except Exception as e:
    print(json.dumps({{"error": str(e), "traceback": traceback.format_exc()}}))
'''
        
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            env={**os.environ, 'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', '')}
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Subprocess failed: {result.stderr}")
        
        response = json.loads(result.stdout.strip())
        
        if "error" in response:
            raise RuntimeError(f"Subprocess error: {response['error']}")
        
        self._initialized = True
        return response["results"]
    
    def execute(self, query: str) -> Union[Dict[str, Any], List[Any]]:
        """Execute a single query"""
        results = self._execute_in_subprocess([query])
        result = results[0]
        
        if not result["success"]:
            raise RuntimeError(f"Query failed: {result.get('error', 'Unknown error')}")
        
        if "rows" in result:
            return result["rows"]
        return result
    
    def execute_many(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple queries in one subprocess call"""
        return self._execute_in_subprocess(queries)


def with_json_subprocess(db_path: str):
    """Context manager for JSON subprocess operations"""
    import contextlib
    
    @contextlib.contextmanager
    def _wrapper():
        wrapper = KuzuJSONSubprocess(db_path)
        yield wrapper
    
    return _wrapper()