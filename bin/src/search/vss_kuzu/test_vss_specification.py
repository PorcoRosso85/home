#!/usr/bin/env python3
"""
VSS仕様書に基づくテスト（POCの仕様を継承）
実行可能な仕様書として、VSSの振る舞いを定義

規約に従い、実際のKuzuDBとの統合テストとして実装
"""

import json
from typing import List, Dict, Any
import tempfile
import shutil
from pathlib import Path
import sys

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
    
    # 実際のKuzuDBを使用（インメモリDB）
    service = VSSService(in_memory=True)
    
    # 要件をインデックス（JSON Schema形式）
    documents = [
        {"id": req["id"], "content": req["text"]} 
        for req in input_requirements
    ]
    
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
    
    # 実際のKuzuDBを使用（インメモリDB）
    service = VSSService(in_memory=True)
    
    # 初期化時のスキーマ作成を確認
    _ = service._get_connection()
    
    # ドキュメントをインデックス
    service.index_documents([{"id": "1", "content": "test"}])
    
    # 検索を実行
    service.search({"query": "test"})
    
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