#!/usr/bin/env python3
"""最小再現テスト - database_factoryのセグフォルトを再現"""
import tempfile
import pytest


def test_create_persistent_database():
    """requirement/graphで発生するセグフォルトの最小再現"""
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test.db"
        
        # データベース作成
        db = kuzu.Database(db_path)
        assert db is not None
        
        # ファイルが作成されたか確認
        import os
        assert os.path.exists(db_path)


def test_multiple_database_creation():
    """複数のデータベース作成でセグフォルトが発生するか"""
    import kuzu
    
    databases = []
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 10個のデータベースを作成
        for i in range(10):
            db_path = f"{tmp_dir}/test_{i}.db"
            db = kuzu.Database(db_path)
            databases.append(db)
            
        assert len(databases) == 10
        
        # 各データベースでコネクション作成
        for i, db in enumerate(databases):
            conn = kuzu.Connection(db)
            result = conn.execute("RETURN 1 as value")
            assert result.has_next()
            assert result.get_next()[0] == 1


def test_in_memory_database():
    """インメモリデータベースの作成"""
    import kuzu
    
    db = kuzu.Database(":memory:")
    assert db is not None
    
    conn = kuzu.Connection(db)
    result = conn.execute("RETURN 42 as answer")
    assert result.has_next()
    assert result.get_next()[0] == 42


if __name__ == "__main__":
    print("=== Database Factory Segfault Minimal Test ===")
    test_create_persistent_database()
    print("✓ test_create_persistent_database passed")
    
    test_multiple_database_creation()
    print("✓ test_multiple_database_creation passed")
    
    test_in_memory_database()
    print("✓ test_in_memory_database passed")