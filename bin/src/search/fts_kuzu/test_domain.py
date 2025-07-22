#!/usr/bin/env python3
"""
ドメイン層のテスト - ビジネスロジック関連
埋め込み生成、距離計算、類似度スコアリングなど
"""

import pytest
from typing import List, Tuple

import sys
sys.path.insert(0, '.')

from domain import (
    calculate_cosine_similarity,
    cosine_distance_to_similarity,
    sort_results_by_similarity,
    select_top_k_results,
    find_semantically_similar_documents,
    validate_embedding_dimension,
    group_documents_by_topic_similarity,
    SearchResult,
    # FTS specific types
    FTSSearchResult,
    IndexResult,
    FTSError,
    FTSErrorType
)


class TestDomain:
    """ドメインロジックのテストクラス"""
    
    def test_vector_search_returns_semantically_similar_documents(self):
        """ベクトル検索が意味的に類似したドキュメントを返すこと"""
        # 類似性の異なるドキュメントを準備（ダミー埋め込み）
        # 実際の環境では埋め込みモデルが生成するが、テストでは手動で設定
        doc_embeddings = [
            ("REQ001", "ユーザー認証機能を実装する", [0.8, 0.2, 0.1]),
            ("REQ002", "ログインシステムを構築する", [0.7, 0.3, 0.1]),  # REQ001と類似
            ("REQ003", "データベースを設計する", [0.1, 0.1, 0.9]),      # 無関係
        ]
        
        # クエリの埋め込み（認証システムに関連）
        query_embedding = [0.75, 0.25, 0.1]
        
        # 検索実行
        results = find_semantically_similar_documents(
            query_embedding,
            doc_embeddings,
            limit=3
        )
        
        # 検証
        assert len(results) == 3
        
        # 認証系のドキュメントが上位2件に含まれること
        top_2_ids = [r.id for r in results[:2]]
        assert set(top_2_ids) == {"REQ001", "REQ002"}
        
        # データベース系が最下位であること
        assert results[-1].id == "REQ003"
        
        # スコアが降順であること
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_search_converts_distance_to_score_correctly(self):
        """検索が距離をスコアに正しく変換すること（score = 1 - distance）"""
        # 様々な距離値でテスト
        test_cases = [
            (0.0, 1.0),    # 距離0 → スコア1.0
            (0.5, 0.5),    # 距離0.5 → スコア0.5
            (1.0, 0.0),    # 距離1.0 → スコア0.0
            (1.5, -0.5),   # 距離1.5 → スコア-0.5
            (2.0, -1.0),   # 距離2.0 → スコア-1.0
        ]
        
        for distance, expected_score in test_cases:
            score = cosine_distance_to_similarity(distance)
            assert abs(score - expected_score) < 0.0001
    
    def test_search_orders_results_by_similarity(self):
        """検索結果が類似度順で並ぶこと"""
        # 異なるスコアを持つ検索結果を作成
        results = [
            SearchResult("1", "機械学習の基礎", 0.6, 0.4, []),
            SearchResult("2", "機械学習とディープラーニング", 0.9, 0.1, []),
            SearchResult("3", "Python プログラミング", 0.3, 0.7, []),
            SearchResult("4", "機械学習の応用", 0.8, 0.2, []),
            SearchResult("5", "データベース設計", 0.1, 0.9, [])
        ]
        
        # ソート実行
        sorted_results = sort_results_by_similarity(results)
        
        # 検証
        assert len(sorted_results) == 5
        
        # スコアが降順であること
        scores = [r.score for r in sorted_results]
        assert scores == sorted(scores, reverse=True)
        
        # 期待される順序
        expected_order = ["2", "4", "1", "3", "5"]
        actual_order = [r.id for r in sorted_results]
        assert actual_order == expected_order
    
    def test_search_returns_top_k_similar_documents(self):
        """検索が上位k件の類似ドキュメントを返すこと"""
        # テスト用の検索結果（既にソート済み）
        results = [
            SearchResult("1", "最も類似", 0.9, 0.1, []),
            SearchResult("2", "2番目に類似", 0.7, 0.3, []),
            SearchResult("3", "3番目に類似", 0.5, 0.5, []),
            SearchResult("4", "4番目に類似", 0.3, 0.7, []),
            SearchResult("5", "最も類似度が低い", 0.1, 0.9, [])
        ]
        
        # k=2で上位2件を取得
        top_2 = select_top_k_results(results, 2)
        
        # 検証
        assert len(top_2) == 2
        assert top_2[0].id == "1"
        assert top_2[1].id == "2"
        
        # k=0の場合は空リスト
        assert select_top_k_results(results, 0) == []
        
        # k > len(results)の場合は全件
        assert len(select_top_k_results(results, 10)) == 5
    
    def test_indexing_multiple_documents_with_different_topics_succeeds(self):
        """異なるトピックの複数ドキュメントをグループ化できること"""
        # 異なるトピックのドキュメント（ダミー埋め込み）
        documents = [
            ("1", "Pythonプログラミング", [0.9, 0.1, 0.0, 0.0]),
            ("2", "機械学習とディープラーニング", [0.0, 0.9, 0.1, 0.0]),
            ("3", "データベース設計", [0.0, 0.0, 0.9, 0.1]),
            ("4", "Python開発環境", [0.8, 0.2, 0.0, 0.0]),  # 1と類似
            ("5", "深層学習フレームワーク", [0.0, 0.8, 0.2, 0.0])  # 2と類似
        ]
        
        # グループ化実行（閾値0.7）
        groups = group_documents_by_topic_similarity(documents, 0.7)
        
        # 検証
        assert len(groups) == 3  # 3つのトピックグループ
        
        # 各グループのサイズを確認
        group_sizes = sorted([len(g) for g in groups], reverse=True)
        assert group_sizes == [2, 2, 1]  # 2つの2要素グループと1つの1要素グループ
        
        # グループ内のドキュメントが類似していることを確認
        for group in groups:
            if len(group) > 1:
                # グループ内の最初のドキュメントと他のドキュメントの類似度を確認
                base_embedding = group[0][2]
                for _, _, embedding in group[1:]:
                    similarity = calculate_cosine_similarity(base_embedding, embedding)
                    assert similarity >= 0.7


