"""
データベースサービス

このモジュールでは、Kuzuデータベースの初期化と操作に関するサービス関数を提供します。
"""

import os
from typing import Optional, Tuple, Any

from upsert.application.types import (
    DatabaseConnection,
    DatabaseError,
    DatabaseResult,
    DatabaseInitializationSuccess,
    DatabaseInitializationError,
    DatabaseInitializationResult,
)
from upsert.infrastructure.variables import DB_DIR, DB_NAME


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


def get_connection() -> DatabaseResult:
    """データベース接続を取得する
    
    Returns:
        DatabaseResult: 成功時はデータベース接続、失敗時はエラー情報
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
        
        return {"connection": conn}
    
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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
