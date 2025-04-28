"""
データベース接続モジュール（リファクタリング版）

このモジュールでは、KuzuDBへの接続機能を提供します。
query/call_dml.pyの単純化されたローダーを利用するよう更新されています。
"""

import os
import re
from typing import Dict, Any, Optional, Union, Tuple, List

from upsert.infrastructure.variables import DB_DIR, QUERY_DIR
from upsert.application.types import (
    DatabaseConnection,
    DatabaseError,
    DatabaseResult,
    DatabaseInitializationSuccess,
    DatabaseInitializationError,
    DatabaseInitializationResult,
    QueryLoaderResult,
)

# サブモジュールのインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from query.call_dml import create_query_loader


def load_ddl_from_file(ddl_file_path: str) -> List[str]:
    """DDLファイルからSQL文を読み込む
    
    Args:
        ddl_file_path: DDLファイルのパス
        
    Returns:
        List[str]: SQL文のリスト
    """
    if not os.path.exists(ddl_file_path):
        raise FileNotFoundError(f"DDLファイルが見つかりません: {ddl_file_path}")
        
    with open(ddl_file_path, 'r') as f:
        content = f.read()
    
    # コメント行を削除し、セミコロンで分割
    statements = []
    lines = content.split('\n')
    current_statement = []
    
    for line in lines:
        # コメント行をスキップ
        if line.strip().startswith('//'):
            continue
            
        # 空行をスキップ
        if not line.strip():
            continue
            
        current_statement.append(line)
        
        # セミコロンが含まれている場合、ステートメントが完了
        if ';' in line:
            statements.append('\n'.join(current_statement))
            current_statement = []
    
    # セミコロンで終わらない残りのステートメントを追加
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    return statements


def get_connection(db_path: str = None, with_query_loader: bool = False, in_memory: bool = None) -> Union[DatabaseResult, QueryLoaderResult]:
    """データベース接続を取得する統合関数
    
    Args:
        db_path: データベースディレクトリのパス（デフォルト: variables.get_db_dir()）
        with_query_loader: クエリローダーも一緒に取得するかどうか
        in_memory: インメモリモードで接続するかどうか（デフォルト: variables.IN_MEMORY_MODE）
    
    Returns:
        Union[DatabaseResult, QueryLoaderResult]: 成功時はデータベース接続（とクエリローダー）、失敗時はエラー情報
    """
    try:
        import kuzu
        from upsert.infrastructure.variables import get_db_dir, IN_MEMORY_MODE
        
        # デフォルト値の処理
        if db_path is None:
            db_path = get_db_dir()
            
        if in_memory is None:
            in_memory = IN_MEMORY_MODE
        
        # 接続の作成（条件分岐）
        if not in_memory:
            # ディスクモード接続
            if not os.path.exists(db_path):
                return {
                    "code": "DB_NOT_FOUND",
                    "message": f"データベースディレクトリが見つかりません: {db_path}"
                }
            db = kuzu.Database(db_path)
        else:
            # インメモリモード接続
            db = kuzu.Database()
        
        conn = kuzu.Connection(db)
        
        # クエリローダー作成と設定（シンプル化された版を使用）
        if with_query_loader:
            # 簡素化したクエリローダーを使用（ディレクトリパスのみ渡す）
            loader = create_query_loader(QUERY_DIR)
            # 接続オブジェクトに関連づける（呼び出し側の互換性のため）
            conn._query_loader = loader
            # 互換性のあるレスポンス形式
            return {
                "connection": conn,
                "query_loader": loader
            }
        
        return {"connection": conn}
    
    except Exception as e:
        return {
            "code": "DB_CONNECTION_ERROR",
            "message": f"データベース接続エラー: {str(e)}"
        }


# 後方互換性のための関数
def create_connection(db_path: str = DB_DIR) -> DatabaseResult:
    """データベース接続を作成する（後方互換性のため）
    
    Args:
        db_path: データベースディレクトリのパス（デフォルト: DB_DIR）
    
    Returns:
        DatabaseResult: 成功時は接続オブジェクト、失敗時はエラー情報
    """
    # get_connection関数にディスクモードで委譲
    return get_connection(db_path=db_path, with_query_loader=False, in_memory=False)


def init_database(db_path: str = None, in_memory: bool = None) -> DatabaseInitializationResult:
    """データベースの初期化
    
    Args:
        db_path: データベースディレクトリのパス（デフォルト: variables.get_db_dir()）
        in_memory: インメモリモードで接続するかどうか（デフォルト: variables.IN_MEMORY_MODE）
    
    Returns:
        DatabaseInitializationResult: 成功時はデータベース接続、失敗時はエラー情報
    """
    try:
        # 必要なインポートをローカルで行う
        import kuzu
        from upsert.infrastructure.variables import get_db_dir, IN_MEMORY_MODE
        
        # db_pathが指定されていない場合は変数から取得
        if db_path is None:
            db_path = get_db_dir()
            
        # in_memoryが指定されていない場合は変数から取得
        if in_memory is None:
            in_memory = IN_MEMORY_MODE
            
        # ディスクモードの場合のみディレクトリを作成
        if not in_memory:
            # ディレクトリが存在しない場合は作成
            os.makedirs(db_path, exist_ok=True)
            
            # データベース接続（ディスクモード）
            db = kuzu.Database(db_path)
        else:
            # データベース接続（インメモリモード）
            db = kuzu.Database()
            
        conn = kuzu.Connection(db)
        
        # DDLファイルのパスを取得
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        ddl_file_path = os.path.join(project_root, "query", "function_schema_ddl.cypher")
        
        # DDLファイルが存在するか確認
        if not os.path.exists(ddl_file_path):
            return {
                "code": "DDL_FILE_NOT_FOUND",
                "message": f"DDLファイルが見つかりません: {ddl_file_path}"
            }
        
        print(f"DDLファイルを読み込みます: {ddl_file_path}")
        
        try:
            # DDLファイルからSQL文を読み込む
            statements = load_ddl_from_file(ddl_file_path)
            
            # 各ステートメントを実行
            for statement in statements:
                try:
                    # 空のステートメントはスキップ
                    if not statement.strip():
                        continue
                    
                    # DDLを実行
                    conn.execute(statement)
                    
                    # テーブル名を抽出して出力
                    if "CREATE NODE TABLE" in statement:
                        table_name = re.search(r"CREATE NODE TABLE (\w+)", statement)
                        if table_name:
                            print(f"{table_name.group(1)} テーブルを作成しました")
                    elif "CREATE REL TABLE" in statement:
                        table_name = re.search(r"CREATE REL TABLE (\w+)", statement)
                        if table_name:
                            print(f"{table_name.group(1)} エッジテーブルを作成しました")
                
                except Exception as stmt_error:
                    # テーブルが既に存在する場合はスキップ
                    if "already exists" in str(stmt_error):
                        table_match = re.search(r"Table (\w+) already exists", str(stmt_error))
                        if table_match:
                            print(f"{table_match.group(1)} テーブルは既に存在します")
                    else:
                        raise stmt_error
            
            return {
                "message": "データベースの初期化が完了しました",
                "connection": conn
            }
            
        except Exception as ddl_error:
            return {
                "code": "DDL_EXECUTION_ERROR",
                "message": f"DDL実行エラー: {str(ddl_error)}"
            }
    
    except Exception as e:
        return {
            "code": "DB_INIT_ERROR",
            "message": f"データベース初期化エラー: {str(e)}"
        }
