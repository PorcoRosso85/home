#!/usr/bin/env python
"""
KuzuDBへの直接クエリテスト
"""
import sys
sys.path.insert(0, '/home/nixos/bin/src')

import os
import kuzu


def direct_query_test():
    """KuzuDBに直接クエリ"""
    
    # データベース接続
    db_path = os.path.expanduser("~/.rgl/graph.db")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    print("=== KuzuDB直接クエリ ===\n")
    
    # 1. 全要件を確認
    print("1. 登録されている全要件:")
    result = conn.execute("""
        MATCH (r:RequirementEntity)
        RETURN r.id, r.title, r.tags
        ORDER BY r.id
    """)
    
    while result.has_next():
        row = result.get_next()
        print(f"   {row[0]}: {row[1]}")
        print(f"     Tags: {row[2]}")
    
    # 2. 依存関係を確認
    print("\n2. 依存関係:")
    result = conn.execute("""
        MATCH (from:RequirementEntity)-[d:DEPENDS_ON]->(to:RequirementEntity)
        RETURN from.title, to.title, d.reason
    """)
    
    while result.has_next():
        row = result.get_next()
        print(f"   「{row[0]}」→「{row[1]}」")
        print(f"     理由: {row[2]}")
    
    # 3. 階層を遡るクエリ（親を探す）
    print("\n3. 抽象要件への遡り（もし階層関係があれば）:")
    
    # PARENT_OF関係は未実装なので、依存関係から推測
    print("\n   依存関係の逆引き（何が依存しているか）:")
    result = conn.execute("""
        MATCH (to:RequirementEntity)<-[d:DEPENDS_ON]-(from:RequirementEntity)
        WHERE to.id = 'req_517454'
        RETURN from.id, from.title
    """)
    
    while result.has_next():
        row = result.get_next()
        print(f"   グラフDBに依存: {row[0]} - {row[1]}")
    
    # 4. タグベースの階層推定
    print("\n4. タグから階層を推定:")
    for level in ["L0_vision", "L1_architecture", "L2_implementation"]:
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE $tag IN r.tags
            RETURN r.title
        """, {"tag": level})
        
        titles = []
        while result.has_next():
            row = result.get_next()
            titles.append(row[0])
        
        if titles:
            print(f"   {level}: {', '.join(titles)}")
    
    conn.close()
    
    print("\n=== 結論 ===")
    print("✓ 依存関係のクエリは可能")
    print("✓ タグによる階層分類は可能")
    print("✗ 親子関係（PARENT_OF）は未実装")
    print("\n現状では「どの抽象的な要件のためのものか」は")
    print("タグ（L0/L1/L2）から推測するしかない")


if __name__ == "__main__":
    direct_query_test()