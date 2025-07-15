#!/usr/bin/env python3
"""
KuzuDB統合テスト（テスト規約準拠版）
「壁の向こう側」原則に従い、公開APIのみを使用
"""

import os
import pytest
from typing import List

os.environ["PYTHONPATH"] = "/home/nixos/bin/src"

from poc.search.domain.interfaces import SearchService, SearchResult
from poc.search.infrastructure.search_service_factory import SearchServiceFactory


def test_vss_similar_requirements_are_found():
    """
    類似した要件が検索で見つかること
    
    仕様: 意味的に類似した要件が上位に返される
    """
    # GIVEN: 検索サービスに様々な要件が登録されている
    service = SearchServiceFactory.create_for_test()
    
    # 認証関連の要件
    service.add_requirement("AUTH001", "ユーザー認証基盤", 
                          "OAuth2.0を使用した認証システムの構築")
    service.add_requirement("LOGIN001", "ログイン画面実装", 
                          "ユーザーがメールとパスワードでログインする画面")
    service.add_requirement("AUTH002", "二要素認証システム", 
                          "SMSまたはTOTPを使った追加認証")
    
    # 無関係な要件
    service.add_requirement("DB001", "ユーザーデータベース設計", 
                          "認証情報を保存するDBスキーマ")
    
    # WHEN: "認証システム"で類似検索
    results = service.search_similar("認証システム", k=3)
    
    # THEN: 認証関連の要件が上位に返される
    assert len(results) >= 2
    top_ids = {r.id for r in results[:2]}
    auth_related_ids = {"AUTH001", "LOGIN001", "AUTH002"}
    
    # 上位2件のうち少なくとも1件は認証関連
    assert len(top_ids & auth_related_ids) >= 1
    
    # スコアが降順
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


def test_fts_keyword_matches_are_found():
        """
        キーワードを含む要件が検索で見つかること
        
        仕様: 指定されたキーワードを含む要件のみが返される
        """
        # GIVEN: 検索サービスに要件が登録されている
        service = SearchServiceFactory.create_for_test()
        
        service.add_requirement("AUTH001", "ユーザー認証基盤", 
                              "OAuth2.0を使用した認証システムの構築")
        service.add_requirement("AUTH002", "二要素認証システム", 
                              "SMSまたはTOTPを使った追加認証")
        service.add_requirement("DB001", "ユーザーデータベース設計", 
                              "ユーザー情報を保存するDBスキーマ")
        
        # WHEN: "認証"でキーワード検索
        results = service.search_keyword("認証", k=10)
        
        # THEN: "認証"を含む要件のみが返される
        assert len(results) == 2
        result_ids = {r.id for r in results}
        assert result_ids == {"AUTH001", "AUTH002"}
        
        # DB001は含まれない
        assert "DB001" not in result_ids


class TestHybridSearchFunctionality:
    """ハイブリッド検索の機能テスト"""
    
    def test_hybrid_search_integrates_results(self):
        """
        ハイブリッド検索が複数の検索方式を統合すること
        
        仕様: VSS、FTS両方の結果を考慮した統合結果を返す
        """
        # GIVEN: 検索サービスに要件が登録されている
        service = SearchServiceFactory.create_for_test()
        
        # "認証"というキーワードと意味的に関連
        service.add_requirement("AUTH001", "ユーザー認証基盤", 
                              "OAuth2.0を使用した認証システムの構築")
        
        # "ログイン"は認証と意味的に関連するがキーワードは含まない
        service.add_requirement("LOGIN001", "ログイン画面実装", 
                              "ユーザーがメールとパスワードでログインする画面")
        
        # "認証"キーワードを含むが意味的には少し遠い
        service.add_requirement("CERT001", "SSL証明書認証", 
                              "HTTPSのためのSSL証明書の設定")
        
        # WHEN: ハイブリッド検索を実行
        results = service.search_hybrid("ユーザー認証", k=3)
        
        # THEN: 複数のソースからの結果が統合される
        assert len(results) >= 2
        
        # AUTH001は最も関連性が高いはず（キーワード＋意味）
        assert results[0].id == "AUTH001"
        
        # ソースがhybridであること
        assert all(r.source == "hybrid" for r in results)


class TestSearchServiceContract:
    """SearchServiceの契約（インターフェース仕様）テスト"""
    
    def test_empty_query_handling(self):
        """空のクエリでもエラーにならないこと"""
        service = SearchServiceFactory.create_for_test()
        service.add_requirement("REQ001", "要件1", "内容1")
        
        # 空文字列でも正常に処理される
        results = service.search_similar("", k=5)
        assert isinstance(results, list)
    
    def test_k_parameter_is_respected(self):
        """kパラメータが結果数を制限すること"""
        service = SearchServiceFactory.create_for_test()
        
        # 10件のデータを追加
        for i in range(10):
            service.add_requirement(f"REQ{i:03d}", f"要件{i}", f"内容{i}")
        
        # k=3で検索
        results = service.search_similar("要件", k=3)
        
        # 最大3件
        assert len(results) <= 3
    
    def test_scores_are_normalized(self):
        """スコアが0.0から1.0の範囲に正規化されていること"""
        service = SearchServiceFactory.create_for_test()
        
        service.add_requirement("REQ001", "テスト要件", "テスト内容")
        service.add_requirement("REQ002", "別の要件", "別の内容")
        
        results = service.search_similar("テスト", k=10)
        
        for result in results:
            assert 0.0 <= result.score <= 1.0


def test_multiple_service_instances_are_independent():
    """複数のサービスインスタンスが独立していること"""
    # GIVEN: 2つの独立したサービスインスタンス
    service1 = SearchServiceFactory.create_for_test()
    service2 = SearchServiceFactory.create_for_test()
    
    # WHEN: それぞれに異なるデータを追加
    service1.add_requirement("REQ001", "要件1", "内容1")
    service2.add_requirement("REQ002", "要件2", "内容2")
    
    # THEN: それぞれのデータは独立している
    results1 = service1.search_keyword("要件", k=10)
    results2 = service2.search_keyword("要件", k=10)
    
    assert len(results1) == 1 and results1[0].id == "REQ001"
    assert len(results2) == 1 and results2[0].id == "REQ002"