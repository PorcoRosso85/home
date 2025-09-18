#!/usr/bin/env python3
"""
エラーハンドリングとパイプライン堅牢性のテスト
"""
import subprocess
import sys
import pytest

@pytest.fixture
def python_executable():
    """Python実行ファイルのパスを提供"""
    return sys.executable

def test_error_propagation(python_executable):
    """エラーが適切に伝播することを確認"""
    # エラーを起こすスクリプト
    result = subprocess.run(
        [python_executable, 'vessel.py'],
        input='raise ValueError("Test error")',
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0, "Should have non-zero exit code"
    assert "Error executing script" in result.stderr, f"Error not in stderr: {result.stderr}"
    assert "Test error" in result.stderr, f"Error message not found: {result.stderr}"

def test_pipeline_stops_on_error(python_executable):
    """パイプラインがエラーで停止することを確認"""
    # エラーを起こすパイプライン
    cmd = f"""echo 'print(1/0)' | {python_executable} vessel.py || echo "PIPELINE_STOPPED" """
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    
    assert "PIPELINE_STOPPED" in result.stdout, "Pipeline should stop on error"

def test_graceful_error_handling(python_executable):
    """データ認識型vesselのエラーハンドリング"""
    # 不正なデータでエラー
    result = subprocess.run(
        [python_executable, 'vessel_data.py', 'print(int(data))'],
        input='not_a_number',
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0, "Should fail on invalid data"
    assert "invalid literal for int()" in result.stderr or "ValueError" in result.stderr

def test_partial_pipeline_success(python_executable):
    """部分的な成功の確認"""
    # Step 1: 成功
    step1 = subprocess.run(
        [python_executable, 'vessel.py'],
        input='print("SUCCESS")',
        capture_output=True,
        text=True
    )
    
    assert step1.returncode == 0
    assert step1.stdout.strip() == "SUCCESS"
    
    # Step 2: 失敗
    step2 = subprocess.run(
        [python_executable, 'vessel_data.py', 'raise Exception("Step 2 failed")'],
        input=step1.stdout,
        capture_output=True,
        text=True
    )
    
    assert step2.returncode != 0

def test_error_recovery_pattern(python_executable):
    """エラー回復パターンの実装"""
    recovery_script = '''
try:
    # 危険な操作
    result = 10 / int(data)
    print(f"Result: {result}")
except ZeroDivisionError:
    print("Error: Division by zero, using default value 0")
except ValueError:
    print("Error: Invalid number, using default value 1")
'''
    
    # ゼロ除算のケース
    result1 = subprocess.run(
        [python_executable, 'vessel_data.py', recovery_script],
        input='0',
        capture_output=True,
        text=True
    )
    
    assert result1.returncode == 0  # エラーをキャッチしたので成功
    assert "Division by zero" in result1.stdout
    
    # 不正な値のケース
    result2 = subprocess.run(
        [python_executable, 'vessel_data.py', recovery_script],
        input='abc',
        capture_output=True,
        text=True
    )
    
    assert result2.returncode == 0
    assert "Invalid number" in result2.stdout