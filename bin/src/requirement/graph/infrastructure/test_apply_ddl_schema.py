"""
Tests for Apply DDL Schema
"""

# Environment variables setup for tests
# テスト用環境設定
from .variables import setup_test_environment
setup_test_environment()

from .apply_ddl_schema import apply_ddl_schema
from .database_factory import create_database, create_connection


def test_apply_ddl_schema_テスト環境_正常適用():
    """apply_ddl_schema_テスト環境_スキーマが正常に適用される"""
    # Act
    success = apply_ddl_schema(db_path=":memory:", create_test_data=True)

    # Assert
    assert success

    # スキーマが適用されたか確認
    # Note: インメモリDBのため、新しいインスタンスを作成
    test_db = create_database(in_memory=True, use_cache=False, test_unique=True)
    conn = create_connection(test_db)
    
    # スキーマを再適用（インメモリDBのため）
    apply_ddl_schema(db_path=":memory:", create_test_data=True)

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


def test_apply_ddl_schema_スキーマなし_エラー処理():
    """apply_ddl_schema_存在しないスキーマ_エラーが適切に処理される"""
    # Arrange
    # os.path.existsをモックして、スキーマファイルが存在しない状況をシミュレート
    import unittest.mock

    with unittest.mock.patch('os.path.exists', return_value=False):
        # Act
        success = apply_ddl_schema()

        # Assert
        assert not success
