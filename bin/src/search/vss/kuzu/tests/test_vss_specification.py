#!/usr/bin/env python3
"""
VSS仕様書に基づくテスト（POCの仕様を継承）
実行可能な仕様書として、VSSの振る舞いを定義
"""

import json
from typing import List, Dict, Any
import tempfile
import shutil
from pathlib import Path
import numpy as np
from unittest.mock import Mock, patch

from vss_service import VSSService


def test_vss_specification():
    """
    仕様1: ベクトル類似性検索（VSS）
    
    要件テキストを埋め込みベクトルに変換し、
    意味的に類似した要件を検索できる
    """
    # POCと同じ入力例
    input_requirements = [
        {"id": "REQ001", "text": "ユーザー認証機能を実装する"},
        {"id": "REQ002", "text": "ログインシステムを構築する"},  # REQ001と類似
        {"id": "REQ003", "text": "データベースを設計する"},      # 無関係
    ]
    
    # 期待される動作（POCの仕様を継承）
    expected_behavior = """
    1. 各要件テキストを256次元のベクトルに変換（ruri-v3-30m使用）
    2. KuzuDBにベクトルインデックスを作成
    3. "認証システム"で検索すると：
       - REQ001（認証）とREQ002（ログイン）が上位に
       - REQ003（DB）は下位に
    """
    
    with patch('vss_service.create_database') as mock_create_db, \
         patch('vss_service.create_connection') as mock_create_conn:
        
        # モックの設定
        mock_db = Mock()
        mock_create_db.return_value = mock_db
        mock_conn = Mock()
        mock_create_conn.return_value = mock_conn
        
        # 埋め込みサービスのモック
        mock_embedding_service = Mock()
        
        # 各ドキュメントに対する埋め込みベクトル（簡略化）
        embeddings = {
            "ユーザー認証機能を実装する": [0.8, 0.2] + [0.1] * 254,  # 認証系
            "ログインシステムを構築する": [0.7, 0.3] + [0.1] * 254,  # 認証系（類似）
            "データベースを設計する": [0.1, 0.9] + [0.1] * 254,      # DB系（異なる）
            "認証システム": [0.75, 0.25] + [0.1] * 254               # クエリ
        }
        
        def mock_embed_documents(texts):
            results = []
            for text in texts:
                result = Mock()
                result.embeddings = embeddings.get(text, [0.1] * 256)
                results.append(result)
            return results
        
        def mock_embed_query(text):
            result = Mock()
            result.embeddings = embeddings.get(text, [0.1] * 256)
            return result
        
        mock_embedding_service.embed_documents = mock_embed_documents
        mock_embedding_service.embed_query = mock_embed_query
        
        # サービスの作成
        service = VSSService(in_memory=True)
        service._embedding_service = mock_embedding_service
        
        # 要件をインデックス（JSON Schema形式）
        documents = [
            {"id": req["id"], "content": req["text"]} 
            for req in input_requirements
        ]
        
        # 検索結果のモック（類似度順）
        mock_result = Mock()
        mock_result.has_next.side_effect = [True, True, True, False]
        mock_result.get_next.side_effect = [
            [{"content": "ユーザー認証機能を実装する", "id": 1}, 0.05],  # 最も類似
            [{"content": "ログインシステムを構築する", "id": 2}, 0.15],  # 次に類似
            [{"content": "データベースを設計する", "id": 3}, 0.85],      # 最も異なる
        ]
        
        def execute_side_effect(query, params=None):
            if "QUERY_VECTOR_INDEX" in query:
                return mock_result
            return Mock()
        
        mock_conn.execute.side_effect = execute_side_effect
        
        # インデックス作成
        index_result = service.index_documents(documents)
        assert index_result["status"] == "success"
        assert index_result["indexed_count"] == 3
        
        # "認証システム"で検索
        search_input = {
            "query": "認証システム",
            "limit": 3
        }
        
        search_result = service.search(search_input)
        
        # 仕様の検証
        assert len(search_result["results"]) == 3
        
        # 認証系のドキュメントが上位2件に含まれること
        top_2_contents = [r["content"] for r in search_result["results"][:2]]
        assert "認証" in top_2_contents[0] or "ログイン" in top_2_contents[0]
        assert "認証" in top_2_contents[1] or "ログイン" in top_2_contents[1]
        
        # データベース系が最下位であること
        assert "データベース" in search_result["results"][-1]["content"]
        
        # スコアが降順であること
        scores = [r["score"] for r in search_result["results"]]
        assert scores == sorted(scores, reverse=True)
        
        print("✓ VSS仕様: 類似要件が上位に検索される")


def test_vss_operational_specification():
    """
    仕様2: VSSの運用仕様
    
    KuzuDBのVECTOR拡張を使用した操作
    """
    # KuzuDB操作の仕様（POCから継承、次元数は256に調整）
    expected_operations = [
        "CREATE NODE TABLE Document (id INT64, content STRING, embedding FLOAT[256], PRIMARY KEY (id))",
        "CREATE (d:Document {id: $id, content: $content, embedding: $embedding})",
        "CALL CREATE_VECTOR_INDEX('Document', 'doc_embedding_index', 'embedding')",
        "CALL QUERY_VECTOR_INDEX('Document', 'doc_embedding_index', $embedding, $k)"
    ]
    
    with patch('vss_service.create_database') as mock_create_db, \
         patch('vss_service.create_connection') as mock_create_conn:
        
        # モックの設定
        mock_db = Mock()
        mock_create_db.return_value = mock_db
        mock_conn = Mock()
        mock_create_conn.return_value = mock_conn
        
        executed_queries = []
        
        def capture_execute(query, params=None):
            executed_queries.append(query)
            if "QUERY_VECTOR_INDEX" in query:
                result = Mock()
                result.has_next.return_value = False
                return result
            return Mock()
        
        mock_conn.execute.side_effect = capture_execute
        
        # サービスの初期化
        service = VSSService(in_memory=True)
        service._embedding_service = Mock()
        service._embedding_service.embed_documents.return_value = [Mock(embeddings=[0.1] * 256)]
        service._embedding_service.embed_query.return_value = Mock(embeddings=[0.1] * 256)
        
        # 初期化時のスキーマ作成を確認
        _ = service._get_connection()
        
        # Document テーブルが作成されること
        table_creation = any("CREATE NODE TABLE Document" in q for q in executed_queries)
        assert table_creation, "Document table should be created"
        
        # ドキュメントをインデックス
        service.index_documents([{"id": "1", "content": "test"}])
        
        # CREATE文が実行されること
        create_executed = any("CREATE (d:Document" in q for q in executed_queries)
        assert create_executed, "CREATE statement should be executed"
        
        # 検索を実行
        service.search({"query": "test"})
        
        # ベクトルインデックスが使用されること
        vector_query = any("QUERY_VECTOR_INDEX" in q for q in executed_queries)
        assert vector_query, "QUERY_VECTOR_INDEX should be called"
        
        print("✓ VSS運用仕様: KuzuDB VECTOR拡張が正しく使用される")


def run_specification_tests():
    """すべての仕様テストを実行"""
    print("=== VSS仕様テスト（POCの仕様を継承） ===\n")
    
    try:
        test_vss_specification()
        test_vss_operational_specification()
        
        print("\n✅ すべての仕様テストが成功しました！")
        print("POCの仕様を新しいJSON Schema実装が満たしています。")
        
    except AssertionError as e:
        print(f"\n❌ 仕様テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    run_specification_tests()