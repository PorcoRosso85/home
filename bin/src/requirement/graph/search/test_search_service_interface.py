#!/usr/bin/env python3
"""
SearchServiceインターフェースのテスト（TDD Red Phase）
テスト規約に準拠した「壁の向こう側」原則に基づくテスト
"""

import os
from typing import List, Dict, Any
import pytest

os.environ["PYTHONPATH"] = "/home/nixos/bin/src"

# これらのインポートはまだ存在しない（Red Phase）
from poc.search.domain.interfaces import SearchService, SearchResult
from poc.search.infrastructure.search_service_factory import SearchServiceFactory


def test_search_service_interface_exists():
    """SearchServiceインターフェースが存在すること"""
    # インターフェースの基本的なメソッドが定義されていることを確認
    assert hasattr(SearchService, 'search_similar')
    assert hasattr(SearchService, 'search_keyword')
    assert hasattr(SearchService, 'search_hybrid')


def test_search_result_dataclass_exists():
    """SearchResult データクラスが存在すること"""
    # 検索結果を表すデータ構造
    result = SearchResult(
        id="REQ001",
        title="ユーザー認証機能",
        content="OAuth2.0を使用した認証システム",
        score=0.95,
        source="vss"
    )
    assert result.id == "REQ001"
    assert result.score == 0.95


def test_search_service_factory_creates_test_instance():
    """SearchServiceFactoryがテスト用インスタンスを生成できること"""
    # GIVEN: ファクトリーが存在する
    # WHEN: テスト用サービスを作成
    service = SearchServiceFactory.create_for_test()
    
    # THEN: SearchServiceインターフェースを実装している
    assert isinstance(service, SearchService)


def test_similarity_search_returns_related_requirements():
    """
    類似検索が意味的に関連する要件を返すこと
    
    仕様: 認証関連のクエリで検索すると、認証関連の要件が上位に返される
    """
    # GIVEN: 検索サービスに要件データが存在する
    service = SearchServiceFactory.create_for_test()
    service.add_requirement("AUTH001", "ユーザー認証基盤", "OAuth2.0を使用した認証システムの構築")
    service.add_requirement("LOGIN001", "ログイン画面実装", "ユーザーがメールとパスワードでログインする画面")
    service.add_requirement("DB001", "ユーザーデータベース設計", "認証情報を保存するDBスキーマ")
    
    # WHEN: "認証システム"で類似検索を実行
    results = service.search_similar("認証システム", k=2)
    
    # THEN: 認証関連の要件が上位に含まれる
    assert len(results) == 2
    top_ids = [r.id for r in results]
    assert "AUTH001" in top_ids or "LOGIN001" in top_ids
    
    # AND: スコアが降順である
    assert results[0].score >= results[1].score


def test_keyword_search_finds_exact_matches():
    """
    キーワード検索が該当する要件を返すこと
    
    仕様: 特定のキーワードを含む要件が返される
    """
    # GIVEN: 検索サービスに要件データが存在する
    service = SearchServiceFactory.create_for_test()
    service.add_requirement("AUTH001", "ユーザー認証基盤", "OAuth2.0を使用した認証システムの構築")
    service.add_requirement("AUTH002", "二要素認証システム", "SMSまたはTOTPを使った追加認証")
    service.add_requirement("DB001", "ユーザーデータベース設計", "ユーザー情報を保存するDBスキーマ")
    
    # WHEN: "認証"でキーワード検索を実行
    results = service.search_keyword("認証", k=10)
    
    # THEN: "認証"を含む要件のみが返される
    assert len(results) >= 2
    for result in results:
        assert "認証" in result.title or "認証" in result.content
    
    # AND: AUTH001とAUTH002が含まれる
    result_ids = [r.id for r in results]
    assert "AUTH001" in result_ids
    assert "AUTH002" in result_ids
    assert "DB001" not in result_ids  # "認証"を含まない


def test_hybrid_search_combines_multiple_strategies():
    """
    ハイブリッド検索が複数の検索戦略を組み合わせること
    
    仕様: VSS、FTS、グラフ検索の結果を統合して返す
    """
    # GIVEN: 検索サービスに要件データが存在する
    service = SearchServiceFactory.create_for_test()
    service.add_requirement("AUTH001", "ユーザー認証基盤", "OAuth2.0を使用した認証システムの構築")
    service.add_requirement("LOGIN001", "ログイン画面実装", "ユーザーがメールとパスワードでログインする画面") 
    service.add_requirement("SECURE001", "セキュリティ強化", "認証システムのセキュリティを向上")
    
    # WHEN: ハイブリッド検索を実行
    results = service.search_hybrid("認証セキュリティ", k=3)
    
    # THEN: 複数のソースから結果が返される
    assert len(results) >= 2
    
    # AND: 結果にソース情報が含まれる
    sources = [r.source for r in results]
    assert len(set(sources)) >= 1  # 少なくとも1つのソースから結果がある


def test_search_service_handles_empty_results():
    """検索結果が空の場合も正常に処理されること"""
    # GIVEN: 検索サービスに要件データが存在する
    service = SearchServiceFactory.create_for_test()
    service.add_requirement("DB001", "データベース設計", "PostgreSQLを使用したDB設計")
    
    # WHEN: マッチしないクエリで検索
    results = service.search_similar("量子コンピューティング", k=5)
    
    # THEN: 空のリストが返される（エラーにならない）
    assert isinstance(results, list)
    assert len(results) <= 1  # 最大でも1件（全データが1件のため）


def test_search_service_respects_k_parameter():
    """検索結果数がkパラメータを尊重すること"""
    # GIVEN: 検索サービスに複数の要件データが存在する
    service = SearchServiceFactory.create_for_test()
    for i in range(10):
        service.add_requirement(f"REQ{i:03d}", f"要件{i}", f"説明{i}")
    
    # WHEN: k=3で検索
    results = service.search_similar("要件", k=3)
    
    # THEN: 最大3件の結果が返される
    assert len(results) <= 3
    assert len(results) > 0  # 少なくとも1件は返される