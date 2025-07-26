"""
共通のテストフィクスチャ
高速なインメモリデータベースとサブプロセス最適化を提供
"""
import pytest
import tempfile
import subprocess
import json
import sys
import os
from typing import Dict, Any, Optional
import uuid


def run_system_optimized(input_data: Dict[str, Any], db_path: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """最適化されたrun_system関数（タイムアウトとクリーンアップ付き）"""
    env = os.environ.copy()
    if db_path:
        env["RGL_DB_PATH"] = db_path

    python_cmd = sys.executable
    # run.pyの絶対パスを計算
    run_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.py")
    
    # プロセスを作成
    process = subprocess.Popen(
        [python_cmd, run_py_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        # タイムアウト付きで実行
        stdout, stderr = process.communicate(
            input=json.dumps(input_data),
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        # タイムアウト時は強制終了
        process.kill()
        stdout, stderr = process.communicate()
        return {
            "error": "Process timeout",
            "stderr": stderr,
            "timeout": timeout
        }
    finally:
        # 確実にプロセスをクリーンアップ
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    # 結果をパース
    if stdout:
        lines = stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    
    return {"error": "No valid JSON output", "stderr": stderr}


@pytest.fixture
def inmemory_db():
    """インメモリデータベースを使用するフィクスチャ"""
    # ユニークなインメモリDB識別子を生成
    db_id = str(uuid.uuid4())
    db_path = f":memory:{db_id}"
    
    # スキーマ初期化
    result = run_system_optimized({"type": "schema", "action": "apply"}, db_path)
    if "error" in result:
        pytest.fail(f"Failed to initialize schema: {result}")
    
    yield db_path
    
    # インメモリDBは自動的にクリーンアップされる


@pytest.fixture
def file_db():
    """ファイルベースのデータベースを使用するフィクスチャ（必要な場合のみ）"""
    with tempfile.TemporaryDirectory() as db_dir:
        # スキーマ初期化
        result = run_system_optimized({"type": "schema", "action": "apply"}, db_dir)
        if "error" in result:
            pytest.fail(f"Failed to initialize schema: {result}")
        
        yield db_dir


@pytest.fixture
def run_system():
    """最適化されたrun_system関数を提供するフィクスチャ"""
    return run_system_optimized


# E2Eテストのマーカーを自動的に追加
import inspect

def pytest_collection_modifyitems(items):
    """run_systemを使用するテストに自動的にe2eマーカーを追加"""
    for item in items:
        # テスト関数のソースコードを確認
        if hasattr(item, "function"):
            try:
                source = inspect.getsource(item.function)
                if "run_system" in source:
                    item.add_marker(pytest.mark.e2e)
            except (OSError, TypeError):
                # ソースコードが取得できない場合はスキップ
                pass