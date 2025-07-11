"""
DDLスキーマ適用スクリプト
重要: graph/ddl/ディレクトリのスキーマのみを参照すること
他のDDL（kuzu/query/ddl等）は参照禁止
"""

import os
import sys
from typing import Optional

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from .variables import RGL_DB_PATH

from .ddl_schema_manager import DDLSchemaManager
from .logger import debug, info, warn, error
from .database_factory import create_database, create_connection


def apply_ddl_schema(db_path: Optional[str] = None, create_test_data: bool = False) -> bool:
    """
    DDLスキーマを適用

    Args:
        db_path: データベースパス（Noneの場合はデフォルト）
        create_test_data: テストデータを作成するか

    Returns:
        成功したかどうか
    """
    info("rgl.schema", "Starting DDL schema application", db_path=db_path, create_test_data=create_test_data)

    # スキーマファイルのパスを取得（graph/ddl/migrations/を参照）
    # __file__を使用して絶対パスを取得（sys.pathの変更に影響されない）
    schema_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "ddl",
        "migrations",
        "3.2.0_current.cypher"
    )

    if not os.path.exists(schema_path):
        error("rgl.schema", "Schema file not found", path=schema_path)
        # print文を削除（JSON出力を汚染しないため）
        return False

    # 接続を確立
    try:
        if db_path is None:
            db_path = RGL_DB_PATH
        
        # インメモリDBの場合はディレクトリ作成をスキップ
        if db_path == ":memory:":
            debug("rgl.schema", "Using in-memory database")
            db = create_database(in_memory=True, use_cache=False, test_unique=True)
        else:
            debug("rgl.schema", "Creating database directory", path=db_path)
            os.makedirs(db_path, exist_ok=True)
            db = create_database(path=db_path)

        info("rgl.schema", "Connecting to database")
        conn = create_connection(db)
        debug("rgl.schema", "Database connection established")
    except Exception as e:
        error("rgl.schema", "Failed to connect to database", error=str(e))
        # print文を削除（JSON出力を汚染しないため）
        return False

    manager = DDLSchemaManager(conn)

    # スキーマを適用
    info("rgl.schema", "Applying schema", schema_path=schema_path)
    info("rgl.schema", "Applying schema", path=schema_path)
    success, results = manager.apply_schema(schema_path)
    debug("rgl.schema", "Schema application completed", success=success, result_count=len(results))

    # 結果をログに記録
    for result in results:
        debug("rgl.schema", "Schema statement result", result=result)

    if not success:
        warn("rgl.schema", "Schema application failed, rolling back")
        _, rollback_results = manager.rollback()
        for result in rollback_results:
            debug("rgl.schema", "Rollback result", result=result)
        conn.close()
        return False

    # テストデータ作成
    if create_test_data:
        info("rgl.schema", "Creating test data")
        success, results = manager.create_test_data()
        for result in results:
            debug("rgl.schema", "Test data result", result=result)

    info("rgl.schema", "Schema application completed successfully")
    conn.close()
    return True


# CLIエントリポイントは削除されました
# apply_ddl_schema()関数を直接呼び出してください
