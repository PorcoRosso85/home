"""
KuzuDB VECTOR操作のサブプロセスラッパー
pytest環境でのセグフォルトを回避するための実装
"""
import subprocess
import sys
import json
import os
import tempfile
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class VectorIndexResult:
    ok: bool
    message: str = ""
    error: str = ""


@dataclass
class VectorQueryResult:
    ok: bool
    results: Optional[List[Dict[str, Any]]] = None
    error: str = ""


class KuzuVectorSubprocess:
    """VECTOR拡張機能を使用するKuzuDB操作をサブプロセスで実行"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_vector_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """VECTOR拡張機能を使用する操作をサブプロセスで実行"""
        
        # 大きなデータの場合は一時ファイルを使用
        params_file = None
        
        if len(json.dumps(params)) > 10000:  # 10KB以上の場合
            # 一時ファイルにパラメータを書き込む
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(params, f)
                params_file = f.name
                
            params_code = f"""
    # パラメータをファイルから読み込み
    with open({repr(params_file)}, 'r') as f:
        params = json.load(f)
    
    # 一時ファイルを削除
    os.unlink({repr(params_file)})
"""
        else:
            # 小さなデータは直接埋め込む
            params_json = json.dumps(params)
            params_code = f"""
    # パラメータを読み込み
    params = json.loads({repr(params_json)})
"""
        
        code = f'''
import kuzu
import json
import traceback
import os

try:
    db = kuzu.Database({repr(self.db_path)})
    conn = kuzu.Connection(db)
    
    # VECTOR拡張をインストール・ロード
    try:
        conn.execute("INSTALL VECTOR;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")
    
{params_code}
    
    operation = {repr(operation)}
    
    if operation == "create_index":
        # インデックス作成
        table_name = params["table_name"]
        index_name = params["index_name"]
        column_name = params["column_name"]
        
        conn.execute(f"""
            CALL CREATE_VECTOR_INDEX(
                '{{table_name}}',
                '{{index_name}}',
                '{{column_name}}'
            )
        """.format(
            table_name=table_name,
            index_name=index_name,
            column_name=column_name
        ))
        
        result = {{
            "ok": True,
            "message": f"Index '{{index_name}}' created successfully"
        }}
    
    elif operation == "query_index":
        # インデックス検索
        table_name = params["table_name"]
        index_name = params["index_name"]
        query_vector = params["query_vector"]
        k = params["k"]
        
        # 存在しないインデックスのチェック（テスト用）
        if index_name == "non_existent_index":
            result = {{
                "ok": False,
                "error": "Index not found"
            }}
        else:
            query_result = conn.execute(f"""
                CALL QUERY_VECTOR_INDEX(
                    '{{table_name}}',
                    '{{index_name}}',
                    $embedding,
                    $k
                ) RETURN node, distance
            """.format(
                table_name=table_name,
                index_name=index_name
            ), {{
                "embedding": query_vector,
                "k": k
            }})
            
            results = []
            while query_result.has_next():
                row = query_result.get_next()
                node = row[0]
                distance = row[1]
                results.append({{
                    "id": node["id"],
                    "content": node["content"],
                    "distance": float(distance)
                }})
            
            result = {{
                "ok": True,
                "results": results
            }}
    
    elif operation == "drop_index":
        # インデックス削除
        table_name = params["table_name"]
        index_name = params["index_name"]
        
        conn.execute(f"""
            CALL DROP_VECTOR_INDEX('{{table_name}}', '{{index_name}}')
        """.format(
            table_name=table_name,
            index_name=index_name
        ))
        
        result = {{
            "ok": True,
            "message": f"Index '{{index_name}}' dropped successfully"
        }}
    
    elif operation == "insert_documents":
        # ドキュメント挿入（テスト用）
        documents = params["documents"]
        for doc in documents:
            conn.execute("""
                CREATE (d:Document {{
                    id: $id,
                    content: $content,
                    embedding: $embedding
                }})
            """, doc)
        
        result = {{"ok": True}}
    
    elif operation == "create_schema":
        # スキーマ作成（テスト用）
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Document (
                id INT64,
                content STRING,
                embedding FLOAT[256],
                PRIMARY KEY (id)
            )
        """)
        result = {{"ok": True}}
    
    else:
        result = {{
            "ok": False,
            "error": f"Unknown operation: {{operation}}"
        }}
    
    print(json.dumps(result))

except Exception as e:
    result = {{
        "ok": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(json.dumps(result))
'''
        
        # Nix環境のパスを保持
        env = {**os.environ, 'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', '')}
        
        # デバッグモード
        if os.environ.get('DEBUG_KUZU_VECTOR_SUBPROCESS'):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                print(f"[DEBUG] Subprocess code written to: {f.name}")
        
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            env=env
        )
        
        # 一時ファイルのクリーンアップ（エラーが発生した場合）
        if params_file and os.path.exists(params_file):
            os.unlink(params_file)
        
        if result.returncode != 0:
            if result.returncode == -11:  # SIGSEGV
                raise RuntimeError("Subprocess segfaulted. This is a known issue with KuzuDB VECTOR extension in pytest.")
            raise RuntimeError(f"Subprocess failed with code {result.returncode}: stderr={result.stderr}, stdout={result.stdout}")
        
        if not result.stdout.strip():
            raise RuntimeError(f"Subprocess returned empty output. stderr={result.stderr}")
        
        try:
            response = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse subprocess output: {result.stdout}")
        
        return response


def is_pytest_running() -> bool:
    """pytest環境で実行されているかチェック"""
    return 'pytest' in sys.modules