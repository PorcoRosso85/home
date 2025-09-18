#!/usr/bin/env python3
"""KuzuDBのスキーマを調査するスクリプト"""
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from graph.infrastructure.cypher_executor import CypherExecutor

def setup_db_connection():
    """データベース接続のセットアップ"""
    os.environ["LD_LIBRARY_PATH"] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
    os.environ["RGL_DB_PATH"] = "/home/nixos/bin/src/kuzu/kuzu_db"
    
    # 直接KuzuDBに接続
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kuzu", 
        "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu/__init__.py"
    )
    kuzu = importlib.util.module_from_spec(spec)
    sys.modules['kuzu'] = kuzu
    spec.loader.exec_module(kuzu)
    
    db = kuzu.Database("/home/nixos/bin/src/kuzu/kuzu_db")
    return kuzu.Connection(db)

def investigate_schema():
    """スキーマを調査"""
    conn = setup_db_connection()
    executor = CypherExecutor(conn)
    
    print("=== KuzuDB スキーマ調査 ===\n")
    
    # 1. RequirementEntityの実際のデータを確認
    print("1. RequirementEntityの実際のデータ（1件）:")
    result = executor.execute("""
        MATCH (r:RequirementEntity)
        RETURN r
        LIMIT 1
    """)
    if result["data"]:
        print(f"  データ: {result['data'][0][0]}")
    else:
        print("  データなし")
    
    # 2. RequirementEntityのプロパティキーを調査
    print("\n2. RequirementEntityで実際に使用されているプロパティ:")
    result = executor.execute("""
        MATCH (r:RequirementEntity)
        RETURN r.id, r.title, r.description, r.priority, r.requirement_type, r.verification_required
        LIMIT 1
    """)
    if result["data"]:
        props = ["id", "title", "description", "priority", "requirement_type", "verification_required"]
        for i, prop in enumerate(props):
            print(f"  {prop}: {result['data'][0][i]}")
    
    # 3. hierarchy_levelプロパティの存在確認
    print("\n3. hierarchy_levelプロパティの存在確認:")
    try:
        result = executor.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.hierarchy_level
            LIMIT 1
        """)
        print(f"  hierarchy_levelの値: {result['data'][0][0] if result['data'] else 'データなし'}")
    except Exception as e:
        print(f"  エラー: {str(e)}")
    
    # 4. LocationURIのプロパティ確認
    print("\n4. LocationURIの実際のデータ（1件）:")
    result = executor.execute("""
        MATCH (l:LocationURI)
        RETURN l
        LIMIT 1
    """)
    if result["data"]:
        print(f"  データ: {result['data'][0][0]}")
    
    # 5. ノードのカウント
    print("\n5. 各ノードタイプのカウント:")
    node_types = ["RequirementEntity", "LocationURI", "ReferenceEntity", "CodeEntity", "VersionState"]
    for node_type in node_types:
        result = executor.execute(f"MATCH (n:{node_type}) RETURN count(n)")
        print(f"  {node_type}: {result['data'][0][0]}件")
    
    # 6. データベースのスキーマ情報取得を試みる
    print("\n6. KuzuDB固有のスキーマ情報取得の試み:")
    try:
        # KuzuDBのcatalog関数を使用してみる
        result = executor.execute("CALL show_tables() RETURN *")
        print("  テーブル情報:")
        for row in result["data"]:
            print(f"    {row}")
    except Exception as e:
        print(f"  show_tables()エラー: {str(e)}")
    
    try:
        # 別の方法を試す
        result = executor.execute("CALL table_info('RequirementEntity') RETURN *")
        print("  RequirementEntityのテーブル情報:")
        for row in result["data"]:
            print(f"    {row}")
    except Exception as e:
        print(f"  table_info()エラー: {str(e)}")

if __name__ == "__main__":
    investigate_schema()