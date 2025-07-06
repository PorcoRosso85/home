#!/usr/bin/env python3
"""実行順序依存性のテスト - 特定の順序でセグフォルトが発生するか"""
import tempfile
import pytest


class TestExecutionOrder:
    """requirement/graphの実行順序を模倣"""
    
    def test_cypher_executor_simulation(self):
        """CypherExecutorのようなテストをシミュレート"""
        # モックコネクションでクエリ実行をシミュレート
        class MockConnection:
            def execute(self, query):
                class Result:
                    def has_next(self):
                        return True
                    def get_next(self):
                        return [1]
                return Result()
        
        conn = MockConnection()
        result = conn.execute("MATCH (n) RETURN n")
        assert result.has_next()
    
    def test_database_factory_after_executor(self):
        """CypherExecutorテストの後にdatabase_factoryテストを実行"""
        import kuzu
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = f"{tmp_dir}/test.db"
            db = kuzu.Database(db_path)
            
            assert db is not None
            
            # コネクション作成
            conn = kuzu.Connection(db)
            result = conn.execute("RETURN 1 as value")
            assert result.has_next()
            assert result.get_next()[0] == 1


def test_mixed_database_types():
    """異なるタイプのデータベースを混在させた場合"""
    import kuzu
    
    # インメモリ
    db_memory = kuzu.Database(":memory:")
    conn_memory = kuzu.Connection(db_memory)
    
    # 永続化
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_persistent = kuzu.Database(f"{tmp_dir}/test.db")
        conn_persistent = kuzu.Connection(db_persistent)
        
        # 両方でクエリ実行
        for conn in [conn_memory, conn_persistent]:
            result = conn.execute("RETURN 1")
            assert result.has_next()


def test_json_extension_before_database_factory():
    """JSON拡張機能のテスト後にdatabase_factoryテストを実行"""
    import kuzu
    
    # JSON拡張機能をシミュレート（実際にはロードしない）
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        
        # 基本的なテーブル作成
        conn.execute("CREATE NODE TABLE Test (id INT64 PRIMARY KEY)")
        
    # その後、database_factoryのようなテスト
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/factory_test.db"
        db = kuzu.Database(db_path)
        assert db is not None


def test_pytest_fixture_simulation():
    """pytestのfixtureをシミュレート"""
    import kuzu
    
    # tmp_pathフィクスチャのシミュレーション
    import pathlib
    
    for i in range(3):
        tmp_path = pathlib.Path(tempfile.mkdtemp())
        
        try:
            db_path = tmp_path / f"test_{i}.db"
            db = kuzu.Database(str(db_path))
            
            conn = kuzu.Connection(db)
            result = conn.execute(f"RETURN {i}")
            assert result.has_next()
            
        finally:
            # cleanup
            import shutil
            if tmp_path.exists():
                shutil.rmtree(tmp_path)


if __name__ == "__main__":
    print("=== Execution Order Dependency Test ===")
    
    # 実行順序をシミュレート
    order_test = TestExecutionOrder()
    order_test.test_cypher_executor_simulation()
    print("✓ Cypher executor simulation passed")
    
    order_test.test_database_factory_after_executor()
    print("✓ Database factory after executor passed")
    
    test_mixed_database_types()
    print("✓ Mixed database types passed")
    
    test_json_extension_before_database_factory()
    print("✓ JSON extension before database factory passed")
    
    test_pytest_fixture_simulation()
    print("✓ Pytest fixture simulation passed")