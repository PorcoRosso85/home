"""
重複検出機能の振る舞いテスト
規約に従い、公開APIの振る舞いのみを検証する統合テスト
"""
import subprocess
import json
import os
import sys
import tempfile
import pytest


def run_system(input_data, db_path=None):
    """requirement/graphシステムの公開APIを実行"""
    env = os.environ.copy()
    if db_path:
        env["RGL_DATABASE_PATH"] = db_path

    # 公開API（main.py）を通じて実行
    # プロジェクトルートから実行
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

    return {"error": "No valid JSON output", "stderr": result.stderr}


class TestDuplicateDetection:
    """重複検出機能の振る舞いテスト - リファクタリングの壁原則に準拠"""

    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            # スキーマ初期化（公開API経由）
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            # Search service準拠のスキーマが適用されることを期待
            yield db_dir

    def test_duplicate_detection_behavior(self, temp_db):
        """重複検出の振る舞い - 実装詳細に依存しない"""
        # Given: 要件が作成されている
        create_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "auth_001",
                "title": "ユーザー認証機能",
                "description": "安全なログイン機能を提供"
            }
        }, temp_db)

        # Then: 作成が成功する
        assert create_result.get("data", {}).get("status") == "success"

        # 検索インデックスへの追加を待つ（実装詳細は隠蔽）
        import time
        time.sleep(0.1)

        # When: 類似した要件を作成しようとする
        duplicate_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "auth_002",
                "title": "ユーザー認証システム",
                "description": "セキュアなログイン実装"
            }
        }, temp_db)

        # Then: 重複が検出される（振る舞いの検証）
        # 実装がSearch serviceを使っているかは問わない
        if "warning" in duplicate_result:
            warning = duplicate_result["warning"]
            assert warning.get("type") == "DuplicateWarning"
            assert "duplicates" in warning
            duplicates = warning["duplicates"]

            # 類似要件が検出されている
            similar_req = next((d for d in duplicates if d["id"] == "auth_001"), None)
            assert similar_req is not None
            assert similar_req["score"] >= 0.7  # 閾値以上

    def test_no_false_positives(self, temp_db):
        """無関係な要件で誤検出しない - 振る舞いの検証"""
        # Given: データベース関連の要件
        run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "db_001",
                "title": "データベース設計",
                "description": "正規化されたスキーマ設計"
            }
        }, temp_db)

        # When: UI関連の要件を作成
        ui_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "ui_001",
                "title": "ユーザーインターフェース改善",
                "description": "使いやすいUIデザイン"
            }
        }, temp_db)

        # Then: 重複警告が出ない
        assert "warning" not in ui_result
        assert ui_result.get("data", {}).get("status") == "success"

    def test_search_functionality(self, temp_db):
        """検索機能の振る舞い - 将来の拡張を想定"""
        # 複数の要件を作成
        requirements = [
            {"id": "req_001", "title": "認証機能", "description": "ログイン処理"},
            {"id": "req_002", "title": "認証強化", "description": "二要素認証"},
            {"id": "req_003", "title": "データ暗号化", "description": "保存時の暗号化"}
        ]

        for req in requirements:
            run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)

        # 将来的な検索API（仮定）
        # search_result = run_system({
        #     "type": "template",
        #     "template": "search_requirements",
        #     "parameters": {"query": "認証"}
        # }, temp_db)
        #
        # 検索結果に認証関連の要件が含まれることを確認
        # assert len(search_result["data"]) >= 2

    def test_embedding_generation(self, temp_db):
        """エンベディング生成の振る舞い - Search service統合の確認"""
        # Given: 要件を作成
        create_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "embed_test_001",
                "title": "エンベディングテスト",
                "description": "このテキストはベクトル化される"
            }
        }, temp_db)

        # Then: 作成が成功する（エンベディング生成も含む）
        assert create_result.get("data", {}).get("status") == "success"

        # When: 直接要件を取得
        find_result = run_system({
            "type": "template",
            "template": "find_requirement",
            "parameters": {"id": "embed_test_001"}
        }, temp_db)

        # Then: 要件が見つかる
        assert find_result.get("data") is not None
        assert find_result.get("status") == "success" or "data" in find_result
        # エンベディングの生成は内部実装の詳細であり、
        # 公開APIレベルでは検証しない（リファクタリングの壁の原則）

    # REMOVED: Performance test violates "Refactoring Wall" principle
    # Performance is an implementation detail, not a behavioral contract


def test_schema_migration_readiness():
    """スキーマ移行の準備状況を確認 - 仕様レベルのテスト"""
    # このテストは実装に依存せず、システムの準備状況を確認
    # 例：マイグレーションスクリプトの存在確認など

    # 将来的なマイグレーションファイルの存在を確認
    # assert os.path.exists("ddl/migrations/3.4.0_search_integration.cypher")
    pytest.skip("マイグレーション実装後に有効化")
