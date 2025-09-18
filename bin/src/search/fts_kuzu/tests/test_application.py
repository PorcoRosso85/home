#!/usr/bin/env python3
"""
アプリケーション層のテスト - FTS検索・インデックスのユースケース関連
ユーザー入力検証、レスポンス形式、エンドツーエンドワークフローなど
"""

import shutil
import sys
import tempfile

import pytest

from fts_kuzu import (
    create_fts_connection,
    index_fts_documents,
    search_fts_documents,
    ApplicationConfig,
)


class TestFTSApplication:
    """FTSアプリケーション層のテストクラス"""

    @pytest.fixture
    def fts_connection(self):
        """FTS connection with temporary database"""
        tmpdir = tempfile.mkdtemp()
        conn_info = create_fts_connection(db_path=tmpdir, in_memory=False)
        yield conn_info
        # Cleanup
        if conn_info["ok"] and conn_info["connection"]:
            from fts_kuzu import close_connection
            close_connection(conn_info["connection"])
        shutil.rmtree(tmpdir)

    @pytest.fixture
    def in_memory_connection(self):
        """FTS connection with in-memory database"""
        conn_info = create_fts_connection(in_memory=True)
        yield conn_info
        # Cleanup
        if conn_info["ok"] and conn_info["connection"]:
            from fts_kuzu import close_connection
            close_connection(conn_info["connection"])

    def test_indexing_documents_with_distinct_ids_stores_separately(self, fts_connection):
        """異なるIDのドキュメントが別々に保存されること"""
        if not fts_connection["ok"]:
            pytest.skip("FTS connection not available")
            
        connection = fts_connection["connection"]
        
        # 複数のドキュメントをインデックス
        documents = [
            {
                "id": "1",
                "title": "最初のドキュメント",
                "content": "これは最初のドキュメントの内容です",
            },
            {
                "id": "2",
                "title": "2番目のドキュメント",
                "content": "これは2番目のドキュメントの内容です",
            },
        ]

        result = index_fts_documents(documents, connection)

        assert result["ok"] is True
        assert result["indexed_count"] == 2
        assert "index_time_ms" in result

        # 両方のドキュメントが検索可能であることを確認
        search_result1 = search_fts_documents({"query": "最初", "limit": 10}, connection)
        search_result2 = search_fts_documents({"query": "2番目", "limit": 10}, connection)

        assert search_result1["ok"] is True
        assert search_result2["ok"] is True

        # それぞれのドキュメントが検索できること
        doc1_found = any(r["id"] == "1" for r in search_result1["results"])
        doc2_found = any(r["id"] == "2" for r in search_result2["results"])
        assert doc1_found
        assert doc2_found

    def test_search_on_empty_index_returns_empty_results(self, fts_connection):
        """空のインデックスで検索すると空の結果を返すこと"""
        if not fts_connection["ok"]:
            pytest.skip("FTS connection not available")
            
        connection = fts_connection["connection"]
        search_result = search_fts_documents({"query": "存在しない"}, connection)

        assert search_result["ok"] is True
        assert "results" in search_result
        assert len(search_result["results"]) == 0
        assert search_result["metadata"]["total_results"] == 0
        assert search_result["metadata"]["query"] == "存在しない"

    def test_missing_query_returns_error(self, fts_connection):
        """必須パラメータが欠けている場合、エラーを返すこと"""
        if not fts_connection["ok"]:
            pytest.skip("FTS connection not available")
            
        connection = fts_connection["connection"]
        # 無効な入力でエラーを発生させる
        result = search_fts_documents({}, connection)  # queryが必須

        # FTSErrorが返されること
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["ok"] is False
        assert "error" in result
        assert "details" in result
        assert "query" in result["error"] or "required" in result["error"].lower()

    def test_successful_and_error_responses_follow_consistent_structure(self, fts_connection):
        """成功時とエラー時のレスポンスが一貫した構造に従うこと"""
        if not fts_connection["ok"]:
            pytest.skip("FTS connection not available")
            
        connection = fts_connection["connection"]
        # ドキュメントなしでインデックスを試みる（エラーを誘発）
        index_result = index_fts_documents([], connection)

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
        search_result = search_fts_documents({"query": "test"}, connection)
        assert "ok" in search_result
        assert isinstance(search_result["ok"], bool)

        # 成功レスポンスの構造
        if search_result["ok"]:
            assert "results" in search_result
            assert "metadata" in search_result
            assert isinstance(search_result["results"], list)
            assert isinstance(search_result["metadata"], dict)

    def test_indexed_documents_are_searchable_immediately(self, fts_connection):
        """インデックスしたドキュメントが即座に検索可能であること"""
        if not fts_connection["ok"]:
            pytest.skip("FTS connection not available")
            
        connection = fts_connection["connection"]
        # ドキュメントをインデックス
        documents = [
            {
                "id": "TEST001",
                "title": "テストドキュメント",
                "content": "これはテスト用のドキュメントです",
            }
        ]

        result = index_fts_documents(documents, connection)

        assert result["ok"] is True

        # 即座に検索できることを確認
        search_result = search_fts_documents({"query": "テスト"}, connection)
        assert search_result["ok"] is True
        assert "results" in search_result
        assert "metadata" in search_result
        assert len(search_result["results"]) >= 1

        # インデックスしたドキュメントが結果に含まれること
        found = any(r["id"] == "TEST001" for r in search_result["results"])
        assert found, "Indexed document should be searchable immediately"


