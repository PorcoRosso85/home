#!/usr/bin/env python3
"""
Cross-Graph Relationship Test - ATTACHしたmasterノードへのREL作成
"""
import kuzu
import shutil
from pathlib import Path

def test_cross_graph_relationship():
    print("=== Derivedグラフの再構築 ===")
    # Derivedを作り直し（RELテーブル追加）
    db_path = Path("derived_with_rel.kuzu")
    if db_path.exists():
        shutil.rmtree(db_path)
    
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    # Employeeテーブル作成
    conn.execute("""
        CREATE NODE TABLE Employee(
            person_id STRING PRIMARY KEY,
            department STRING,
            salary DOUBLE
        )
    """)
    
    # Projectテーブル作成（derived独自）
    conn.execute("""
        CREATE NODE TABLE Project(
            id STRING PRIMARY KEY,
            name STRING,
            budget DOUBLE
        )
    """)
    
    # RELテーブル定義（Employee -> Project）
    conn.execute("""
        CREATE REL TABLE WORKS_ON(
            FROM Employee TO Project,
            role STRING
        )
    """)
    
    # データ投入
    conn.execute("""
        CREATE (e1:Employee {person_id: 'P001', department: 'Engineering', salary: 120000})
    """)
    conn.execute("""
        CREATE (e2:Employee {person_id: 'P002', department: 'Finance', salary: 95000})
    """)
    conn.execute("""
        CREATE (proj1:Project {id: 'PROJ001', name: 'AI Platform', budget: 500000})
    """)
    conn.execute("""
        CREATE (proj2:Project {id: 'PROJ002', name: 'Data Pipeline', budget: 300000})
    """)
    
    # Employee -> Project のREL作成
    conn.execute("""
        MATCH (e:Employee {person_id: 'P001'}), (p:Project {id: 'PROJ001'})
        CREATE (e)-[:WORKS_ON {role: 'Lead Developer'}]->(p)
    """)
    
    print("✅ Derived graph with relationships created")
    
    print("\n=== MasterをATTACH ===")
    conn.execute("ATTACH 'master.kuzu' AS master (dbtype kuzu)")
    print("✅ Master attached")
    
    print("\n=== Cross-Graph REL作成の試み ===")
    
    # 1. ATTACHしたPersonノードへのREL作成を試みる
    try:
        # PersonからProjectへのRELテーブル定義を試みる
        conn.execute("""
            CREATE REL TABLE PERSON_MANAGES_PROJECT(
                FROM Person TO Project,
                since DATE
            )
        """)
        print("❌ Cross-graph REL table created (unexpected)")
    except Exception as e:
        print(f"✅ Cannot create REL table in read-only ATTACH: {str(e)[:80]}...")
    
    # 2. 既存ノード間でのREL作成を試みる
    try:
        conn.execute("""
            MATCH (p:Person {id: 'P001'})
            MATCH (org:Organization {id: 'O001'})
            CREATE (p)-[:TEST_REL]->(org)
        """)
        print("❌ Created REL in attached DB (unexpected)")
    except Exception as e:
        print(f"✅ Cannot create REL in read-only ATTACH: {str(e)[:80]}...")
    
    print("\n=== Virtual Join Pattern（実行時結合）===")
    # PersonとEmployeeを仮想的に結合
    result = conn.execute("""
        MATCH (p:Person)
        RETURN p.id AS person_id, p.name, p.age
    """)
    
    persons = {}
    while result.has_next():
        row = result.get_next()
        persons[row[0]] = {'name': row[1], 'age': row[2]}
    
    print("Master Persons:")
    for pid, pdata in persons.items():
        print(f"  {pid}: {pdata['name']} (age {pdata['age']})")
    
    # DETACH してderivedのデータを取得
    conn.execute("DETACH master")
    
    result = conn.execute("""
        MATCH (e:Employee)-[w:WORKS_ON]->(proj:Project)
        RETURN e.person_id, e.department, proj.name, w.role
    """)
    
    print("\nDerived Relationships:")
    while result.has_next():
        row = result.get_next()
        person_id = row[0]
        if person_id in persons:
            print(f"  {persons[person_id]['name']} ({row[1]}) -> {row[2]} as {row[3]}")
    
    print("\n=== 結論 ===")
    print("1. ATTACHしたDBは完全に読み取り専用")
    print("2. Cross-graph RELは作成不可")
    print("3. アプリケーション層での仮想結合が必要")
    print("4. または、データの選択的コピーが必要")
    
    conn.close()

if __name__ == "__main__":
    test_cross_graph_relationship()