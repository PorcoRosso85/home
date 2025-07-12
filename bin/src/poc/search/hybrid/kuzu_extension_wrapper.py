#!/usr/bin/env python3
"""
KuzuDB VSS/FTS拡張機能のサブプロセスラッパー
pytest環境でのセグフォルトを回避しながら実機能をテスト
"""
import subprocess
import sys
import json
import os
from typing import Any, Dict, List, Optional
import tempfile

class KuzuExtensionSubprocess:
    """VSS/FTS拡張機能を使用するKuzuDB操作をサブプロセスで実行"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_vss_query(
        self, 
        table_name: str,
        index_name: str,
        query_embedding: List[float],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """VSSクエリをサブプロセスで実行"""
        
        # エンベディングを文字列形式に変換
        embedding_str = "[" + ", ".join(str(v) for v in query_embedding) + "]"
        
        code = f'''
import kuzu
import json
import traceback

try:
    db = kuzu.Database({repr(self.db_path)})
    conn = kuzu.Connection(db)
    
    # Install and load VECTOR extension
    try:
        conn.execute("INSTALL vector;")
    except:
        pass  # Already installed
    
    conn.execute("LOAD EXTENSION vector;")
    
    # Execute VSS query
    result = conn.execute("""
        CALL QUERY_VECTOR_INDEX(
            '{table_name}',
            '{index_name}',
            {embedding_str},
            {k}
        ) RETURN element_id, score;
    """)
    
    results = []
    while result.has_next():
        row = result.get_next()
        results.append({{
            "element_id": str(row[0]),
            "score": float(row[1])
        }})
    
    print(json.dumps({{"success": True, "results": results}}))

except Exception as e:
    print(json.dumps({{
        "success": False, 
        "error": str(e), 
        "traceback": traceback.format_exc()
    }}))
'''

        return self._execute_subprocess(code)

    def execute_fts_query(
        self,
        table_name: str,
        index_name: str,
        query: str,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """FTSクエリをサブプロセスで実行"""
        
        code = f'''
import kuzu
import json
import traceback

try:
    db = kuzu.Database({repr(self.db_path)})
    conn = kuzu.Connection(db)
    
    # Install and load FTS extension
    try:
        conn.execute("INSTALL fts;")
    except:
        pass  # Already installed
    
    conn.execute("LOAD EXTENSION fts;")
    
    # Execute FTS query
    result = conn.execute("""
        CALL QUERY_FTS_INDEX(
            '{table_name}',
            '{index_name}',
            '{query}',
            {k}
        ) RETURN element_id, score;
    """)
    
    results = []
    while result.has_next():
        row = result.get_next()
        results.append({{
            "element_id": str(row[0]),
            "score": float(row[1])
        }})
    
    print(json.dumps({{"success": True, "results": results}}))

except Exception as e:
    print(json.dumps({{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}))
'''

        return self._execute_subprocess(code)

    def create_vss_index(
        self,
        table_name: str,
        index_name: str,
        embedding_column: str
    ) -> bool:
        """VSSインデックスをサブプロセスで作成"""
        
        code = f'''
import kuzu
import json
import traceback

try:
    db = kuzu.Database({repr(self.db_path)})
    conn = kuzu.Connection(db)
    
    # Install and load VECTOR extension
    try:
        conn.execute("INSTALL vector;")
    except:
        pass
    
    conn.execute("LOAD EXTENSION vector;")
    
    # Create VSS index
    conn.execute("""
        CALL CREATE_VECTOR_INDEX(
            '{table_name}',
            '{index_name}',
            '{embedding_column}'
        );
    """)
    
    print(json.dumps({{"success": True}}))

except Exception as e:
    print(json.dumps({{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}))
'''

        result = self._execute_subprocess(code)
        return len(result) > 0 and result[0].get("success", False)

    def create_fts_index(
        self,
        table_name: str,
        index_name: str,
        columns: List[str]
    ) -> bool:
        """FTSインデックスをサブプロセスで作成"""
        
        columns_str = "[" + ", ".join(f"'{col}'" for col in columns) + "]"
        
        code = f'''
import kuzu
import json
import traceback

try:
    db = kuzu.Database({repr(self.db_path)})
    conn = kuzu.Connection(db)
    
    # Install and load FTS extension
    try:
        conn.execute("INSTALL fts;")
    except:
        pass
    
    conn.execute("LOAD EXTENSION fts;")
    
    # Create FTS index
    conn.execute("""
        CALL CREATE_FTS_INDEX(
            '{table_name}',
            '{index_name}',
            {columns_str}
        );
    """)
    
    print(json.dumps({{"success": True}}))

except Exception as e:
    print(json.dumps({{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}))
'''

        result = self._execute_subprocess(code)
        return len(result) > 0 and result[0].get("success", False)

    def _execute_subprocess(self, code: str) -> List[Dict[str, Any]]:
        """サブプロセスでコードを実行"""
        
        # 環境変数を設定
        env = {**os.environ, 'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', '')}
        
        # デバッグモードの場合はコードをファイルに保存
        if os.environ.get('DEBUG_KUZU_SUBPROCESS'):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                print(f"[DEBUG] Subprocess code written to: {f.name}")

        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode != 0:
            if result.returncode == -11:  # SIGSEGV
                raise RuntimeError(
                    "Subprocess segfaulted. This is a known issue with KuzuDB extensions in pytest."
                )
            raise RuntimeError(
                f"Subprocess failed with code {result.returncode}: "
                f"stderr={result.stderr}, stdout={result.stdout}"
            )

        if not result.stdout.strip():
            raise RuntimeError(f"Subprocess returned empty output. stderr={result.stderr}")

        try:
            response = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse subprocess output: {result.stdout}")

        if isinstance(response, dict):
            if response.get("success"):
                return response.get("results", [response])
            else:
                error = response.get('error', 'Unknown error')
                traceback = response.get('traceback', '')
                raise RuntimeError(f"Subprocess error: {error}\nTraceback: {traceback}")
        
        return []


def is_pytest_running() -> bool:
    """pytest環境で実行されているかチェック"""
    return 'pytest' in sys.modules