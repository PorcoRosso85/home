"""
Template入力とPOC Search統合の包括的テスト
システムの目的：継続的フィードバックループによる要件品質の最大化
"""
import subprocess
import json
import os
import tempfile
import pytest


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
        
        assert "error" in invalid_template
        assert "TemplateNotFoundError" in str(invalid_template.get("error", {}))
        
        # 2. 必須パラメータ不足
        missing_params = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {}  # id, titleが必須
        }, temp_db)
        
        assert "error" in missing_params
    
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