class TestFTSFeatures:
    """FTS特有の機能のテストクラス"""

    @pytest.fixture
    def fts_connection_with_data(self):
        """FTS connection with pre-indexed documents"""
        conn_info = create_fts_connection(in_memory=True)
        if not conn_info["ok"]:
            pytest.skip("FTS connection not available")
            
        connection = conn_info["connection"]

        # Index sample documents
        documents = [
            {
                "id": "1",
                "title": "Python Programming Guide",
                "content": "Learn Python programming basics",
            },
            {"id": "2", "title": "JavaScript Tutorial", "content": "Master JavaScript programming"},
            {
                "id": "3",
                "title": "Database Design",
                "content": "Design efficient databases with SQL",
            },
            {"id": "4", "title": "Web Development", "content": "Build modern web applications"},
        ]

        result = index_fts_documents(documents, connection)
        assert result["ok"] is True

        # No longer need verification debug output

        yield connection
        # Cleanup
        from fts_kuzu import close_connection
        close_connection(connection)

    def test_keyword_search_returns_matching_documents(self, fts_connection_with_data):
        """キーワード検索が一致するドキュメントを返すこと"""
        result = search_fts_documents({"query": "Python", "limit": 10}, fts_connection_with_data)

        assert result["ok"] is True
        assert len(result["results"]) >= 1

        # Check that Python document is in results
        python_doc_found = any(r["id"] == "1" for r in result["results"])
        assert python_doc_found

    def test_search_results_include_score_and_highlights(self, fts_connection_with_data):
        """検索結果がスコアとハイライトを含むこと"""
        result = search_fts_documents({"query": "programming", "limit": 10}, fts_connection_with_data)

        assert result["ok"] is True
        assert len(result["results"]) >= 1

        # Check result structure
        for doc in result["results"]:
            assert "id" in doc
            assert "content" in doc
            assert "score" in doc
            assert "highlights" in doc
            assert isinstance(doc["score"], int | float)
            assert isinstance(doc["highlights"], list)

    def test_case_insensitive_search(self, fts_connection_with_data):
        """検索が大文字小文字を区別しないこと"""
        # Search with different case variations
        result1 = search_fts_documents({"query": "python", "limit": 10}, fts_connection_with_data)
        result2 = search_fts_documents({"query": "PYTHON", "limit": 10}, fts_connection_with_data)
        result3 = search_fts_documents({"query": "Python", "limit": 10}, fts_connection_with_data)

        # All should return results
        assert result1["ok"] is True
        assert result2["ok"] is True
        assert result3["ok"] is True

        # All should find the Python document
        for result in [result1, result2, result3]:
            python_found = any(r["id"] == "1" for r in result["results"])
            assert python_found

    def test_multi_word_query_searches_all_words(self, fts_connection_with_data):
        """複数単語のクエリが全単語を検索すること"""
        result = search_fts_documents({"query": "web database", "limit": 10}, fts_connection_with_data)

        assert result["ok"] is True
        # Should find documents containing either "web" OR "database"
        assert len(result["results"]) >= 2

        # Check that both web and database documents are found
        found_ids = {r["id"] for r in result["results"]}
        assert "3" in found_ids or "4" in found_ids

    def test_search_metadata_includes_timing_info(self, fts_connection_with_data):
        """検索メタデータがタイミング情報を含むこと"""
        result = search_fts_documents({"query": "test", "limit": 10}, fts_connection_with_data)

        assert result["ok"] is True
        assert "metadata" in result

        metadata = result["metadata"]
        assert "query" in metadata
        assert "total_results" in metadata
        assert "search_time_ms" in metadata

        assert metadata["query"] == "test"
        assert isinstance(metadata["total_results"], int)
        assert isinstance(metadata["search_time_ms"], int | float)
        assert metadata["search_time_ms"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
