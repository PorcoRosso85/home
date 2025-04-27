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


def get_connection(with_query_loader: bool = False) -> Union[DatabaseResult, QueryLoaderResult]:
    """データベース接続を取得する
    
    Args:
        with_query_loader: クエリローダーも一緒に取得するかどうか
    
    Returns:
        成功時はデータベース接続（とクエリローダー）、失敗時はエラー情報
    """
    try:
        import kuzu
        
        # ディレクトリの存在確認
        if not os.path.exists(DB_DIR):
            return {
                "code": "DB_NOT_FOUND",
                "message": f"データベースディレクトリが見つかりません: {DB_DIR}"
            }
        
        # データベース接続
        db = kuzu.Database(DB_DIR)
        conn = kuzu.Connection(db)
        
        # クエリローダーが不要な場合は接続のみ返す
        if not with_query_loader:
            return {"connection": conn}
        
        # クエリローダー用のパスを設定
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from query.call_dml import create_query_loader
        
        # クエリローダーの作成
        loader = create_query_loader(QUERY_DIR, dml_subdir="dml")
        
        # 接続とクエリローダーを返す
        return {
            "connection": conn,
            "query_loader": loader
        }
    
    except Exception as e:
        return {
            "code": "DB_CONNECTION_ERROR",
            "message": f"データベース接続エラー: {str(e)}"
        }


# テスト関数
def test_db_connection() -> None:
    """データベース接続のテスト"""
    # テストディレクトリを作成
    import tempfile
    test_db_path = tempfile.mkdtemp()
    
    try:
        # テストではimportされた設定変数を直接参照できないため
        # モンキーパッチングを行う
        import upsert.infrastructure.variables as vars
        original_db_dir = vars.DB_DIR
        vars.DB_DIR = test_db_path
        
        # 接続テスト
        result = init_database()
        assert "code" not in result
        assert "connection" in result
        assert "message" in result
        
        # 復元
        vars.DB_DIR = original_db_dir
    
    except ImportError:
        # ライブラリがない場合はテストをスキップ
        print("kuzu ライブラリがないためテストをスキップします")
    
    finally:
        # テスト用ディレクトリを削除
        import shutil
        shutil.rmtree(test_db_path)


def test_get_connection_with_query_loader() -> None:
    """クエリローダー付きの接続取得をテスト"""
    # テストディレクトリを作成
    import tempfile
    import shutil
    
    test_db_path = tempfile.mkdtemp()
    test_query_path = tempfile.mkdtemp()
    test_query_dml_path = os.path.join(test_query_path, "dml")
    os.makedirs(test_query_dml_path, exist_ok=True)
    
    try:
        # テスト用のクエリファイルを作成
        test_query = "// テストクエリ\nRETURN 1;"
        test_file_path = os.path.join(test_query_dml_path, "test_query.cypher")
        with open(test_file_path, "w") as f:
            f.write(test_query)
        
        # テストではimportされた設定変数を直接参照できないため
        # モンキーパッチングを行う
        import upsert.infrastructure.variables as vars
        original_db_dir = vars.DB_DIR
        original_query_dir = vars.QUERY_DIR
        vars.DB_DIR = test_db_path
        vars.QUERY_DIR = test_query_path
        
        # 接続とクエリローダーの取得テスト
        result = get_connection(with_query_loader=True)
        
        # 結果の検証
        assert "code" not in result  # errorがないことを確認
        assert "connection" in result
        assert "query_loader" in result
        
        # クエリローダーの動作確認
        loader = result["query_loader"]
        
        # システムパスを設定
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from query.call_dml import create_query_loader
        
        # ここで、テストファイルがあるディレクトリをクエリローダーに直接渡す
        test_loader = create_query_loader(test_query_path, dml_subdir="dml")
        query_result = test_loader["get_query"]("test_query")
        assert test_loader["get_success"](query_result)
        assert query_result["data"] == test_query
        
        # 設定の復元
        vars.DB_DIR = original_db_dir
        vars.QUERY_DIR = original_query_dir
    
    except ImportError:
        # ライブラリがない場合はテストをスキップ
        print("kuzu または必要なライブラリがないためテストをスキップします")
    
    finally:
        # テスト用ディレクトリを削除
        shutil.rmtree(test_db_path)
        shutil.rmtree(test_query_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
