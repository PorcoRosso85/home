#\!/usr/bin/env python3
import sys
sys.path.append('.')

from infrastructure.database_factory import create_database, create_connection
from infrastructure.ddl_schema_manager import DDLSchemaManager
import os

# 山田さん（PM）のシナリオ
print("=== 山田さん（PM）が要件グラフ構築を開始 ===")
print("DBを初期化中...")

# DBを作成
db = create_database('./pm_requirements.db')
conn = create_connection('./pm_requirements.db')

# スキーマを適用
schema_dir = './ddl/migrations'
manager = DDLSchemaManager(conn, schema_dir)
manager.apply_schema('3.4.0_search_integration.cypher')

print("✅ DB初期化完了")

# 最初の要件を追加
print("\n要件を追加します...")
conn.execute("""
CREATE (r:Requirement {
    id: 'PM-001',
    title: '顧客管理システム',
    description: '顧客情報の登録・検索・編集機能',
    created_at: datetime('2024-01-15T10:00:00'),
    type: 'epic'
})
""")
print("✅ PM-001: 顧客管理システム を追加")

# 子要件を追加
conn.execute("""
CREATE (r:Requirement {
    id: 'PM-002', 
    title: '顧客検索機能',
    description: '名前、電話番号、メールで検索',
    created_at: datetime('2024-01-15T10:15:00'),
    type: 'feature'
})
""")

# 依存関係を作成
conn.execute("""
MATCH (parent:Requirement {id: 'PM-001'})
MATCH (child:Requirement {id: 'PM-002'})
CREATE (child)-[:DEPENDS_ON]->(parent)
""")
print("✅ PM-002: 顧客検索機能 を追加（PM-001に依存）")

# 検索してみる
print("\n登録した要件を確認...")
result = conn.execute("MATCH (r:Requirement) RETURN r.id, r.title")
for row in result:
    print(f"  - {row[0]}: {row[1]}")

print("\n山田さん「Cypherクエリ直書きは大変だな...」")
