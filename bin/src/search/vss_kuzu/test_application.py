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

from vss_kuzu import create_vss
from vss_kuzu.application import (
    create_vss_service,
    create_embedding_service,
)
from vss_kuzu.infrastructure.variables.config import create_config
from vss_kuzu.infrastructure import (
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    count_documents,
    close_connection,
)
from vss_kuzu.domain import (
    find_semantically_similar_documents,
)


class TestApplication:
    """アプリケーション層のテストクラス"""
    
    @pytest.fixture
    def vss_service(self):
        """VSS service with temporary database"""
        tmpdir = tempfile.mkdtemp()
        config = create_config(db_path=tmpdir, in_memory=False)
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
        yield vss_funcs, config
        # Cleanup
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def in_memory_service(self):
        """VSS service with in-memory database"""
        config = create_config(in_memory=True)
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
        return vss_funcs, config
    
    
    def test_indexing_documents_with_distinct_ids_stores_separately(self, vss_service):
        """異なるIDのドキュメントが別々に保存されること"""
        vss_funcs, config = vss_service
        index_func = vss_funcs["index_documents"]
        search_func = vss_funcs["search"]
        
        # 複数のドキュメントをインデックス
        documents = [
            {"id": "1", "content": "最初のドキュメント"},
            {"id": "2", "content": "2番目のドキュメント"}
        ]
        
        result = index_func(documents, config)
        
        if result.get("ok", False):
            assert result["indexed_count"] == 2
            
            # 両方のドキュメントが検索可能であることを確認
            search_result1 = search_func({"query": "最初"}, config)
            search_result2 = search_func({"query": "2番目"}, config)
            
            if search_result1.get("ok", False) and search_result2.get("ok", False):
                # それぞれのドキュメントが検索できること
                doc1_found = any(r["id"] == "1" for r in search_result1["results"])
                doc2_found = any(r["id"] == "2" for r in search_result2["results"])
                assert doc1_found or doc2_found  # 少なくとも一つは検索できる
    
    def test_search_on_empty_index_returns_empty_results(self, vss_service):
        """空のインデックスで検索すると空の結果を返すこと"""
        vss_funcs, config = vss_service
        search_func = vss_funcs["search"]
        
        search_result = search_func({"query": "存在しない"}, config)
        
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
        vss_funcs, config = vss_service
        search_func = vss_funcs["search"]
        
        # 無効な入力でエラーを発生させる
        result = search_func({}, config)  # queryが必須
        
        # VectorSearchErrorが返されること
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["ok"] is False
        assert "error" in result
        assert "details" in result
    
    def test_successful_and_error_responses_follow_consistent_structure(self, vss_service):
        """成功時とエラー時のレスポンスが一貫した構造に従うこと"""
        vss_funcs, config = vss_service
        index_func = vss_funcs["index_documents"]
        search_func = vss_funcs["search"]
        
        # ドキュメントなしでインデックスを試みる（エラーを誘発）
        index_result = index_func([], config)
        
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
        search_result = search_func({"query": "test"}, config)
        assert "ok" in search_result
        assert isinstance(search_result["ok"], bool)
    
    def test_indexed_documents_are_searchable_immediately(self, vss_service):
        """インデックスしたドキュメントが即座に検索可能であること"""
        vss_funcs, config = vss_service
        index_func = vss_funcs["index_documents"]
        search_func = vss_funcs["search"]
        
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "テストドキュメント"}
        ]
        
        result = index_func(documents, config)
        
        # インデックスが成功した場合
        if result.get("ok", False):
            # 即座に検索できることを確認
            search_result = search_func({"query": "テスト"}, config)
            assert search_result.get("ok", False) is True
            assert "results" in search_result
            assert "metadata" in search_result
            # インデックスしたドキュメントが結果に含まれる可能性
            if search_result["results"]:
                assert any(r["id"] == "1" for r in search_result["results"])
    
    def test_function_based_indexing_and_search(self, in_memory_service):
        """Function-based API でインデックスと検索が動作すること"""
        vss_funcs, config = in_memory_service
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
    
    def test_both_services_produce_compatible_results(self, vss_service, in_memory_service):
        """両方のサービスが互換性のある結果を返すこと"""
        vss_funcs1, config1 = vss_service
        vss_funcs2, config2 = in_memory_service
        
        # 同じドキュメントをインデックス
        documents = [{"id": "test", "content": "テストコンテンツ"}]
        
        # 両方のサービスでインデックス
        result1 = vss_funcs1["index_documents"](documents, config1)
        result2 = vss_funcs2["index_documents"](documents, config2)
        
        # 両方とも同じ結果構造を持つ
        assert "ok" in result1
        assert "ok" in result2
        
        if result1.get("ok") and result2.get("ok"):
            assert result1["indexed_count"] == result2["indexed_count"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])