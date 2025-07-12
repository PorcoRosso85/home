#!/usr/bin/env python
"""
エンドツーエンドテスト
実際のtemplate入力からPOC search統合までの動作確認
"""
import tempfile
import json
import subprocess
import os


def run_command(command, input_data=None):
    """コマンドを実行して結果を返す"""
    env = os.environ.copy()
    env['PYTHONPATH'] = '/home/nixos/bin/src'
    
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        env=env
    )
    
    stdout, stderr = proc.communicate(input=input_data)
    return proc.returncode, stdout, stderr


def main():
    print("=== エンドツーエンドテスト ===\n")
    
    with tempfile.TemporaryDirectory() as db_dir:
        # 環境変数設定
        os.environ['RGL_DATABASE_PATH'] = db_dir
        
        # 1. スキーマ初期化
        print("1. スキーマ初期化")
        input_data = json.dumps({"type": "schema", "action": "apply"})
        code, stdout, stderr = run_command("uv run python run.py", input_data)
        
        if code == 0 and "success" in stdout:
            print("✅ スキーマ初期化成功")
        else:
            print(f"❌ スキーマ初期化失敗: {stderr}")
            return
        
        # 2. 要件作成（1件目）
        print("\n2. 要件作成（1件目）")
        req1 = {
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_001",
                "title": "ユーザー認証機能の実装",
                "description": "ログイン、ログアウト、パスワードリセット機能を含む"
            }
        }
        code, stdout, stderr = run_command("uv run python run.py", json.dumps(req1))
        
        if code == 0:
            print("✅ 要件1作成成功")
        else:
            print(f"❌ 要件1作成失敗: {stderr}")
        
        # 3. 要件作成（2件目 - 類似）
        print("\n3. 要件作成（類似要件で重複チェック）")
        req2 = {
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_002",
                "title": "ユーザー認証システムの構築",
                "description": "セキュアなログイン機能の実装"
            }
        }
        code, stdout, stderr = run_command("uv run python run.py", json.dumps(req2))
        
        # 結果を解析
        try:
            lines = stdout.strip().split('\n')
            for line in reversed(lines):
                if line.strip():
                    result = json.loads(line)
                    break
            
            if "warning" in result:
                print("✅ 重複チェック機能動作確認")
                print(f"   警告: {result['warning']['message']}")
                print(f"   重複候補数: {len(result['warning'].get('duplicates', []))}")
            else:
                print("⚠️ 重複チェックがスキップされました")
        except Exception as e:
            print(f"❌ 結果解析エラー: {e}")
        
        # 4. 要件検索
        print("\n4. 要件検索")
        search = {
            "type": "template",
            "template": "find_requirement",
            "parameters": {"id": "req_001"}
        }
        code, stdout, stderr = run_command("uv run python run.py", json.dumps(search))
        
        if code == 0 and "req_001" in stdout:
            print("✅ 要件検索成功")
        else:
            print(f"❌ 要件検索失敗: {stderr}")
        
        # 5. 要件一覧
        print("\n5. 要件一覧取得")
        list_req = {
            "type": "template",
            "template": "list_requirements",
            "parameters": {"limit": 10}
        }
        code, stdout, stderr = run_command("uv run python run.py", json.dumps(list_req))
        
        if code == 0:
            print("✅ 要件一覧取得成功")
        else:
            print(f"❌ 要件一覧取得失敗: {stderr}")
    
    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    main()