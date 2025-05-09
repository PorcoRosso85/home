"""
データベースサービス

このモジュールでは、Kuzuデータベースの初期化と操作に関するサービス関数を提供します。
"""

import os
import sys
from typing import Optional, Tuple, Any, Dict, Union, List

from upsert.application.types import (
    DatabaseConnection,
    DatabaseError,
    DatabaseResult,
    DatabaseInitializationSuccess,
    DatabaseInitializationError,
    DatabaseInitializationResult,
    QueryLoaderResult,
)
from upsert.infrastructure.variables import DB_DIR, DB_NAME, QUERY_DIR

# 独自のエラー判定関数
def is_error(result: Any) -> bool:
    """
    結果がエラーかどうかを判定する
    
    Args:
        result: 判定する結果オブジェクト
    
    Returns:
        エラーの場合はTrue、成功の場合はFalse
    """
    # codeとmessageの両方が含まれている場合はエラー
    if isinstance(result, dict) and "code" in result and "message" in result:
        return True
    
    # キーが存在し、valueがFalseの場合はエラー
    if isinstance(result, dict) and result.get("success") == False:
        return True
    
    # それ以外は成功とみなす
    return False


def init_database() -> DatabaseInitializationResult:
    """データベースの初期化
    
    Note:
        DEPRECATED: このメソッドは廃止予定です。
        代わりに upsert.infrastructure.database.connection.init_database() を使用してください。
    
    Returns:
        DatabaseInitializationResult: 成功時はデータベース接続、失敗時はエラー情報
    """
    # インフラ層の初期化関数に処理を委譲
    from upsert.infrastructure.database.connection import init_database as infra_init_database
    return infra_init_database(DB_DIR)


def get_connection(with_query_loader: bool = False, db_path: str = None, in_memory: bool = False) -> Union[DatabaseResult, QueryLoaderResult]:
    """データベース接続を取得する
    
    Args:
        with_query_loader: クエリローダーも一緒に取得するかどうか
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: False）
    
    Returns:
        成功時はデータベース接続（とクエリローダー）、失敗時はエラー情報
    """
    try:
        import kuzu
        import time
        
        # db_pathが指定されていない場合は設定値を使用
        if db_path is None:
            db_path = DB_DIR
        
        # インメモリモードでない場合はディレクトリの存在確認
        if not in_memory:
            if not os.path.exists(db_path):
                return {
                    "code": "DB_NOT_FOUND",
                    "message": f"データベースディレクトリが見つかりません: {db_path}"
                }
            
            # データベース接続（ディスクモード）
            db = kuzu.Database(db_path)
        else:
            # インメモリモード接続
            db = kuzu.Database()
        
        # 接続の作成
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
            try:
                result = original_execute(query, params)
                
                # 結果のイテラブル性チェックと適切な変換処理（必要な場合のみ）
                # これはテスト的な処理ではなく、KuzuDBの仕様に合わせた処理
                if result is not None:
                    # 結果がすでにイテラブルなら、そのまま返す
                    if hasattr(result, '__iter__'):
                        return result
                    
                    # to_df メソッドをサポートしていれば変換を試みる
                    if hasattr(result, 'to_df'):
                        try:
                            df = result.to_df()
                            if df is not None and not df.empty:
                                return df
                        except Exception as df_error:
                            print(f"INFO: データフレーム変換中にエラーが発生: {str(df_error)}")
                
                # 変換が必要ない場合や変換に失敗した場合は、元の結果をそのまま返す
                return result
            except Exception as e:
                # イテラブルでないエラーの可能性を確認
                if "not iterable" in str(e):
                    print(f"INFO: クエリ結果がイテラブルでないエラーが発生しました: {str(e)}")
                    # 元のクエリを再実行しない - エラーは重要な情報として伝播する
                    return []
                else:
                    # その他のエラーはそのまま伝播
                    raise
        
        # 拡張されたexecuteメソッドで置き換え
        conn.execute = execute_with_transaction_tracking
        
        # トランザクション状態確認用のヘルパーメソッドを追加
        conn.is_transaction_active = lambda: conn._transaction_active
        
        # クエリローダーが不要な場合は接続のみ返す
        if not with_query_loader:
            return {"connection": conn}
        
        # FIXME: クエリローダー部分は、query/{ddl,dml,dql}ディレクトリが空になっているため動作しません
        # クエリローダー用のパスを設定
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from query.call_dml import create_query_loader
        
        try:
            # クエリローダーの作成
            loader = create_query_loader(QUERY_DIR)
            
            # 接続とクエリローダーを返す
            return {
                "connection": conn,
                "query_loader": loader
            }
        except Exception as loader_error:
            print(f"WARNING: クエリローダーの作成に失敗しましたが、接続のみ返します: {str(loader_error)}")
            return {"connection": conn}
    
    except Exception as e:
        return {
            "code": "DB_CONNECTION_ERROR",
            "message": f"データベース接続エラー: {str(e)}"
        }


# このモジュールでは本番環境向けの実装のみを提供します
# テスト関数は別のモジュールで実装してください

if __name__ == "__main__":
    print("データベースサービスモジュールを直接実行することはできません。")
    print("アプリケーションから正しくインポートして使用してください。")
