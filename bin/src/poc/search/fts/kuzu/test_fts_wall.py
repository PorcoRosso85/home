#!/usr/bin/env python3
"""
壁の向こうのテスト - FTS検索システム
ユーザーが実際に使う機能を検証する統合テスト
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List

# Import test setup
from test_env_setup import get_test_connection

# テストデータの準備
SAMPLE_DOCS = [
    {
        "id": "doc1",
        "title": "KuzuDB Vector Extension",
        "content": "KuzuDB provides vector search capabilities through the VECTOR extension. This allows for similarity search using embeddings."
    },
    {
        "id": "doc2", 
        "title": "Full Text Search Guide",
        "content": "This guide covers full text search implementation using KuzuDB FTS extension. Includes indexing and query examples."
    },
    {
        "id": "doc3",
        "title": "Authentication System",
        "content": "Our authentication system handles user login and authorization. Supports OAuth2 and JWT tokens."
    },
    {
        "id": "doc4",
        "title": "Graph Database Tutorial",
        "content": "Learn how to use KuzuDB for graph data modeling. Covers nodes, relationships, and Cypher queries."
    }
]


class TestFTSWall:
    """壁の向こうのテスト - ユーザーが実際に使う機能"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        from fts_facade import create_text_search
        self.conn = get_test_connection()
        self.fts_ops = create_text_search(self.conn)
    
    def test_文書を検索できる(self):
        """
        ユーザーストーリー: 開発者として、キーワードで関連文書を検索したい
        """
        # Given: 文書がシステムに登録されている
        # (setup_methodで初期化済み)
        
        # When: 「vector」で検索する
        result = self.fts_ops["search"]("vector", False)
        
        # Then: 関連文書が見つかる
        assert result["ok"] is True
        assert len(result["results"]) > 0
        
        # 検索結果にvectorが含まれている
        found_vector_doc = False
        for doc in result["results"]:
            content = doc["title"] + " " + doc["content"]
            if "vector" in content.lower():
                found_vector_doc = True
                break
        
        assert found_vector_doc, "Vector関連の文書が見つからない"
    
    def test_複数キーワードで絞り込み検索できる(self):
        """
        ユーザーストーリー: 複数のキーワードで正確な検索をしたい
        """
        # Given: 複数の文書が登録されている
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 「kuzu database」で AND検索する
        result = fts_ops["search"]("kuzu database", True)
        
        # Then: 両方のキーワードを含む文書のみ返る
        assert result["ok"] is True
        
        for doc in result["results"]:
            content = doc["title"] + " " + doc["content"]
            content_lower = content.lower()
            assert "kuzu" in content_lower and "database" in content_lower
    
    def test_重要度順に検索結果が並ぶ(self):
        """
        ユーザーストーリー: 最も関連性の高い文書を最初に見たい
        """
        # Given: 複数の関連文書が存在
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 一般的なキーワードで検索
        result = fts_ops["search"]("system", False)
        
        # Then: スコア順（重要度順）に並んでいる
        assert result["ok"] is True
        
        if len(result["results"]) > 1:
            scores = [doc["score"] for doc in result["results"]]
            assert scores == sorted(scores, reverse=True), "検索結果がスコア順に並んでいない"
    
    def test_日本語でも検索できる(self):
        """
        ユーザーストーリー: 日本語のキーワードでも検索したい
        """
        # Given: 日本語を含む文書が登録されている
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 日本語キーワードで検索
        result = fts_ops["search"]("認証", False)
        
        # Then: エラーなく結果が返る
        assert result["ok"] is True
        # 日本語検索でもシステムが正常動作することを確認
        assert isinstance(result["results"], list)
    
    def test_検索結果が空でもエラーにならない(self):
        """
        ユーザーストーリー: 見つからない場合でも適切に処理されてほしい
        """
        # Given: システムが正常に動作している
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 存在しないキーワードで検索
        result = fts_ops["search"]("nonexistent_keyword_xyz", False)
        
        # Then: エラーではなく空の結果が返る
        assert result["ok"] is True
        assert isinstance(result["results"], list)
        # 空の結果でも正常なレスポンス
    
    def test_システムが高速に応答する(self):
        """
        ユーザーストーリー: 検索は素早く結果を返してほしい
        """
        # Given: システムが初期化されている
        from fts_facade import create_text_search
        import time
        
        fts_ops = self.fts_ops
        
        # When: 検索を実行
        start_time = time.time()
        result = fts_ops["search"]("test", False)
        end_time = time.time()
        
        # Then: 1秒以内に結果が返る
        search_time = end_time - start_time
        assert search_time < 1.0, f"検索に{search_time:.3f}秒かかった（1秒以内であるべき）"
        assert result["ok"] is True
    
    def test_大文字小文字を区別せずに検索できる(self):
        """
        ユーザーストーリー: 大文字小文字を気にせず検索したい
        """
        # Given: 大文字小文字の混在する文書
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 小文字で検索
        result_lower = fts_ops["search"]("kuzu", False)
        # When: 大文字で検索
        result_upper = fts_ops["search"]("KUZU", False)
        
        # Then: 同じ結果が返る
        assert result_lower["ok"] is True
        assert result_upper["ok"] is True
        assert len(result_lower["results"]) == len(result_upper["results"])
    
    def test_無効な検索クエリを適切に処理する(self):
        """
        ユーザーストーリー: 間違った入力でもシステムが壊れないでほしい
        """
        # Given: システムが動作している
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 空のクエリで検索
        result = fts_ops["search"]("", False)
        
        # Then: 適切なエラーメッセージが返る
        assert result["ok"] is False
        assert "empty query" in result["error"].lower()
    
    def test_特殊文字を含む検索でも動作する(self):
        """
        ユーザーストーリー: 特殊文字を含む技術用語でも検索したい
        """
        # Given: システムが動作している
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 特殊文字を含む検索
        result = fts_ops["search"]("C++ OAuth2", False)
        
        # Then: エラーなく処理される
        assert result["ok"] is True
        assert isinstance(result["results"], list)


    def test_ステミングが機能する(self):
        """
        ユーザーストーリー: 単語の変化形でも同じ結果を得たい
        """
        # Given: システムが動作している
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: running, run, runsで検索
        result_running = fts_ops["search"]("running", False)
        result_run = fts_ops["search"]("run", False)
        result_runs = fts_ops["search"]("runs", False)
        
        # Then: 同じドキュメントが見つかる（ステミングによる正規化）
        assert result_running["ok"] is True
        assert result_run["ok"] is True
        assert result_runs["ok"] is True
        
        # 結果の文書IDが同じであることを確認
        if len(result_running["results"]) > 0:
            running_ids = {doc["id"] for doc in result_running["results"]}
            run_ids = {doc["id"] for doc in result_run["results"]}
            runs_ids = {doc["id"] for doc in result_runs["results"]}
            
            # 共通のドキュメントが存在することを確認
            common_docs = running_ids & run_ids & runs_ids
            assert len(common_docs) > 0, "ステミングが機能していない"
    
    def test_複数フィールドから検索できる(self):
        """
        ユーザーストーリー: タイトルと本文の両方から検索したい
        """
        # Given: タイトルと本文に異なるキーワードを持つ文書
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: タイトルにあるキーワードで検索
        title_result = fts_ops["search"]("Extension", False)
        
        # When: 本文にあるキーワードで検索
        content_result = fts_ops["search"]("embeddings", False)
        
        # Then: 両方の検索で結果が返る
        assert title_result["ok"] is True
        assert content_result["ok"] is True
        
        # タイトルのキーワードでも見つかる
        title_found = False
        for doc in title_result["results"]:
            if "Extension" in doc["title"]:
                title_found = True
                break
        assert title_found, "タイトルフィールドが検索対象になっていない"
        
        # 本文のキーワードでも見つかる
        content_found = False
        for doc in content_result["results"]:
            if "embeddings" in doc["content"]:
                content_found = True
                break
        assert content_found, "コンテンツフィールドが検索対象になっていない"


