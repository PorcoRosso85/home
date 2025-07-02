"""
Tests for Apply DDL Schema
"""
import tempfile
import shutil
import os
import sys

# Environment variables setup for tests
# テスト用環境設定
from .variables import setup_test_environment
setup_test_environment()

# Import kuzu directly
import kuzu

from .apply_ddl_schema import apply_ddl_schema


def test_apply_ddl_schema_テスト環境_正常適用():
    """apply_ddl_schema_テスト環境_スキーマが正常に適用される"""
    # Arrange
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Act
        success = apply_ddl_schema(db_path=temp_dir, create_test_data=True)
        
        # Assert
        assert success
        
        # スキーマが適用されたか確認
        test_db = kuzu.Database(temp_dir)
        conn = kuzu.Connection(test_db)
        
        # LocationURIノードの確認
        result = conn.execute("MATCH (l:LocationURI) RETURN count(l) as cnt")
        assert result.has_next()
        assert result.get_next()[0] >= 3  # テストデータが作成されている
        
        # RequirementEntityの確認
        result = conn.execute("MATCH (r:RequirementEntity) RETURN count(r) as cnt")
        assert result.has_next()
        assert result.get_next()[0] >= 2
        
        # LOCATES関係の確認
        result = conn.execute("MATCH (l:LocationURI)-[:LOCATES]->(r:RequirementEntity) RETURN count(*) as cnt")
        assert result.has_next()
        assert result.get_next()[0] >= 2
        
        conn.close()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_apply_ddl_schema_スキーマなし_エラー処理():
    """apply_ddl_schema_存在しないスキーマ_エラーが適切に処理される"""
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