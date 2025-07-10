"""
シンプルなE2Eテスト - デバッグ用
"""
import json
import subprocess
import os
import tempfile
import shutil


def test_simple_e2e():
    """最小限のE2Eテストでシステムの動作を確認"""
    # 一時ディレクトリ作成
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test.db")

    try:
        # 環境変数設定
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
        env['RGL_DB_PATH'] = test_db_path
        env['RGL_SKIP_SCHEMA_CHECK'] = 'true'

        venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        run_py = os.path.join(os.path.dirname(__file__), 'run.py')

        # 1. スキーマ適用
        print(f"=== Applying schema to {test_db_path} ===")
        schema_input = json.dumps({
            "type": "schema",
            "action": "apply",
            "create_test_data": False
        })

        result = subprocess.run(
            [venv_python, run_py],
            input=schema_input,
            capture_output=True,
            text=True,
            env=env
        )

        print(f"Schema result: {result.stdout}")
        print(f"Schema stderr: {result.stderr}")
        assert result.returncode == 0

        # 2. シンプルなクエリ実行
        print("\n=== Executing simple query ===")
        simple_query_input = json.dumps({
            "type": "cypher",
            "query": "CREATE (r:RequirementEntity {id: 'TEST_001', title: 'Test'})"
        })

        result = subprocess.run(
            [venv_python, run_py],
            input=simple_query_input,
            capture_output=True,
            text=True,
            env=env
        )

        print(f"Query result: {result.stdout}")
        print(f"Query stderr: {result.stderr}")

        # 結果解析
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line:
                    try:
                        parsed = json.loads(line)
                        print(f"Parsed line: {parsed}")
                    except:
                        print(f"Failed to parse: {line}")

        assert result.returncode == 0

    finally:
        # クリーンアップ
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_simple_e2e()
