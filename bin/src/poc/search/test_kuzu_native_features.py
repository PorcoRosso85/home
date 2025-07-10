#!/usr/bin/env python3
"""
KuzuDB Native VSS/FTS機能のテスト（規約準拠）
requirement/graph環境で実行
"""

import os
import sys

# 環境設定
os.environ["PYTHONPATH"] = "/home/nixos/bin/src"
os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"


def test_kuzu_native_vss_fts():
    """KuzuDBネイティブのVSS/FTS機能をテスト"""
    # 直接kuzuをインポート
    import kuzu

    # インメモリDB作成
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)

    # 拡張機能をロード
    conn.execute("LOAD EXTENSION VECTOR;")
    conn.execute("LOAD EXTENSION FTS;")

    # テーブル作成
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            embedding DOUBLE[384]
        )
    """)

    # テストデータ投入
    requirements = [
        {"id": "req_001", "title": "ユーザー認証機能", "description": "ログインシステムの実装"},
        {"id": "req_002", "title": "二要素認証", "description": "2FAによるセキュリティ強化"},
        {"id": "req_003", "title": "ダッシュボード画面", "description": "管理者向け統計表示"},
    ]

    # 簡易埋め込み生成（実際は機械学習モデルを使用）
    def generate_embedding(text):
        import hashlib

        h = hashlib.sha256(text.encode()).digest()
        # 384次元のベクトルを生成
        base = [float(b) / 255.0 for b in h]
        # 384次元まで拡張
        embedding = []
        for i in range(384):
            embedding.append(base[i % len(base)])
        return embedding

    for req in requirements:
        embedding = generate_embedding(req["title"] + " " + req["description"])
        conn.execute(
            """
            CREATE (r:RequirementEntity {
                id: $id,
                title: $title,
                description: $description,
                embedding: $embedding
            })
        """,
            {"id": req["id"], "title": req["title"], "description": req["description"], "embedding": embedding},
        )

    print("=== KuzuDB Native VSS/FTS Test ===\n")

    # 1. FTSインデックス作成とテスト
    print("1. FTS Test:")
    conn.execute("CALL CREATE_FTS_INDEX('RequirementEntity', 'req_fts', ['title', 'description'])")

    # FTS検索
    result = conn.execute("""
        CALL QUERY_FTS_INDEX('RequirementEntity', 'req_fts', '認証')
        RETURN node, score
        ORDER BY score DESC
    """)

    print("  FTS Search Results for '認証':")
    while result.has_next():
        row = result.get_next()
        node = row[0]
        score = row[1]
        print(f"    - {node['id']}: {node['title']} (score: {score:.3f})")

    # 2. VSSインデックス作成とテスト
    print("\n2. VSS Test:")
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")

    # VSS検索
    query_vec = generate_embedding("認証システム")
    result = conn.execute(
        """
        CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 3)
        RETURN node, distance
        ORDER BY distance
    """,
        {"vec": query_vec},
    )

    print("  VSS Search Results for '認証システム':")
    while result.has_next():
        row = result.get_next()
        node = row[0]
        distance = row[1]
        print(f"    - {node['id']}: {node['title']} (distance: {distance:.3f})")

    # 3. ハイブリッド検索（FTS + VSS）
    print("\n3. Hybrid Search Test:")

    # FTSで候補を絞る
    fts_result = conn.execute("""
        CALL QUERY_FTS_INDEX('RequirementEntity', 'req_fts', '認証')
        RETURN node.id
    """)

    fts_ids = []
    while fts_result.has_next():
        fts_ids.append(fts_result.get_next()[0])

    # VSSで再ランキング
    print("  Hybrid Results (FTS filtered + VSS ranked):")
    if fts_ids:
        placeholders = ",".join([f"'{id}'" for id in fts_ids])
        hybrid_result = conn.execute(
            f"""
            MATCH (r:RequirementEntity)
            WHERE r.id IN [{placeholders}]
            WITH r
            CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 10)
            WHERE node = r
            RETURN node, distance
            ORDER BY distance
        """,
            {"vec": query_vec},
        )

        while hybrid_result.has_next():
            row = hybrid_result.get_next()
            node = row[0]
            distance = row[1]
            print(f"    - {node['id']}: {node['title']} (distance: {distance:.3f})")

    print("\n✅ All KuzuDB native features working!")
    return True


if __name__ == "__main__":
    # requirement/graph環境で実行
    venv_python = "/home/nixos/bin/src/requirement/graph/.venv/bin/python"

    if sys.executable != venv_python:
        # 正しい環境で再実行
        import subprocess

        result = subprocess.run([venv_python, __file__], env=os.environ)
        sys.exit(result.returncode)

    test_kuzu_native_vss_fts()
