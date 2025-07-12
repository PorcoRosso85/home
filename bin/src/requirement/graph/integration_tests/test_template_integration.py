"""
Template入力とPOC Search統合の包括的テスト
システムの目的：継続的フィードバックループによる要件品質の最大化
"""
import subprocess
import json
import os
import tempfile
import pytest
from typing import List, Tuple, Any
import random
import string


def run_command(input_data, db_path):
    """requirement/graphシステムを実行"""
    env = os.environ.copy()
    env["RGL_DATABASE_PATH"] = db_path
    env["PYTHONPATH"] = "/home/nixos/bin/src"
    
    result = subprocess.run(
        ["uv", "run", "python", "run.py"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.stdout:
        # 複数行のJSONL出力から最後の有効なJSONを取得
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    
    return {"error": "No valid JSON output", "stderr": result.stderr}


class TestTemplateIntegration:
    """Template入力の統合テスト - システムの振る舞いを検証"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベースディレクトリを提供"""
        with tempfile.TemporaryDirectory() as db_dir:
            # スキーマ初期化
            result = run_command({"type": "schema", "action": "apply"}, db_dir)
            assert result.get("status") == "success" or result.get("data", {}).get("status") == "success"
            yield db_dir
    
    def test_requirement_lifecycle_with_feedback(self, temp_db):
        """要件のライフサイクル全体とフィードバックループを検証"""
        
        # 1. 要件作成
        create_result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_001",
                "title": "ユーザー認証機能",
                "description": "ログイン・ログアウト機能の実装"
            }
        }, temp_db)
        
        assert create_result.get("data", {}).get("status") == "success"
        
        # 2. 類似要件作成時の重複検出フィードバック
        duplicate_result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_002",
                "title": "ユーザー認証システム",  # 類似タイトル
                "description": "セキュアなログイン機能"
            }
        }, temp_db)
        
        # 重複警告の確認（POC searchが統合されていれば）
        # 現状ではデータがないため警告は出ないが、構造は確認
        assert "error" not in duplicate_result
        
        # 3. 依存関係の追加
        dependency_result = run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "req_002",
                "parent_id": "req_001"
            }
        }, temp_db)
        
        assert dependency_result.get("data", {}).get("status") == "success"
        
        # 4. 循環依存の検出（フィードバックループの検証）
        circular_result = run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "req_001",
                "parent_id": "req_002"  # これで循環が発生
            }
        }, temp_db)
        
        # 循環依存のエラーフィードバックを期待
        assert "error" in circular_result or circular_result.get("data", {}).get("status") != "success"
        
        # 5. 要件の検索
        search_result = run_command({
            "type": "template",
            "template": "find_requirement",
            "parameters": {"id": "req_001"}
        }, temp_db)
        
        assert search_result.get("data", {}).get("status") == "success"
        
        # 6. 要件の更新
        update_result = run_command({
            "type": "template",
            "template": "update_requirement",
            "parameters": {
                "id": "req_001",
                "status": "implemented"
            }
        }, temp_db)
        
        assert update_result.get("data", {}).get("status") == "success"
    
    def test_template_validation_feedback(self, temp_db):
        """テンプレート検証のフィードバックを確認"""
        
        # 1. 無効なテンプレート名
        invalid_template = run_command({
            "type": "template",
            "template": "invalid_template_name",
            "parameters": {}
        }, temp_db)
        
        assert "error" in invalid_template or "error" in invalid_template.get("data", {})
        error_data = invalid_template.get("error") or invalid_template.get("data", {}).get("error", {})
        assert "TemplateNotFoundError" in str(error_data)
        
        # 2. 必須パラメータ不足
        missing_params = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {}  # id, titleが必須
        }, temp_db)
        
        assert "error" in missing_params or "error" in missing_params.get("data", {})
    
    @pytest.mark.skip(reason="パフォーマンス改善が必要")
    def test_depth_limit_feedback(self, temp_db):
        """深さ制限のフィードバックを確認"""
        
        # 深い依存関係チェーンの作成
        requirements = []
        for i in range(10):
            req_id = f"req_depth_{i}"
            requirements.append(req_id)
            
            # 要件作成
            result = run_command({
                "type": "template",
                "template": "create_requirement",
                "parameters": {
                    "id": req_id,
                    "title": f"要件 レベル{i}",
                    "description": f"深さ{i}の要件"
                }
            }, temp_db)
            
            assert result.get("data", {}).get("status") == "success"
            
            # 前の要件への依存関係を追加（チェーンを作る）
            if i > 0:
                dep_result = run_command({
                    "type": "template",
                    "template": "add_dependency",
                    "parameters": {
                        "child_id": req_id,
                        "parent_id": requirements[i-1]
                    }
                }, temp_db)
                
                # 深さ制限に達した場合のフィードバックを確認
                if i >= 5:  # 仮定：深さ制限が5
                    # エラーまたは警告が期待される
                    pass
    
    @pytest.mark.skip(reason="パフォーマンス改善が必要 - 7つのsubprocessが遅い")
    def test_template_scenarios_table_driven(self, temp_db):
        """テーブル駆動テスト(TDT) - 具体的なシナリオを網羅的に検証"""
        
        # テストケース: (template, parameters, expected_status, description)
        test_cases: List[Tuple[str, dict, str, str]] = [
            # 正常系
            ("create_requirement", 
             {"id": "req_tdt_001", "title": "認証機能"}, 
             "success", 
             "最小限の正常ケース"),
            
            ("create_requirement", 
             {"id": "req_tdt_002", "title": "ログイン", "description": "詳細な説明", "status": "proposed"}, 
             "success", 
             "全パラメータ指定"),
            
            # 異常系
            ("create_requirement", 
             {"id": "req_tdt_003"}, 
             "error", 
             "必須パラメータ(title)不足"),
            
            ("create_requirement", 
             {"title": "タイトルのみ"}, 
             "error", 
             "必須パラメータ(id)不足"),
            
            ("unknown_template", 
             {"id": "test"}, 
             "error", 
             "存在しないテンプレート"),
            
            # 依存関係
            ("add_dependency",
             {"child_id": "req_tdt_001", "parent_id": "req_tdt_002"},
             "success",
             "正常な依存関係追加"),
            
            ("add_dependency",
             {"child_id": "req_tdt_001"},
             "error",
             "parent_id不足"),
        ]
        
        for template, params, expected_status, description in test_cases:
            result = run_command({
                "type": "template",
                "template": template,
                "parameters": params
            }, temp_db)
            
            if expected_status == "success":
                assert result.get("data", {}).get("status") == "success", f"Failed: {description}"
            else:
                assert "error" in result or result.get("data", {}).get("status") != "success", f"Failed: {description}"
    
    @pytest.mark.skip(reason="conventionsに従い将来的に採用, skip解除は許可が必要")
    def test_circular_dependency_property_based(self, temp_db):
        """プロパティベーステスト(PBT) - 循環依存は必ず検出される不変条件を検証"""
        
        # ランダムな要件グラフを生成してテスト
        for trial in range(5):  # 5回の試行
            requirements = []
            
            # ランダムな数の要件を作成 (3-8個)
            num_requirements = random.randint(3, 8)
            
            # 要件を作成
            for i in range(num_requirements):
                req_id = f"req_pbt_{trial}_{i}"
                requirements.append(req_id)
                
                result = run_command({
                    "type": "template",
                    "template": "create_requirement",
                    "parameters": {
                        "id": req_id,
                        "title": f"PBT要件{i}"
                    }
                }, temp_db)
                
                assert result.get("data", {}).get("status") == "success"
            
            # ランダムに依存関係を追加（ただし循環を作らない）
            for i in range(1, num_requirements):
                parent_idx = random.randint(0, i-1)
                
                result = run_command({
                    "type": "template",
                    "template": "add_dependency",
                    "parameters": {
                        "child_id": requirements[i],
                        "parent_id": requirements[parent_idx]
                    }
                }, temp_db)
                
                assert result.get("data", {}).get("status") == "success"
            
            # 意図的に循環を作成
            cycle_start = random.randint(0, num_requirements-2)
            cycle_end = random.randint(cycle_start+1, num_requirements-1)
            
            circular_result = run_command({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": requirements[cycle_start],
                    "parent_id": requirements[cycle_end]
                }
            }, temp_db)
            
            # プロパティ：どんな循環も必ず検出される
            assert "error" in circular_result or circular_result.get("data", {}).get("status") != "success", \
                f"循環依存が検出されませんでした: {requirements[cycle_start]} -> {requirements[cycle_end]}"
    
    @pytest.mark.skip(reason="conventionsに従い将来的に採用, skip解除は許可が必要")
    def test_search_score_property(self, temp_db):
        """プロパティベーステスト(PBT) - POC searchスコアは常に0.0-1.0の範囲"""
        
        # ランダムなテキストで要件を作成
        for i in range(10):
            random_text = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=random.randint(10, 50)))
            
            result = run_command({
                "type": "template",
                "template": "create_requirement",
                "parameters": {
                    "id": f"req_score_{i}",
                    "title": random_text,
                    "description": f"Description: {random_text}"
                }
            }, temp_db)
            
            # POC searchが統合されていれば、スコアが返される可能性がある
            if "duplicates" in result.get("data", {}):
                duplicates = result["data"]["duplicates"]
                for dup in duplicates:
                    score = dup.get("score", 0.0)
                    # プロパティ：スコアは必ず0.0-1.0の範囲
                    assert 0.0 <= score <= 1.0, f"スコアが範囲外: {score}"
    
    @pytest.mark.skip(reason="conventionsに従い将来的に採用, skip解除は許可が必要")
    def test_feedback_snapshot(self, temp_db):
        """スナップショットテスト(SST) - エラーメッセージの形式を検証"""
        
        # 様々なエラーケースのスナップショット
        error_cases = [
            {
                "input": {
                    "type": "template",
                    "template": "invalid_template",
                    "parameters": {}
                },
                "expected_error_type": "TemplateNotFoundError",
                "description": "無効なテンプレート名"
            },
            {
                "input": {
                    "type": "template",
                    "template": "create_requirement",
                    "parameters": {}
                },
                "expected_error_type": "MissingParameterError",
                "description": "必須パラメータ不足"
            },
            {
                "input": {
                    "type": "invalid_type",
                    "query": "test"
                },
                "expected_error_type": "InvalidInputTypeError",
                "description": "無効な入力タイプ"
            }
        ]
        
        snapshots = []
        
        for case in error_cases:
            result = run_command(case["input"], temp_db)
            
            # エラー応答の構造を記録（スナップショット）
            # エラーは直接またはdata内にある可能性がある
            has_direct_error = "error" in result
            has_nested_error = "error" in result.get("data", {})
            error_obj = result.get("error") or result.get("data", {}).get("error", {})
            
            snapshot = {
                "description": case["description"],
                "has_error": has_direct_error or has_nested_error,
                "error_keys": sorted(error_obj.keys()) if isinstance(error_obj, dict) else [],
                "has_timestamp": "timestamp" in result,
                "has_type": "type" in result,
                "result": result  # デバッグ用
            }
            
            snapshots.append(snapshot)
        
        # スナップショット検証：エラー応答は一貫した構造を持つ
        for snapshot in snapshots:
            assert snapshot["has_error"], f"{snapshot['description']}でエラーが返されませんでした: {snapshot['result']}"
            assert snapshot["has_timestamp"] or snapshot["has_type"], f"{snapshot['description']}で基本構造がありません"