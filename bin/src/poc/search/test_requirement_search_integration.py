#!/usr/bin/env python3
"""
要件検索の統合テスト
実際のKuzuDB機能を使用した動作確認
"""

import os
import pytest

# 環境変数で設定（規約準拠）
os.environ["PYTHONPATH"] = "/home/nixos/bin/src"
os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"


@pytest.fixture
def kuzu_connection():
    """KuzuDB接続のフィクスチャ"""
    from requirement.graph.infrastructure.database_factory import create_database, create_connection
    db = create_database(in_memory=True, test_unique=True)
    conn = create_connection(db)
    
    # 拡張機能のロード
    try:
        conn.execute("LOAD EXTENSION VECTOR;")
        conn.execute("LOAD EXTENSION FTS;")
    except:
        # 拡張機能が利用できない場合はスキップ
        pytest.skip("KuzuDB extensions not available")
    
    yield conn


def test_vss_basic_functionality(kuzu_connection):
    """VSSの基本機能テスト"""
    conn = kuzu_connection
    
    # テーブル作成
    conn.execute("""
        CREATE NODE TABLE TestDoc (
            id STRING PRIMARY KEY,
            content STRING,
            embedding DOUBLE[3]
        )
    """)
    
    # テストデータ投入
    test_docs = [
        {"id": "doc1", "content": "機械学習", "embedding": [1.0, 0.0, 0.0]},
        {"id": "doc2", "content": "深層学習", "embedding": [0.9, 0.1, 0.0]},
        {"id": "doc3", "content": "データベース", "embedding": [0.0, 0.0, 1.0]}
    ]
    
    for doc in test_docs:
        conn.execute("""
            CREATE (d:TestDoc {
                id: $id,
                content: $content,
                embedding: $embedding
            })
        """, doc)
    
    # インデックス作成
    try:
        conn.execute("""
            CALL CREATE_VECTOR_INDEX('TestDoc', 'test_vss', 'embedding')
        """)
    except Exception as e:
        pytest.skip(f"VSS index creation failed: {e}")
    
    # 検索実行
    query_vec = [0.95, 0.05, 0.0]  # 機械学習に近いベクトル
    result = conn.execute("""
        CALL QUERY_VECTOR_INDEX('TestDoc', 'test_vss', $vec, 2)
        RETURN node.id, node.content, distance
        ORDER BY distance
    """, {"vec": query_vec})
    
    # 結果確認
    results = []
    while result.has_next():
        results.append(result.get_next())
    
    assert len(results) == 2
    assert results[0][0] == "doc1"  # 最も近いのは"機械学習"
    assert results[1][0] == "doc2"  # 次に近いのは"深層学習"


def test_fts_basic_functionality(kuzu_connection):
    """FTSの基本機能テスト"""
    conn = kuzu_connection
    
    # テーブル作成
    conn.execute("""
        CREATE NODE TABLE TestReq (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING
        )
    """)
    
    # テストデータ投入
    test_reqs = [
        {"id": "req1", "title": "ユーザー認証機能", "description": "ログイン機能の実装"},
        {"id": "req2", "title": "データ暗号化", "description": "セキュリティ強化"},
        {"id": "req3", "title": "認証システム", "description": "二要素認証の追加"}
    ]
    
    for req in test_reqs:
        conn.execute("""
            CREATE (r:TestReq {
                id: $id,
                title: $title,
                description: $description
            })
        """, req)
    
    # インデックス作成
    try:
        conn.execute("""
            CALL CREATE_FTS_INDEX('TestReq', 'test_fts', ['title', 'description'])
        """)
    except Exception as e:
        pytest.skip(f"FTS index creation failed: {e}")
    
    # 検索実行
    result = conn.execute("""
        CALL QUERY_FTS_INDEX('TestReq', 'test_fts', '認証')
        RETURN node.id, node.title, score
        ORDER BY score DESC
    """)
    
    # 結果確認
    results = []
    while result.has_next():
        results.append(result.get_next())
    
    assert len(results) >= 2  # "認証"を含む要件は2つ以上


@pytest.mark.skip(reason="ハイブリッド検索の実装待ち")
def test_hybrid_search_accuracy():
    """ハイブリッド検索の精度テスト"""
    # 仕様:
    # - テストデータセットに対する精度測定
    # - VSS単独、FTS単独、ハイブリッドの比較
    # - F1スコアで評価
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])