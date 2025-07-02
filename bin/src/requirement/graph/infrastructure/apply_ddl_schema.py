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

from .variables import LD_LIBRARY_PATH, RGL_DB_PATH

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
    
    # スキーマファイルのパスを取得（graph/ddl/を参照）
    schema_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "ddl", 
        "schema.cypher"
    )
    
    if not os.path.exists(schema_path):
        error("rgl.schema", "Schema file not found", path=schema_path)
        print(f"Error: Schema file not found: {schema_path}")
        return False
    
    # 接続を確立
    try:
        if db_path is None:
            db_path = RGL_DB_PATH
        debug("rgl.schema", "Creating database directory", path=db_path)
        os.makedirs(db_path, exist_ok=True)
        
        info("rgl.schema", "Connecting to database")
        db = create_database(path=db_path)
        conn = create_connection(db)
        debug("rgl.schema", "Database connection established")
    except Exception as e:
        error("rgl.schema", "Failed to connect to database", error=str(e))
        print(f"Error: Failed to connect to database: {e}")
        return False
    
    manager = DDLSchemaManager(conn)
    
    # スキーマを適用
    info("rgl.schema", "Applying schema", schema_path=schema_path)
    print(f"Applying schema from: {schema_path}")
    success, results = manager.apply_schema(schema_path)
    debug("rgl.schema", "Schema application completed", success=success, result_count=len(results))
    
    for result in results:
        print(result)
    
    if not success:
        print("\nSchema application failed. Rolling back...")
        _, rollback_results = manager.rollback()
        for result in rollback_results:
            print(result)
        conn.close()
        return False
    
    # テストデータ作成
    if create_test_data:
        print("\nCreating test data...")
        success, results = manager.create_test_data()
        for result in results:
            print(result)
    
    print("\nSchema application completed successfully!")
    conn.close()
    return True


if __name__ == "__main__":
    """スクリプトとして実行された場合"""
    import argparse
    parser = argparse.ArgumentParser(description="Apply DDL schema to KuzuDB")
    parser.add_argument("--db-path", help="Database path", default=None)
    parser.add_argument("--test-data", action="store_true", help="Create test data")
    args = parser.parse_args()
    
    success = apply_ddl_schema(db_path=args.db_path, create_test_data=args.test_data)
    sys.exit(0 if success else 1)
