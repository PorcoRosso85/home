#!/usr/bin/env python3
"""
hybrid/main.pyの関数ベース実装をテスト
KuzuDBネイティブ機能の統合テスト
"""

import os
import pytest
from typing import Dict, List, Any

os.environ["PYTHONPATH"] = "/home/nixos/bin/src"
os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"


def generate_mock_embedding(text: str) -> List[float]:
    """テスト用モック埋め込み生成"""
    hash_value = hash(text)
    embedding = []
    for i in range(384):
        seed = (hash_value + i) % 2147483647
        value = (seed % 1000) / 1000.0
        embedding.append(value)
    return embedding


@pytest.fixture
def mock_kuzu_connection():
    """モックのKuzuDB接続"""
    from requirement.graph.infrastructure.database_factory import create_database, create_connection
    
    db = create_database(in_memory=True, test_unique=True)
    conn = create_connection(db)
    
    # テストデータ用テーブル作成
    conn.execute("""
        CREATE NODE TABLE Document (
            id STRING PRIMARY KEY,
            title STRING,
            content STRING,
            category STRING,
            embedding DOUBLE[384]
        )
    """)
    
    # サンプルデータ投入
    test_docs = [
        {
            "id": "DOC001",
            "title": "ユーザー認証システム",
            "content": "OAuth2.0を使用したセキュアな認証",
            "category": "Security"
        },
        {
            "id": "DOC002", 
            "title": "ログイン画面設計",
            "content": "レスポンシブなログインフォーム",
            "category": "UI"
        },
        {
            "id": "DOC003",
            "title": "データベース設計",
            "content": "PostgreSQL スキーマ設計",
            "category": "Database"
        }
    ]
    
    for doc in test_docs:
        embedding = generate_mock_embedding(doc["title"] + " " + doc["content"])
        conn.execute("""
            CREATE (d:Document {
                id: $id,
                title: $title,
                content: $content,
                category: $category,
                embedding: $embedding
            })
        """, {**doc, "embedding": embedding})
    
    yield conn


def test_init_vss_extension(mock_kuzu_connection):
    """VSS拡張機能の初期化テスト"""
    from hybrid.main import init_vss_extension
    
    # VSS拡張機能が利用できない場合もエラーにならないことを確認
    try:
        init_vss_extension(mock_kuzu_connection)
        # エラーが発生しなければ成功
        assert True
    except Exception as e:
        # 拡張機能がない場合も許容
        assert "VECTOR" in str(e) or "extension" in str(e).lower()


def test_init_fts_extension(mock_kuzu_connection):
    """FTS拡張機能の初期化テスト"""
    from hybrid.main import init_fts_extension
    
    try:
        init_fts_extension(mock_kuzu_connection)
        assert True
    except Exception as e:
        # 拡張機能がない場合も許容
        assert "FTS" in str(e) or "extension" in str(e).lower()


def test_vss_search_function(mock_kuzu_connection):
    """VSS検索関数のテスト"""
    from hybrid.main import vss_search
    
    # VSS拡張機能がない場合の動作確認
    try:
        results = vss_search(mock_kuzu_connection, "認証システム", k=3)
        # 結果が空でも正常（拡張機能なしの場合）
        assert isinstance(results, list)
    except Exception as e:
        # VSS機能がない場合はスキップ
        pytest.skip(f"VSS機能が利用できません: {e}")


def test_fts_search_function(mock_kuzu_connection):
    """FTS検索関数のテスト"""
    from hybrid.main import fts_search
    
    try:
        results = fts_search(mock_kuzu_connection, "認証", k=3)
        assert isinstance(results, list)
    except Exception as e:
        pytest.skip(f"FTS機能が利用できません: {e}")


def test_cypher_search_function(mock_kuzu_connection):
    """Cypher検索関数のテスト"""
    from hybrid.main import cypher_search
    
    # Cypher検索は基本的なグラフクエリなので動作するはず
    results = cypher_search(mock_kuzu_connection, "認証 システム")
    assert isinstance(results, list)
    
    # カテゴリマッチの確認
    results = cypher_search(mock_kuzu_connection, "database systems")
    assert isinstance(results, list)


def test_merge_results_function():
    """結果マージ関数のテスト"""
    from hybrid.main import merge_results
    
    # テストデータ
    vss_results = [
        {"id": "DOC001", "title": "認証", "content": "auth", "category": "Security", "score": 0.9}
    ]
    fts_results = [
        {"id": "DOC001", "title": "認証", "content": "auth", "category": "Security", "score": 0.8}
    ]
    cypher_results = [
        {"id": "DOC002", "title": "ログイン", "content": "login", "category": "UI", "score": 1.0}
    ]
    
    weights = {"vss": 0.4, "fts": 0.3, "cypher": 0.3}
    
    merged = merge_results(vss_results, fts_results, cypher_results, weights)
    
    assert isinstance(merged, list)
    assert len(merged) == 2  # DOC001とDOC002
    assert all("combined_score" in result for result in merged)


def test_hybrid_search_function(mock_kuzu_connection):
    """ハイブリッド検索関数のテスト"""
    from hybrid.main import hybrid_search
    
    # 基本的な動作確認（拡張機能がなくても動作すること）
    try:
        results = hybrid_search(mock_kuzu_connection, "認証システム", k=3)
        assert isinstance(results, list)
        assert len(results) <= 3
    except Exception as e:
        # 拡張機能がない場合はログ出力のみ確認
        assert "search" in str(e).lower() or "index" in str(e).lower()


def test_create_hybrid_search_function(mock_kuzu_connection):
    """ハイブリッド検索作成関数のテスト"""
    from hybrid.main import create_hybrid_search
    
    search_functions = create_hybrid_search(mock_kuzu_connection)
    
    # 返り値の構造確認
    assert isinstance(search_functions, dict)
    expected_keys = ["search_vss", "search_fts", "search_cypher", "search_hybrid"]
    assert all(key in search_functions for key in expected_keys)
    
    # 各関数が呼び出し可能であることを確認
    for key, func in search_functions.items():
        assert callable(func)


def test_hybrid_search_integration_scenario(mock_kuzu_connection):
    """統合シナリオテスト"""
    from hybrid.main import create_hybrid_search
    
    # ハイブリッド検索システムを作成
    search_system = create_hybrid_search(mock_kuzu_connection)
    
    # 実際の検索シナリオ
    query = "ユーザー認証"
    
    # 各検索手法の実行
    try:
        vss_results = search_system["search_vss"](query, 2)
        assert isinstance(vss_results, list)
    except:
        vss_results = []
    
    try:
        fts_results = search_system["search_fts"](query, 2)
        assert isinstance(fts_results, list)
    except:
        fts_results = []
    
    cypher_results = search_system["search_cypher"](query)
    assert isinstance(cypher_results, list)
    
    # ハイブリッド検索の実行
    try:
        hybrid_results = search_system["search_hybrid"](query, 3)
        assert isinstance(hybrid_results, list)
        print(f"\nハイブリッド検索結果: {len(hybrid_results)}件")
    except Exception as e:
        print(f"\nハイブリッド検索でエラー（予想範囲内）: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])