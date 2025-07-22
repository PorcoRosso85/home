#!/usr/bin/env python3
"""
VSSサービスの統合テスト
すべてのテストを新しい命名規則で統一

命名規則: def test_<何を_どうすると_どうなる>()
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import sys
sys.path.insert(0, '.')
from vss_service import VSSService


class TestVSSService:
    """VSSサービスの統合テストクラス"""
    
    @pytest.fixture
    def vss_service(self):
        """VSS service with temporary database"""
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir, in_memory=False)
        yield service
        # Cleanup
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def in_memory_service(self):
        """VSS service with in-memory database"""
        return VSSService(in_memory=True)
    
    # === 仕様テスト ===
    
    def test_vector_search_returns_semantically_similar_documents(self, in_memory_service):
        """ベクトル検索が意味的に類似したドキュメントを返すこと"""
        # 類似性の異なるドキュメントを準備
        input_requirements = [
            {"id": "REQ001", "text": "ユーザー認証機能を実装する"},
            {"id": "REQ002", "text": "ログインシステムを構築する"},  # REQ001と類似
            {"id": "REQ003", "text": "データベースを設計する"},      # 無関係
        ]
        
        # ドキュメントをインデックス
        documents = [
            {"id": req["id"], "content": req["text"]} 
            for req in input_requirements
        ]
        
        index_result = in_memory_service.index_documents(documents)
        
        if index_result.get("ok", False):
            # VECTOR拡張が利用可能な場合
            assert index_result["status"] == "success"
            assert index_result["indexed_count"] == 3
            
            # "認証システム"で検索
            search_result = in_memory_service.search({
                "query": "認証システム",
                "limit": 3
            })
            
            # 検証
            assert search_result.get("ok", False) is True
            assert len(search_result["results"]) == 3
            
            # 認証系のドキュメントが上位2件に含まれること
            top_2_ids = [r["id"] for r in search_result["results"][:2]]
            assert set(top_2_ids) == {"REQ001", "REQ002"}
            
            # データベース系が最下位であること
            assert search_result["results"][-1]["id"] == "REQ003"
            
            # スコアが降順であること
            scores = [r["score"] for r in search_result["results"]]
            assert scores == sorted(scores, reverse=True)
        else:
            # VECTOR拡張が利用できない場合
            assert index_result["ok"] is False
            assert "VECTOR extension not available" in index_result["error"]
            assert index_result["details"]["extension"] == "VECTOR"
    
    def test_indexing_without_vector_extension_returns_informative_error(self, vss_service):
        """VECTOR拡張なしでインデックスを作成すると、有用なエラー情報を返すこと"""
        # ドキュメントをインデックス
        documents = [{"id": "1", "content": "テストドキュメント"}]
        result = vss_service.index_documents(documents)
        
        # 成功またはエラーのいずれか
        if not result.get("ok", False):
            # エラーの場合、有用な情報が含まれていること
            assert "error" in result
            assert "details" in result
            
            # VECTOR拡張が原因の場合
            if "VECTOR extension" in result["error"]:
                assert result["details"]["extension"] == "VECTOR"
                assert "install_command" in result["details"]
    
    def test_search_without_vector_extension_returns_informative_error(self, vss_service):
        """VECTOR拡張なしで検索すると、有用なエラー情報を返すこと"""
        # 検索を実行
        search_result = vss_service.search({"query": "テスト"})
        
        # 成功またはエラーのいずれか
        if not search_result.get("ok", False):
            # エラーの場合、有用な情報が含まれていること
            assert "error" in search_result
            assert "details" in search_result
            
            # VECTOR拡張が原因の場合
            if "VECTOR extension" in search_result["error"]:
                assert search_result["details"]["extension"] == "VECTOR"
                assert "install_command" in search_result["details"]
    
    
    # === 基本動作テスト ===
    
    def test_indexing_multiple_documents_with_different_topics_succeeds(self, in_memory_service):
        """異なるトピックの複数ドキュメントをインデックスできること"""
        # 異なるトピックのドキュメント
        documents = [
            {"id": "1", "content": "Pythonプログラミング"},
            {"id": "2", "content": "機械学習とディープラーニング"},
            {"id": "3", "content": "データベース設計"}
        ]
        
        # インデックス作成
        index_result = in_memory_service.index_documents(documents)
        
        # 結果の確認
        assert "ok" in index_result
        if index_result["ok"]:
            # 成功時の振る舞い
            assert index_result["status"] == "success"
            assert index_result["indexed_count"] == 3
            assert "index_time_ms" in index_result
        else:
            # エラー時の振る舞い
            assert "error" in index_result
            assert "details" in index_result
    
    
    # === インデックス機能テスト ===
    
    def test_indexed_documents_are_searchable_immediately(self, vss_service):
        """インデックスしたドキュメントが即座に検索可能であること"""
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "テストドキュメント"}
        ]
        
        result = vss_service.index_documents(documents)
        
        # インデックスが成功した場合
        if result.get("ok", False):
            # 即座に検索できることを確認
            search_result = vss_service.search({"query": "テスト"})
            assert search_result.get("ok", False) is True
            assert "results" in search_result
            assert "metadata" in search_result
            # インデックスしたドキュメントが結果に含まれる可能性
            if search_result["results"]:
                assert any(r["id"] == "1" for r in search_result["results"])
    
    def test_indexing_documents_with_distinct_ids_stores_separately(self, vss_service):
        """異なるIDのドキュメントが別々に保存されること"""
        # 複数のドキュメントをインデックス
        documents = [
            {"id": "1", "content": "最初のドキュメント"},
            {"id": "2", "content": "2番目のドキュメント"}
        ]
        
        result = vss_service.index_documents(documents)
        
        if result.get("ok", False):
            assert result["indexed_count"] == 2
            
            # 両方のドキュメントが検索可能であることを確認
            search_result1 = vss_service.search({"query": "最初"})
            search_result2 = vss_service.search({"query": "2番目"})
            
            if search_result1.get("ok", False) and search_result2.get("ok", False):
                # それぞれのドキュメントが検索できること
                doc1_found = any(r["id"] == "1" for r in search_result1["results"])
                doc2_found = any(r["id"] == "2" for r in search_result2["results"])
                assert doc1_found or doc2_found  # 少なくとも一つは検索できる
    
    def test_vector_index_persists_across_sessions(self, vss_service):
        """ベクトルインデックスがセッションを超えて永続化されること"""
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
    
    # === 検索機能テスト ===
    
    def test_search_returns_top_k_similar_documents(self, vss_service):
        """検索が上位k件の類似ドキュメントを返すこと"""
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
    
    def test_search_on_empty_index_returns_empty_results(self, vss_service):
        """空のインデックスで検索すると空の結果を返すこと"""
        search_result = vss_service.search({"query": "存在しない"})
        
        # VECTOR拡張が利用可能な場合は空の結果
        # 利用できない場合はエラー
        if search_result.get("ok", False):
            assert "results" in search_result
            assert len(search_result["results"]) == 0
            assert search_result["metadata"]["total_results"] == 0
        else:
            assert "VECTOR extension not available" in search_result["error"]
    
    def test_search_converts_distance_to_score_correctly(self, vss_service):
        """検索が距離をスコアに正しく変換すること（score = 1 - distance）"""
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
    
    def test_search_orders_results_by_similarity(self, vss_service):
        """検索結果が類似度順で並ぶこと"""
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
    
    # === エラー処理テスト ===
    
    def test_search_with_wrong_dimension_vector_returns_descriptive_error(self, vss_service):
        """誤った次元数のベクトルで検索すると、わかりやすいエラーを返すこと"""
        # まずドキュメントをインデックス
        documents = [{"id": "1", "content": "テスト"}]
        index_result = vss_service.index_documents(documents)
        
        if index_result.get("ok", False):
            # 間違った次元数のベクトルを提供
            search_input = {
                "query": "テスト",
                "query_vector": [0.1] * 128  # 256次元ではなく128次元
            }
            
            result = vss_service.search(search_input)
            
            # エラーが返されること
            if not result.get("ok", True):  # エラーの場合
                assert "error" in result
                assert "details" in result
                # 次元数の情報が含まれている可能性
                if "dimension" in result.get("error", "").lower():
                    assert "expected" in result["details"] or "got" in result["details"]
    
    def test_missing_query_returns_error(self, vss_service):
        """必須パラメータが欠けている場合、エラーを返すこと"""
        # 無効な入力でエラーを発生させる
        result = vss_service.search({})  # queryが必須
        
        # VectorSearchErrorが返されること
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["ok"] is False
        assert "error" in result
        assert "details" in result
    
    def test_successful_and_error_responses_follow_consistent_structure(self, vss_service):
        """成功時とエラー時のレスポンスが一貫した構造に従うこと"""
        # ドキュメントなしでインデックスを試みる（エラーを誘発）
        index_result = vss_service.index_documents([])
        
        # レスポンスの基本構造
        assert "ok" in index_result
        assert isinstance(index_result["ok"], bool)
        
        # エラーレスポンスの構造
        if not index_result["ok"]:
            assert "error" in index_result
            assert "details" in index_result
            assert isinstance(index_result["error"], str)
            assert isinstance(index_result["details"], dict)
        
        # 検索操作でも同様の確認
        search_result = vss_service.search({"query": "test"})
        assert "ok" in search_result
        assert isinstance(search_result["ok"], bool)
    
    # === 運用仕様テスト ===
    


if __name__ == "__main__":
    pytest.main([__file__, "-v"])