class TestFTSTypes:
    """FTS型定義のテストクラス"""
    
    def test_fts_search_result_contains_required_fields(self):
        """FTSSearchResultが必要なフィールドを含むこと"""
        # FTS検索結果の作成
        result = FTSSearchResult(
            id="DOC001",
            content="Full text search is powerful",
            score=0.95,
            highlights=("Full text search", "powerful"),
            position_info=((0, 16), (20, 28))
        )
        
        # 検証
        assert result.id == "DOC001"
        assert result.content == "Full text search is powerful"
        assert result.score == 0.95
        assert result.highlights == ("Full text search", "powerful")
        assert result.position_info == ((0, 16), (20, 28))
    
    def test_index_result_tracks_indexing_status(self):
        """IndexResultがインデックス作成の状態を追跡すること"""
        # 成功したインデックス作成結果
        success_result = IndexResult(
            document_id="DOC001",
            success=True,
            tokens_count=42,
            index_time_ms=15.3,
            error=None
        )
        
        assert success_result.success is True
        assert success_result.tokens_count == 42
        assert success_result.index_time_ms == 15.3
        assert success_result.error is None
        
        # 失敗したインデックス作成結果
        failed_result = IndexResult(
            document_id="DOC002",
            success=False,
            tokens_count=0,
            index_time_ms=0.0,
            error="Document too large for indexing"
        )
        
        assert failed_result.success is False
        assert failed_result.error == "Document too large for indexing"
    
    def test_fts_error_represents_different_error_types(self):
        """FTSErrorが異なるエラータイプを表現できること"""
        # 解析エラー
        parse_error = FTSError(
            type=FTSErrorType.PARSE_ERROR,
            message="Invalid query syntax: missing closing quote",
            query="search for \"unclosed",
            position=11
        )
        
        assert parse_error.type == FTSErrorType.PARSE_ERROR
        assert "missing closing quote" in parse_error.message
        assert parse_error.query == "search for \"unclosed"
        assert parse_error.position == 11
        
        # インデックスエラー
        index_error = FTSError(
            type=FTSErrorType.INDEX_ERROR,
            message="Index corruption detected",
            query=None,
            position=None
        )
        
        assert index_error.type == FTSErrorType.INDEX_ERROR
        assert index_error.message == "Index corruption detected"
        assert index_error.query is None
    
    def test_fts_search_result_is_immutable(self):
        """FTSSearchResultが不変であること"""
        result = FTSSearchResult(
            id="DOC001",
            content="Immutable data",
            score=0.8,
            highlights=("Immutable",),
            position_info=((0, 9),)
        )
        
        # 変更を試みる（エラーになるはず）
        with pytest.raises(AttributeError):
            result.score = 0.9
        
        with pytest.raises(AttributeError):
            result.highlights.append("new highlight")


