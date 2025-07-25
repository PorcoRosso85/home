"""
Append-Only History機能のテスト仕様

READMEで約束されている「Git-likeなappend-onlyアーキテクチャ」を検証する。
現在は未実装のため、将来の実装ガイドとしてテスト仕様を定義。

README.mdの約束:
- イミュータブルな要件: 一度作成された要件は削除・更新されず、新しいバージョンが追加される
- 完全な履歴追跡: すべての変更は新しいバージョンとして記録され、過去の状態を完全に再現可能
- データの整合性: 削除や更新による不整合が発生しない
- 監査可能性: いつ、誰が、何を、なぜ変更したかを完全に追跡

これらのテストは、append-only機能が実装された際に有効化される。
"""
import pytest
import tempfile
import os
import sys
import subprocess
import json
from datetime import datetime, timedelta

# プロジェクトルートから実行
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_system(input_data, db_path=None):
    """requirement/graphシステムの公開APIを実行"""
    env = os.environ.copy()
    if db_path:
        env["RGL_DATABASE_PATH"] = db_path

    # 現在のPython（venv内）を使用
    python_cmd = sys.executable

    result = subprocess.run(
        [python_cmd, "-m", "requirement.graph"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
        cwd=project_root
    )

    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    parsed = json.loads(line)
                    # ロギング形式のレスポンスの場合、dataフィールドを返す
                    if parsed.get("type") == "result" and "data" in parsed:
                        return parsed["data"]
                    return parsed
                except json.JSONDecodeError:
                    continue

    return {"error": "No valid JSON output", "stderr": result.stderr}


class TestRequirementImmutability:
    """要件のイミュータビリティ（不変性）を検証する仕様"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            # スキーマ初期化（公開API経由）
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            yield db_dir
    
    def test_requirement_update_creates_new_version(self, temp_db):
        """要件の更新は新しいバージョンを作成する仕様
        
        期待される動作:
        1. 既存の要件を「更新」しようとすると、実際には新しいバージョンが作成される
        2. 元のバージョンは変更されず、完全に保持される
        3. 両方のバージョンが履歴として参照可能
        """
        # Given: スキーマ初期化済みのデータベース
        db_path = temp_db
        
        # When: 要件を作成
        result1 = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_auth_001",
                "title": "ユーザー認証機能",
                "description": "基本的なユーザー認証を実装する",
                "status": "proposed",
                "author": "alice",
                "change_reason": "初期要件定義"
            }
        }, db_path)
        
        assert result1.get("status") == "success", f"Failed to create requirement: {result1}"
        
        # Then: 同じIDで更新を試みた場合、新しいバージョンが作成されるべき
        result2 = run_system({
            "type": "template", 
            "template": "update_requirement",  # または将来的には "create_requirement_version"
            "parameters": {
                "id": "req_auth_001",
                "title": "ユーザー認証機能（改訂版）",
                "description": "二要素認証を含む高度なユーザー認証を実装する",
                "status": "active",
                "author": "bob",
                "change_reason": "セキュリティ要件の強化"
            }
        }, db_path)
        
        # 期待される結果:
        # - 新しいバージョン（例: req_auth_001_v2）が作成される
        # - 元のバージョン（req_auth_001_v1）は変更されない
        # - 両方のバージョンが履歴として存在する
        
        # template_processor.pyからの実際のレスポンス構造に合わせて修正
        assert result2.get("status") == "success", f"Update should create new version: {result2}"
        assert result2.get("data", {}).get("version_id") == "req_auth_001_v2", "Should return new version ID"
        assert result2.get("data", {}).get("previous_version") == "req_auth_001", "Should reference previous version"
        
        # 両方のバージョンが存在することを確認
        # 元のバージョンを確認（バージョン番号なしのオリジナル）
        original_check = run_system({
            "type": "template",
            "template": "find_requirement",
            "parameters": {
                "id": "req_auth_001"
            }
        }, db_path)
        
        assert original_check.get("status") == "success", "Original should still exist"
        assert original_check.get("data")[0][1] == "ユーザー認証機能", "Original title should be unchanged"
        assert original_check.get("data")[0][3] == "proposed", "Original status should be unchanged"
        
        # 新しいバージョンを確認
        new_check = run_system({
            "type": "template",
            "template": "find_requirement",
            "parameters": {
                "id": "req_auth_001_v2"
            }
        }, db_path)
        
        assert new_check.get("status") == "success", "New version should exist"
        assert new_check.get("data")[0][1] == "ユーザー認証機能（改訂版）", "New version should have updated title"
        assert new_check.get("data")[0][3] == "active", "New version should have updated status"
    
    def test_requirement_deletion_is_soft_delete(self, temp_db):
        """要件の削除は論理削除（ソフトデリート）として実装される仕様
        
        期待される動作:
        1. 要件を削除しても、実際にはデータは削除されない
        2. 削除フラグまたは削除バージョンが作成される
        3. 削除された要件も履歴として完全に追跡可能
        """
        # Given: 要件が作成済み
        db_path = temp_db
        
        result1 = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_temp_001",
                "title": "一時的な要件",
                "description": "後で削除される要件",
                "status": "active"
            }
        }, db_path)
        
        # When: 要件を削除
        result2 = run_system({
            "type": "template",
            "template": "delete_requirement",
            "parameters": {
                "id": "req_temp_001",
                "author": "alice",
                "change_reason": "要件の見直しにより不要と判断"
            }
        }, db_path)
        
        # Then: 将来実装では、削除は新しいバージョンとして記録される
        # expected_behavior:
        # - 新しいバージョンが作成される（operation: "DELETE"）
        # - 要件のstatusが "deleted" に変更される
        # - 元のデータは保持され、履歴から参照可能
        # - 通常のクエリでは削除された要件は表示されない（フィルタリング）
        
        pytest.skip("Soft delete not yet implemented - feature planned for future release")


class TestCompleteHistoryTracking:
    """完全な履歴追跡機能を検証する仕様"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            yield db_dir
    
    def test_complete_requirement_history_retrieval(self, temp_db):
        """要件の完全な変更履歴を取得する仕様
        
        期待される動作:
        1. 要件のすべてのバージョンを時系列で取得できる
        2. 各バージョンには作成者、変更理由、タイムスタンプが含まれる
        3. バージョン間の差分も確認可能
        """
        # Given: 複数のバージョンを持つ要件
        db_path = temp_db
        
        # 初期作成
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_evolving_001",
                "title": "進化する要件",
                "description": "最初のバージョン",
                "status": "proposed",
                "author": "alice",
                "change_reason": "初期提案"
            }
        }, db_path)
        
        # バージョン2（タイトル変更）
        run_system({
            "type": "template",
            "template": "update_requirement",
            "parameters": {
                "id": "req_evolving_001",
                "title": "進化する要件（改善版）",
                "description": "最初のバージョン",
                "status": "active", 
                "author": "bob",
                "change_reason": "タイトルをより明確に"
            }
        }, db_path)
        
        # バージョン3（説明追加）
        run_system({
            "type": "template",
            "template": "update_requirement",
            "parameters": {
                "id": "req_evolving_001",
                "title": "進化する要件（改善版）",
                "description": "詳細な説明を追加：この要件は継続的な改善を目的とする",
                "status": "active",
                "author": "charlie",
                "change_reason": "詳細説明の追加"
            }
        }, db_path)
        
        # When: 履歴を取得
        result = run_system({
            "type": "template",
            "template": "get_requirement_history",
            "parameters": {
                "id": "req_evolving_001"
            }
        }, db_path)
        
        # Then: 期待される履歴データ
        # expected_history = {
        #     "data": {
        #         "requirement_id": "req_evolving_001",
        #         "current_version": "v3",
        #         "total_versions": 3,
        #         "history": [
        #             {
        #                 "version": "v1",
        #                 "timestamp": "2025-07-24T10:00:00Z",
        #                 "author": "alice",
        #                 "operation": "CREATE",
        #                 "change_reason": "初期提案",
        #                 "title": "進化する要件",
        #                 "description": "最初のバージョン",
        #                 "status": "proposed"
        #             },
        #             {
        #                 "version": "v2",
        #                 "timestamp": "2025-07-24T11:00:00Z",
        #                 "author": "bob",
        #                 "operation": "UPDATE",
        #                 "change_reason": "タイトルをより明確に",
        #                 "title": "進化する要件（改善版）",
        #                 "changes": ["title", "status"]
        #             },
        #             {
        #                 "version": "v3",
        #                 "timestamp": "2025-07-24T12:00:00Z",
        #                 "author": "charlie",
        #                 "operation": "UPDATE",
        #                 "change_reason": "詳細説明の追加",
        #                 "description": "詳細な説明を追加：この要件は継続的な改善を目的とする",
        #                 "changes": ["description"]
        #             }
        #         ]
        #     }
        # }
        
        pytest.skip("Complete history tracking not yet implemented - feature planned for future release")
    
    def test_point_in_time_query(self, temp_db):
        """特定時点の状態を再現する仕様
        
        期待される動作:
        1. 任意の過去の時点を指定して、その時点の要件グラフ全体を再現できる
        2. 特定バージョンの要件とその依存関係を正確に取得
        3. タイムトラベル機能により過去の意思決定を検証可能
        """
        # Given: 時間経過とともに変化する要件グラフ
        db_path = temp_db
        base_time = datetime.now()
        
        # 時点1: 初期要件作成
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_base_001",
                "title": "基本要件",
                "timestamp": base_time.isoformat()
            }
        }, db_path)
        
        # 時点2: 依存要件追加（1時間後）
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_dependent_001",
                "title": "依存要件",
                "timestamp": (base_time + timedelta(hours=1)).isoformat()
            }
        }, db_path)
        
        run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "req_dependent_001",
                "parent_id": "req_base_001",
                "timestamp": (base_time + timedelta(hours=1)).isoformat()
            }
        }, db_path)
        
        # 時点3: 基本要件を更新（2時間後）
        run_system({
            "type": "template",
            "template": "update_requirement",
            "parameters": {
                "id": "req_base_001",
                "title": "基本要件（更新版）",
                "timestamp": (base_time + timedelta(hours=2)).isoformat()
            }
        }, db_path)
        
        # When: 各時点の状態を照会
        # 時点1の状態（基本要件のみ）
        result_t1 = run_system({
            "type": "template",
            "template": "get_graph_at_timestamp",
            "parameters": {
                "timestamp": (base_time + timedelta(minutes=30)).isoformat()
            }
        }, db_path)
        
        # 時点2の状態（依存関係あり、更新前）
        result_t2 = run_system({
            "type": "template",
            "template": "get_graph_at_timestamp", 
            "parameters": {
                "timestamp": (base_time + timedelta(hours=1, minutes=30)).isoformat()
            }
        }, db_path)
        
        # Then: 各時点で異なる状態が再現される
        # expected_t1: req_base_001のみ存在、タイトルは「基本要件」
        # expected_t2: req_base_001とreq_dependent_001が存在、依存関係あり、タイトルは「基本要件」
        # current: すべて存在、req_base_001のタイトルは「基本要件（更新版）」
        
        pytest.skip("Point-in-time queries not yet implemented - feature planned for future release")


