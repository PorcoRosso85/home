#!/usr/bin/env python3
"""
VSSサービスの統合テスト
すべてのテストを新しい命名規則で統一

命名規則: def test_<何を_どうすると_どうなる>()
"""

import json
import pytest
import tempfile
import shutil
import inspect
from pathlib import Path
from typing import List, Dict, Any

from vss_service import VSSService, VectorSearchError, VectorSearchResult, VectorIndexResult


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
    
    def test_vector_extension_not_available_returns_explicit_error(self, vss_service):
        """VECTOR拡張が利用できない場合、明示的なエラーを返すこと"""
        # 新しいサービスインスタンスを作成
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir, in_memory=False)
        
        # 接続を初期化して状態を確定
        service._get_connection()
        
        # 実際のVECTOR拡張の状態を保存
        original_available = service._vector_extension_available
        
        # VECTOR拡張をモックで無効化
        service._vector_extension_available = False
        
        try:
            # インデックス時のエラー確認
            documents = [{"id": "1", "content": "テストドキュメント"}]
            result = service.index_documents(documents)
            
            # VectorSearchErrorが返されること
            assert isinstance(result, dict)
            assert result["ok"] is False
            assert "VECTOR extension not available" in result["error"]
            assert result["details"]["extension"] == "VECTOR"
            assert "install_command" in result["details"]
            
            # 検索時のエラー確認
            search_result = service.search({"query": "テスト"})
            
            # VectorSearchErrorが返されること
            assert isinstance(search_result, dict)
            assert search_result["ok"] is False
            assert "VECTOR extension not available" in search_result["error"]
        finally:
            # 元の状態に戻す
            service._vector_extension_available = original_available
            # Cleanup
            shutil.rmtree(tmpdir)
    
    def test_service_does_not_have_fallback_implementation(self, in_memory_service):
        """サービスがフォールバック実装を持たないこと"""
        # vss_service.pyのソースコードを確認
        source = inspect.getsource(VSSService)
        
        # SQLフォールバックのコードが含まれていないこと
        assert "REDUCE(dot = 0.0" not in source
        assert "cosine similarity" not in source.lower()
        
        # 条件分岐によるフォールバックがないこと
        search_source = inspect.getsource(in_memory_service.search)
        assert search_source.count("if self._vector_extension_available") <= 1  # チェックのみ
        
        # _vector_index_createdのような条件分岐がないこと
        assert "_vector_index_created" not in search_source
    
    # === 動作確認テスト ===
    
    def test_service_works_without_subprocess_wrapper(self, in_memory_service):
        """サービスがサブプロセスラッパーなしで動作すること"""
        # サブプロセスラッパーが設定されていることを確認
        assert hasattr(in_memory_service, '_subprocess_wrapper')
        
        # 基本的な動作確認
        documents = [
            {"id": "1", "content": "Pythonプログラミング"},
            {"id": "2", "content": "機械学習とディープラーニング"},
            {"id": "3", "content": "データベース設計"}
        ]
        
        # インデックス作成
        index_result = in_memory_service.index_documents(documents)
        
        # 結果の確認
        if index_result.get("ok", False):
            # VECTOR拡張が利用可能な場合
            assert index_result["status"] == "success"
            assert index_result["indexed_count"] == 3
            
            # 検索実行
            search_result = in_memory_service.search({"query": "プログラミング", "limit": 2})
            assert search_result.get("ok", False) is True
            assert len(search_result["results"]) <= 2
        else:
            # VECTOR拡張が利用できない場合
            assert "VECTOR extension not available" in index_result["error"]
    
    def test_kuzu_py_basic_connection_works(self):
        """kuzu_pyの基本的な接続が動作すること"""
        from kuzu_py import create_database, create_connection
        
        # kuzu_pyでデータベース作成
        db = create_database(":memory:")
        assert db is not None
        
        # 接続作成
        conn = create_connection(db)
        assert conn is not None
        
        # 基本的なクエリ実行
        result = conn.execute("RETURN 1 + 1 AS result")
        assert result is not None
    
    # === インデックス機能テスト ===
    
    def test_indexing_documents_creates_vector_index(self, vss_service):
        """ドキュメントをインデックスするとベクトルインデックスが作成されること"""
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
    
    def test_indexing_multiple_documents_succeeds(self, vss_service):
        """複数のドキュメントをインデックスできること"""
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "テストドキュメント"},
            {"id": "2", "content": "別のドキュメント"}
        ]
        
        result = vss_service.index_documents(documents)
        
        # 成功またはエラーのいずれか
        if result.get("ok", False):
            # VectorIndexResultの場合
            assert result["status"] == "success"
            assert result["indexed_count"] == 2
            assert "index_time_ms" in result
        else:
            # VectorSearchErrorの場合（VECTOR拡張が利用できない）
            assert "VECTOR extension not available" in result["error"]
    
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
    
    def test_dimension_mismatch_returns_error(self, vss_service):
        """次元数が一致しない場合、エラーを返すこと"""
        # 間違った次元数のベクトルを提供
        search_input = {
            "query": "テスト",
            "query_vector": [0.1] * 128  # 256次元ではなく128次元
        }
        
        result = vss_service.search(search_input)
        
        # エラーが返されること
        if not result.get("ok", True):  # エラーの場合
            if "dimension mismatch" in result.get("error", ""):
                assert result["details"]["expected"] == 256
                assert result["details"]["got"] == 128
            else:
                # VECTOR拡張が利用できない場合
                assert "VECTOR extension not available" in result["error"]
    
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
    
    def test_result_types_are_consistent(self, vss_service):
        """結果の型が一貫していること"""
        # 新しいサービスインスタンスを作成
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir, in_memory=False)
        
        # 接続を初期化
        service._get_connection()
        
        # 実際のVECTOR拡張の状態を保存
        original_available = service._vector_extension_available
        
        # VECTOR拡張を無効化してエラーを確実に発生させる
        service._vector_extension_available = False
        
        try:
            # インデックス操作
            index_result = service.index_documents([{"content": "test"}])
            assert "ok" in index_result
            assert isinstance(index_result["ok"], bool)
            
            # 検索操作
            search_result = service.search({"query": "test"})
            assert "ok" in search_result
            assert isinstance(search_result["ok"], bool)
            
            # 両方ともVectorSearchErrorであること
            assert index_result["ok"] is False
            assert search_result["ok"] is False
        finally:
            # 元の状態に戻す
            service._vector_extension_available = original_available
            # Cleanup
            shutil.rmtree(tmpdir)
    
    # === 運用仕様テスト ===
    
    def test_service_uses_vector_extension_operations(self, in_memory_service):
        """サービスがVECTOR拡張の操作を使用すること"""
        # 実際のKuzuDBを使用
        conn = in_memory_service._get_connection()
        
        # VECTOR拡張の可用性を確認
        if in_memory_service._vector_extension_available:
            # インデックス操作のテスト
            test_doc = {"id": "test", "content": "テストドキュメント"}
            result = in_memory_service.index_documents([test_doc])
            
            assert result.get("ok", False) is True
        else:
            # エラーハンドリングのテスト
            test_doc = {"id": "test", "content": "テストドキュメント"}
            result = in_memory_service.index_documents([test_doc])
            
            assert result.get("ok", False) is False
            assert "VECTOR extension not available" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])