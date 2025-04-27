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

# クエリローダーモジュールのパスをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# upsert自身で判定ロジックを実装し、call_dmlからはcreate_query_loaderのみをインポート
from query.call_dml import create_query_loader

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
    
    Returns:
        DatabaseInitializationResult: 成功時はデータベース接続、失敗時はエラー情報
    """
    try:
        # 必要なインポートをローカルで行う
        import kuzu
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(DB_DIR, exist_ok=True)
        
        # データベース接続
        db = kuzu.Database(DB_DIR)
        conn = kuzu.Connection(db)
        
        # 各テーブルを作成
        success, error = create_function_table(conn)
        if not success:
            return {
                "code": "TABLE_CREATION_ERROR",
                "message": f"Function テーブル作成エラー: {error}"
            }
        
        success, error = create_parameter_table(conn)
        if not success:
            return {
                "code": "TABLE_CREATION_ERROR",
                "message": f"Parameter テーブル作成エラー: {error}"
            }
        
        success, error = create_has_parameter_table(conn)
        if not success:
            return {
                "code": "TABLE_CREATION_ERROR",
                "message": f"HasParameter テーブル作成エラー: {error}"
            }
        
        success, error = create_return_type_table(conn)
        if not success:
            return {
                "code": "TABLE_CREATION_ERROR",
                "message": f"ReturnType テーブル作成エラー: {error}"
            }
        
        success, error = create_has_return_type_table(conn)
        if not success:
            return {
                "code": "TABLE_CREATION_ERROR",
                "message": f"HasReturnType テーブル作成エラー: {error}"
            }
        
        return {
            "message": "データベースの初期化が完了しました",
            "connection": conn
        }
    
    except Exception as e:
        return {
            "code": "DB_INIT_ERROR",
            "message": f"データベース初期化エラー: {str(e)}"
        }


def create_function_table(conn: Any) -> Tuple[bool, Optional[str]]:
    """Function型のノードテーブルを作成する
    
    Args:
        conn: データベース接続
    
    Returns:
        Tuple[bool, Optional[str]]: 成功時は(True, None)、失敗時は(False, エラーメッセージ)
    """
    try:
        conn.execute(f"""
        CREATE NODE TABLE Function (
            title STRING,
            description STRING,
            type STRING,
            pure BOOLEAN,
            async BOOLEAN,
            PRIMARY KEY (title)
        )
        """)
        print("Function テーブルを作成しました")
        return True, None
    
    except Exception as e:
        if "already exists" in str(e):
            print("Function テーブルは既に存在します")
            return True, None
        else:
            print(f"テーブル作成エラー: {str(e)}")
            return False, str(e)


def create_parameter_table(conn: Any) -> Tuple[bool, Optional[str]]:
    """Parameter型のノードテーブルを作成する
    
    Args:
        conn: データベース接続
    
    Returns:
        Tuple[bool, Optional[str]]: 成功時は(True, None)、失敗時は(False, エラーメッセージ)
    """
    try:
        conn.execute(f"""
        CREATE NODE TABLE Parameter (
            name STRING,
            type STRING,
            description STRING,
            required BOOLEAN,
            PRIMARY KEY (name)
        )
        """)
        print("Parameter テーブルを作成しました")
        return True, None
    
    except Exception as e:
        if "already exists" in str(e):
            print("Parameter テーブルは既に存在します")
            return True, None
        else:
            print(f"テーブル作成エラー: {str(e)}")
            return False, str(e)


def create_has_parameter_table(conn: Any) -> Tuple[bool, Optional[str]]:
    """HasParameter型のエッジテーブルを作成する
    
    Args:
        conn: データベース接続
    
    Returns:
        Tuple[bool, Optional[str]]: 成功時は(True, None)、失敗時は(False, エラーメッセージ)
    """
    try:
        conn.execute(f"""
        CREATE REL TABLE HasParameter (
            FROM Function TO Parameter,
            order_index INT
        )
        """)
        print("HasParameter エッジテーブルを作成しました")
        return True, None
    
    except Exception as e:
        if "already exists" in str(e):
            print("HasParameter エッジテーブルは既に存在します")
            return True, None
        else:
            print(f"エッジテーブル作成エラー: {str(e)}")
            return False, str(e)


def create_return_type_table(conn: Any) -> Tuple[bool, Optional[str]]:
    """ReturnType型のノードテーブルを作成する
    
    Args:
        conn: データベース接続
    
    Returns:
        Tuple[bool, Optional[str]]: 成功時は(True, None)、失敗時は(False, エラーメッセージ)
    """
    try:
        conn.execute(f"""
        CREATE NODE TABLE ReturnType (
            type STRING,
            description STRING,
            PRIMARY KEY (type)
        )
        """)
        print("ReturnType テーブルを作成しました")
        return True, None
    
    except Exception as e:
        if "already exists" in str(e):
            print("ReturnType テーブルは既に存在します")
            return True, None
        else:
            print(f"テーブル作成エラー: {str(e)}")
            return False, str(e)


def create_has_return_type_table(conn: Any) -> Tuple[bool, Optional[str]]:
    """HasReturnType型のエッジテーブルを作成する
    
    Args:
        conn: データベース接続
    
    Returns:
        Tuple[bool, Optional[str]]: 成功時は(True, None)、失敗時は(False, エラーメッセージ)
    """
    try:
        conn.execute(f"""
        CREATE REL TABLE HasReturnType (
            FROM Function TO ReturnType
        )
        """)
        print("HasReturnType エッジテーブルを作成しました")
        return True, None
    
    except Exception as e:
        if "already exists" in str(e):
            print("HasReturnType エッジテーブルは既に存在します")
            return True, None
        else:
            print(f"エッジテーブル作成エラー: {str(e)}")
            return False, str(e)


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
    os.makedirs(test_query_dml_path)
    
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
