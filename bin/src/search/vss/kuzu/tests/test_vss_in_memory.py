#!/usr/bin/env python3
"""
In-memory KuzuDBを使用したVSSテスト
実際のKuzuDBインスタンスで統合テストを実行
"""

import pytest
import json
from pathlib import Path

from vss_service import VSSService


class TestVSSWithInMemoryKuzu:
    """In-memory KuzuDBを使用した統合テスト"""
    
    @pytest.fixture
    def vss_service(self):
        """In-memory VSS service"""
        # In-memoryデータベースを使用
        service = VSSService(in_memory=True)
        yield service
        # クリーンアップは不要（in-memoryなので）
    
    def test_basic_indexing_and_search(self, vss_service):
        """基本的なインデックスと検索機能のテスト"""
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "ユーザー認証機能を実装する"},
            {"id": "2", "content": "ログインシステムを構築する"},
            {"id": "3", "content": "データベースを設計する"}
        ]
        
        result = vss_service.index_documents(documents)
        assert result["status"] == "success"
        assert result["indexed_count"] == 3
        
        # 検索を実行
        search_result = vss_service.search({
            "query": "認証",
            "limit": 3
        })
        
        # 結果の検証
        assert "results" in search_result
        assert "metadata" in search_result
        assert len(search_result["results"]) > 0
        assert search_result["metadata"]["model"] == "ruri-v3-30m"
        assert search_result["metadata"]["dimension"] == 256
    
    def test_empty_search_results(self, vss_service):
        """空のデータベースでの検索テスト"""
        # 何もインデックスしていない状態で検索
        search_result = vss_service.search({
            "query": "存在しないコンテンツ"
        })
        
        assert search_result["results"] == []
        assert search_result["metadata"]["total_results"] == 0
    
    def test_threshold_filtering(self, vss_service):
        """しきい値フィルタリングのテスト"""
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "完全一致するテキスト"},
            {"id": "2", "content": "部分的に関連するテキスト"},
            {"id": "3", "content": "全く関係ないコンテンツ"}
        ]
        
        vss_service.index_documents(documents)
        
        # 高いしきい値で検索
        search_result = vss_service.search({
            "query": "完全一致するテキスト",
            "threshold": 0.8,
            "limit": 10
        })
        
        # 高スコアの結果のみが返されることを確認
        for result in search_result["results"]:
            assert result["score"] >= 0.8
    
    def test_json_schema_validation(self, vss_service):
        """JSON Schema検証のテスト"""
        # 無効な入力
        with pytest.raises(ValueError, match="Invalid input"):
            vss_service.search({
                "limit": 5  # queryが必須なのに欠けている
            })
        
        # 無効な型
        with pytest.raises(ValueError, match="Invalid input"):
            vss_service.search({
                "query": 123,  # stringであるべき
                "limit": 5
            })
        
        # 有効な入力
        try:
            vss_service.search({
                "query": "テスト",
                "limit": 5
            })
        except ValueError:
            pytest.fail("Valid input should not raise ValueError")
    
    def test_result_ordering(self, vss_service):
        """結果の順序付けテスト"""
        # 複数のドキュメントをインデックス
        documents = [
            {"id": "1", "content": "Python プログラミング"},
            {"id": "2", "content": "Python 機械学習"},
            {"id": "3", "content": "JavaScript プログラミング"},
            {"id": "4", "content": "Python データ分析"},
            {"id": "5", "content": "Java プログラミング"}
        ]
        
        vss_service.index_documents(documents)
        
        # "Python"で検索
        search_result = vss_service.search({
            "query": "Python",
            "limit": 5
        })
        
        # スコアが降順であることを確認
        scores = [r["score"] for r in search_result["results"]]
        assert scores == sorted(scores, reverse=True)
        
        # 距離が昇順であることを確認（もし含まれていれば）
        if all("distance" in r for r in search_result["results"]):
            distances = [r["distance"] for r in search_result["results"]]
            assert distances == sorted(distances)


@pytest.mark.integration
class TestVSSIntegration:
    """統合テストマーカー付きテスト"""
    
    def test_full_workflow(self):
        """完全なワークフローのテスト"""
        # In-memoryサービスの作成
        service = VSSService(in_memory=True)
        
        # 1. 初期状態の確認
        result = service.search({"query": "test"})
        assert result["results"] == []
        
        # 2. ドキュメントの追加
        docs = [
            {"id": "doc1", "content": "検索エンジンの実装"},
            {"id": "doc2", "content": "検索アルゴリズムの最適化"}
        ]
        index_result = service.index_documents(docs)
        assert index_result["indexed_count"] == 2
        
        # 3. 検索の実行
        search_result = service.search({
            "query": "検索",
            "limit": 2
        })
        
        # 4. 結果の検証
        assert len(search_result["results"]) == 2
        assert all("検索" in r["content"] for r in search_result["results"])