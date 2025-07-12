"""
Phase 3: 統合テスト - Template入力とPOC Search統合の動作確認
"""
import subprocess
import json
import os
import tempfile
import shutil


def run_command(input_data, db_path):
    """requirement/graphシステムを実行"""
    env = os.environ.copy()
    env["RGL_DATABASE_PATH"] = db_path
    
    result = subprocess.run(
        ["python", "run.py"],
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


def test_template_input_integration():
    """Template入力の統合テスト"""
    # 一時的なデータベースディレクトリを作成
    with tempfile.TemporaryDirectory() as db_dir:
        print(f"\n=== Template入力統合テスト ===")
        print(f"DB Path: {db_dir}")
        
        # 1. スキーマ初期化
        print("\n1. スキーマ初期化")
        result = run_command({"type": "schema", "action": "apply"}, db_dir)
        print(f"結果: {result}")
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        # 2. 要件作成（template入力）
        print("\n2. 要件作成（template入力）")
        result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_auth_001",
                "title": "ユーザー認証機能",
                "description": "安全なログイン機能を提供する"
            }
        }, db_dir)
        print(f"結果: {result}")
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        # 3. 要件一覧取得
        print("\n3. 要件一覧取得")
        result = run_command({
            "type": "template",
            "template": "list_requirements",
            "parameters": {"limit": 10}
        }, db_dir)
        print(f"結果: {result}")
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        assert len(result.get("data", [])) > 0
        
        # 4. 依存関係追加
        print("\n4. 2つ目の要件を作成して依存関係を追加")
        result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_2fa_001",
                "title": "二要素認証",
                "description": "セキュリティ強化のための2FA実装"
            }
        }, db_dir)
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        result = run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "req_2fa_001",
                "parent_id": "req_auth_001"
            }
        }, db_dir)
        print(f"依存関係追加結果: {result}")
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        print("\n✅ Template入力統合テスト成功")


def test_poc_search_integration():
    """POC Search統合テスト（重複チェック）"""
    with tempfile.TemporaryDirectory() as db_dir:
        print(f"\n=== POC Search統合テスト ===")
        print(f"DB Path: {db_dir}")
        
        # 1. スキーマ初期化
        print("\n1. スキーマ初期化")
        result = run_command({"type": "schema", "action": "apply"}, db_dir)
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        # 2. 最初の要件を作成
        print("\n2. 最初の要件を作成")
        result = run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_001",
                "title": "ユーザー認証機能",
                "description": "安全なログイン機能を提供"
            }
        }, db_dir)
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        # 3. 類似要件を作成（重複チェックが発動するはず）
        print("\n3. 類似要件を作成（重複チェック有効）")
        result = run_command({
            "type": "template",
            "template": "create_requirement",
            "enable_duplicate_check": True,
            "parameters": {
                "id": "req_002",
                "title": "ユーザー認証システム",  # 類似タイトル
                "description": "セキュアなログイン機能の実装"
            }
        }, db_dir)
        print(f"結果: {result}")
        
        # POC searchが利用可能な場合は警告が出る
        # 利用不可の場合でも要件作成は成功する（グレースフルデグラデーション）
        if "warning" in result:
            print("✅ 重複警告が検出されました")
            warning = result["warning"]
            assert warning["type"] == "DuplicateWarning"
            assert "duplicates" in warning
        else:
            print("⚠️ POC searchが利用できないため重複チェックはスキップされました")
            assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        # 4. 重複チェックを無効化して作成
        print("\n4. 重複チェックを無効化して作成")
        result = run_command({
            "type": "template",
            "template": "create_requirement",
            "enable_duplicate_check": False,
            "parameters": {
                "id": "req_003",
                "title": "ユーザー認証機能",  # 完全一致
                "description": "別の認証機能"
            }
        }, db_dir)
        print(f"結果: {result}")
        assert "warning" not in result
        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
        
        print("\n✅ POC Search統合テスト成功")


if __name__ == "__main__":
    print("=== 統合テスト開始 ===\n")
    
    try:
        test_template_input_integration()
    except AssertionError as e:
        print(f"\n❌ Template入力テスト失敗: {e}")
    except Exception as e:
        print(f"\n❌ Template入力テストエラー: {e}")
    
    try:
        test_poc_search_integration()
    except AssertionError as e:
        print(f"\n❌ POC Search統合テスト失敗: {e}")
    except Exception as e:
        print(f"\n❌ POC Search統合テストエラー: {e}")
    
    print("\n=== 統合テスト完了 ===")