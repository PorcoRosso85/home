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
# より堅牢なパス解決 - モジュール基準ではなくプロジェクトルート基準
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# 絶対パスをsys.pathに追加
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# 統一されたクエリローダーをインポート
from query.call_cypher import create_query_loader


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


def get_connection(db_path: str, with_query_loader: bool = True, in_memory: bool = False) -> Union[DatabaseResult, QueryLoaderResult]:
    """データベース接続を取得する統合関数（トランザクション状態追跡機能追加）
    
    KuzuDBのトランザクション処理特性に合わせて、接続状態を追跡する機能を強化しました。
    クエリローダーは常に初期化されます（後方互換性のため引数は残していますが、デフォルトでTrue）。
    
    Args:
        db_path: データベースディレクトリのパス
        with_query_loader: クエリローダーも一緒に取得するかどうか（デフォルトでTrue、後方互換性のため）
        in_memory: インメモリモードで接続するかどうか（デフォルトでFalse）
    
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
        
        # クエリローダー作成と設定（常に初期化）
        # 統一されたクエリローダーを使用（with_query_loader引数は後方互換性のため残すが無視）
        loader = create_query_loader(QUERY_DIR)
        
        # 接続オブジェクトに関連づける
        conn._query_loader = loader
        
        # 診断情報としてクエリローダーの状態を出力
        available_queries = loader["get_available_queries"]()
        if available_queries:
            print(f"DEBUG: クエリローダー初期化成功 - 利用可能なクエリ数: {len(available_queries)}")
        else:
            print("WARNING: クエリローダーは初期化されましたが、クエリが見つかりません")
        
        # 統一されたレスポンス形式で返す
        return {
            "connection": conn,
            "query_loader": loader
        }
    
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
    # 常にクエリローダーを有効にして接続を作成
    return get_connection(db_path=db_path, with_query_loader=True, in_memory=False)


def init_database(db_path: str, in_memory: bool) -> DatabaseInitializationResult:
    """データベースの初期化
    
    Args:
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
    
    Returns:
        DatabaseInitializationResult: 成功時はデータベース接続、失敗時はエラー情報
    """
    # データベース初期化の構成情報
    init_config = {
        "db_path": db_path,
        "in_memory": in_memory,
        "initialized_tables": [],
        "existing_tables": [],
        "errors": []
    }
    
    # ローカルインポート
    try:
        import kuzu
    except ImportError as e:
        return {
            "code": "MODULE_IMPORT_ERROR",
            "message": f"KuzuDBライブラリのインポートに失敗しました: {str(e)}"
        }
    
    # データベースインスタンス作成
    try:
        # ディスクモードの場合のみディレクトリを作成
        if not in_memory:
            # ディレクトリが存在しない場合は作成
            try:
                os.makedirs(db_path, exist_ok=True)
            except OSError as dir_error:
                return {
                    "code": "DB_PATH_ERROR",
                    "message": f"データベースディレクトリの作成に失敗しました: {str(dir_error)}"
                }
            
            # データベース接続（ディスクモード）
            db = kuzu.Database(db_path)
        else:
            # データベース接続（インメモリモード）
            db = kuzu.Database()
        
        # 接続作成
        conn = kuzu.Connection(db)
    except Exception as db_error:
        return {
            "code": "DB_CONNECTION_ERROR",
            "message": f"データベース接続の作成に失敗しました: {str(db_error)}"
        }
    
    # クエリローダーを初期化して関数スキーマクエリを取得する
    print("DDLクエリをローダー経由で読み込みます: function_schema")
    
    # クエリローダー作成
    try:
        loader = create_query_loader(QUERY_DIR)
        
        # function_schemaクエリを取得
        query_result = loader["get_query"]("function_schema")
        
        if not loader["get_success"](query_result):
            # クエリ取得に失敗した場合
            return {
                "code": "DDL_LOAD_ERROR",
                "message": f"DDLクエリの取得に失敗しました: {query_result.get('error', '不明なエラー')}",
                "details": {
                    "query_name": "function_schema",
                    "error": query_result.get("error", "不明なエラー")
                }
            }
        
        # クエリ内容を取得してセミコロンで分割
        schema_query = query_result["data"]
        statements = [stmt.strip() for stmt in schema_query.split(';') if stmt.strip()]
    except Exception as loader_error:
        return {
            "code": "QUERY_LOADER_ERROR",
            "message": f"クエリローダーの初期化に失敗しました: {str(loader_error)}"
        }
    
    # トランザクション管理
    transaction_active = False
    try:
        # トランザクション開始（可能であれば）
        try:
            conn.execute("BEGIN TRANSACTION")
            transaction_active = True
            print("DEBUG: 初期化用トランザクションを開始しました")
        except Exception as tx_error:
            print(f"WARNING: トランザクション開始に失敗しました - トランザクションなしで続行します: {str(tx_error)}")
        
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
                        table_name_str = table_name.group(1)
                        print(f"{table_name_str} テーブルを作成しました")
                        init_config["initialized_tables"].append(table_name_str)
                elif "CREATE REL TABLE" in statement:
                    table_name = re.search(r"CREATE REL TABLE (\w+)", statement)
                    if table_name:
                        table_name_str = table_name.group(1)
                        print(f"{table_name_str} エッジテーブルを作成しました")
                        init_config["initialized_tables"].append(table_name_str)
            
            except Exception as stmt_error:
                # テーブルが既に存在する場合はスキップ
                if "already exists" in str(stmt_error):
                    table_match = re.search(r"Table (\w+) already exists", str(stmt_error))
                    if table_match:
                        table_name_str = table_match.group(1)
                        print(f"{table_name_str} テーブルは既に存在します")
                        init_config["existing_tables"].append(table_name_str)
                else:
                    # その他のエラーは記録して続行
                    error_info = {
                        "statement": statement,
                        "error": str(stmt_error)
                    }
                    init_config["errors"].append(error_info)
                    print(f"WARNING: ステートメント実行エラー: {str(stmt_error)}")
        
        # トランザクションのコミット（アクティブな場合）
        if transaction_active:
            try:
                conn.execute("COMMIT")
                print("DEBUG: 初期化用トランザクションをコミットしました")
                
                # トランザクション状態をリセット
                transaction_active = False
            except Exception as commit_error:
                print(f"WARNING: トランザクションのコミットに失敗しました: {str(commit_error)}")
                # トランザクションの状態を不明として扱う
                transaction_active = False
                
                # エラーを記録
                init_config["errors"].append({
                    "type": "commit_error",
                    "error": str(commit_error)
                })
    except Exception as process_error:
        # 処理中に発生した例外を処理
        if transaction_active:
            try:
                conn.execute("ROLLBACK")
                print("DEBUG: エラーによりトランザクションをロールバックしました")
            except Exception as rollback_error:
                print(f"ERROR: トランザクションのロールバックに失敗しました: {str(rollback_error)}")
                init_config["errors"].append({
                    "type": "rollback_error",
                    "error": str(rollback_error)
                })
        
        return {
            "code": "DDL_EXECUTION_ERROR",
            "message": f"DDL実行エラー: {str(process_error)}",
            "details": init_config
        }
    
    # 一時待機して、データベースの状態が安定するのを待つ
    import time
    time.sleep(0.5)  # 500ms待機
    
    # 成功結果を返す
    return {
        "message": "データベースの初期化が完了しました",
        "connection": conn,
        "details": init_config
    }
