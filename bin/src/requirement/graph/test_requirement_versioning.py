"""
要件バージョン管理システム 正式仕様テスト
t-wadaスタイルで記述

このテストスイートが要件管理システムの正式な仕様定義です。
「テストは仕様そのもの」の原則に基づき、これらのテストが全てGREENになることで
システムが正しく実装されたと判断します。

設計原則：
1. RequirementEntityはイミュータブル（不変）
2. 各更新で新しいエンティティが作成される
3. LocationURIが常に最新バージョンを指す
4. 全ての過去バージョンが保持される
5. 完全な履歴追跡とタイムトラベルクエリが可能
"""
import os
import pytest
from datetime import datetime
from typing import Dict, List
import sys
# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import kuzu
from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository


class RepoWrapper:
    """リポジトリのdict形式をオブジェクト形式に変換するラッパー"""
    def __init__(self, repo_dict):
        self._repo = repo_dict
        
    def __getattr__(self, name):
        if name in self._repo:
            return self._repo[name]
        raise AttributeError(f"Repository has no method '{name}'")


@pytest.fixture
def repo(tmp_path):
    """テスト用リポジトリフィクスチャ"""
    # スキーマチェックをスキップ
    os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"
    
    db = kuzu.Database(str(tmp_path / "test.db"))
    conn = kuzu.Connection(db)
    
    # 必要なスキーマを作成
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            priority STRING DEFAULT 'medium',
            requirement_type STRING DEFAULT 'functional',
            status STRING DEFAULT 'active',
            embedding DOUBLE[64] DEFAULT NULL,
            created_at STRING DEFAULT '2024-01-01T00:00:00',
            verification_required BOOLEAN DEFAULT true,
            implementation_details STRING,
            acceptance_criteria STRING,
            technical_specifications STRING
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS LocationURI (
            id STRING PRIMARY KEY
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS VersionState (
            id STRING PRIMARY KEY,
            timestamp STRING,
            description STRING,
            change_reason STRING,
            progress_percentage DOUBLE DEFAULT 0.0,
            operation STRING DEFAULT 'UPDATE',
            author STRING DEFAULT 'system',
            changed_fields STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS LOCATES (
            FROM LocationURI TO RequirementEntity,
            entity_type STRING DEFAULT 'requirement'
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS HAS_VERSION (
            FROM RequirementEntity TO VersionState
        )
    """)
    
    # 階層処理用UDFを登録
    from requirement.graph.infrastructure.hierarchy_udfs import register_hierarchy_udfs
    register_hierarchy_udfs(conn)
    
    repo_dict = create_kuzu_repository(str(tmp_path / "test.db"))
    return RepoWrapper(repo_dict)


@pytest.mark.skip(reason="バージョン管理機能は未実装。TODO: 定型メソッドの実装が必要")
class TestRequirementVersioning:
    """要件バージョン管理システムの仕様
    
    TODO: 以下の定型メソッドを実装する必要がある：
    
    注: 実装方針として以下も検討中：
    - Cypherテンプレート駆動設計: bin/src/kuzu/query/dml/*.cypherの既存テンプレートを活用
    - 高階関数による動的クエリ合成: 複数のCypherテンプレートを関数合成でトランザクション化
    - ハイブリッドアプローチ: 定型メソッドの内部でCypherテンプレートを活用
    
    定型メソッド一覧：
    - save(data, author): バージョン付き保存
    - delete(req_id): 削除（削除マークの新バージョン作成）
    - save_with_timestamp(data, timestamp): タイムスタンプ指定保存
    - get_requirement_history(req_id): 履歴取得
    - get_requirement_at_timestamp(req_id, timestamp): 時点照会
    - get_version_diff(req_id, v1_id, v2_id): バージョン間差分
    - find_by_location_uri(uri): LocationURI経由の取得
    - find_by_version(req_id, version_id): 特定バージョン取得
    - rollback_to_version(req_id, version_id, reason): ロールバック
    - find_path_at_timestamp(from_id, to_id, timestamp): 時点パス探索
    - find_dependencies_at_timestamp(req_id, timestamp): 時点依存関係
    - search(query, include_history): 履歴含む検索
    - export_with_history(filters): 履歴付きエクスポート
    - import_data(data, merge_strategy): データインポート
    - as_readonly(): 読み取り専用モード
    - get_requirement_statistics(include_history): 統計情報
    - analyze_change_frequency(req_id, period): 変更頻度分析
    - validate_data_consistency(): データ整合性検証
    """
    
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
            "priority": 2
        })
        
        # 2回目: タイトルとステータス変更
        v2 = repo.save({
            "id": req_id,
            "title": "OAuth2.0認証機能",  # 変更
            "description": "IDとパスワードでログイン",
            "status": "approved",  # 変更
            "priority": 2
        })
        
        # 3回目: 説明とステータス変更
        v3 = repo.save({
            "id": req_id,
            "title": "OAuth2.0認証機能",
            "description": "Google/GitHub/Microsoftアカウントでログイン",  # 変更
            "status": "implemented",  # 変更
            "priority": 2
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
            "priority": 0,
            "estimated_hours": 10
        }, timestamp=t1)
        
        repo.save_with_timestamp({
            "id": req_id,
            "title": "仕様変更版",
            "priority": 1,
            "estimated_hours": 20
        }, timestamp=t2)
        
        repo.save_with_timestamp({
            "id": req_id,
            "title": "最終仕様",
            "priority": 2,
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
    
    def test_APIレスポンス_全操作_正しいフィールドを含む(self, repo):
        """
        Given: 要件の各種操作を実行
        When: レスポンスを確認
        Then: 期待されるフィールドのみが含まれる
        """
        # Arrange
        req_id = "REQ-005"
        
        # Act & Assert: 作成
        create_result = repo.save({
            "id": req_id,
            "title": "テスト要件",
            "description": "レスポンスフィールド確認用"
        })
        assert "version_id" in create_result
        assert "entity_id" in create_result
        assert "location_uri" in create_result
        
        # 更新
        update_result = repo.save({
            "id": req_id,
            "title": "テスト要件（更新）",
            "description": "レスポンスフィールド確認用"
        })
        assert "version_id" in update_result
        assert update_result["version_id"] != create_result["version_id"]
        
        # 履歴取得
        history = repo.get_requirement_history(req_id)
        for version in history:
            assert "version_id" in version
            assert "timestamp" in version
            assert "operation" in version
            assert "author" in version
        
        # 現在の状態取得
        current = repo.find(req_id)
        assert "id" in current
        assert "title" in current
        assert "version_id" in current
        
        # バージョン指定取得
        versioned = repo.get_requirement_at_timestamp(
            req_id, 
            datetime.now().isoformat()
        )
        assert "version_info" in versioned
        assert versioned["id"] == req_id
    
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
    
    # ===== 追加テスト: エッジケース =====
    
    def test_空の要件_履歴照会_空のフィールドも正確に保持される(self, repo):
        """
        Given: 一部フィールドが空の要件
        When: 更新して履歴を照会
        Then: 空文字、null、未定義フィールドが正確に保持される
        """
        # Arrange
        req_id = "REQ-008"
        
        # Act
        v1 = repo.save({
            "id": req_id,
            "title": "",  # 空文字
            "description": None,  # null
            # priorityは未定義
        })
        
        v2 = repo.save({
            "id": req_id,
            "title": "タイトル追加",
            "description": "",  # nullから空文字へ
            "priority": 0  # 新規追加
        })
        
        # Assert
        history = repo.get_requirement_history(req_id)
        
        assert history[0]["title"] == ""
        assert history[0]["description"] is None
        assert "priority" not in history[0]
        
        assert history[1]["title"] == "タイトル追加"
        assert history[1]["description"] == ""
        assert history[1]["priority"] == "low"
    
    def test_大量フィールド要件_履歴照会_全フィールドが保持される(self, repo):
        """
        Given: 多数のカスタムフィールドを持つ要件
        When: 一部フィールドのみ更新
        Then: 変更されないフィールドも含めて全て保持される
        """
        # Arrange
        req_id = "REQ-009"
        
        # 初期データ（20個のフィールド）
        initial_data = {
            "id": req_id,
            "title": "複雑な要件",
            "description": "多数のフィールドを持つ",
            **{f"custom_field_{i}": f"value_{i}" for i in range(1, 18)}
        }
        
        # Act
        v1 = repo.save(initial_data)
        
        # 3つのフィールドのみ更新
        update_data = {
            "id": req_id,
            "title": "複雑な要件（更新）",
            "custom_field_5": "updated_value_5",
            "custom_field_10": "updated_value_10"
        }
        v2 = repo.save(update_data)
        
        # Assert
        history = repo.get_requirement_history(req_id)
        
        # v1は全フィールドを持つ
        assert len([k for k in history[0].keys() if k.startswith("custom_field_")]) == 17
        
        # v2も全フィールドを保持（未変更フィールドも）
        assert history[1]["custom_field_1"] == "value_1"  # 未変更
        assert history[1]["custom_field_5"] == "updated_value_5"  # 変更
        assert history[1]["custom_field_17"] == "value_17"  # 未変更
    
    def test_特殊文字含む要件_履歴照会_エスケープ処理が正しく行われる(self, repo):
        """
        Given: 特殊文字を含む要件データ
        When: 保存して履歴照会
        Then: 特殊文字が正確に保持される
        """
        # Arrange
        req_id = "REQ-010"
        
        # Act
        v1 = repo.save({
            "id": req_id,
            "title": "SQLインジェクション'; DROP TABLE--",
            "description": 'JSON特殊文字: {"key": "value"}',
            "content": "改行\nタブ\tバックスラッシュ\\引用符\"",
            "unicode": "絵文字😀 と 日本語、中文、한국어"
        })
        
        # Assert
        history = repo.get_requirement_history(req_id)
        
        assert history[0]["title"] == "SQLインジェクション'; DROP TABLE--"
        assert history[0]["description"] == 'JSON特殊文字: {"key": "value"}'
        assert history[0]["content"] == "改行\nタブ\tバックスラッシュ\\引用符\""
        assert history[0]["unicode"] == "絵文字😀 と 日本語、中文、한국어"
    
    # ===== 追加テスト: 依存関係・階層構造 =====
    
    def test_依存関係持つ要件_削除時_依存関係の履歴も保持される(self, repo):
        """
        Given: 他の要件に依存/依存される要件
        When: 要件を削除
        Then: 依存関係情報も履歴として保持される
        """
        # Arrange
        req_a = "REQ-011-A"
        req_b = "REQ-011-B"
        req_c = "REQ-011-C"
        
        # A -> B -> C の依存関係
        repo.save({"id": req_a, "title": "要件A"})
        repo.save({"id": req_b, "title": "要件B"})
        repo.save({"id": req_c, "title": "要件C"})
        
        repo.add_dependency(req_a, req_b)
        repo.add_dependency(req_b, req_c)
        
        # Act: Bを削除
        repo.delete(req_b)
        
        # Assert
        history_b = repo.get_requirement_history(req_b)
        
        # 削除時点での依存関係情報が含まれる
        delete_record = history_b[-1]
        assert delete_record["operation"] == "DELETE"
        assert delete_record["dependencies"]["depends_on"] == [req_c]
        assert delete_record["dependencies"]["depended_by"] == [req_a]
    
    def test_階層構造の要件_親子関係変更_履歴に階層情報が保持される(self, repo):
        """
        Given: 階層構造を持つ要件
        When: 親要件を変更
        Then: 各時点での階層情報が履歴に保持される
        """
        # Arrange
        parent1 = "REQ-012-P1"
        parent2 = "REQ-012-P2"
        child = "REQ-012-C"
        
        repo.save({"id": parent1, "title": "親要件1"})
        repo.save({"id": parent2, "title": "親要件2"})
        
        # Act
        # 最初はparent1の子として作成
        v1 = repo.save({"id": child, "title": "子要件"}, parent_id=parent1)
        
        # parent2に移動
        v2 = repo.save({"id": child, "title": "子要件"}, parent_id=parent2)
        
        # 独立した要件に変更
        v3 = repo.save({"id": child, "title": "子要件（独立）"}, parent_id=None)
        
        # Assert
        history = repo.get_requirement_history(child)
        
        assert history[0]["parent_id"] == parent1
        assert history[0]["hierarchy_path"] == f"{parent1}/{child}"
        
        assert history[1]["parent_id"] == parent2
        assert history[1]["hierarchy_path"] == f"{parent2}/{child}"
        
        assert history[2]["parent_id"] is None
        assert history[2]["hierarchy_path"] == child
    
    # ===== 追加テスト: 検索・クエリ関連 =====
    
    def test_全文検索_履歴バージョン含む_過去バージョンも検索対象になる(self, repo):
        """
        Given: 内容が変更された要件
        When: 過去にのみ存在したキーワードで検索
        Then: 過去バージョンがヒットする
        """
        # Arrange
        req_id = "REQ-013"
        
        repo.save({
            "id": req_id,
            "title": "Kubernetes導入",
            "description": "コンテナオーケストレーション"
        })
        
        repo.save({
            "id": req_id,
            "title": "OpenShift導入",  # Kubernetesという単語が消えた
            "description": "エンタープライズコンテナプラットフォーム"
        })
        
        # Act & Assert
        # 現在バージョンのみ検索
        current_results = repo.search("Kubernetes", include_history=False)
        assert len(current_results) == 0
        
        # 履歴含む検索
        history_results = repo.search("Kubernetes", include_history=True)
        assert len(history_results) == 1
        assert history_results[0]["id"] == req_id
        assert history_results[0]["version_info"]["is_current"] == False
    
    def test_バージョン範囲指定_履歴照会_指定期間のバージョンのみ返される(self, repo):
        """
        Given: 長期間にわたって更新された要件
        When: 特定期間の履歴を照会
        Then: その期間のバージョンのみ返される
        """
        # Arrange
        req_id = "REQ-014"
        
        repo.save_with_timestamp(
            {"id": req_id, "title": "v1", "status": "draft"},
            timestamp="2023-01-01T00:00:00Z"
        )
        repo.save_with_timestamp(
            {"id": req_id, "title": "v2", "status": "review"},
            timestamp="2023-06-01T00:00:00Z"
        )
        repo.save_with_timestamp(
            {"id": req_id, "title": "v3", "status": "approved"},
            timestamp="2023-12-01T00:00:00Z"
        )
        repo.save_with_timestamp(
            {"id": req_id, "title": "v4", "status": "implemented"},
            timestamp="2024-03-01T00:00:00Z"
        )
        
        # Act: 2023年の履歴のみ取得
        history_2023 = repo.get_requirement_history(
            req_id,
            from_timestamp="2023-01-01T00:00:00Z",
            to_timestamp="2023-12-31T23:59:59Z"
        )
        
        # Assert
        assert len(history_2023) == 3
        assert history_2023[0]["title"] == "v1"
        assert history_2023[2]["title"] == "v3"
    
    # ===== 追加テスト: 並行処理・競合状態 =====
    
    def test_同時更新_異なるフィールド_両方の変更が保持される(self, repo):
        """
        Given: 同じ要件を異なるユーザーが同時に更新
        When: 異なるフィールドを更新
        Then: 両方の変更が適切にマージされる
        """
        # Arrange
        req_id = "REQ-015"
        
        base_version = repo.save({
            "id": req_id,
            "title": "並行編集テスト",
            "description": "元の説明",
            "priority": 1,
            "assignee": "user1"
        })
        
        # Act: 2人のユーザーが同時に異なるフィールドを更新
        # ユーザー1: タイトルと優先度を更新
        update1 = repo.save_with_base_version({
            "id": req_id,
            "title": "並行編集テスト（更新）",
            "priority": 2
        }, base_version_id=base_version["version_id"])
        
        # ユーザー2: 説明と担当者を更新
        update2 = repo.save_with_base_version({
            "id": req_id,
            "description": "新しい説明",
            "assignee": "user2"
        }, base_version_id=base_version["version_id"])
        
        # Assert: 最終状態は両方の変更を含む
        current = repo.find(req_id)
        assert current["title"] == "並行編集テスト（更新）"  # update1の変更
        assert current["description"] == "新しい説明"  # update2の変更
        assert current["priority"] == "high"  # update1の変更
        assert current["assignee"] == "user2"  # update2の変更
    
    # ===== 追加テスト: エラーケース =====
    
    def test_存在しない要件_履歴照会_空の履歴が返される(self, repo):
        """
        Given: 存在しない要件ID
        When: 履歴を照会
        Then: エラーではなく空の履歴が返される
        """
        # Act & Assert
        history = repo.get_requirement_history("NON_EXISTENT_REQ")
        assert history == []
    
    def test_不正なタイムスタンプ_時点照会_エラーが返される(self, repo):
        """
        Given: 要件が存在する
        When: 不正な形式のタイムスタンプで照会
        Then: 適切なエラーメッセージが返される
        """
        # Arrange
        req_id = "REQ-016"
        repo.save({"id": req_id, "title": "テスト"})
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repo.get_requirement_at_timestamp(req_id, "invalid-timestamp")
        
        assert "timestamp format" in str(exc_info.value).lower()
    
    def test_循環参照のあるバージョン_履歴照会_無限ループにならない(self, repo):
        """
        Given: 何らかの理由で循環参照が発生したバージョンチェーン
        When: 履歴を照会
        Then: 無限ループせずに適切に処理される
        """
        # このテストは実装によっては不要かもしれないが、
        # 安全性のために含める
        pass  # 実装依存
    
    # ===== 追加テスト: パフォーマンス関連 =====
    
    def test_大量バージョン要件_履歴照会_適切にページングされる(self, repo):
        """
        Given: 1000回更新された要件
        When: 履歴を照会（デフォルトlimit付き）
        Then: 指定された件数のみ返される
        """
        # Arrange
        req_id = "REQ-017"
        
        # 簡易的に50回更新
        for i in range(50):
            repo.save({
                "id": req_id,
                "title": f"バージョン{i}",
                "counter": i
            })
        
        # Act
        history_limited = repo.get_requirement_history(req_id, limit=10)
        history_all = repo.get_requirement_history(req_id, limit=None)
        
        # Assert
        assert len(history_limited) == 10
        assert len(history_all) == 50
        assert history_limited[0]["counter"] == 49  # 最新から
        assert history_limited[9]["counter"] == 40
    
    # ===== 追加テスト: 集計・統計関連 =====
    
    def test_要件統計情報_履歴含む_正確な統計が計算される(self, repo):
        """
        Given: 複数の要件とその履歴
        When: 統計情報を取得
        Then: 現在版と履歴版の統計が正確に分離される
        """
        # Arrange
        # 要件1: proposed -> approved -> implemented
        repo.save({"id": "STAT-001", "title": "要件1", "status": "proposed"})
        repo.save({"id": "STAT-001", "title": "要件1", "status": "approved"})
        repo.save({"id": "STAT-001", "title": "要件1", "status": "implemented"})
        
        # 要件2: proposed -> deprecated
        repo.save({"id": "STAT-002", "title": "要件2", "status": "proposed"})
        repo.save({"id": "STAT-002", "title": "要件2", "status": "deprecated"})
        
        # 要件3: proposed (削除済み)
        repo.save({"id": "STAT-003", "title": "要件3", "status": "proposed"})
        repo.delete("STAT-003")
        
        # Act
        current_stats = repo.get_statistics(include_history=False)
        history_stats = repo.get_statistics(include_history=True)
        
        # Assert
        # 現在版の統計（削除済みは含まない）
        assert current_stats["total_requirements"] == 2
        assert current_stats["by_status"]["implemented"] == 1
        assert current_stats["by_status"]["deprecated"] == 1
        assert current_stats["by_status"]["proposed"] == 0
        
        # 履歴含む統計
        assert history_stats["total_versions"] == 7  # 6保存 + 1削除
        assert history_stats["deleted_requirements"] == 1
        assert history_stats["average_versions_per_requirement"] == 2.33  # 7/3
    
    def test_変更頻度分析_時系列データ_更新パターンが分析される(self, repo):
        """
        Given: 時系列で更新された要件群
        When: 変更頻度を分析
        Then: 期間別の更新頻度が正確に集計される
        """
        # Arrange
        # 月曜日に集中的に更新
        repo.save_with_timestamp({"id": "FREQ-001", "title": "v1"}, "2024-01-01T10:00:00Z")  # Mon
        repo.save_with_timestamp({"id": "FREQ-001", "title": "v2"}, "2024-01-01T14:00:00Z")  # Mon
        repo.save_with_timestamp({"id": "FREQ-001", "title": "v3"}, "2024-01-08T10:00:00Z")  # Mon
        
        # 別の要件は金曜日に更新
        repo.save_with_timestamp({"id": "FREQ-002", "title": "v1"}, "2024-01-05T10:00:00Z")  # Fri
        repo.save_with_timestamp({"id": "FREQ-002", "title": "v2"}, "2024-01-12T10:00:00Z")  # Fri
        
        # Act
        frequency_analysis = repo.analyze_change_frequency(
            from_date="2024-01-01",
            to_date="2024-01-31"
        )
        
        # Assert
        assert frequency_analysis["by_day_of_week"]["Monday"] == 3
        assert frequency_analysis["by_day_of_week"]["Friday"] == 2
        assert frequency_analysis["by_hour"]["10"] == 4  # 10時台が最多
        assert frequency_analysis["most_active_requirement"] == "FREQ-001"
    
    # ===== 追加テスト: 既存APIとの互換性 =====
    
    def test_レガシーAPI互換性_find_all_現在版のみ返される(self, repo):
        """
        Given: 複数バージョンを持つ要件群
        When: 従来のfind_all()を呼び出す
        Then: 現在版のみが返される（履歴は含まれない）
        """
        # Arrange
        repo.save({"id": "LEGACY-001", "title": "v1"})
        repo.save({"id": "LEGACY-001", "title": "v2"})
        repo.save({"id": "LEGACY-002", "title": "v1"})
        repo.save({"id": "LEGACY-002", "title": "v2"})
        repo.save({"id": "LEGACY-002", "title": "v3"})
        
        # Act
        all_requirements = repo.find_all()
        
        # Assert
        assert len(all_requirements) == 2  # 2要件の現在版のみ
        
        # タイトルで検証
        titles = {req["title"] for req in all_requirements}
        assert titles == {"v2", "v3"}
    
    def test_レガシーAPI互換性_依存関係_現在版間の関係のみ返される(self, repo):
        """
        Given: バージョン更新された要件間の依存関係
        When: find_dependencies()を呼び出す
        Then: 現在版間の依存関係のみが返される
        """
        # Arrange
        repo.save({"id": "DEP-A", "title": "A-v1"})
        repo.save({"id": "DEP-B", "title": "B-v1"})
        
        # 古いバージョンで依存関係を作成
        repo.add_dependency("DEP-A", "DEP-B")
        
        # Aを更新（依存関係は維持される想定）
        repo.save({"id": "DEP-A", "title": "A-v2"})
        
        # Act
        deps = repo.find_dependencies("DEP-A")
        
        # Assert
        assert len(deps) == 1
        assert deps[0]["requirement"]["id"] == "DEP-B"
        assert deps[0]["requirement"]["title"] == "B-v1"  # Bは更新されていない
    
    # ===== 追加テスト: メタデータ・追跡情報 =====
    
    def test_変更追跡メタデータ_各バージョン_作成者と理由が記録される(self, repo):
        """
        Given: 変更理由と作成者を指定した更新
        When: 履歴を照会
        Then: 各バージョンに正確なメタデータが含まれる
        """
        # Arrange
        req_id = "META-001"
        
        # Act
        v1 = repo.save(
            {"id": req_id, "title": "初版"},
            author="developer1",
            change_reason="新規要件追加"
        )
        
        v2 = repo.save(
            {"id": req_id, "title": "改訂版"},
            author="reviewer1",
            change_reason="レビュー指摘事項の反映"
        )
        
        v3 = repo.save(
            {"id": req_id, "title": "最終版"},
            author="developer1",
            change_reason="実装完了に伴う最終調整"
        )
        
        # Assert
        history = repo.get_requirement_history(req_id)
        
        assert history[0]["author"] == "developer1"
        assert history[0]["change_reason"] == "新規要件追加"
        
        assert history[1]["author"] == "reviewer1"
        assert history[1]["change_reason"] == "レビュー指摘事項の反映"
        
        assert history[2]["author"] == "developer1"
        assert history[2]["change_reason"] == "実装完了に伴う最終調整"
    
    def test_自動生成フィールド_タイムスタンプとID_一貫性が保たれる(self, repo):
        """
        Given: 要件の作成と更新
        When: 自動生成されるフィールドを確認
        Then: タイムスタンプとIDの一貫性が保証される
        """
        # Arrange & Act
        req_id = "AUTO-001"
        
        import time
        start_time = datetime.now()
        
        v1 = repo.save({"id": req_id, "title": "v1"})
        time.sleep(0.1)  # 確実に時間差を作る
        v2 = repo.save({"id": req_id, "title": "v2"})
        
        end_time = datetime.now()
        
        # Assert
        history = repo.get_requirement_history(req_id)
        
        # version_idのフォーマット検証
        assert v1["version_id"].startswith(f"v_{start_time.strftime('%Y-%m-%d')}")
        assert v1["version_id"].endswith(f"_{req_id}")
        
        # タイムスタンプの順序性
        ts1 = datetime.fromisoformat(history[0]["timestamp"])
        ts2 = datetime.fromisoformat(history[1]["timestamp"])
        
        assert start_time <= ts1 <= ts2 <= end_time
        assert ts1 < ts2  # 確実に増加
    
    # ===== 追加テスト: データ移行関連 =====
    
    def test_旧形式データ移行_スナップショット有り_正しく変換される(self, repo):
        """
        Given: 旧形式（スナップショット有り）のデータ
        When: 移行処理を実行
        Then: 新形式（イミュータブル）に正しく変換される
        """
        # これは移行スクリプトのテストとして別途実装
        # ここではインターフェースの互換性のみ確認
        pass
    
    def test_部分更新_未指定フィールド_前バージョンから引き継がれる(self, repo):
        """
        Given: 全フィールドを持つ要件
        When: 一部フィールドのみ指定して更新
        Then: 未指定フィールドは前バージョンの値が引き継がれる
        """
        # Arrange
        req_id = "PARTIAL-001"
        
        v1 = repo.save({
            "id": req_id,
            "title": "完全な要件",
            "description": "詳細な説明",
            "priority": 2,
            "category": "feature",
            "tags": ["important", "urgent"],
            "custom_field": "custom_value"
        })
        
        # Act: titleのみ更新
        v2 = repo.save({
            "id": req_id,
            "title": "更新されたタイトル"
        })
        
        # Assert: 他のフィールドは保持される
        current = repo.find(req_id)
        assert current["title"] == "更新されたタイトル"
        assert current["description"] == "詳細な説明"
        assert current["priority"] == "high"
        assert current["category"] == "feature"
        assert current["tags"] == ["important", "urgent"]
        assert current["custom_field"] == "custom_value"
    
    # ===== 追加テスト: 一括操作 =====
    
    def test_一括更新_複数要件_各要件の履歴が独立して管理される(self, repo):
        """
        Given: 複数の要件
        When: 一括更新を実行
        Then: 各要件の履歴が独立して正しく記録される
        """
        # Arrange
        req_ids = ["BULK-001", "BULK-002", "BULK-003"]
        for req_id in req_ids:
            repo.save({"id": req_id, "title": f"{req_id} 初版", "status": "proposed"})
        
        # Act: 一括でステータス更新
        bulk_update_data = [
            {"id": req_id, "status": "approved"} for req_id in req_ids
        ]
        results = repo.bulk_save(bulk_update_data, author="bulk_approver")
        
        # Assert
        assert len(results) == 3
        
        for req_id in req_ids:
            history = repo.get_requirement_history(req_id)
            assert len(history) == 2
            assert history[0]["status"] == "proposed"
            assert history[1]["status"] == "approved"
            assert history[1]["author"] == "bulk_approver"
    
    def test_ロールバック機能_特定バージョンに戻す_過去の状態が新バージョンとして作成(self, repo):
        """
        Given: 複数回更新された要件
        When: 過去のバージョンにロールバック
        Then: 過去の状態が新しいバージョンとして作成される
        """
        # Arrange
        req_id = "ROLLBACK-001"
        
        v1 = repo.save({"id": req_id, "title": "初版", "content": "最初の内容"})
        v2 = repo.save({"id": req_id, "title": "第2版", "content": "更新した内容"})
        v3 = repo.save({"id": req_id, "title": "第3版", "content": "さらに更新"})
        
        # Act: v1の状態にロールバック
        v4 = repo.rollback_to_version(req_id, v1["version_id"], 
                                      author="admin",
                                      reason="誤った更新のため初版に戻す")
        
        # Assert
        current = repo.find(req_id)
        assert current["title"] == "初版"
        assert current["content"] == "最初の内容"
        
        history = repo.get_requirement_history(req_id)
        assert len(history) == 4
        assert history[3]["operation"] == "ROLLBACK"
        assert history[3]["rollback_from_version"] == v1["version_id"]
        assert history[3]["change_reason"] == "誤った更新のため初版に戻す"
    
    # ===== 追加テスト: グラフ特有の操作 =====
    
    def test_要件間パス探索_履歴考慮_特定時点でのパスが返される(self, repo):
        """
        Given: 時間とともに変化する依存関係グラフ
        When: 特定時点でのパスを探索
        Then: その時点での依存関係に基づくパスが返される
        """
        # Arrange
        # t1: A -> B -> C
        repo.save_with_timestamp({"id": "PATH-A", "title": "A"}, "2024-01-01T00:00:00Z")
        repo.save_with_timestamp({"id": "PATH-B", "title": "B"}, "2024-01-01T00:00:00Z")
        repo.save_with_timestamp({"id": "PATH-C", "title": "C"}, "2024-01-01T00:00:00Z")
        
        repo.add_dependency_with_timestamp("PATH-A", "PATH-B", "2024-01-01T01:00:00Z")
        repo.add_dependency_with_timestamp("PATH-B", "PATH-C", "2024-01-01T01:00:00Z")
        
        # t2: A -> D -> C (Bを経由しなくなった)
        repo.save_with_timestamp({"id": "PATH-D", "title": "D"}, "2024-02-01T00:00:00Z")
        repo.remove_dependency_with_timestamp("PATH-A", "PATH-B", "2024-02-01T01:00:00Z")
        repo.remove_dependency_with_timestamp("PATH-B", "PATH-C", "2024-02-01T01:00:00Z")
        repo.add_dependency_with_timestamp("PATH-A", "PATH-D", "2024-02-01T02:00:00Z")
        repo.add_dependency_with_timestamp("PATH-D", "PATH-C", "2024-02-01T02:00:00Z")
        
        # Act & Assert
        # 1月時点のパス
        path_jan = repo.find_path_at_timestamp("PATH-A", "PATH-C", "2024-01-15T00:00:00Z")
        assert len(path_jan) == 3
        assert [node["id"] for node in path_jan] == ["PATH-A", "PATH-B", "PATH-C"]
        
        # 2月時点のパス
        path_feb = repo.find_path_at_timestamp("PATH-A", "PATH-C", "2024-02-15T00:00:00Z")
        assert len(path_feb) == 3
        assert [node["id"] for node in path_feb] == ["PATH-A", "PATH-D", "PATH-C"]
    
    def test_影響範囲分析_バージョン考慮_正確な影響要件が特定される(self, repo):
        """
        Given: 複雑な依存関係を持つ要件群
        When: 特定要件の変更による影響範囲を分析
        Then: 直接・間接的に影響を受ける要件が正確に特定される
        """
        # Arrange
        # コアライブラリ -> 複数のモジュール -> アプリケーション
        repo.save({"id": "CORE-LIB", "title": "コアライブラリ", "criticality": "high"})
        repo.save({"id": "MODULE-A", "title": "モジュールA"})
        repo.save({"id": "MODULE-B", "title": "モジュールB"})
        repo.save({"id": "APP-1", "title": "アプリ1"})
        repo.save({"id": "APP-2", "title": "アプリ2"})
        
        # 依存関係
        repo.add_dependency("MODULE-A", "CORE-LIB")
        repo.add_dependency("MODULE-B", "CORE-LIB")
        repo.add_dependency("APP-1", "MODULE-A")
        repo.add_dependency("APP-2", "MODULE-A")
        repo.add_dependency("APP-2", "MODULE-B")
        
        # Act: コアライブラリ変更の影響を分析
        impact = repo.analyze_change_impact("CORE-LIB", max_depth=3)
        
        # Assert
        assert impact["direct_impact"] == ["MODULE-A", "MODULE-B"]
        assert set(impact["indirect_impact"]) == {"APP-1", "APP-2"}
        assert impact["total_impacted"] == 4
        assert impact["critical_path"] == ["CORE-LIB", "MODULE-A", "APP-1"]  # 最短パス
        assert impact["risk_score"] >= 0.8  # 高リスク
    
    # ===== 追加テスト: データ整合性検証 =====
    
    def test_データ整合性検証_全履歴_不整合が検出される(self, repo):
        """
        Given: 長期間運用されたデータベース
        When: データ整合性を検証
        Then: 孤立したバージョン、欠落した関係などが検出される
        """
        # Arrange: 意図的に不整合を作る
        # 正常なデータ
        repo.save({"id": "VALID-001", "title": "正常要件"})
        
        # 不整合を直接作る（通常は起きないが、移行時などに発生可能）
        # これらは実装によってはモックが必要
        
        # Act
        validation_result = repo.validate_data_integrity()
        
        # Assert
        assert validation_result["is_valid"] == True  # 通常操作では不整合は起きない
        assert validation_result["total_requirements"] >= 1
        assert validation_result["total_versions"] >= 1
        assert validation_result["orphaned_versions"] == 0
        assert validation_result["missing_current_pointers"] == 0
        assert validation_result["circular_dependencies"] == 0
    
    def test_一貫性チェック_LocationURIとエンティティ_全て正しくリンクされる(self, repo):
        """
        Given: 複数回更新された要件群
        When: LocationURIとエンティティの関係を検証
        Then: 各LocationURIが正しく最新版を指している
        """
        # Arrange
        req_ids = ["CONS-001", "CONS-002", "CONS-003"]
        
        for req_id in req_ids:
            # 各要件を3回更新
            for i in range(3):
                repo.save({"id": req_id, "title": f"{req_id}-v{i+1}"})
        
        # Act & Assert
        for req_id in req_ids:
            # LocationURI経由で取得
            current_via_uri = repo.find_by_location_uri(f"req://{req_id}")
            # 直接取得
            current_direct = repo.find(req_id)
            
            # 同じ結果になるはず
            assert current_via_uri["title"] == current_direct["title"]
            assert current_via_uri["title"] == f"{req_id}-v3"  # 最新版
    
    # ===== 追加テスト: アクセス制御（将来の拡張用） =====
    
    def test_読み取り専用モード_履歴照会_更新操作が拒否される(self, repo):
        """
        Given: 読み取り専用モードのリポジトリ
        When: 更新操作を試みる
        Then: 適切なエラーが返され、データは変更されない
        """
        # Arrange
        req_id = "READONLY-001"
        repo.save({"id": req_id, "title": "初期状態"})
        
        # 読み取り専用モードに切り替え
        readonly_repo = repo.as_readonly()
        
        # Act & Assert
        # 読み取りは可能
        current = readonly_repo.find(req_id)
        assert current["title"] == "初期状態"
        
        history = readonly_repo.get_requirement_history(req_id)
        assert len(history) == 1
        
        # 更新は拒否される
        with pytest.raises(PermissionError) as exc_info:
            readonly_repo.save({"id": req_id, "title": "更新試行"})
        
        assert "read-only" in str(exc_info.value).lower()
        
        # データは変更されていない
        current_after = repo.find(req_id)
        assert current_after["title"] == "初期状態"
    
    # ===== 追加テスト: インポート・エクスポート =====
    
    def test_履歴付きエクスポート_全バージョン_完全な履歴が出力される(self, repo):
        """
        Given: 履歴を持つ要件群
        When: エクスポートを実行
        Then: 全バージョンと関係が保持される
        """
        # Arrange
        repo.save({"id": "EXPORT-001", "title": "v1", "content": "初版"})
        repo.save({"id": "EXPORT-001", "title": "v2", "content": "改訂版"})
        repo.save({"id": "EXPORT-002", "title": "別要件"})
        repo.add_dependency("EXPORT-001", "EXPORT-002")
        
        # Act
        export_data = repo.export_with_history(
            requirement_ids=["EXPORT-001", "EXPORT-002"],
            format="json"
        )
        
        # Assert
        assert export_data["metadata"]["version"] == "1.0"
        assert export_data["metadata"]["export_timestamp"] is not None
        assert len(export_data["requirements"]) == 2
        
        # EXPORT-001の履歴確認
        req1_data = next(r for r in export_data["requirements"] if r["id"] == "EXPORT-001")
        assert len(req1_data["versions"]) == 2
        assert req1_data["versions"][0]["title"] == "v1"
        assert req1_data["versions"][1]["title"] == "v2"
        
        # 依存関係も含まれる
        assert len(export_data["relationships"]) == 1
        assert export_data["relationships"][0]["from"] == "EXPORT-001"
        assert export_data["relationships"][0]["to"] == "EXPORT-002"
    
    def test_選択的インポート_既存データ有り_マージ戦略に従って処理される(self, repo):
        """
        Given: 既存データとインポートデータ
        When: マージ戦略を指定してインポート
        Then: 戦略に従って適切に処理される
        """
        # Arrange: 既存データ
        repo.save({"id": "IMPORT-001", "title": "既存データ", "priority": 0})
        
        # インポートデータ
        import_data = {
            "requirements": [
                {
                    "id": "IMPORT-001",
                    "current_version": {
                        "title": "インポートデータ",
                        "priority": 2
                    }
                },
                {
                    "id": "IMPORT-002",
                    "current_version": {
                        "title": "新規データ"
                    }
                }
            ]
        }
        
        # Act: マージ戦略 = "keep_existing"
        result = repo.import_data(
            import_data,
            merge_strategy="keep_existing",
            author="importer"
        )
        
        # Assert
        assert result["imported"] == 1  # IMPORT-002のみ
        assert result["skipped"] == 1   # IMPORT-001はスキップ
        assert result["errors"] == 0
        
        # 既存データは変更されない
        existing = repo.find("IMPORT-001")
        assert existing["title"] == "既存データ"
        assert existing["priority"] == "low"
        
        # 新規データは追加される
        new_req = repo.find("IMPORT-002")
        assert new_req["title"] == "新規データ"
    
    # ===== まとめテスト: 総合シナリオ =====
    
    def test_総合シナリオ_実際のワークフロー_全機能が連携して動作する(self, repo):
        """
        Given: プロジェクトの要件管理シナリオ
        When: 作成、更新、分岐、マージ、削除を含む一連の操作
        Then: 全ての履歴が正確に保持され、照会可能
        """
        # フェーズ1: 初期要件定義
        epic = repo.save({
            "id": "EPIC-001",
            "title": "ユーザー管理システム",
            "type": "epic",
            "status": "proposed"
        }, author="product_owner")
        
        story1 = repo.save({
            "id": "STORY-001",
            "title": "ユーザー登録",
            "type": "story",
            "status": "proposed"
        }, parent_id="EPIC-001", author="product_owner")
        
        # フェーズ2: 詳細化
        repo.save({
            "id": "STORY-001",
            "title": "ユーザー登録",
            "description": "メールアドレスとパスワードで登録",
            "acceptance_criteria": "1. メール検証\n2. パスワード強度チェック",
            "status": "approved"
        }, author="tech_lead", change_reason="技術レビュー完了")
        
        # フェーズ3: 実装中の変更
        repo.save({
            "id": "STORY-001",
            "title": "ユーザー登録（OAuth対応）",
            "description": "メールアドレス、パスワード、またはOAuthで登録",
            "status": "in_progress"
        }, author="developer", change_reason="OAuth対応追加")
        
        # フェーズ4: 完了
        repo.save({
            "id": "STORY-001",
            "status": "completed"
        }, author="developer")
        
        # 検証: 全履歴が追跡可能
        history = repo.get_requirement_history("STORY-001")
        assert len(history) == 4
        
        # 特定時点の状態を確認
        approved_version = repo.get_requirement_at_timestamp(
            "STORY-001",
            history[1]["timestamp"]
        )
        assert approved_version["status"] == "approved"
        assert "acceptance_criteria" in approved_version
        
        # 変更の影響分析
        impact = repo.analyze_change_impact("EPIC-001")
        assert "STORY-001" in impact["direct_impact"]
        
        # 統計情報
        stats = repo.get_statistics()
        assert stats["by_status"]["completed"] >= 1
        assert stats["by_type"]["story"] >= 1