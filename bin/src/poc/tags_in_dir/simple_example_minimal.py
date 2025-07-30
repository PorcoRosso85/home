#!/usr/bin/env python3
"""最小限のKuzuDB使用例"""

from kuzu_storage import KuzuStorage
from tags_in_dir import Symbol

# 1. シンプルなシンボルを作成
symbols = [
    Symbol(name="hello", kind="function", location_uri="file:///test.py#L1"),
    Symbol(name="world", kind="function", location_uri="file:///test.py#L5"),
]

# 2. KuzuDBに保存
storage = KuzuStorage(":memory:")
storage.store_symbols(symbols)

# 3. CALLS関係を追加
storage.create_calls_relationship(
    from_location_uri="file:///test.py#L5",  # world関数から
    to_location_uri="file:///test.py#L1"     # hello関数を呼ぶ
)

# 4. Cypherクエリ実行
print("=== 全シンボル ===")
result = storage.execute_cypher("MATCH (s:Symbol) RETURN s.name, s.location_uri")
for row in result:
    print(f"{row[0]}: {row[1]}")

print("\n=== 呼び出し関係 ===")
result = storage.execute_cypher("""
    MATCH (caller:Symbol)-[:CALLS]->(callee:Symbol)
    RETURN caller.name, callee.name
""")
for row in result:
    print(f"{row[0]} -> {row[1]}")