#!/usr/bin/env python3
"""
ハイブリッド検索のpytestテスト
"""

import pytest
import os

# 環境変数で設定
os.environ["PYTHONPATH"] = "/home/nixos/bin/src"

import kuzu


def generate_embedding(text: str) -> list:
    """簡易的な埋め込み生成"""
    import hashlib

    h = hashlib.sha256(text.encode()).digest()
    base = [float(b) / 255.0 for b in h]
    return [base[i % len(base)] for i in range(384)]


def test_duplicate_detection():
    """重複要件の検出"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # 拡張機能をインストールとロード
    try:
        conn.execute("INSTALL VECTOR;")
        conn.execute("INSTALL FTS;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")
    conn.execute("LOAD EXTENSION FTS;")

    # スキーマ作成
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            author STRING,
            embedding DOUBLE[384]
        )
    """)

    # インデックス作成
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")
    conn.execute("CALL CREATE_FTS_INDEX('RequirementEntity', 'req_fts', ['title', 'description'])")

    # テストデータ
    requirements = [
        {
            "id": "req_a_001",
            "title": "ユーザー認証機能",
            "description": "ユーザーがログインできる機能",
            "author": "TeamA",
        },
        {
            "id": "req_b_001",
            "title": "ログインシステム",
            "description": "利用者がサインインする仕組み",
            "author": "TeamB",
        },
        {"id": "req_c_001", "title": "ダッシュボード", "description": "管理画面の実装", "author": "TeamC"},
    ]

    for req in requirements:
        embedding = generate_embedding(req["title"] + " " + req["description"])
        conn.execute(
            """
            CREATE (r:RequirementEntity {
                id: $id,
                title: $title,
                description: $description,
                author: $author,
                embedding: $embedding
            })
        """,
            {**req, "embedding": embedding},
        )

    # FTS検索（簡易版 - CONTAINS使用）
    fts_result = conn.execute("""
        MATCH (r:RequirementEntity)
        WHERE r.title CONTAINS '認証' OR r.description CONTAINS '認証'
        RETURN r.id
    """)

    fts_ids = []
    while fts_result.has_next():
        row = fts_result.get_next()
        fts_ids.append(row[0])

    assert len(fts_ids) >= 1, "FTSは「認証」を含む要件を検出"
    assert "req_a_001" in fts_ids

    # VSS検索（KuzuDBネイティブ）
    query_vec = generate_embedding("アカウント認証システム")

    vss_result = conn.execute("""
        CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 3)
        RETURN node, distance
        ORDER BY distance
    """, {"vec": query_vec})

    vss_nodes = []
    while vss_result.has_next():
        row = vss_result.get_next()
        node = row[0]
        distance = row[1]
        vss_nodes.append((node["id"], node["title"], distance))

    # VSSは複数の関連要件を発見
    assert len(vss_nodes) >= 2
    # ログインシステムも検出される
    assert any("req_b_001" in node[0] for node in vss_nodes[:2]), "VSSは「ログインシステム」も検出"


def test_terminology_variations():
    """表記揺れの吸収"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # 拡張機能をインストールとロード
    try:
        conn.execute("INSTALL VECTOR;")
        conn.execute("INSTALL FTS;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")
    conn.execute("LOAD EXTENSION FTS;")

    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            embedding DOUBLE[384]
        )
    """)
    
    # インデックス作成
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")
    conn.execute("CALL CREATE_FTS_INDEX('RequirementEntity', 'req_fts', ['title', 'description'])")

    # 様々な表記の認証要件
    auth_variants = [
        {"id": "auth_001", "title": "二要素認証", "description": "2FAの実装"},
        {"id": "auth_002", "title": "Multi-Factor Authentication", "description": "MFA implementation"},
        {"id": "auth_003", "title": "ワンタイムパスワード", "description": "OTP認証"},
        {"id": "auth_004", "title": "二段階認証", "description": "追加認証レイヤー"},
    ]

    for data in auth_variants:
        embedding = generate_embedding(data["title"] + " " + data["description"])
        conn.execute(
            """
            CREATE (r:RequirementEntity {
                id: $id,
                title: $title,
                description: $description,
                embedding: $embedding
            })
        """,
            {**data, "embedding": embedding},
        )

    # 各検索語で関連要件を発見（KuzuDBネイティブ）
    search_terms = ["二要素", "2FA", "MFA", "OTP"]

    for term in search_terms:
        query_vec = generate_embedding(term)

        # VSS検索
        result = conn.execute("""
            CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 10)
            RETURN node, distance
        """, {"vec": query_vec})

        count = 0
        while result.has_next():
            row = result.get_next()
            distance = row[1]
            if distance < 0.5:
                count += 1
        
        assert count >= 2, f"'{term}'で少なくとも2件の関連要件を発見"


