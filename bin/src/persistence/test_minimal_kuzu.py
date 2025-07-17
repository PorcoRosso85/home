#!/usr/bin/env python3
"""最小限のKuzuDB in-memory動作テスト"""

import sys
import traceback

def test_kuzu_import():
    """Kuzuのインポートテスト"""
    try:
        import kuzu
        print(f"✓ Kuzu import successful")
        return True
    except ImportError as e:
        print(f"✗ Kuzu import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False

def test_in_memory_database():
    """In-memoryデータベースの基本動作テスト"""
    try:
        import kuzu
        
        # In-memoryデータベース作成
        db = kuzu.Database(":memory:")
        print("✓ In-memory database created")
        
        # コネクション作成
        conn = kuzu.Connection(db)
        print("✓ Connection created")
        
        # スキーマ作成
        conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))")
        print("✓ Schema created")
        
        # データ挿入
        conn.execute("CREATE (:Person {name: 'Alice', age: 30})")
        conn.execute("CREATE (:Person {name: 'Bob', age: 25})")
        print("✓ Data inserted")
        
        # クエリ実行
        result = conn.execute("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age")
        rows = result.get_as_df()
        print("✓ Query executed")
        print(f"  Results: {len(rows)} rows")
        for _, row in rows.iterrows():
            print(f"  - {row['p.name']}: {row['p.age']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Database operation failed: {e}")
        traceback.print_exc()
        return False

def test_persistence_module():
    """persistenceモジュールの動作テスト"""
    try:
        # kuzu_pyディレクトリからインポート
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kuzu_py'))
        from core.database import create_database, create_connection
        
        # In-memoryデータベース作成（テスト用ユニーク）
        db = create_database(":memory:", test_unique=True)
        print("✓ Persistence module: database created")
        
        # コネクション作成
        conn = create_connection(db)
        print("✓ Persistence module: connection created")
        
        # 基本操作
        conn.execute("CREATE NODE TABLE Test(id INT64, PRIMARY KEY (id))")
        conn.execute("CREATE (:Test {id: 1})")
        result = conn.execute("MATCH (t:Test) RETURN t.id")
        
        if result.has_next():
            print("✓ Persistence module: operations successful")
            return True
        else:
            print("✗ Persistence module: no results returned")
            return False
            
    except Exception as e:
        print(f"✗ Persistence module failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("=== KuzuDB Minimal Test ===\n")
    
    results = []
    
    # 1. インポートテスト
    print("1. Import Test")
    results.append(test_kuzu_import())
    print()
    
    # 2. 基本動作テスト
    if results[0]:  # インポート成功時のみ
        print("2. In-Memory Database Test")
        results.append(test_in_memory_database())
        print()
        
        print("3. Persistence Module Test")
        results.append(test_persistence_module())
        print()
    
    # 結果サマリー
    print("=== Summary ===")
    total = len(results)
    passed = sum(results)
    print(f"Tests: {passed}/{total} passed")
    
    if passed == total:
        print("\n✓ All tests passed - KuzuDB is working correctly")
        return 0
    else:
        print("\n✗ Some tests failed - KuzuDB has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())