class TestFTSSearchLogic:
    """FTS検索ロジックのテストクラス"""
    
    def test_single_keyword_search_returns_matching_documents(self):
        """単一キーワード検索が一致するドキュメントを返すこと"""
        # テスト用ドキュメント
        documents = [
            ("DOC001", "Python programming tutorial", "Learn Python basics"),
            ("DOC002", "JavaScript guide", "JavaScript for beginners"),
            ("DOC003", "Python advanced topics", "Deep dive into Python"),
            ("DOC004", "Database design", "SQL and NoSQL basics")
        ]
        
        # 検索実行（実装前なので失敗する）
        from domain import search_documents_by_keyword
        results = search_documents_by_keyword(documents, "Python")
        
        # 検証
        assert len(results) == 2  # DOC001とDOC003がマッチ
        assert all("Python" in r.content for r in results)
        assert results[0].id in ["DOC001", "DOC003"]
    
    def test_multiple_keywords_or_search_returns_any_match(self):
        """複数キーワードのOR検索がいずれかに一致するドキュメントを返すこと"""
        documents = [
            ("DOC001", "Python programming", "Learn Python"),
            ("DOC002", "Java programming", "Learn Java"),
            ("DOC003", "Database design", "SQL basics"),
            ("DOC004", "Web development", "HTML and CSS")
        ]
        
        # OR検索実行（実装前なので失敗する）
        from domain import search_documents_with_or_logic
        results = search_documents_with_or_logic(documents, ["Python", "Java"])
        
        # 検証
        assert len(results) == 2  # DOC001とDOC002がマッチ
        result_ids = [r.id for r in results]
        assert set(result_ids) == {"DOC001", "DOC002"}
    
    def test_bm25_scoring_ranks_documents_by_relevance(self):
        """BM25スコアリングが関連性でドキュメントをランク付けすること"""
        documents = [
            ("DOC001", "Python Python Python", "Lots of Python"),
            ("DOC002", "Python programming", "Learn Python"),
            ("DOC003", "Advanced Python", "Python deep dive"),
            ("DOC004", "JavaScript", "No Python here")
        ]
        
        # BM25検索実行（実装前なので失敗する）
        from domain import search_with_bm25_scoring
        results = search_with_bm25_scoring(documents, "Python")
        
        # 検証
        assert len(results) >= 3
        # DOC001が最高スコア（Pythonが最も多い）
        assert results[0].id == "DOC001"
        assert results[0].score > results[1].score
        # スコアが降順
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_search_results_include_position_highlights(self):
        """検索結果が一致位置のハイライト情報を含むこと"""
        documents = [
            ("DOC001", "Introduction to Python programming", 
             "Python is a versatile programming language")
        ]
        
        # ハイライト付き検索（実装前なので失敗する）
        from domain import search_with_highlights
        results = search_with_highlights(documents, "Python")
        
        # 検証
        assert len(results) == 1
        result = results[0]
        assert hasattr(result, 'highlights')
        assert len(result.highlights) == 2  # タイトルと内容の2箇所
        assert "Python" in result.highlights[0]
        assert hasattr(result, 'position_info')
        assert len(result.position_info) == 2


