#!/usr/bin/env python3
"""Debug POC search integration"""

import json
import tempfile
import os
import sys
import subprocess

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_system(input_data, db_path=None):
    """requirement/graphシステムの公開APIを実行"""
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/nixos/bin/src"
    if db_path:
        env["RGL_DATABASE_PATH"] = db_path
    
    # venvのPythonを使用
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = sys.executable
    
    # プロジェクトルートから実行
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = subprocess.run(
        [python_cmd, "-m", "requirement.graph"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
        cwd=project_root
    )
    
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    
    return {"error": "No valid JSON output", "stderr": result.stderr}

def main():
    with tempfile.TemporaryDirectory() as db_dir:
        print(f"Using temp db: {db_dir}")
        
        # Initialize schema
        schema_result = run_system({"type": "schema", "action": "apply"}, db_dir)
        print(f"Schema result: {schema_result}")
        
        # Create first requirement
        create1_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_001",
                "title": "ユーザー認証システム",
                "description": "ログイン機能の実装"
            }
        }, db_dir)
        print(f"Create 1 result: {create1_result}")
        
        # Create similar requirement
        create2_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_002",
                "title": "認証システム",
                "description": "ユーザーログイン機能"
            }
        }, db_dir)
        print(f"Create 2 result: {create2_result}")

if __name__ == "__main__":
    main()