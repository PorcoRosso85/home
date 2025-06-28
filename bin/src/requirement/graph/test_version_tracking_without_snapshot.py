"""
TDD REDフェーズテスト - スナップショット削除後の仕様
t-wadaスタイルで記述

このテストは現在の実装では失敗する（RED）
実装を修正してテストを通す（GREEN）ことで仕様を満たす
"""
import pytest
from datetime import datetime
from typing import Dict, List


class TestVersionTrackingWithoutSnapshot:
    """スナップショット機能削除後のバージョン管理仕様"""
    
    def test_要件更新時_履歴照会_各バージョンの実際の状態を返す(self, repo):
        """
        Given: 要件が3回更新される（タイトル、説明、ステータスが段階的に変化）
        When: 履歴を照会する
        Then: 各時点での実際の値が返される（現在の値ではない）
        """
        # Arrange
        req_id = "REQ-001"
        
        # Act: 3回の更新
        # 1回目: 初期作成
        v1 = repo.save({
            "id": req_id,
            "title": "ユーザー認証機能",
            "description": "IDとパスワードでログイン",
            "status": "proposed",
            "priority": "high"
        })
        
        # 2回目: タイトルとステータス変更
        v2 = repo.save({
            "id": req_id,
            "title": "OAuth2.0認証機能",  # 変更
            "description": "IDとパスワードでログイン",
            "status": "approved",  # 変更
            "priority": "high"
        })
        
        # 3回目: 説明とステータス変更
        v3 = repo.save({
            "id": req_id,
            "title": "OAuth2.0認証機能",
            "description": "Google/GitHub/Microsoftアカウントでログイン",  # 変更
            "status": "implemented",  # 変更
            "priority": "high"
        })
        
        # Assert: 履歴照会
        history = repo.get_requirement_history(req_id)
        
        assert len(history) == 3
        
        # 各バージョンの実際の状態を検証
        assert history[0]["title"] == "ユーザー認証機能"
        assert history[0]["description"] == "IDとパスワードでログイン"
        assert history[0]["status"] == "proposed"
        
        assert history[1]["title"] == "OAuth2.0認証機能"
        assert history[1]["description"] == "IDとパスワードでログイン"  # 説明は変更なし
        assert history[1]["status"] == "approved"
        
        assert history[2]["title"] == "OAuth2.0認証機能"
        assert history[2]["description"] == "Google/GitHub/Microsoftアカウントでログイン"
        assert history[2]["status"] == "implemented"
    
    def test_要件削除時_履歴照会_削除前の全バージョンにアクセス可能(self, repo):
        """
        Given: 要件が作成・更新後に削除される
        When: 削除後に履歴を照会する
        Then: 削除前の全バージョンと削除操作自体が履歴に含まれる
        """
        # Arrange
        req_id = "REQ-002"
        
        # Act
        # 作成
        v1 = repo.save({
            "id": req_id,
            "title": "廃止予定API",
            "description": "レガシーシステムとの連携API",
            "status": "implemented"
        })
        
        # 更新（廃止予定に）
        v2 = repo.save({
            "id": req_id,
            "title": "廃止予定API",
            "description": "レガシーシステムとの連携API",
            "status": "deprecated"
        })
        
        # 削除
        v3 = repo.delete(req_id)
        
        # Assert: 削除後の履歴照会
        history = repo.get_requirement_history(req_id)
        
        assert len(history) == 3
        
        # 作成時
        assert history[0]["operation"] == "CREATE"
        assert history[0]["title"] == "廃止予定API"
        assert history[0]["status"] == "implemented"
        
        # 更新時
        assert history[1]["operation"] == "UPDATE"
        assert history[1]["status"] == "deprecated"
        
        # 削除時
        assert history[2]["operation"] == "DELETE"
        assert history[2]["title"] == "廃止予定API"  # 削除時点の内容が保持される
        assert history[2]["status"] == "deprecated"
    
    def test_特定時点照会_タイムスタンプ指定_その時点の正確な状態を返す(self, repo):
        """
        Given: 要件が時系列で3回更新される
        When: 特定のタイムスタンプで状態を照会する
        Then: その時点での正確な状態が返される
        """
        # Arrange
        req_id = "REQ-003"
        
        # タイムスタンプを明示的に指定
        t1 = "2024-01-01T10:00:00Z"
        t2 = "2024-02-01T10:00:00Z"
        t3 = "2024-03-01T10:00:00Z"
        
        # Act: タイムスタンプ付きで保存
        repo.save_with_timestamp({
            "id": req_id,
            "title": "初期仕様",
            "priority": "low",
            "estimated_hours": 10
        }, timestamp=t1)
        
        repo.save_with_timestamp({
            "id": req_id,
            "title": "仕様変更版",
            "priority": "medium",
            "estimated_hours": 20
        }, timestamp=t2)
        
        repo.save_with_timestamp({
            "id": req_id,
            "title": "最終仕様",
            "priority": "high",
            "estimated_hours": 40
        }, timestamp=t3)
        
        # Assert: 各時点での状態を検証
        # 1月15日時点（v1の後）
        state_jan = repo.get_requirement_at_timestamp(req_id, "2024-01-15T00:00:00Z")
        assert state_jan["title"] == "初期仕様"
        assert state_jan["priority"] == "low"
        assert state_jan["estimated_hours"] == 10
        
        # 2月15日時点（v2の後）
        state_feb = repo.get_requirement_at_timestamp(req_id, "2024-02-15T00:00:00Z")
        assert state_feb["title"] == "仕様変更版"
        assert state_feb["priority"] == "medium"
        assert state_feb["estimated_hours"] == 20
        
        # 1月以前（データなし）
        state_before = repo.get_requirement_at_timestamp(req_id, "2023-12-31T23:59:59Z")
        assert state_before is None
    
    def test_バージョン間差分_2つのバージョンID指定_正確な変更内容を返す(self, repo):
        """
        Given: 要件が複数フィールド変更される
        When: 2つのバージョン間の差分を計算する
        Then: 変更されたフィールドと前後の値が正確に返される
        """
        # Arrange
        req_id = "REQ-004"
        
        # Act
        v1 = repo.save({
            "id": req_id,
            "title": "REST API設計",
            "description": "RESTful APIの実装",
            "method": "GET/POST/PUT/DELETE",
            "authentication": "Basic認証",
            "tags": ["API", "REST", "backend"]
        })
        
        v2 = repo.save({
            "id": req_id,
            "title": "GraphQL API設計",  # 変更
            "description": "GraphQL APIの実装",  # 変更
            "method": "Query/Mutation",  # 変更
            "authentication": "JWT認証",  # 変更
            "tags": ["API", "GraphQL", "backend"]  # 部分変更
        })
        
        # Assert: 差分計算
        diff = repo.calculate_version_diff(req_id, v1["version_id"], v2["version_id"])
        
        assert diff["version_from"] == v1["version_id"]
        assert diff["version_to"] == v2["version_id"]
        assert set(diff["changed_fields"]) == {"title", "description", "method", "authentication", "tags"}
        
        # 各フィールドの変更内容
        assert diff["changes"]["title"]["before"] == "REST API設計"
        assert diff["changes"]["title"]["after"] == "GraphQL API設計"
        
        assert diff["changes"]["method"]["before"] == "GET/POST/PUT/DELETE"
        assert diff["changes"]["method"]["after"] == "Query/Mutation"
        
        assert diff["changes"]["authentication"]["before"] == "Basic認証"
        assert diff["changes"]["authentication"]["after"] == "JWT認証"
        
        assert diff["changes"]["tags"]["before"] == ["API", "REST", "backend"]
        assert diff["changes"]["tags"]["after"] == ["API", "GraphQL", "backend"]
    
    def test_スナップショットID廃止_全レスポンス_snapshot_idフィールドが存在しない(self, repo):
        """
        Given: 要件の各種操作を実行
        When: レスポンスを確認
        Then: いずれのレスポンスにもsnapshot_idが含まれない
        """
        # Arrange
        req_id = "REQ-005"
        
        # Act & Assert: 作成
        create_result = repo.save({
            "id": req_id,
            "title": "テスト要件",
            "description": "スナップショットID確認用"
        })
        assert "snapshot_id" not in create_result
        assert "version_id" in create_result  # version_idは含まれる
        
        # 更新
        update_result = repo.save({
            "id": req_id,
            "title": "テスト要件（更新）",
            "description": "スナップショットID確認用"
        })
        assert "snapshot_id" not in update_result
        
        # 履歴取得
        history = repo.get_requirement_history(req_id)
        for version in history:
            assert "snapshot_id" not in version
            assert "version_id" in version
        
        # 現在の状態取得
        current = repo.find(req_id)
        assert "snapshot_id" not in current
        
        # バージョン指定取得
        versioned = repo.get_requirement_at_timestamp(
            req_id, 
            datetime.now().isoformat()
        )
        assert "snapshot_id" not in versioned
    
    def test_イミュータブル要件エンティティ_更新時_新しいエンティティが作成される(self, repo):
        """
        Given: 要件が存在する
        When: 要件を更新する
        Then: 既存エンティティは変更されず、新しいバージョンのエンティティが作成される
        """
        # Arrange
        req_id = "REQ-006"
        
        # Act: 初回作成
        v1 = repo.save({
            "id": req_id,
            "title": "不変要件",
            "content": "このエンティティは変更されない"
        })
        v1_entity_id = v1["entity_id"]  # 実際のエンティティID
        
        # 更新
        v2 = repo.save({
            "id": req_id,
            "title": "不変要件（更新版）",
            "content": "新しいエンティティが作成される"
        })
        v2_entity_id = v2["entity_id"]
        
        # Assert: 異なるエンティティIDを持つ
        assert v1_entity_id != v2_entity_id
        
        # 古いバージョンのエンティティが変更されていないことを確認
        old_entity = repo.get_entity_by_id(v1_entity_id)
        assert old_entity["title"] == "不変要件"
        assert old_entity["content"] == "このエンティティは変更されない"
        
        # 新しいバージョンのエンティティを確認
        new_entity = repo.get_entity_by_id(v2_entity_id)
        assert new_entity["title"] == "不変要件（更新版）"
        assert new_entity["content"] == "新しいエンティティが作成される"
    
    def test_LocationURIポインタ_更新時_最新バージョンを指す(self, repo):
        """
        Given: LocationURIで管理される要件
        When: 要件が更新される
        Then: LocationURIは常に最新バージョンのエンティティを指す
        """
        # Arrange
        req_id = "REQ-007"
        
        # Act: 3回更新
        v1 = repo.save({"id": req_id, "title": "v1", "status": "draft"})
        v2 = repo.save({"id": req_id, "title": "v2", "status": "review"})
        v3 = repo.save({"id": req_id, "title": "v3", "status": "approved"})
        
        # Assert: LocationURI経由で最新版を取得
        current = repo.find_by_location_uri(f"req://{req_id}")
        assert current["title"] == "v3"
        assert current["status"] == "approved"
        assert current["version_id"] == v3["version_id"]
        
        # 過去バージョンは直接アクセスで取得可能
        past_v1 = repo.find_by_version(req_id, v1["version_id"])
        assert past_v1["title"] == "v1"
        assert past_v1["status"] == "draft"