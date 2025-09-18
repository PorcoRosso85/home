#!/usr/bin/env python3
"""
ATTACH機能の検証 - derivedからmasterを参照
"""
import kuzu
from pathlib import Path

def test_attach():
    # Derived DBに接続
    conn = kuzu.Connection(kuzu.Database("derived.kuzu"))
    
    print("=== ATTACH前の状態 ===")
    # Employeeデータのみアクセス可能
    result = conn.execute("MATCH (e:Employee) RETURN count(e)")
    print(f"Employee count: {result.get_next()[0]}")
    
    # Personにアクセスしようとするとエラー
    try:
        conn.execute("MATCH (p:Person) RETURN count(p)")
        print("Person accessible (unexpected)")
    except Exception as e:
        print(f"Person not accessible (expected): {str(e)[:50]}...")
    
    print("\n=== ATTACHの実行 ===")
    # MasterをATTACH
    conn.execute("ATTACH 'master.kuzu' AS master (dbtype kuzu)")
    print("✅ Master graph attached")
    
    print("\n=== ATTACH後の状態 ===")
    # Personデータにアクセス可能に
    result = conn.execute("MATCH (p:Person) RETURN count(p)")
    print(f"Person count: {result.get_next()[0]}")
    
    result = conn.execute("MATCH (o:Organization) RETURN count(o)")
    print(f"Organization count: {result.get_next()[0]}")
    
    print("\n=== 結合クエリの実行 ===")
    # ATTACHすると元のテーブルにアクセスできなくなる制約を確認
    try:
        result = conn.execute("MATCH (e:Employee) RETURN count(e)")
        print(f"Employee still accessible: {result.get_next()[0]}")
    except Exception as e:
        print(f"⚠️ Employee not accessible after ATTACH: {str(e)[:100]}...")
        print("This is a KuzuDB limitation: ATTACH replaces the current database context")
    
    # Masterのデータは参照可能
    result = conn.execute("""
        MATCH (p:Person)-[w:WORKS_FOR]->(o:Organization)
        RETURN p.name, p.age, o.name, w.since
        ORDER BY p.name
    """)
    
    print("Master graph data (via ATTACH):")
    print("-" * 60)
    while result.has_next():
        row = result.get_next()
        print(f"{row[0]} (age {row[1]}) works for {row[2]} since {row[3]}")
    
    print("\n=== 更新制約の検証 ===")
    # Masterデータの更新を試みる（失敗するはず）
    try:
        conn.execute("MATCH (p:Person {id: 'P001'}) SET p.name = 'Alice Updated'")
        print("❌ Master data updated (unexpected)")
    except Exception as e:
        print(f"✅ Master data is read-only: {str(e)[:100]}...")
    
    # Derivedデータは更新不可（ATTACHによりコンテキスト切り替わるため）
    try:
        conn.execute("MATCH (e:Employee {person_id: 'P001'}) SET e.salary = 130000.0")
        print("❌ Employee data updated (unexpected)")
    except Exception as e:
        print(f"✅ Employee table not accessible during ATTACH: {str(e)[:50]}...")
    
    print("\n=== DETACH実行 ===")
    conn.execute("DETACH master")
    print("✅ Master graph detached")
    
    # DETACH後はPersonにアクセス不可
    try:
        conn.execute("MATCH (p:Person) RETURN count(p)")
        print("Person still accessible (unexpected)")
    except Exception as e:
        print(f"✅ Person not accessible after DETACH: {str(e)[:50]}...")
    
    conn.close()

if __name__ == "__main__":
    test_attach()