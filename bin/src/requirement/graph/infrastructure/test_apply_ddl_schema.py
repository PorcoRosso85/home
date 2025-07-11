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
    # テスト用のDBインスタンスを作成
    test_db = create_database(in_memory=True, use_cache=False, test_unique=True)
    conn = create_connection(test_db)
    
    # スキーマを直接適用
    from .ddl_schema_manager import DDLSchemaManager
    import os
    from pathlib import Path
    
    manager = DDLSchemaManager(conn)
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(current_dir, "ddl", "migrations", "3.2.0_current.cypher")
    
    # Act
    success, results = manager.apply_schema(schema_path)
    
    # Assert
    assert success
    assert len(results) > 0
    
    # テストデータを作成
    conn.execute("""
        CREATE (loc1:LocationURI {id: 'loc_001'}),
               (loc2:LocationURI {id: 'loc_002'}),
               (loc3:LocationURI {id: 'loc_003'}),
               (req1:RequirementEntity {id: 'req_001', title: 'Test Req 1'}),
               (req2:RequirementEntity {id: 'req_002', title: 'Test Req 2'})
    """)
    
    conn.execute("""
        MATCH (l:LocationURI), (r:RequirementEntity)
        WHERE l.id IN ['loc_001', 'loc_002'] AND r.id IN ['req_001', 'req_002']
        CREATE (l)-[:LOCATES]->(r)
    """)

    # LocationURIノードの確認
    result = conn.execute("MATCH (l:LocationURI) RETURN count(l) as cnt")
    assert result.has_next()
    assert result.get_next()[0] >= 3

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
