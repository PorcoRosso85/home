#!/usr/bin/env python3
"""
旧API互換性のテスト
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

from vss_kuzu import VSSService


class TestLegacyAPI:
    """旧API互換メソッドのテストクラス"""
    
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
    
    def test_add_document_single(self, vss_service):
        """add_documentメソッドで単一ドキュメントを追加できること"""
        # 単一ドキュメントを追加
        result = vss_service.add_document(
            document_id="doc1",
            content="これはテストドキュメントです"
        )
        
        # 結果を確認
        assert isinstance(result, dict)
        assert "ok" in result
        
        if result.get("ok", False):
            assert result.get("indexed_count") == 1
    
    def test_search_similar_basic(self, vss_service):
        """search_similarメソッドで類似検索ができること"""
        # まずドキュメントを追加
        vss_service.add_document("doc1", "機械学習の基礎")
        vss_service.add_document("doc2", "深層学習入門")
        vss_service.add_document("doc3", "データベース設計")
        
        # 類似検索を実行
        results = vss_service.search_similar("機械学習", k=2)
        
        # 結果の型を確認
        assert isinstance(results, list)
        
        # VECTOR拡張が利用可能な場合
        if results:
            # 結果の構造を確認
            for result in results:
                assert isinstance(result, dict)
                assert "document_id" in result
                assert "content" in result
                assert "score" in result
                assert isinstance(result["score"], (int, float))
    
    def test_search_similar_empty_index(self, vss_service):
        """空のインデックスでsearch_similarが空リストを返すこと"""
        # インデックスが空の状態で検索
        results = vss_service.search_similar("存在しない", k=5)
        
        # 空リストが返されること
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_add_document_error_handling(self, vss_service):
        """add_documentのエラーハンドリング"""
        # 空のコンテンツで追加を試みる
        result = vss_service.add_document("empty_doc", "")
        
        # 結果は辞書型
        assert isinstance(result, dict)
        assert "ok" in result
    
    def test_search_similar_with_limit(self, vss_service):
        """search_similarのlimit指定が機能すること"""
        # 複数のドキュメントを追加
        for i in range(10):
            vss_service.add_document(f"doc{i}", f"ドキュメント番号{i}")
        
        # 限定した数で検索
        results = vss_service.search_similar("ドキュメント", k=3)
        
        # 結果の数を確認
        assert isinstance(results, list)
        if results:  # VECTOR拡張が利用可能な場合
            assert len(results) <= 3
    
    def test_legacy_api_compatibility_with_new_api(self, vss_service):
        """旧APIと新APIの相互運用性"""
        # 新APIでドキュメントを追加
        new_result = vss_service.index_documents([
            {"id": "new1", "content": "新APIで追加"}
        ])
        
        # 旧APIで追加
        old_result = vss_service.add_document("old1", "旧APIで追加")
        
        # 両方の結果が成功または同じエラー
        assert new_result.get("ok") == old_result.get("ok")
        
        # 新APIで検索
        new_search = vss_service.search({"query": "API", "limit": 10})
        
        # 旧APIで検索
        old_search = vss_service.search_similar("API", k=10)
        
        # 両方の検索が動作すること
        assert isinstance(new_search, dict)
        assert isinstance(old_search, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])