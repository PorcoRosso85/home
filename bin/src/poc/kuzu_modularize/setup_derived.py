#!/usr/bin/env python3
"""
Derived Graph Setup - ユースケース固有の拡張データ
"""
import kuzu
import shutil
from pathlib import Path

def setup_derived():
    # 既存DBがあれば削除
    db_path = Path("derived.kuzu")
    if db_path.exists():
        shutil.rmtree(db_path)
    
    # Derived DB作成
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    # 独自スキーマ定義（Masterのデータは参照のみ）
    conn.execute("""
        CREATE NODE TABLE Employee(
            person_id STRING PRIMARY KEY,
            department STRING,
            salary DOUBLE,
            hire_date DATE
        )
    """)
    
    # 独自データ投入
    conn.execute("""
        CREATE (e1:Employee {
            person_id: 'P001', 
            department: 'Engineering',
            salary: 120000.0,
            hire_date: date('2020-01-01')
        })
    """)
    
    conn.execute("""
        CREATE (e2:Employee {
            person_id: 'P002',
            department: 'Finance',
            salary: 95000.0,
            hire_date: date('2021-06-15')
        })
    """)
    
    # 確認クエリ（独自データのみ）
    result = conn.execute("""
        MATCH (e:Employee)
        RETURN e.person_id, e.department, e.salary
    """)
    
    print("Derived Graph Created (独自データ):")
    print("-" * 40)
    while result.has_next():
        row = result.get_next()
        print(f"Employee {row[0]}: {row[1]} dept, ${row[2]:,.0f}")
    
    conn.close()
    print("\n✅ Derived graph setup complete (without ATTACH yet)")

if __name__ == "__main__":
    setup_derived()