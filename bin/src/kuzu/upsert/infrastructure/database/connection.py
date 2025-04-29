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


def get_connection(db_path: str, with_query_loader: bool, in_memory: bool) -> Union[DatabaseResult, QueryLoaderResult]:
    """データベース接続を取得する統合関数（トランザクション状態追跡機能追加）
    
    KuzuDBのトランザクション処理特性に合わせて、接続状態を追跡する機能を強化しました。
    
    Args:
        db_path: データベースディレクトリのパス
        with_query_loader: クエリローダーも一緒に取得するかどうか
        in_memory: インメモリモードで接続するかどうか
    
    Returns:
        Union[DatabaseResult, QueryLoaderResult]: 成功時はデータベース接続（とクエリローダー）、失敗時はエラー情報
    """
    try:
        import kuzu
        import time
        
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
        
        # トランザクション状態追跡機能を追加
        # 接続オブジェクトを拡張して、トランザクション状態を追跡
        conn._transaction_active = False
        
        # オリジナルのexecuteメソッドを保存
        original_execute = conn.execute
        
        # executeメソッドをオーバーライドして、トランザクション状態を追跡する拡張版を作成
        def execute_with_transaction_tracking(query: str, params=None):
            # トランザクション関連コマンドの検出
            is_begin = query.strip().upper().startswith("BEGIN")
            is_commit = query.strip().upper().startswith("COMMIT")
            is_rollback = query.strip().upper().startswith("ROLLBACK")
            
            # トランザクション開始
            if is_begin:
                try:
                    result = original_execute(query, params)
                    conn._transaction_active = True
                    return result
                except Exception as e:
                    # トランザクション開始に失敗した場合は状態を更新しない
                    print(f"DEBUG: BEGIN TRANSACTION 失敗: {str(e)}")
                    raise
            
            # トランザクションコミット
            elif is_commit:
                if conn._transaction_active:
                    try:
                        result = original_execute(query, params)
                        conn._transaction_active = False
                        # KuzuDBの内部状態同期のために短い待機を追加
                        time.sleep(0.1)
                        return result
                    except Exception as e:
                        # コミット失敗時もトランザクション状態をリセット（安全側に倒す）
                        print(f"DEBUG: COMMIT 失敗: {str(e)}")
                        conn._transaction_active = False
                        raise
                else:
                    # アクティブなトランザクションがない場合は警告のみ
                    print("WARNING: アクティブなトランザクションがない状態でのCOMMITをスキップします")
                    return None
            
            # トランザクションロールバック
            elif is_rollback:
                if conn._transaction_active:
                    try:
                        result = original_execute(query, params)
                        conn._transaction_active = False
                        # KuzuDBの内部状態同期のために短い待機を追加
                        time.sleep(0.1)
                        return result
                    except Exception as e:
                        # ロールバック失敗時もトランザクション状態をリセット（安全側に倒す）
                        print(f"DEBUG: ROLLBACK 失敗: {str(e)}")
                        conn._transaction_active = False
                        raise
                else:
                    # アクティブなトランザクションがない場合は警告のみ
                    print("WARNING: アクティブなトランザクションがない状態でのROLLBACKをスキップします")
                    return None
            
            # その他のクエリはそのまま実行
            else:
                return original_execute(query, params)
        
        # 拡張されたexecuteメソッドで置き換え
        conn.execute = execute_with_transaction_tracking
        
        # トランザクション状態確認用のヘルパーメソッドを追加
        conn.is_transaction_active = lambda: conn._transaction_active
        
        # クエリローダー作成と設定（シンプル化された版を使用）
        if with_query_loader:
            # 簡素化したクエリローダーを使用（ディレクトリパスのみ渡す）
            loader = create_query_loader(QUERY_DIR)
            # query_typeデフォルト値を"dml"に設定したget_query_wrapperを上書き
            original_get_query = loader["get_query"]
            def get_query_with_default(query_name, query_type="dml"):
                return original_get_query(query_name, query_type)
            loader["get_query"] = get_query_with_default
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
def create_connection(db_path: str) -> DatabaseResult:
    """データベース接続を作成する（後方互換性のため）
    
    Args:
        db_path: データベースディレクトリのパス
    
    Returns:
        DatabaseResult: 成功時は接続オブジェクト、失敗時はエラー情報
    """
    # get_connection関数にディスクモードで委譲
    return get_connection(db_path=db_path, with_query_loader=False, in_memory=False)


def init_database(db_path: str, in_memory: bool) -> DatabaseInitializationResult:
    """データベースの初期化
    
    Args:
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
    
    Returns:
        DatabaseInitializationResult: 成功時はデータベース接続、失敗時はエラー情報
    """
    try:
        # 必要なインポートをローカルで行う
        import kuzu
            
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
        ddl_file_path = os.path.join(project_root, "query", "ddl", "function_schema.cypher")
        
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