class TestAuditTrail:
    """監査証跡（Audit Trail）機能を検証する仕様"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            yield db_dir
    
    def test_complete_audit_trail(self, temp_db):
        """完全な監査証跡を記録・取得する仕様
        
        期待される動作:
        1. すべての操作（作成、更新、削除）に対して以下を記録:
           - いつ（タイムスタンプ）
           - 誰が（作成者/更新者）
           - 何を（変更内容）
           - なぜ（変更理由）
        2. 監査ログは改ざん不可能（append-only）
        3. コンプライアンス要件を満たす詳細な記録
        """
        # Given: 様々な操作を含む要件の変更
        db_path = temp_db
        
        # 一連の操作を実行
        operations = [
            {
                "type": "template",
                "template": "create_requirement",
                "parameters": {
                    "id": "req_audit_001",
                    "title": "監査対象要件",
                    "description": "コンプライアンステスト用",
                    "author": "alice",
                    "change_reason": "新規プロジェクト開始",
                    "timestamp": "2025-07-24T10:00:00Z"
                }
            },
            {
                "type": "template",
                "template": "update_requirement",
                "parameters": {
                    "id": "req_audit_001",
                    "status": "active",
                    "author": "bob",
                    "change_reason": "レビュー完了により承認",
                    "timestamp": "2025-07-24T14:00:00Z"
                }
            },
            {
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": "req_audit_001",
                    "parent_id": "req_base_system",
                    "author": "charlie",
                    "change_reason": "基本システムへの依存を明確化",
                    "timestamp": "2025-07-24T15:00:00Z"
                }
            }
        ]
        
        for op in operations:
            run_system(op, db_path)
        
        # When: 監査証跡を取得
        result = run_system({
            "type": "template",
            "template": "get_audit_trail",
            "parameters": {
                "entity_type": "requirement",
                "entity_id": "req_audit_001",
                "include_related": True  # 関連する操作（依存関係など）も含む
            }
        }, db_path)
        
        # Then: 期待される監査証跡
        # expected_audit_trail = {
        #     "data": {
        #         "entity_id": "req_audit_001",
        #         "audit_entries": [
        #             {
        #                 "timestamp": "2025-07-24T10:00:00Z",
        #                 "author": "alice",
        #                 "operation": "CREATE",
        #                 "entity_type": "requirement",
        #                 "change_reason": "新規プロジェクト開始",
        #                 "details": {
        #                     "title": "監査対象要件",
        #                     "description": "コンプライアンステスト用"
        #                 }
        #             },
        #             {
        #                 "timestamp": "2025-07-24T14:00:00Z",
        #                 "author": "bob",
        #                 "operation": "UPDATE",
        #                 "entity_type": "requirement",
        #                 "change_reason": "レビュー完了により承認",
        #                 "changes": {
        #                     "status": {"from": "proposed", "to": "active"}
        #                 }
        #             },
        #             {
        #                 "timestamp": "2025-07-24T15:00:00Z",
        #                 "author": "charlie",
        #                 "operation": "ADD_DEPENDENCY",
        #                 "entity_type": "relationship",
        #                 "change_reason": "基本システムへの依存を明確化",
        #                 "details": {
        #                     "relationship_type": "DEPENDS_ON",
        #                     "from": "req_audit_001",
        #                     "to": "req_base_system"
        #                 }
        #             }
        #         ]
        #     }
        # }
        
        pytest.skip("Audit trail functionality not yet implemented - feature planned for future release")
    
    def test_audit_trail_immutability(self, temp_db):
        """監査証跡の不変性を検証する仕様
        
        期待される動作:
        1. 一度記録された監査証跡は変更・削除不可能
        2. 監査証跡の改ざん試行は検出される
        3. 監査証跡自体もバージョン管理される
        """
        # Given: 監査証跡が存在する
        db_path = temp_db
        
        # 要件を作成（監査証跡が生成される）
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_immutable_001",
                "title": "不変性テスト要件",
                "author": "alice",
                "change_reason": "監査証跡テスト"
            }
        }, db_path)
        
        # When: 監査証跡を改ざんしようとする
        # 注: 実際のシステムではこのような直接的な改ざんAPIは存在しないはず
        result = run_system({
            "type": "cypher",
            "query": "MATCH (v:VersionState) WHERE v.change_reason = '監査証跡テスト' SET v.author = 'eve'"
        }, db_path)
        
        # Then: 期待される動作
        # - 改ざん試行は失敗する（エラー）
        # - または、改ざん試行自体が新しい監査証跡として記録される
        # - 元の監査証跡は変更されない
        
        pytest.skip("Audit trail immutability not yet implemented - feature planned for future release")


class TestVersionComparison:
    """バージョン比較機能を検証する仕様"""
    
    @pytest.fixture  
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            yield db_dir
    
    def test_version_diff_generation(self, temp_db):
        """バージョン間の差分を生成する仕様
        
        期待される動作:
        1. 任意の2つのバージョン間の差分を取得できる
        2. 追加・変更・削除された属性が明確に表示される
        3. 構造的な差分（依存関係の変化など）も含まれる
        """
        # Given: 複数バージョンの要件
        db_path = temp_db
        
        # v1: 初期バージョン
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_diff_001",
                "title": "差分テスト要件",
                "description": "初期バージョン",
                "status": "proposed",
                "priority": "medium"
            }
        }, db_path)
        
        # v2: 複数の変更
        run_system({
            "type": "template",
            "template": "update_requirement",
            "parameters": {
                "id": "req_diff_001",
                "title": "差分テスト要件（改訂版）",  # 変更
                "description": "詳細な説明を追加",      # 変更
                "status": "active",                   # 変更
                "priority": "high",                   # 変更
                "tags": ["security", "performance"]   # 追加
            }
        }, db_path)
        
        # When: バージョン間の差分を取得
        result = run_system({
            "type": "template",
            "template": "get_version_diff",
            "parameters": {
                "requirement_id": "req_diff_001",
                "from_version": "v1",
                "to_version": "v2"
            }
        }, db_path)
        
        # Then: 期待される差分情報
        # expected_diff = {
        #     "data": {
        #         "requirement_id": "req_diff_001",
        #         "from_version": "v1",
        #         "to_version": "v2",
        #         "changes": {
        #             "modified": {
        #                 "title": {
        #                     "old": "差分テスト要件",
        #                     "new": "差分テスト要件（改訂版）"
        #                 },
        #                 "description": {
        #                     "old": "初期バージョン",
        #                     "new": "詳細な説明を追加"
        #                 },
        #                 "status": {
        #                     "old": "proposed",
        #                     "new": "active"
        #                 },
        #                 "priority": {
        #                     "old": "medium",
        #                     "new": "high"
        #                 }
        #             },
        #             "added": {
        #                 "tags": ["security", "performance"]
        #             },
        #             "removed": {}
        #         },
        #         "summary": "4 fields modified, 1 field added"
        #     }
        # }
        
        pytest.skip("Version comparison not yet implemented - feature planned for future release")
    
    def test_rollback_to_previous_version(self, temp_db):
        """以前のバージョンへのロールバック仕様
        
        期待される動作:
        1. 任意の過去バージョンに「ロールバック」できる
        2. ロールバックは新しいバージョンとして記録される（履歴は保持）
        3. ロールバックの理由も記録される
        """
        # Given: 問題のあるバージョンが作成された
        db_path = temp_db
        
        # v1: 正常なバージョン
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_rollback_001",
                "title": "ロールバックテスト要件",
                "description": "正常な初期バージョン",
                "status": "active"
            }
        }, db_path)
        
        # v2: 問題のあるバージョン
        run_system({
            "type": "template",
            "template": "update_requirement",
            "parameters": {
                "id": "req_rollback_001",
                "title": "間違った変更",
                "description": "誤った要件内容",
                "status": "deprecated"  # 誤ったステータス
            }
        }, db_path)
        
        # When: v1にロールバック
        result = run_system({
            "type": "template",
            "template": "rollback_requirement",
            "parameters": {
                "requirement_id": "req_rollback_001",
                "target_version": "v1",
                "author": "alice",
                "change_reason": "v2の変更は誤りだったため、v1の内容に戻す"
            }
        }, db_path)
        
        # Then: 期待される結果
        # - 新しいバージョン（v3）が作成される
        # - v3の内容はv1と同じ
        # - v2は履歴として残る
        # - ロールバック操作も監査証跡に記録される
        
        # expected_result = {
        #     "data": {
        #         "status": "success",
        #         "new_version": "v3",
        #         "rolled_back_from": "v2",
        #         "rolled_back_to": "v1",
        #         "message": "Successfully rolled back to version v1"
        #     }
        # }
        
        pytest.skip("Version rollback not yet implemented - feature planned for future release")


def test_append_only_architecture_spec():
    """Append-Onlyアーキテクチャの将来仕様を文書化するテスト"""
    # このテストは、将来実装されるappend-only機能の期待される動作を記述
    
    expected_features = [
        {
            "feature": "Immutable Requirements",
            "description": "要件は一度作成されたら変更不可、新バージョンのみ追加",
            "benefits": ["データ整合性", "履歴の完全性", "監査可能性"]
        },
        {
            "feature": "Complete History Tracking",
            "description": "すべての変更を完全に追跡、任意時点の再現が可能",
            "benefits": ["意思決定の透明性", "問題の原因追跡", "コンプライアンス対応"]
        },
        {
            "feature": "Audit Trail",
            "description": "いつ、誰が、何を、なぜ変更したかを永続的に記録",
            "benefits": ["説明責任", "規制要件対応", "セキュリティ監査"]
        },
        {
            "feature": "Version Comparison",
            "description": "バージョン間の差分表示とロールバック機能",
            "benefits": ["変更の可視化", "誤った変更の修正", "レビュープロセス支援"]
        },
        {
            "feature": "Soft Delete",
            "description": "削除操作も新バージョンとして記録、データは保持",
            "benefits": ["誤削除の回復", "削除履歴の追跡", "完全なデータライフサイクル管理"]
        }
    ]
    
    # 将来の実装で、これらの機能が提供されることを期待
    assert len(expected_features) == 5
    
    # 現時点では仕様の文書化のみ
    pytest.skip("Append-only architecture features documented for future implementation")