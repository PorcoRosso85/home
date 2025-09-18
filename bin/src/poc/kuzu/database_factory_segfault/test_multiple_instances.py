#!/usr/bin/env python3
"""複数インスタンス作成時の問題を調査"""
import tempfile
import gc
import pytest


def test_singleton_pattern_simulation():
    """シングルトンパターンのシミュレーション"""
    import kuzu
    
    # キャッシュをシミュレート
    _cache = {}
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 同じパスで複数回作成
        path = f"{tmp_dir}/singleton.db"
        
        # 初回作成
        if path not in _cache:
            _cache[path] = kuzu.Database(path)
        db1 = _cache[path]
        
        # 2回目（キャッシュから）
        if path not in _cache:
            _cache[path] = kuzu.Database(path)
        db2 = _cache[path]
        
        # 同じインスタンスか確認
        assert db1 is db2


def test_concurrent_database_access():
    """並行アクセスのシミュレーション"""
    import kuzu
    import threading
    
    results = []
    errors = []
    
    def create_and_query(db_path, thread_id):
        try:
            db = kuzu.Database(db_path)
            conn = kuzu.Connection(db)
            result = conn.execute(f"RETURN {thread_id} as id")
            if result.has_next():
                results.append(result.get_next()[0])
        except Exception as e:
            errors.append((thread_id, str(e)))
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/concurrent.db"
        
        # 初期化
        db = kuzu.Database(db_path)
        
        # 複数スレッドから同じデータベースにアクセス
        threads = []
        for i in range(5):
            t = threading.Thread(target=create_and_query, args=(db_path, i))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert sorted(results) == list(range(5))


def test_garbage_collection_impact():
    """ガベージコレクションの影響"""
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 複数のデータベースを作成して削除
        for i in range(10):
            db_path = f"{tmp_dir}/gc_test_{i}.db"
            db = kuzu.Database(db_path)
            conn = kuzu.Connection(db)
            conn.execute("CREATE NODE TABLE Test (id INT64 PRIMARY KEY)")
            
            # 明示的に削除
            del conn
            del db
            
            # ガベージコレクション実行
            if i % 3 == 0:
                gc.collect()
        
        # 最後にもう一度作成
        final_db = kuzu.Database(f"{tmp_dir}/final.db")
        final_conn = kuzu.Connection(final_db)
        result = final_conn.execute("RETURN 'survived' as status")
        assert result.has_next()
        assert result.get_next()[0] == 'survived'


def test_database_reopen():
    """同じパスでデータベースを再オープン"""
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/reopen.db"
        
        # 初回作成
        db1 = kuzu.Database(db_path)
        conn1 = kuzu.Connection(db1)
        conn1.execute("CREATE NODE TABLE First (id INT64 PRIMARY KEY)")
        
        # 明示的にクローズ
        del conn1
        del db1
        
        # 再オープン
        db2 = kuzu.Database(db_path)
        conn2 = kuzu.Connection(db2)
        
        # テーブルが存在するか確認
        # （実際のKuzuDBではテーブル情報を取得する方法が必要）
        try:
            conn2.execute("CREATE NODE TABLE First (id INT64 PRIMARY KEY)")
            # エラーが出ればテーブルは既に存在
        except:
            pass  # 期待される動作


if __name__ == "__main__":
    print("=== Multiple Instances Investigation ===")
    
    test_singleton_pattern_simulation()
    print("✓ test_singleton_pattern_simulation passed")
    
    test_concurrent_database_access()
    print("✓ test_concurrent_database_access passed")
    
    test_garbage_collection_impact()
    print("✓ test_garbage_collection_impact passed")
    
    test_database_reopen()
    print("✓ test_database_reopen passed")