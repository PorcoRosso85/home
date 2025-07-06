"""
KuzuDB JSON操作のサブプロセスラッパー
pytest環境でのセグフォルトを回避するための最小限の実装
"""
import subprocess
import sys
import json
import os
import tempfile
from typing import Any, Dict, List, Union, Optional


class KuzuJSONSubprocess:
    """JSON拡張機能を使用するKuzuDB操作をサブプロセスで実行"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute_with_json(self, queries: List[str]) -> List[Dict[str, Any]]:
        """JSON拡張機能を使用するクエリをサブプロセスで実行"""
        # クエリをPythonコードに埋め込む際のエスケープ処理
        escaped_queries = repr(queries)
        
        code = f'''
import kuzu
import json
import traceback

try:
    db = kuzu.Database({repr(self.db_path)})
    conn = kuzu.Connection(db)
    
    # Always install and load JSON extension
    try:
        conn.execute("INSTALL json;")
        conn.execute("LOAD EXTENSION json;")
    except:
        pass  # Already installed
    
    results = []
    queries = {escaped_queries}
    for query in queries:
        try:
            result = conn.execute(query)
            
            # Check if this is a query with results
            if result is not None and hasattr(result, 'has_next') and result.has_next():
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
        
        # サブプロセスで実行
        # Nix環境のパスを設定 - LD_LIBRARY_PATHを明示的に保持
        env = {**os.environ, 'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', '')}
        
        # デバッグ用にコードをファイルに書き出す
        if os.environ.get('DEBUG_KUZU_SUBPROCESS'):
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                print(f"[DEBUG] Subprocess code written to: {f.name}")
                print(f"[DEBUG] You can run it with: python {f.name}")
        
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode != 0:
            if result.returncode == -11:  # SIGSEGV
                raise RuntimeError(f"Subprocess segfaulted. This is a known issue with KuzuDB JSON extension in pytest.")
            raise RuntimeError(f"Subprocess failed with code {result.returncode}: stderr={result.stderr}, stdout={result.stdout}")
        
        if not result.stdout.strip():
            raise RuntimeError(f"Subprocess returned empty output. stderr={result.stderr}")
        
        try:
            response = json.loads(result.stdout.strip())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse subprocess output: {result.stdout}")
        
        if "error" in response:
            traceback = response.get('traceback', '')
            raise RuntimeError(f"Subprocess error: {response['error']}\nTraceback: {traceback}")
        
        return response["results"]
    
    def execute_single(self, query: str) -> Dict[str, Any]:
        """単一のクエリを実行"""
        results = self.execute_with_json([query])
        return results[0]


def is_pytest_running() -> bool:
    """pytest環境で実行されているかチェック"""
    return 'pytest' in sys.modules


def execute_with_json_safe(db_path: str, query: str) -> Any:
    """
    JSON拡張機能を使用するクエリを安全に実行
    pytest環境ではサブプロセスを使用
    """
    if is_pytest_running():
        # pytest環境ではサブプロセスを使用
        wrapper = KuzuJSONSubprocess(db_path)
        result = wrapper.execute_single(query)
        if not result["success"]:
            raise RuntimeError(f"Query failed: {result.get('error', 'Unknown error')}")
        return result.get("rows", [])
    else:
        # 通常環境では直接実行
        import kuzu
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # JSON拡張機能をロード
        try:
            conn.execute("INSTALL json;")
            conn.execute("LOAD EXTENSION json;")
        except:
            pass
        
        result = conn.execute(query)
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        return rows