class TestFTSWallIntegration:
    """統合レベルの壁の向こうテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        from fts_facade import create_text_search
        self.conn = get_test_connection()
        self.fts_ops = create_text_search(self.conn)
    
    def test_検索システム全体が動作する(self):
        """
        ユーザーストーリー: 一連の検索タスクを通して作業できる
        """
        # Given: 検索システムが利用可能
        from fts_facade import create_text_search
        fts_ops = self.fts_ops
        
        # When: 段階的に検索を実行
        
        # 1. 広範囲検索
        broad_result = fts_ops["search"]("kuzu", False)
        assert broad_result["ok"] is True
        
        # 2. 絞り込み検索
        narrow_result = fts_ops["search"]("kuzu vector", True)
        assert narrow_result["ok"] is True
        
        # 3. フレーズ検索
        phrase_result = fts_ops["search_phrase"]('"vector search"')
        assert phrase_result["ok"] is True
        
        # Then: 全ての検索が成功し、結果の関連性が保たれる
        assert len(broad_result["results"]) >= len(narrow_result["results"])
        # 絞り込み検索の方が結果が少ない（または同じ）
        
    def test_検索システムが実用的なパフォーマンスを持つ(self):
        """
        ユーザーストーリー: 日常的な作業で使える速度で動作してほしい
        """
        # Given: 多数の検索クエリ
        from fts_facade import create_text_search
        import time
        
        fts_ops = self.fts_ops
        queries = ["kuzu", "database", "vector", "search", "graph"]
        
        # When: 連続して検索を実行
        start_time = time.time()
        
        for query in queries:
            result = fts_ops["search"](query, False)
            assert result["ok"] is True
        
        total_time = time.time() - start_time
        
        # Then: 平均的な検索時間が実用的
        avg_time = total_time / len(queries)
        assert avg_time < 0.5, f"平均検索時間{avg_time:.3f}秒は実用的でない"
        
        # システム全体として5秒以内
        assert total_time < 5.0, f"5つの検索に{total_time:.3f}秒は長すぎる"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])