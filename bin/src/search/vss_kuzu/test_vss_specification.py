#!/usr/bin/env python3
"""
VSS仕様書に基づくテスト（規約準拠版）
実行可能な仕様書として、VSSの振る舞いを定義

規約に従い、VECTOR拡張が必須であることを明示
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
    
    規約準拠: VECTOR拡張が必須
    """
    # POCと同じ入力例
    input_requirements = [
        {"id": "REQ001", "text": "ユーザー認証機能を実装する"},
        {"id": "REQ002", "text": "ログインシステムを構築する"},  # REQ001と類似
        {"id": "REQ003", "text": "データベースを設計する"},      # 無関係
    ]
    
    # 期待される動作（VECTOR拡張必須）
    expected_behavior = """
    1. 各要件テキストを256次元のベクトルに変換（ruri-v3-30m使用）
    2. KuzuDBのVECTOR拡張を使用してインデックスを作成
    3. "認証システム"で検索すると：
       - REQ001（認証）とREQ002（ログイン）が上位に
       - REQ003（DB）は下位に
    4. VECTOR拡張が利用できない場合はエラーを返す
    """
    
    # 実際のKuzuDBを使用（インメモリDB）
    service = VSSService(in_memory=True)
    
    # 要件をインデックス
    documents = [
        {"id": req["id"], "content": req["text"]} 
        for req in input_requirements
    ]
    
    # インデックス作成
    index_result = service.index_documents(documents)
    
    # VECTOR拡張の有無で処理を分岐
    if index_result.get("ok", False):
        # VECTOR拡張が利用可能な場合
        assert index_result["status"] == "success"
        assert index_result["indexed_count"] == 3
        
        # "認証システム"で検索
        search_input = {
            "query": "認証システム",
            "limit": 3
        }
        
        search_result = service.search(search_input)
        
        # 仕様の検証
        assert search_result.get("ok", False) is True
        assert len(search_result["results"]) == 3
        
        # 認証系のドキュメントが上位2件に含まれること
        top_2_ids = [r["id"] for r in search_result["results"][:2]]
        assert set(top_2_ids) == {"REQ001", "REQ002"}  # 順序は問わない
        
        # データベース系が最下位であること
        assert search_result["results"][-1]["id"] == "REQ003"
        
        # スコアが降順であること
        scores = [r["score"] for r in search_result["results"]]
        assert scores == sorted(scores, reverse=True)
        
        print("✓ VSS仕様: 類似要件が上位に検索される（VECTOR拡張使用）")
    
    else:
        # VECTOR拡張が利用できない場合
        assert index_result["ok"] is False
        assert "VECTOR extension not available" in index_result["error"]
        assert index_result["details"]["extension"] == "VECTOR"
        
        print("✓ VSS仕様: VECTOR拡張が利用できない場合、明示的なエラーを返す")


def test_vss_operational_specification():
    """
    仕様2: VSSの運用仕様
    
    KuzuDBのVECTOR拡張を使用した操作（規約準拠版）
    """
    # KuzuDB操作の仕様（VECTOR拡張必須）
    expected_operations = [
        "LOAD EXTENSION VECTOR;",
        "CREATE NODE TABLE Document (id STRING, content STRING, embedding FLOAT[256], PRIMARY KEY (id))",
        "CREATE (d:Document {id: $id, content: $content, embedding: $embedding})",
        "CALL CREATE_VECTOR_INDEX('Document', 'doc_embedding_index', 'embedding')",
        "CALL QUERY_VECTOR_INDEX('Document', 'doc_embedding_index', $embedding, $k)"
    ]
    
    # 実際のKuzuDBを使用（インメモリDB）
    service = VSSService(in_memory=True)
    
    # 初期化時のスキーマ作成を確認
    conn = service._get_connection()
    
    # VECTOR拡張の可用性を確認
    if service._vector_extension_available:
        print("✓ VECTOR拡張が利用可能")
        
        # インデックス操作のテスト
        test_doc = {"id": "test", "content": "テストドキュメント"}
        result = service.index_documents([test_doc])
        
        assert result.get("ok", False) is True
        print("✓ ベクトルインデックスの作成成功")
        
    else:
        print("✓ VECTOR拡張が利用できない環境")
        
        # エラーハンドリングのテスト
        test_doc = {"id": "test", "content": "テストドキュメント"}
        result = service.index_documents([test_doc])
        
        assert result.get("ok", False) is False
        assert "VECTOR extension not available" in result["error"]
        print("✓ 適切なエラーメッセージを返す")


def test_vss_error_handling_compliance():
    """
    仕様3: エラー処理規約への準拠
    
    フォールバックを使用せず、明示的なエラーを返す
    """
    service = VSSService(in_memory=True)
    
    # フォールバック実装が存在しないことを確認
    import inspect
    source = inspect.getsource(VSSService)
    
    # SQLフォールバックのコードが含まれていないこと
    assert "REDUCE(dot = 0.0" not in source
    assert "cosine similarity" not in source.lower()
    
    # 条件分岐によるフォールバックがないこと
    search_source = inspect.getsource(service.search)
    assert search_source.count("if self._vector_extension_available") <= 1  # チェックのみ
    
    print("✓ フォールバック実装が存在しない（規約準拠）")
    
    # エラー型の確認
    # VECTOR拡張を無効化
    service._vector_extension_available = False
    
    result = service.search({"query": "test"})
    assert result.get("ok", False) is False
    assert "error" in result
    assert "details" in result
    
    print("✓ 明示的なエラー型（ErrorDict）を使用")