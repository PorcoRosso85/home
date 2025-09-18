#!/usr/bin/env python3
"""
SearchAdapter互換機能のテスト【重要】

requirement/graphから移行されたテスト
requirement/graphのSearchAdapterが依存するFTS機能の動作確認
"""

import tempfile
import pytest

from fts_kuzu import create_fts


class TestSearchAdapterCompatibility:
    """SearchAdapter互換機能のテストスイート"""

    def test_add_to_index_functionality(self):
        """add_to_indexに相当する機能が正常動作"""
        fts = create_fts(in_memory=True)

        # requirement形式（id, title, description）のドキュメント追加
        requirement_docs = [
            {
                "id": "auth_001",
                "title": "ユーザー認証機能",
                "description": "安全なログイン機能を提供"
            },
            {
                "id": "auth_002", 
                "title": "パスワードリセット機能",
                "description": "メールによるパスワード再設定機能"
            },
            {
                "id": "db_001",
                "title": "データベース設計",
                "description": "PostgreSQLを使用した効率的なスキーマ設計"
            },
            {
                "id": "api_001",
                "title": "REST API実装",
                "description": "RESTfulなAPIエンドポイントの設計と実装"
            }
        ]

        # FTSではdescriptionをcontentとして扱う
        fts_docs = []
        for req in requirement_docs:
            fts_docs.append({
                "id": req["id"],
                "title": req["title"],
                "content": req.get("description", "")  # descriptionをcontentにマッピング
            })

        # インデックスに追加
        result = fts.index(fts_docs)
        assert result["ok"] is True
        assert result["indexed_count"] == 4

        # 各ドキュメントが検索可能か確認
        # Test 1: IDで確実に特定できることを確認
        for doc in requirement_docs:
            search_result = fts.search(doc["id"])
            assert search_result["ok"] is True
            assert any(r["id"] == doc["id"] for r in search_result["results"])

        # Test 2: タイトルでの検索
        search_result = fts.search("認証機能")
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 1
        assert any(r["id"] == "auth_001" for r in search_result["results"])

        # Test 3: 説明文（description/content）での検索
        search_result = fts.search("PostgreSQL")
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 1
        assert any(r["id"] == "db_001" for r in search_result["results"])

        # Test 4: 複数の要件が同じキーワードを含む場合
        search_result = fts.search("機能")
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 2  # "認証機能"と"パスワードリセット機能"

        # Test 5: インクリメンタルな追加
        additional_req = {
            "id": "sec_001",
            "title": "セキュリティ監査",
            "description": "定期的なセキュリティ監査とログ分析"
        }
        
        fts_doc = {
            "id": additional_req["id"],
            "title": additional_req["title"],
            "content": additional_req["description"]
        }
        
        result = fts.index([fts_doc])
        assert result["ok"] is True
        assert result["indexed_count"] == 1

        # 新しく追加したドキュメントも検索可能
        search_result = fts.search("監査")
        assert search_result["ok"] is True
        assert any(r["id"] == "sec_001" for r in search_result["results"])

        fts.close()

    def test_search_hybrid_functionality(self):
        """search_hybridに相当する機能のテスト"""
        fts = create_fts(in_memory=True)

        # テストデータの準備
        test_requirements = [
            {
                "id": "req_001",
                "title": "ユーザー認証システム",
                "content": "セキュアなログイン機能の実装。二要素認証をサポート。"
            },
            {
                "id": "req_002",
                "title": "認証トークン管理",
                "content": "JWTトークンによる認証状態の管理機能"
            },
            {
                "id": "req_003",
                "title": "ユーザープロファイル管理",
                "content": "ユーザー情報の登録・更新・削除機能"
            },
            {
                "id": "req_004",
                "title": "アクセス制御システム",
                "content": "ロールベースのアクセス制御（RBAC）の実装"
            },
            {
                "id": "req_005",
                "title": "監査ログ機能",
                "content": "ユーザーの操作履歴を記録する監査ログシステム"
            }
        ]

        result = fts.index(test_requirements)
        assert result["ok"] is True

        # Test 1: キーワード検索の精度
        # 単一キーワード
        search_result = fts.search("認証", limit=5)
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 2  # req_001とreq_002が該当
        
        # 検索結果のランキングを確認
        result_ids = [r["id"] for r in search_result["results"]]
        # "認証"を含むドキュメントが上位に来ること
        assert "req_001" in result_ids[:2]
        assert "req_002" in result_ids[:2]

        # Test 2: 複数キーワードの検索（OR検索）
        search_result = fts.search("ユーザー 認証", limit=5)
        assert search_result["ok"] is True
        # "ユーザー"または"認証"を含むドキュメント
        assert len(search_result["results"]) >= 3

        # Test 3: 部分一致検索
        search_result = fts.search("ログ", limit=5)
        assert search_result["ok"] is True
        # "ログイン"と"ログ"の両方がヒット
        result_ids = [r["id"] for r in search_result["results"]]
        assert "req_001" in result_ids  # ログイン
        assert "req_005" in result_ids  # ログ機能

        # Test 4: 英語キーワード検索
        search_result = fts.search("JWT", limit=5)
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 1
        assert search_result["results"][0]["id"] == "req_002"

        # Test 5: 略語検索
        search_result = fts.search("RBAC", limit=5)
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 1
        assert search_result["results"][0]["id"] == "req_004"

        # Test 6: スコアリングの確認
        search_result = fts.search("認証", limit=10)
        assert search_result["ok"] is True
        if len(search_result["results"]) > 1:
            # スコアが降順になっていることを確認
            scores = [r.get("score", 0) for r in search_result["results"]]
            assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

        # Test 7: 検索結果の制限（limit）
        search_result = fts.search("機能", limit=3)
        assert search_result["ok"] is True
        assert len(search_result["results"]) <= 3

        # Test 8: メタデータの確認
        search_result = fts.search("認証", limit=5)
        assert search_result["ok"] is True
        assert "metadata" in search_result
        assert "query" in search_result["metadata"]
        assert search_result["metadata"]["query"] == "認証"
        assert "total_results" in search_result["metadata"]
        assert "search_time_ms" in search_result["metadata"]

        fts.close()

    def test_special_characters_in_search(self):
        """特殊文字を含む検索クエリの処理"""
        fts = create_fts(in_memory=True)

        # 特殊文字を含むドキュメント
        special_docs = [
            {
                "id": "spec_001",
                "title": "メール通知機能",
                "content": "user@example.com 形式のメールアドレス検証"
            },
            {
                "id": "spec_002",
                "title": "SQLクエリ最適化",
                "content": "SELECT * FROM users WHERE status = 'active';"
            },
            {
                "id": "spec_003",
                "title": "価格計算ロジック",
                "content": "価格 = 単価 * 数量 * (1 + 税率)"
            },
            {
                "id": "spec_004",
                "title": "正規表現バリデーション",
                "content": "パターン: ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$"
            },
            {
                "id": "spec_005",
                "title": "APIパス定義",
                "content": "/api/v1/users/{id}/profile"
            }
        ]

        result = fts.index(special_docs)
        assert result["ok"] is True

        # Test 1: SQLインジェクション対策の確認
        injection_queries = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "SELECT * FROM",
            "WHERE status =",
            "'; DELETE FROM"
        ]

        for query in injection_queries:
            # クエリが安全に処理されることを確認（エラーが発生しない）
            search_result = fts.search(query)
            assert search_result["ok"] is True
            # SQLとして実行されないことが重要

        # Test 2: 特殊文字のエスケープ処理
        special_queries = [
            "@example.com",
            "SELECT *",
            "= 単価",
            "^[A-Za-z",
            "/api/v1/"
        ]

        for query in special_queries:
            search_result = fts.search(query)
            assert search_result["ok"] is True
            # エラーなく処理されることを確認

        # Test 3: クォートの処理
        quote_queries = [
            "'active'",
            '"users"',
            "`status`"
        ]

        for query in quote_queries:
            search_result = fts.search(query)
            assert search_result["ok"] is True

        # Test 4: 演算子を含むクエリ
        operator_queries = [
            "+ 税率",
            "* 数量",
            "= 単価"
        ]

        for query in operator_queries:
            search_result = fts.search(query)
            assert search_result["ok"] is True

        # Test 5: パスセパレータ
        path_queries = [
            "/users/",
            "{id}",
            "api/v1"
        ]

        for query in path_queries:
            search_result = fts.search(query)
            assert search_result["ok"] is True

        fts.close()

    def test_requirement_graph_use_cases(self):
        """requirement/graphの実際のユースケースをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/requirement_db"
            fts = create_fts(db_path=db_path)

            # 実際の要件グラフのようなデータ
            requirements = [
                {
                    "id": "auth_base",
                    "title": "基本認証機能",
                    "content": "ユーザーのログイン・ログアウト機能"
                },
                {
                    "id": "auth_session",
                    "title": "セッション管理",
                    "content": "認証後のセッション状態管理。auth_baseに依存"
                },
                {
                    "id": "auth_2fa",
                    "title": "二要素認証",
                    "content": "SMSまたはTOTPによる二要素認証。auth_baseに依存"
                },
                {
                    "id": "user_profile",
                    "title": "ユーザープロファイル",
                    "content": "ユーザー情報の管理機能。auth_sessionに依存"
                },
                {
                    "id": "admin_panel",
                    "title": "管理者パネル",
                    "content": "システム管理者用の管理画面。auth_session, user_profileに依存"
                }
            ]

            # インデックスに追加
            result = fts.index(requirements)
            assert result["ok"] is True

            # Use Case 1: 重複検出のための類似検索
            duplicate_candidates = [
                "ユーザーログイン機能",  # auth_baseと類似
                "管理画面",  # admin_panelと類似
                "二段階認証"  # auth_2faと類似
            ]

            for candidate in duplicate_candidates:
                search_result = fts.search(candidate, limit=3)
                assert search_result["ok"] is True
                # 類似する既存要件が見つかることを確認
                assert len(search_result["results"]) > 0

            # Use Case 2: 依存関係の検索
            # "依存"というキーワードで依存関係を持つ要件を検索
            search_result = fts.search("依存", limit=10)
            assert search_result["ok"] is True
            assert len(search_result["results"]) >= 3  # 依存関係を記述した要件

            # Use Case 3: カテゴリ別検索
            categories = ["認証", "管理", "ユーザー"]
            for category in categories:
                search_result = fts.search(category, limit=10)
                assert search_result["ok"] is True
                assert len(search_result["results"]) > 0

            # Use Case 4: 増分更新シナリオ
            # 新しい要件を追加
            new_requirement = {
                "id": "auth_oauth",
                "title": "OAuth認証",
                "content": "GoogleやGitHubアカウントでのログイン。auth_baseに依存"
            }
            
            result = fts.index([new_requirement])
            assert result["ok"] is True

            # 新しい要件も含めて検索可能
            search_result = fts.search("OAuth Google", limit=5)
            assert search_result["ok"] is True
            assert any(r["id"] == "auth_oauth" for r in search_result["results"])

            # Use Case 5: パフォーマンステスト用の大量要件
            bulk_requirements = []
            for i in range(100):
                bulk_requirements.append({
                    "id": f"perf_req_{i:03d}",
                    "title": f"パフォーマンステスト要件 {i}",
                    "content": f"カテゴリ{i % 10}の要件。優先度{i % 5}"
                })

            result = fts.index(bulk_requirements)
            assert result["ok"] is True
            assert result["indexed_count"] == 100

            # カテゴリでの検索パフォーマンス
            search_result = fts.search("カテゴリ5", limit=20)
            assert search_result["ok"] is True
            assert len(search_result["results"]) == 10  # 100件中10件がカテゴリ5

            fts.close()

    def test_search_result_format_compatibility(self):
        """SearchAdapterと互換性のある検索結果フォーマット"""
        fts = create_fts(in_memory=True)

        # テストデータ
        docs = [
            {
                "id": "format_001",
                "title": "検索結果フォーマット",
                "content": "標準的な検索結果のフォーマットを確認"
            }
        ]

        result = fts.index(docs)
        assert result["ok"] is True

        # 検索実行
        search_result = fts.search("フォーマット", limit=5)
        assert search_result["ok"] is True

        # 結果フォーマットの確認
        assert "results" in search_result
        assert isinstance(search_result["results"], list)

        if len(search_result["results"]) > 0:
            first_result = search_result["results"][0]
            
            # 必須フィールドの確認
            assert "id" in first_result
            assert "content" in first_result
            assert "score" in first_result
            
            # スコアは数値
            assert isinstance(first_result["score"], (int, float))
            assert first_result["score"] >= 0
            
            # ハイライト情報（オプション）
            if "highlights" in first_result:
                assert isinstance(first_result["highlights"], list)

        # メタデータの確認
        assert "metadata" in search_result
        metadata = search_result["metadata"]
        assert "total_results" in metadata
        assert "query" in metadata
        assert metadata["query"] == "フォーマット"

        fts.close()

    def test_error_handling_compatibility(self):
        """SearchAdapterと互換性のあるエラーハンドリング"""
        fts = create_fts(in_memory=True)

        # Test 1: 空のクエリ
        result = fts.search("")
        assert result["ok"] is False
        assert "error" in result
        assert "details" in result

        # Test 2: 不正なドキュメント形式
        result = fts.index([{"no_id": "invalid"}])
        assert result["ok"] is False
        assert "error" in result
        assert "missing required 'id'" in result["error"].lower()

        # Test 3: 空のドキュメントリスト
        result = fts.index([])
        assert result["ok"] is False
        assert "error" in result
        assert "No documents provided" in result["error"]

        # エラー後も正常に動作することを確認
        valid_doc = [{"id": "valid", "content": "正常なドキュメント"}]
        result = fts.index(valid_doc)
        assert result["ok"] is True

        search_result = fts.search("正常")
        assert search_result["ok"] is True

        fts.close()