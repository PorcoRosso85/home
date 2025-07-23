#!/usr/bin/env python3
"""
ドメイン層のテスト - ビジネスロジック関連
埋め込み生成、距離計算、類似度スコアリングなど
"""

import sys

import pytest

sys.path.insert(0, ".")

from domain import (
    FTSError,
    FTSErrorType,
    # FTS specific types
    FTSSearchResult,
    IndexResult,
)


# TestDomain class removed - VSS functionality deprecated


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
            position_info=((0, 16), (20, 28)),
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
            document_id="DOC001", success=True, tokens_count=42, index_time_ms=15.3, error=None
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
            error="Document too large for indexing",
        )

        assert failed_result.success is False
        assert failed_result.error == "Document too large for indexing"

    def test_fts_error_represents_different_error_types(self):
        """FTSErrorが異なるエラータイプを表現できること"""
        # 解析エラー
        parse_error = FTSError(
            type=FTSErrorType.PARSE_ERROR,
            message="Invalid query syntax: missing closing quote",
            query='search for "unclosed',
            position=11,
        )

        assert parse_error.type == FTSErrorType.PARSE_ERROR
        assert "missing closing quote" in parse_error.message
        assert parse_error.query == 'search for "unclosed'
        assert parse_error.position == 11

        # インデックスエラー
        index_error = FTSError(
            type=FTSErrorType.INDEX_ERROR,
            message="Index corruption detected",
            query=None,
            position=None,
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
            position_info=((0, 9),),
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
            ("DOC004", "Database design", "SQL and NoSQL basics"),
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
            ("DOC004", "Web development", "HTML and CSS"),
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
            ("DOC004", "JavaScript", "No Python here"),
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
            (
                "DOC001",
                "Introduction to Python programming",
                "Python is a versatile programming language",
            )
        ]

        # ハイライト付き検索（実装前なので失敗する）
        from domain import search_with_highlights

        results = search_with_highlights(documents, "Python")

        # 検証
        assert len(results) == 1
        result = results[0]
        assert hasattr(result, "highlights")
        assert len(result.highlights) == 2  # タイトルと内容の2箇所
        assert "Python" in result.highlights[0]
        assert hasattr(result, "position_info")
        assert len(result.position_info) == 2


class TestAdvancedFTSFeatures:
    """高度なFTS機能のテストクラス"""

    def test_phrase_search_finds_exact_phrases(self):
        """フレーズ検索が完全一致するフレーズを見つけること"""
        documents = [
            ("DOC001", "Machine learning algorithms", "Advanced machine learning techniques"),
            ("DOC002", "Learning machine operation", "How to operate learning machines"),
            ("DOC003", "Machine algorithms for learning", "Algorithms that help machines learn"),
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
            ("DOC004", "Web development with Flask", "Another Python web framework"),
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
            ("DOC004", "Web Development", "Using Python for web applications"),
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
            (
                "DOC001",
                "Requirements Document",
                "INTRODUCTION: System overview\nREQUIREMENTS: User authentication needed\nAPPENDIX: References",
            ),
            (
                "DOC002",
                "Design Document",
                "OVERVIEW: Architecture\nREQUIREMENTS: Database design\nIMPLEMENTATION: Code structure",
            ),
            (
                "DOC003",
                "Test Plan",
                "INTRODUCTION: Testing approach\nTEST CASES: Authentication tests\nRESULTS: All passed",
            ),
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