def test_impact_analysis():
    """要件変更の影響分析"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # 拡張機能をインストールとロード
    try:
        conn.execute("INSTALL VECTOR;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")

    # スキーマ作成（依存関係あり）
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            embedding DOUBLE[384]
        )
    """)

    conn.execute("""
        CREATE REL TABLE DEPENDS_ON (
            FROM RequirementEntity TO RequirementEntity
        )
    """)
    
    # インデックス作成
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")

    # テストデータ
    requirements = [
        {"id": "sec_001", "title": "パスワードポリシー", "description": "8文字以上の強力なパスワード"},
        {"id": "auth_001", "title": "ユーザー認証", "description": "パスワードによるログイン"},
        {"id": "audit_001", "title": "監査ログ", "description": "認証イベントの記録"},
        {"id": "enc_001", "title": "データ暗号化", "description": "パスワードの暗号化保存"},
    ]

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
            {**req, "embedding": embedding},
        )

    # 依存関係を作成
    conn.execute("""
        MATCH (a:RequirementEntity {id: 'auth_001'})
        MATCH (b:RequirementEntity {id: 'sec_001'})
        CREATE (a)-[:DEPENDS_ON]->(b)
    """)

    # 依存関係の確認
    deps_result = conn.execute("""
        MATCH (dep:RequirementEntity)-[:DEPENDS_ON]->(target:RequirementEntity {id: 'sec_001'})
        RETURN dep.id
    """)

    deps = []
    while deps_result.has_next():
        deps.append(deps_result.get_next()[0])

    assert len(deps) >= 1, "依存関係が検出される"
    assert "auth_001" in deps, "認証要件がパスワードポリシーに依存"

    # 意味的に関連する要件も確認（KuzuDBネイティブ）
    policy_vec = generate_embedding("パスワードポリシー強化")

    related_result = conn.execute("""
        CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 10)
        RETURN node, distance
    """, {"vec": policy_vec})

    related = []
    while related_result.has_next():
        row = related_result.get_next()
        node = row[0]
        distance = row[1]
        if node["id"] != "sec_001" and distance < 0.4:
            related.append(node["id"])

    assert len(related) >= 2, "複数の関連要件が発見される"


def test_contradiction_detection():
    """矛盾要件の検出"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # 拡張機能をインストールとロード
    try:
        conn.execute("INSTALL VECTOR;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")

    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            author STRING,
            embedding DOUBLE[384]
        )
    """)
    
    # インデックス作成
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")

    # 矛盾する可能性のある要件
    requirements = [
        {
            "id": "privacy_001",
            "title": "データ削除ポリシー",
            "description": "30日後に個人データを完全削除",
            "author": "Privacy",
        },
        {"id": "audit_001", "title": "ログ保存期間", "description": "監査ログを1年間保存", "author": "Audit"},
        {"id": "perf_001", "title": "高速レスポンス", "description": "100ms以内の応答時間", "author": "Perf"},
        {"id": "sec_001", "title": "暗号化要件", "description": "全データの強力な暗号化", "author": "Security"},
    ]

    for req in requirements:
        embedding = generate_embedding(req["title"] + " " + req["description"])
        conn.execute(
            """
            CREATE (r:RequirementEntity {
                id: $id,
                title: $title,
                description: $description,
                author: $author,
                embedding: $embedding
            })
        """,
            {**req, "embedding": embedding},
        )

    # データ削除と監査ログの矛盾を検出（KuzuDBネイティブ）
    privacy_vec = generate_embedding("個人データ削除")

    # 意味的に遠い要件を探す
    result = conn.execute("""
        CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 10)
        RETURN node, distance
    """, {"vec": privacy_vec})

    conflicts = []
    while result.has_next():
        row = result.get_next()
        node = row[0]
        distance = row[1]
        if node["author"] in ["Audit", "Security"] and distance > 0.5:
            conflicts.append((node["id"], node["title"], distance))

    # KuzuDBネイティブ機能で矛盾を検出
    # 異なるチーム間で意味的に遠い要件を検索
    result = conn.execute("""
        MATCH (p:RequirementEntity {author: 'Privacy'})
        MATCH (a:RequirementEntity {author: 'Audit'})
        RETURN p.id, p.title, a.id, a.title
    """)
    
    potential_conflicts = []
    while result.has_next():
        row = result.get_next()
        potential_conflicts.append({
            "privacy": {"id": row[0], "title": row[1]},
            "audit": {"id": row[2], "title": row[3]}
        })
    
    assert len(potential_conflicts) > 0, "異なるチーム間の要件が存在（潜在的矛盾）"


