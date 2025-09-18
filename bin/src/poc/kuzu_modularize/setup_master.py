#!/usr/bin/env python3
"""
Master Graph Setup - 基本データの真実の源泉
"""
import kuzu
import shutil
from pathlib import Path

def setup_master():
    # 既存DBがあれば削除
    db_path = Path("master.kuzu")
    if db_path.exists():
        shutil.rmtree(db_path)
    
    # Master DB作成
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    # スキーマ定義
    conn.execute("""
        CREATE NODE TABLE Person(
            id STRING PRIMARY KEY,
            name STRING,
            age INT32,
            birth_date DATE
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE Organization(
            id STRING PRIMARY KEY,
            name STRING,
            type STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE WORKS_FOR(
            FROM Person TO Organization,
            since DATE
        )
    """)
    
    # データ投入
    conn.execute("""
        CREATE (p1:Person {id: 'P001', name: 'Alice', age: 30, birth_date: date('1994-01-15')})
    """)
    conn.execute("""
        CREATE (p2:Person {id: 'P002', name: 'Bob', age: 28, birth_date: date('1996-05-20')})
    """)
    conn.execute("""
        CREATE (o1:Organization {id: 'O001', name: 'TechCorp', type: 'Technology'})
    """)
    conn.execute("""
        CREATE (o2:Organization {id: 'O002', name: 'FinanceInc', type: 'Finance'})
    """)
    
    # リレーション作成
    conn.execute("""
        MATCH (p:Person {id: 'P001'}), (o:Organization {id: 'O001'})
        CREATE (p)-[:WORKS_FOR {since: date('2020-01-01')}]->(o)
    """)
    conn.execute("""
        MATCH (p:Person {id: 'P002'}), (o:Organization {id: 'O002'})
        CREATE (p)-[:WORKS_FOR {since: date('2021-06-15')}]->(o)
    """)
    
    # 確認クエリ
    result = conn.execute("""
        MATCH (p:Person)-[w:WORKS_FOR]->(o:Organization)
        RETURN p.name, o.name, w.since
    """)
    
    print("Master Graph Created:")
    print("-" * 40)
    while result.has_next():
        row = result.get_next()
        print(f"{row[0]} works for {row[1]} since {row[2]}")
    
    conn.close()
    print("\n✅ Master graph setup complete")

if __name__ == "__main__":
    setup_master()