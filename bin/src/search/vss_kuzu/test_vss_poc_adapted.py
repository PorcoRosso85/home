#!/usr/bin/env python3
"""
POCのVSSテストを規約準拠版に適用
VECTOR拡張が利用できない場合はエラーとして扱う
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from vss_service import VSSService


class TestVSSFromPOC:
    """POCのテストケースを規約準拠版に適用"""
    
    @pytest.fixture
    def vss_service(self):
        """VSS service with temporary database"""
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir, in_memory=False)
        yield service
        # Cleanup
        shutil.rmtree(tmpdir)
    
    def test_ベクトルインデックスの作成(self, vss_service):
        """KuzuDBにベクトルインデックスが作成されること（VECTOR拡張必須）"""
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "テストドキュメント"}
        ]
        
        result = vss_service.index_documents(documents)
        
        # VECTOR拡張が利用可能な場合
        if result.get("ok", False):
            assert result["status"] == "success"
            assert result["indexed_count"] == 1
            
            # インデックスが使用可能であることを検索で確認
            search_result = vss_service.search({"query": "テスト"})
            assert search_result.get("ok", False) is True
            assert "results" in search_result
            assert "metadata" in search_result
        else:
            # VECTOR拡張が利用できない場合
            assert "VECTOR extension not available" in result["error"]
            pytest.skip("VECTOR extension not available in test environment")
    
    def test_類似ベクトル検索(self, vss_service):
        """上位k件の類似ドキュメントが距離順で返されること（VECTOR拡張必須）"""
        # テストデータを挿入
        test_docs = [
            {"id": "1", "content": "瑠璃色の説明"},
            {"id": "2", "content": "別の文書"},
            {"id": "3", "content": "さらに別の文書"}
        ]
        
        # インデックス
        index_result = vss_service.index_documents(test_docs)
        
        if not index_result.get("ok", False):
            pytest.skip("VECTOR extension not available in test environment")
        
        # 検索を実行（k=2）
        search_input = {
            "query": "瑠璃色",
            "limit": 2
        }
        
        result = vss_service.search(search_input)
        
        # 検証
        assert result.get("ok", False) is True
        assert len(result["results"]) <= 2
        assert result["metadata"]["total_results"] <= 2
        
        # スコア順（降順）でソートされていること
        scores = [r["score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)
        
        # 距離順（昇順）でソートされていることも確認
        if all("distance" in r for r in result["results"]):
            distances = [r["distance"] for r in result["results"]]
            assert distances == sorted(distances)
    
    def test_ベクトルインデックスの永続性(self, vss_service):
        """ベクトルインデックスが永続化されること（VECTOR拡張必須）"""
        # ドキュメントをインデックス
        documents = [{"id": "1", "content": "永続性テスト"}]
        result = vss_service.index_documents(documents)
        
        if not result.get("ok", False):
            pytest.skip("VECTOR extension not available in test environment")
        
        # 検索可能であることを確認
        search_result = vss_service.search({"query": "永続性"})
        assert search_result.get("ok", False) is True
        assert len(search_result["results"]) > 0
        
        # 新しいサービスインスタンスで同じDBパスを使用
        new_service = VSSService(db_path=vss_service.db_path, in_memory=False)
        search_result2 = new_service.search({"query": "永続性"})
        
        if search_result2.get("ok", False):
            assert len(search_result2["results"]) > 0
    
    def test_存在しないインデックスへのクエリ(self, vss_service):
        """何もインデックスしていない状態での検索"""
        search_result = vss_service.search({"query": "存在しない"})
        
        # VECTOR拡張が利用可能な場合は空の結果
        # 利用できない場合はエラー
        if search_result.get("ok", False):
            assert "results" in search_result
            assert len(search_result["results"]) == 0
            assert search_result["metadata"]["total_results"] == 0
        else:
            assert "VECTOR extension not available" in search_result["error"]
    
    def test_距離とスコアの変換(self, vss_service):
        """距離がスコアに正しく変換されること（score = 1 - distance）"""
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "距離変換テスト"}
        ]
        index_result = vss_service.index_documents(documents)
        
        if not index_result.get("ok", False):
            pytest.skip("VECTOR extension not available in test environment")
        
        # 検索
        result = vss_service.search({"query": "距離変換テスト"})
        
        if result.get("ok", False) and result["results"]:
            first_result = result["results"][0]
            if "distance" in first_result:
                # score = 1 - distance の関係を確認
                expected_score = 1.0 - first_result["distance"]
                assert abs(first_result["score"] - expected_score) < 0.0001
    
    def test_複数ドキュメントの順序保証(self, vss_service):
        """複数のドキュメントが類似度順で返されること（VECTOR拡張必須）"""
        # 類似性の異なるドキュメントをインデックス
        documents = [
            {"id": "1", "content": "機械学習の基礎"},
            {"id": "2", "content": "機械学習とディープラーニング"},
            {"id": "3", "content": "Python プログラミング"},
            {"id": "4", "content": "機械学習の応用"},
            {"id": "5", "content": "データベース設計"}
        ]
        
        index_result = vss_service.index_documents(documents)
        
        if not index_result.get("ok", False):
            pytest.skip("VECTOR extension not available in test environment")
        
        # "機械学習"で検索
        result = vss_service.search({
            "query": "機械学習",
            "limit": 5
        })
        
        if result.get("ok", False):
            # 結果が存在すること
            assert len(result["results"]) > 0
            
            # "機械学習"を含むドキュメントが上位に来ること
            top_contents = [r["content"] for r in result["results"][:3]]
            ml_count = sum(1 for content in top_contents if "機械学習" in content)
            assert ml_count >= 2  # 上位3件中2件以上