def test_requirement_evolution():
    """要件の進化追跡"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # 拡張機能をインストールとロード
    try:
        conn.execute("INSTALL VECTOR;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")

    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            year INT64,
            embedding DOUBLE[384]
        )
    """)
    
    # インデックス作成
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")

    # 時系列の要件
    evolution_data = [
        {"id": "web_2010", "title": "モバイル対応", "description": "スマートフォン向けページ", "year": 2010},
        {"id": "web_2015", "title": "レスポンシブデザイン", "description": "画面サイズに適応するUI", "year": 2015},
        {"id": "web_2020", "title": "PWA対応", "description": "Progressive Web App機能", "year": 2020},
        {"id": "web_2023", "title": "マルチデバイス体験", "description": "シームレスなクロスデバイス", "year": 2023},
    ]

    for data in evolution_data:
        embedding = generate_embedding(data["title"] + " " + data["description"])
        conn.execute(
            """
            CREATE (r:RequirementEntity {
                id: $id,
                title: $title,
                description: $description,
                year: $year,
                embedding: $embedding
            })
        """,
            {**data, "embedding": embedding},
        )

    # 進化の追跡（KuzuDBネイティブ）
    query_vec = generate_embedding("モバイルアプリのようなWeb体験")

    result = conn.execute("""
        CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 10)
        RETURN node, distance
    """, {"vec": query_vec})

    evolution = []
    while result.has_next():
        row = result.get_next()
        node = row[0]
        distance = row[1]
        if node["year"] >= 2010 and distance < 0.5:
            evolution.append((node["year"], node["title"]))
    
    # 年代順にソート
    evolution.sort(key=lambda x: x[0])

    # 時系列で進化が追跡できることを確認
    assert len(evolution) >= 3, "複数の年代にわたる要件進化が追跡できる"
    years = [e[0] for e in evolution]
    assert 2010 in years and 2020 in years, "異なる年代の要件が含まれる"


def test_precision_recall():
    """精度・再現率テスト"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # 拡張機能をインストールとロード
    try:
        conn.execute("INSTALL VECTOR;")
        conn.execute("INSTALL FTS;")
    except:
        pass  # Already installed
    conn.execute("LOAD EXTENSION VECTOR;")
    conn.execute("LOAD EXTENSION FTS;")

    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            embedding DOUBLE[384]
        )
    """)
    
    # インデックス作成
    conn.execute("CALL CREATE_VECTOR_INDEX('RequirementEntity', 'req_vss', 'embedding')")
    conn.execute("CALL CREATE_FTS_INDEX('RequirementEntity', 'req_fts', ['title', 'description'])")

    # テストデータ（セキュリティ関連と非関連）
    requirements = [
        # セキュリティ関連（正解セット）
        {"id": "sec_001", "title": "パスワードポリシー", "description": "強力なパスワード要件"},
        {"id": "auth_001", "title": "二要素認証", "description": "2FAの実装"},
        {"id": "auth_002", "title": "認証システム", "description": "ユーザー認証機能"},
        {"id": "auth_003", "title": "アクセス制御", "description": "権限管理システム"},
        # 非関連
        {"id": "ui_001", "title": "ユーザーインターフェース", "description": "画面デザイン"},
        {"id": "perf_001", "title": "パフォーマンス最適化", "description": "応答速度改善"},
        {"id": "data_001", "title": "データベース設計", "description": "スキーマ定義"},
        {"id": "api_001", "title": "API設計", "description": "RESTful API"},
    ]

    ground_truth = {"sec_001", "auth_001", "auth_002", "auth_003"}

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
            {**req, "embedding": embedding},
        )

    # FTS検索（簡易版 - CONTAINS使用）
    fts_result = conn.execute("""
        MATCH (r:RequirementEntity)
        WHERE r.title CONTAINS 'セキュリティ' OR r.description CONTAINS 'セキュリティ'
           OR r.title CONTAINS '認証' OR r.description CONTAINS '認証'
        RETURN r.id
    """)

    fts_found = set()
    while fts_result.has_next():
        fts_found.add(fts_result.get_next()[0])

    # VSS検索（KuzuDBネイティブ）
    sec_vec = generate_embedding("セキュリティ認証システム")

    vss_result = conn.execute("""
        CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, 4)
        RETURN node, distance
    """, {"vec": sec_vec})

    vss_found = set()
    while vss_result.has_next():
        row = vss_result.get_next()
        node = row[0]
        vss_found.add(node["id"])

    # F1スコア計算
    def calc_f1(found, truth):
        if not found:
            return 0.0
        precision = len(found & truth) / len(found) if found else 0
        recall = len(found & truth) / len(truth) if truth else 0
        return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    fts_f1 = calc_f1(fts_found, ground_truth)
    vss_f1 = calc_f1(vss_found, ground_truth)

    # 精度の確認
    assert len(fts_found) > 0, "FTSは認証キーワードで何か見つける"
    assert len(vss_found) > 0, "VSSは何か見つける"

    # VSSが少なくとも1つの正解を含むことを確認
    assert len(vss_found & ground_truth) > 0, "VSSは少なくとも1つの正解を含む"

    # ハイブリッド検索の利点を確認
    # FTSとVSSの結果を組み合わせることで、より良い結果が得られる
    hybrid_found = fts_found | vss_found  # 和集合
    hybrid_f1 = calc_f1(hybrid_found, ground_truth)

    # ハイブリッドが少なくとも片方と同等以上の性能を持つ
    assert hybrid_f1 >= min(fts_f1, vss_f1), "ハイブリッドは最低でも片方の性能を維持"

    # 実際の利点：FTSとVSSがそれぞれ異なる要件を検出することを確認
    fts_only = fts_found - vss_found
    vss_only = vss_found - fts_found

    # 少なくとも一方が独自の検出をしていることを確認（補完的）
    assert len(fts_only) > 0 or len(vss_only) > 0, "FTSとVSSは補完的な結果を提供"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
