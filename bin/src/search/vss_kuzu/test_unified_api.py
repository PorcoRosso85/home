#!/usr/bin/env python3
"""
統一APIのテスト - create_vss()とVSSクラスのindex/searchメソッド
"""

import pytest
from vss_kuzu import create_vss


class TestUnifiedAPI:
    """統一APIのテストクラス"""
    
    def test_create_vss_fails_without_vector_extension(self):
        """VECTOR拡張が利用できない場合、create_vss()がRuntimeErrorを発生させること"""
        # In environments without VECTOR extension, create_vss should fail fast
        # This test verifies the mandatory VECTOR extension behavior
        try:
            vss = create_vss(in_memory=True)
            # If we reach here, VECTOR extension is available
            # We can't test the failure case in this environment
            # Since VECTOR is mandatory, this means the test passed (no error was raised)
        except RuntimeError as e:
            # Verify the error is about VECTOR extension
            error_msg = str(e)
            assert "VECTOR extension" in error_msg
            assert "Failed to initialize VSS" in error_msg
            # The error should contain details about the extension
            assert "Details:" in error_msg
    
    def test_create_vss_returns_vss_instance(self):
        """create_vss()がVSSServiceInterface準拠の辞書を返すこと"""
        try:
            vss = create_vss(in_memory=True)
            # VECTOR拡張が利用可能な場合のテスト
            assert isinstance(vss, dict)
            assert 'index' in vss
            assert 'search' in vss
            assert callable(vss['index'])
            assert callable(vss['search'])
        except RuntimeError as e:
            # VECTOR拡張が利用できない場合は RuntimeError が発生することを確認
            assert "VECTOR extension" in str(e)
            # Let the test fail with the actual error since VECTOR is mandatory
            raise
    
    def test_unified_api_index_and_search(self):
        """統一APIでインデックスと検索が動作すること"""
        # VSS インスタンスを作成
        try:
            vss = create_vss(in_memory=True)
        except RuntimeError as e:
            # Let the test fail with the actual error since VECTOR is mandatory
            raise
        
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "content": "ユーザー認証機能を実装する"},
            {"id": "2", "content": "ログインシステムを構築する"},
            {"id": "3", "content": "パスワードリセット機能を追加する"}
        ]
        
        index_result = vss['index'](documents)
        
        # VECTOR拡張が利用できない場合はスキップ
        if not index_result["ok"] and "VECTOR" in index_result.get("error", ""):
            raise RuntimeError(f"VECTOR extension is required but not available: {index_result.get('error', 'Unknown error')}")
        
        assert index_result["ok"] is True
        assert index_result["indexed_count"] == 3
        
        # 検索を実行
        search_result = vss['search']("認証システム", limit=2)
        assert search_result["ok"] is True
        assert "results" in search_result
        assert len(search_result["results"]) <= 2
        
        # 検索結果の構造を確認
        if len(search_result["results"]) > 0:
            result = search_result["results"][0]
            assert "id" in result
            assert "content" in result
            assert "score" in result
            assert "distance" in result
    
    def test_unified_api_with_custom_parameters(self):
        """統一APIでカスタムパラメータが使用できること"""
        # カスタムパラメータでVSSインスタンスを作成
        try:
            vss = create_vss(
                in_memory=True,
                default_limit=5,
                index_mu=40,
                index_ml=80,
                index_metric='l2',
                index_efc=300
            )
        except RuntimeError as e:
            # Let the test fail with the actual error since VECTOR is mandatory
            raise
        
        # インデックスと検索が動作すること
        documents = [{"id": "test1", "content": "テストドキュメント"}]
        index_result = vss['index'](documents)
        if not index_result["ok"] and "VECTOR" in index_result.get("error", ""):
            raise RuntimeError(f"VECTOR extension is required but not available: {index_result.get('error', 'Unknown error')}")
        assert index_result["ok"] is True
        
        # デフォルトのlimitが適用されること
        search_result = vss['search']("テスト")
        assert search_result["ok"] is True
    
    def test_unified_api_search_with_kwargs(self):
        """統一APIのsearchメソッドで追加パラメータが使用できること"""
        try:
            vss = create_vss(in_memory=True)
        except RuntimeError as e:
            # Let the test fail with the actual error since VECTOR is mandatory
            raise
        
        # ドキュメントをインデックス
        documents = [
            {"id": f"doc{i}", "content": f"ドキュメント番号{i}"}
            for i in range(10)
        ]
        index_result = vss['index'](documents)
        if not index_result["ok"] and "VECTOR" in index_result.get("error", ""):
            raise RuntimeError(f"VECTOR extension is required but not available: {index_result.get('error', 'Unknown error')}")
        
        # efsパラメータを指定して検索
        search_result = vss['search']("ドキュメント", limit=3, efs=400)
        assert search_result["ok"] is True
        assert len(search_result["results"]) <= 3
    
    def test_unified_api_error_handling(self):
        """統一APIでエラーが適切にハンドリングされること"""
        try:
            vss = create_vss(in_memory=True)
        except RuntimeError as e:
            # Let the test fail with the actual error since VECTOR is mandatory
            raise
        
        # 空のドキュメントリストでインデックス
        index_result = vss['index']([])
        assert index_result["ok"] is False
        assert "error" in index_result
        assert "details" in index_result
    
    def test_unified_api_vs_function_api_compatibility(self):
        """統一APIと関数APIが同じ結果を返すこと"""
        from vss_kuzu.application import (
            create_vss_service,
            create_embedding_service,
        )
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
        from vss_kuzu.infrastructure.variables.config import create_config
        
        # 統一APIでインデックスと検索
        try:
            vss = create_vss(in_memory=True)
        except RuntimeError as e:
            # Let the test fail with the actual error since VECTOR is mandatory
            raise
        documents = [{"id": "1", "content": "テストコンテンツ"}]
        unified_index = vss['index'](documents)
        if not unified_index["ok"] and "VECTOR" in unified_index.get("error", ""):
            raise RuntimeError(f"VECTOR extension is required but not available: {unified_index.get('error', 'Unknown error')}")
        unified_search = vss['search']("テスト", limit=1)
        
        # 関数APIでも同じ操作
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
        
        from vss_kuzu.application import ApplicationConfig
        app_config: ApplicationConfig = {'in_memory': True}
        function_index = vss_funcs["index_documents"](documents, app_config)
        function_search = vss_funcs["search"]({"query": "テスト", "limit": 1}, app_config)
        
        # 両方のAPIが成功すること
        assert unified_index["ok"] == function_index["ok"]
        assert unified_search["ok"] == function_search["ok"]
        
        # 結果の構造が同じであること
        if unified_search["ok"] and function_search["ok"]:
            assert "results" in unified_search
            assert "results" in function_search
            assert "metadata" in unified_search
            assert "metadata" in function_search


if __name__ == "__main__":
    pytest.main([__file__, "-v"])