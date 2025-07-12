#!/usr/bin/env python
"""
POC Search統合の最終確認
実際にtemplate入力からPOC searchまでの流れを確認
"""
import subprocess
import json
import tempfile
import os


def run_in_nix_develop(command):
    """nix develop環境でコマンドを実行"""
    result = subprocess.run(
        ["nix", "develop", "-c", "bash", "-c", command],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr


def main():
    print("=== POC Search統合の最終確認 ===\n")
    
    # 1. POC searchの独立動作確認
    print("1. POC searchの独立動作確認")
    poc_dir = "/home/nixos/bin/src/poc/search"
    success, stdout, stderr = run_in_nix_develop(f"cd {poc_dir} && python -m pytest test_search_service_interface.py::test_search_service_basic -v")
    
    if success:
        print("✅ POC search単体テスト: PASS")
    else:
        print("❌ POC search単体テスト: FAIL")
        print(f"Error: {stderr[:200]}")
    
    # 2. requirement/graphでのインポート確認
    print("\n2. requirement/graphでのインポート確認")
    test_script = """
import sys
sys.path.insert(0, '/home/nixos/bin/src')
try:
    from poc.search.infrastructure.search_service_factory import SearchServiceFactory
    print('✅ Import successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        test_file = f.name
    
    success, stdout, stderr = run_in_nix_develop(f"cd {os.getcwd()} && python {test_file}")
    print(stdout.strip())
    os.unlink(test_file)
    
    # 3. 統合動作確認
    print("\n3. 統合動作確認（実際のデータフロー）")
    with tempfile.TemporaryDirectory() as db_dir:
        # スキーマ初期化
        cmd = f"""
cd {os.getcwd()} && 
export RGL_DATABASE_PATH={db_dir} && 
export PYTHONPATH=/home/nixos/bin/src && 
echo '{{"type": "schema", "action": "apply"}}' | python run.py
"""
        success, stdout, stderr = run_in_nix_develop(cmd)
        
        if "success" in stdout:
            print("✅ スキーマ初期化: 成功")
        else:
            print(f"❌ スキーマ初期化: 失敗 - {stderr[:200]}")
            return
        
        # 要件作成（重複チェック付き）
        cmd = f"""
cd {os.getcwd()} && 
export RGL_DATABASE_PATH={db_dir} && 
export PYTHONPATH=/home/nixos/bin/src && 
echo '{{"type": "template", "template": "create_requirement", "parameters": {{"id": "test_001", "title": "認証機能"}}}}' | python run.py
"""
        success, stdout, stderr = run_in_nix_develop(cmd)
        
        # 結果の解析
        try:
            lines = stdout.strip().split('\n')
            for line in reversed(lines):
                if line.strip():
                    result = json.loads(line)
                    break
            
            if "warning" in result:
                print("✅ 重複チェック機能: 動作（警告あり）")
                print(f"   警告: {result['warning']['message']}")
            elif result.get("data", {}).get("status") == "success":
                print("✅ 要件作成: 成功（重複チェックはスキップ）")
            else:
                print(f"❌ 要件作成: 失敗 - {result}")
        except Exception as e:
            print(f"❌ 結果解析エラー: {e}")
            print(f"   stdout: {stdout[:200]}")
    
    print("\n=== 確認完了 ===")


if __name__ == "__main__":
    main()