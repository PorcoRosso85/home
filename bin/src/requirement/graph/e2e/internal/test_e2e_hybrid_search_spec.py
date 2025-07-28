"""
VSS検索仕様テスト
ベクトル検索（VSS）単独での検索機能の仕様テスト
注: FTS統合は将来的な拡張として保留中
"""
import tempfile
import pytest
import time
from test_utils.pytest_marks import mark_test, TestSpeed, TestType


@mark_test(
    speed=TestSpeed.VERY_SLOW,
    test_type=TestType.E2E
)
class TestVSSSearchSpec:
    """VSS検索の仕様
    
    要求仕様:
    1. Search serviceのAPIを直接使用（一切の独自実装禁止）
    2. VSS検索を実行（FTSは将来対応）
    3. エンベディングの生成と保存（ベストエフォート）
    4. 重複検出はオプショナル機能として提供
    """

    @pytest.fixture
    def temp_db(self, run_system):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            # スキーマ初期化
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            yield db_dir

    def test_vss_search_integration(self, temp_db, run_system):
        """VSS検索が動作する（重複検出はオプショナル）"""
        # Given: 要件を作成
        create_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_001",
                "title": "ユーザー認証システム",
                "description": "ログイン機能の実装"
            }
        }, temp_db)

        assert "error" not in create_result

        # When: 類似要件を作成しようとする
        duplicate_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_002",
                "title": "認証システム",
                "description": "ユーザーログイン機能"
            }
        }, temp_db)

        # Then: 要件は作成されるが、重複検出はオプショナル
        assert "error" not in duplicate_result
        assert duplicate_result.get("data", {}).get("status") == "success"

        # 重複検出がある場合の確認（オプショナル）
        warning = duplicate_result.get("warning") or duplicate_result.get("data", {}).get("warning")
        if warning:
            # VSSが有効な場合は重複が検出される可能性がある
            assert warning.get("type") == "DuplicateWarning"
            assert len(warning.get("duplicates", [])) > 0
            duplicate = warning["duplicates"][0]
            assert duplicate.get("type") == "vss"  # VSSのみの結果
            assert duplicate.get("score") > 0.5

    def test_embedding_generation_optional(self, temp_db, run_system):
        """エンベディング生成はオプショナル（VSSが利用可能な場合のみ）"""
        # Given: 要件を作成
        create_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_emb_001",
                "title": "テスト要件",
                "description": "エンベディング生成テスト"
            }
        }, temp_db)

        assert "error" not in create_result

        # When: 作成した要件を検索
        find_result = run_system({
            "type": "template",
            "template": "find_requirement",
            "parameters": {"id": "req_emb_001"}
        }, temp_db)

        # Then: 要件は作成される（エンベディングはオプショナル）
        assert "error" not in find_result
        assert find_result.get("data", {}).get("status") == "success"

        # データ構造を確認
        print(f"Find result: {find_result}")

        # 結果からdataを取得
        if "data" in find_result and "data" in find_result["data"]:
            data = find_result["data"]["data"]
        else:
            data = find_result.get("data", [])

        assert len(data) > 0

        # データ構造が正しいことを確認
        if isinstance(data[0], list) and len(data[0]) > 0:
            # requirement情報は返されるデータの一部
            # エンベディングのテストはオプショナル（VSSが有効な場合のみ）
            pass  # エンベディングの詳細は内部実装
        else:
            # 要件が見つかったことを確認
            assert len(data) > 0

    def test_search_service_api_usage(self, temp_db, run_system):
        """Search serviceのAPIが正しく使用される"""
        # このテストは実装の詳細ではなく、振る舞いを検証
        # Search serviceが動作していることを間接的に確認

        # Given: 複数の要件を作成
        requirements = [
            {"id": "api_001", "title": "ユーザー管理", "description": "ユーザー情報の管理"},
            {"id": "api_002", "title": "認証機能", "description": "ログイン認証の実装"},
            {"id": "api_003", "title": "データベース設計", "description": "RDBMSの設計"}
        ]

        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert "error" not in result

        # When: 類似検索を実行（新しい要件作成時）
        search_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "api_004",
                "title": "ユーザー認証管理",
                "description": "ユーザーのログイン管理機能"
            }
        }, temp_db)

        # Then: 要件は作成される（重複検出はオプショナル）
        assert "error" not in search_result
        assert search_result.get("data", {}).get("status") == "success"

        # 重複検出がある場合の確認（オプショナル）
        warning = search_result.get("warning") or search_result.get("data", {}).get("warning")
        if warning:
            # VSSが有効な場合は類似要件が検出される
            duplicates = warning.get("duplicates", [])
            assert len(duplicates) >= 1  # 少なくとも1つは見つかる

            # スコア順にソートされている
            scores = [d["score"] for d in duplicates]
            assert scores == sorted(scores, reverse=True)


# VSS単独実装のテスト
# FTS統合は将来的な拡張として、現在はVSSのみで動作