class TestAdvancedFTSFeatures:
    """高度なFTS機能のテストクラス"""
    
    def test_phrase_search_finds_exact_phrases(self):
        """フレーズ検索が完全一致するフレーズを見つけること"""
        documents = [
            ("DOC001", "Machine learning algorithms", "Advanced machine learning techniques"),
            ("DOC002", "Learning machine operation", "How to operate learning machines"),
            ("DOC003", "Machine algorithms for learning", "Algorithms that help machines learn")
        ]
        
        # フレーズ検索実行（実装前なので失敗する）
        from domain import search_phrase
        results = search_phrase(documents, "machine learning")
        
        # 検証 - DOC001のみが"machine learning"を連続で含む
        assert len(results) == 1
        assert results[0].id == "DOC001"
        assert "machine learning" in results[0].content.lower()
    
    def test_conjunctive_search_returns_all_keywords_match(self):
        """AND検索がすべてのキーワードを含むドキュメントのみ返すこと"""
        documents = [
            ("DOC001", "Python web framework Django", "Build web apps with Python and Django"),
            ("DOC002", "Python programming basics", "Learn Python step by step"),
            ("DOC003", "Django web development", "Django without Python knowledge"),
            ("DOC004", "Web development with Flask", "Another Python web framework")
        ]
        
        # AND検索実行（実装前なので失敗する）
        from domain import validate_conjunctive_results
        results = validate_conjunctive_results(documents, ["Python", "web", "Django"])
        
        # 検証 - DOC001とDOC003がすべてのキーワードを含む
        assert len(results) == 2
        result_ids = [r.id for r in results]
        assert set(result_ids) == {"DOC001", "DOC003"}
        # すべてのキーワードが含まれていることを確認
        for result in results:
            content_lower = result.content.lower()
            assert all(keyword.lower() in content_lower for keyword in ["Python", "web", "Django"])
    
    def test_title_boost_prioritizes_title_matches(self):
        """タイトルブーストがタイトルの一致を優先すること"""
        documents = [
            ("DOC001", "Introduction to Programming", "Python is mentioned here briefly"),
            ("DOC002", "Python Tutorial", "A comprehensive guide to programming"),
            ("DOC003", "Advanced Topics", "Deep dive into Python programming"),
            ("DOC004", "Web Development", "Using Python for web applications")
        ]
        
        # タイトルブースト検索（実装前なので失敗する）
        from domain import boost_title_matches
        results = boost_title_matches(documents, "Python", title_boost=2.0)
        
        # 検証 - タイトルに"Python"を含むDOC002が最高スコア
        assert len(results) >= 3
        assert results[0].id == "DOC002"
        assert results[0].score > results[1].score
        
        # タイトルマッチのスコアが本文のみのマッチより高い
        title_match_score = next(r.score for r in results if r.id == "DOC002")
        body_only_scores = [r.score for r in results if r.id in ["DOC001", "DOC003", "DOC004"]]
        assert all(title_match_score > score for score in body_only_scores)
    
    def test_section_filter_searches_within_specific_sections(self):
        """セクションフィルタが特定セクション内のみを検索すること"""
        # セクション付きドキュメント
        documents = [
            ("DOC001", "Requirements Document", 
             "INTRODUCTION: System overview\nREQUIREMENTS: User authentication needed\nAPPENDIX: References"),
            ("DOC002", "Design Document",
             "OVERVIEW: Architecture\nREQUIREMENTS: Database design\nIMPLEMENTATION: Code structure"),
            ("DOC003", "Test Plan",
             "INTRODUCTION: Testing approach\nTEST CASES: Authentication tests\nRESULTS: All passed")
        ]
        
        # セクション内検索（実装前なので失敗する）
        from domain import filter_by_section
        results = filter_by_section(documents, "authentication", section="REQUIREMENTS")
        
        # 検証 - REQUIREMENTSセクションに"authentication"を含むDOC001のみ
        assert len(results) == 1
        assert results[0].id == "DOC001"
        assert "REQUIREMENTS" in results[0].content
        assert "authentication" in results[0].content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])