"""DDLスキーマ適用スクリプト"""

import os
import sys
from typing import Optional

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from db.kuzu.connection_fixed import get_connection
from requirement.graph.infrastructure.ddl_schema_manager import DDLSchemaManager


def apply_ddl_schema(db_path: Optional[str] = None, create_test_data: bool = False) -> bool:
    """
    DDLスキーマを適用
    
    Args:
        db_path: データベースパス（Noneの場合はデフォルト）
        create_test_data: テストデータを作成するか
        
    Returns:
        成功したかどうか
    """
    # スキーマファイルのパスを取得
    schema_path = os.path.join(
        project_root, 
        "kuzu", 
        "query", 
        "ddl", 
        "schema_v2.cypher"
    )
    
    if not os.path.exists(schema_path):
        print(f"Error: Schema file not found: {schema_path}")
        return False
    
    # 接続を確立
    try:
        conn = get_connection(db_path)
    except Exception as e:
        print(f"Error: Failed to connect to database: {e}")
        return False
    
    manager = DDLSchemaManager(conn)
    
    # スキーマを適用
    print(f"Applying schema from: {schema_path}")
    success, results = manager.apply_schema(schema_path)
    
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


# In-source tests
def test_apply_ddl_schema_テスト環境_正常適用():
    """apply_ddl_schema_テスト環境_スキーマが正常に適用される"""
    import tempfile
    import shutil
    
    # Arrange
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Act
        success = apply_ddl_schema(db_path=temp_dir, create_test_data=True)
        
        # Assert
        assert success
        
        # スキーマが適用されたか確認
        conn = get_connection(temp_dir)
        
        # LocationURIノードの確認
        result = conn.execute("MATCH (l:LocationURI) RETURN count(l) as cnt")
        assert result.has_next()
        assert result.get_next()[0] >= 3  # テストデータが作成されている
        
        # RequirementEntityの確認
        result = conn.execute("MATCH (r:RequirementEntity) RETURN count(r) as cnt")
        assert result.has_next()
        assert result.get_next()[0] >= 2
        
        # LOCATES関係の確認（リネームされたテーブル名を使用）
        result = conn.execute("MATCH (l:LocationURI)-[:LOCATES_LocationURI_RequirementEntity]->(r:RequirementEntity) RETURN count(*) as cnt")
        assert result.has_next()
        assert result.get_next()[0] >= 2
        
        conn.close()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_apply_ddl_schema_スキーマなし_エラー処理():
    """apply_ddl_schema_存在しないスキーマ_エラーが適切に処理される"""
    import tempfile
    
    # Arrange
    # 一時的に間違ったパスを設定
    original_path = sys.path[0]
    sys.path[0] = "/tmp/nonexistent"
    
    try:
        # Act
        success = apply_ddl_schema()
        
        # Assert
        assert not success
        
    finally:
        sys.path[0] = original_path


if __name__ == "__main__":
    # コマンドライン引数の処理
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply DDL schema to KuzuDB")
    parser.add_argument("--db-path", help="Database path")
    parser.add_argument("--test-data", action="store_true", help="Create test data")
    parser.add_argument("--run-tests", action="store_true", help="Run tests instead of applying schema")
    
    args = parser.parse_args()
    
    if args.run_tests:
        print("Running apply_ddl_schema tests...")
        
        test_apply_ddl_schema_テスト環境_正常適用()
        print("✓ test_apply_ddl_schema_テスト環境_正常適用")
        
        test_apply_ddl_schema_スキーマなし_エラー処理()
        print("✓ test_apply_ddl_schema_スキーマなし_エラー処理")
        
        print("All tests passed!")
    else:
        # 実際のスキーマ適用
        apply_ddl_schema(db_path=args.db_path, create_test_data=args.test_data)