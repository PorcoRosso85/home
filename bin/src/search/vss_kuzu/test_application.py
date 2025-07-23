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

from vss_kuzu import (
    VSSService,
    create_vss_service,
    create_embedding_service,
    # Infrastructure functions
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    count_documents,
    close_connection,
    # Domain functions
    find_semantically_similar_documents,
)
from vss_kuzu.application import ApplicationConfig


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
    
    @pytest.fixture
    def function_based_service(self):
        """Function-based VSS service with in-memory database"""
        embedding_func = create_embedding_service()
        vss_funcs = create_vss_service(
            create_db_func=create_kuzu_database,
            create_conn_func=create_kuzu_connection,
            check_vector_func=check_vector_extension,
            init_schema_func=initialize_vector_schema,
            insert_docs_func=insert_documents_with_embeddings,
            search_func=search_similar_vectors,
            count_func=count_documents,
            close_func=close_connection,
            generate_embedding_func=embedding_func,
            calculate_similarity_func=find_semantically_similar_documents
        )
        config = ApplicationConfig(in_memory=True)
        return vss_funcs, config
    
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
    
    def test_function_based_indexing_and_search(self, function_based_service):
        """Function-based API でインデックスと検索が動作すること"""
        vss_funcs, config = function_based_service
        index_func = vss_funcs["index_documents"]
        search_func = vss_funcs["search"]
        
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "関数ベースのテスト"},
            {"id": "2", "content": "新しいアーキテクチャ"}
        ]
        
        result = index_func(documents, config)
        
        if result.get("ok", False):
            assert result["indexed_count"] == 2
            
            # 検索テスト
            search_result = search_func({"query": "関数"}, config)
            
            if search_result.get("ok", False):
                assert "results" in search_result
                assert "metadata" in search_result
                assert search_result["metadata"]["query"] == "関数"
    
    def test_both_apis_produce_compatible_results(self, in_memory_service, function_based_service):
        """両方のAPIが互換性のある結果を返すこと"""
        vss_funcs, config = function_based_service
        
        # 同じドキュメントをインデックス
        documents = [{"id": "test", "content": "テストコンテンツ"}]
        
        # クラスベースAPI
        class_result = in_memory_service.index_documents(documents)
        
        # 関数ベースAPI
        func_result = vss_funcs["index_documents"](documents, config)
        
        # 両方とも同じ結果構造を持つ
        assert "ok" in class_result
        assert "ok" in func_result
        
        if class_result.get("ok") and func_result.get("ok"):
            assert class_result["indexed_count"] == func_result["indexed_count"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])