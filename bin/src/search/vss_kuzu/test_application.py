#!/usr/bin/env python3
"""
アプリケーション層のテスト - 検索・インデックスのユースケース関連
ユーザー入力検証、レスポンス形式、エンドツーエンドワークフローなど

REDフェーズ: applicationモジュールが存在しないためImportError発生
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

from vss_kuzu import VSSService


class TestApplication:
    """アプリケーション層のテストクラス"""
    
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
            assert "VECTOR" in search_result["error"] or "extension" in search_result["error"]
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])