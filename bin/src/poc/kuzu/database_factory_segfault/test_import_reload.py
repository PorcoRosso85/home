#!/usr/bin/env python3
"""importlib.reloadの影響を調査"""
import tempfile
import importlib
import pytest


def test_kuzu_reload_basic():
    """kuzu moduleのreloadが安全か確認"""
    import kuzu
    
    # 初回インポート時のアドレス
    original_module = kuzu
    original_database_class = kuzu.Database
    
    # reload
    importlib.reload(kuzu)
    
    # reloadされたか確認
    assert kuzu is original_module  # 同じモジュールオブジェクト
    # クラスは新しいオブジェクトになる可能性がある
    
    # 基本動作確認
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    result = conn.execute("RETURN 1")
    assert result.has_next()


def test_reload_with_active_database():
    """アクティブなデータベースがある状態でのreload"""
    import kuzu
    
    # データベース作成
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # reload
    importlib.reload(kuzu)
    
    # 既存のコネクションが使えるか
    try:
        result = conn.execute("RETURN 2")
        assert result.has_next()
        assert result.get_next()[0] == 2
    except Exception as e:
        pytest.fail(f"Connection failed after reload: {e}")


def test_multiple_reload_cycles():
    """複数回のreloadサイクル"""
    import kuzu
    
    for i in range(5):
        # reload
        importlib.reload(kuzu)
        
        # 各サイクルでデータベース作成
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        result = conn.execute(f"RETURN {i} as cycle")
        assert result.has_next()
        assert result.get_next()[0] == i


def test_reload_between_tests():
    """テスト間でのreloadシミュレーション"""
    import kuzu
    
    # Test 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        db1 = kuzu.Database(f"{tmp_dir}/test1.db")
        conn1 = kuzu.Connection(db1)
        conn1.execute("CREATE NODE TABLE Test1 (id INT64 PRIMARY KEY)")
    
    # reload (別のテストをシミュレート)
    importlib.reload(kuzu)
    
    # Test 2
    with tempfile.TemporaryDirectory() as tmp_dir:
        db2 = kuzu.Database(f"{tmp_dir}/test2.db")
        conn2 = kuzu.Connection(db2)
        conn2.execute("CREATE NODE TABLE Test2 (id INT64 PRIMARY KEY)")


if __name__ == "__main__":
    print("=== Import Reload Investigation ===")
    
    test_kuzu_reload_basic()
    print("✓ test_kuzu_reload_basic passed")
    
    test_reload_with_active_database()
    print("✓ test_reload_with_active_database passed")
    
    test_multiple_reload_cycles()
    print("✓ test_multiple_reload_cycles passed")
    
    test_reload_between_tests()
    print("✓ test_reload_between_tests passed")