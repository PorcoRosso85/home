#!/usr/bin/env python3
"""最もシンプルなKuzuDBの使用例"""

from kuzu_storage import KuzuStorage
from tags_in_dir import CtagsParser, Symbol

# 1. シンプルなテストファイルを作成
test_code = '''
def hello():
    print("Hello")

def world():
    hello()
    print("World")

def main():
    world()
'''

with open("test_simple.py", "w") as f:
    f.write(test_code)

# 2. ctagsでシンボルを抽出
parser = CtagsParser()
symbols = parser.extract_symbols(".", extensions=[".py"])

print("=== 抽出されたシンボル ===")
for symbol in symbols:
    print(f"{symbol.name}: {symbol.location_uri}")

# 3. KuzuDBに保存
storage = KuzuStorage(":memory:")
storage.store_symbols(symbols)

# 4. 手動でCALLS関係を追加（world -> hello, main -> world）
storage.create_calls_relationship(
    from_uri="file:///home/nixos/bin/src/poc/tags_in_dir/test_simple.py#L5",
    to_uri="file:///home/nixos/bin/src/poc/tags_in_dir/test_simple.py#L2",
    properties={"line_number": 6}
)
storage.create_calls_relationship(
    from_uri="file:///home/nixos/bin/src/poc/tags_in_dir/test_simple.py#L9",
    to_uri="file:///home/nixos/bin/src/poc/tags_in_dir/test_simple.py#L5",
    properties={"line_number": 10}
)

print("\n=== Cypherクエリ実行例 ===")

# 5. 全てのシンボルを取得
print("\n1. 全シンボル:")
result = storage.execute_cypher("MATCH (s:Symbol) RETURN s.name, s.location_uri")
for row in result:
    print(f"  {row[0]}: {row[1]}")

# 6. 呼び出し関係を確認
print("\n2. 呼び出し関係:")
result = storage.execute_cypher("""
    MATCH (caller:Symbol)-[:CALLS]->(callee:Symbol)
    RETURN caller.name, callee.name
""")
for row in result:
    print(f"  {row[0]} -> {row[1]}")

# 7. 最も呼ばれている関数
print("\n3. 呼び出し回数:")
result = storage.execute_cypher("""
    MATCH (s:Symbol)<-[:CALLS]-()
    RETURN s.name, count(*) as call_count
    ORDER BY call_count DESC
""")
for row in result:
    print(f"  {row[0]}: {row[1]}回")

# クリーンアップ
import os
os.remove("test_simple.py")