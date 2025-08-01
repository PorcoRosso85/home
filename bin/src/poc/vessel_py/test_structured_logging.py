#!/usr/bin/env python3
"""
Vesselシステムの構造化ログ出力のテスト
"""
import subprocess
import sys
import json

PYTHON = sys.executable

def test_vessel_structured_error_log():
    """エラー時に構造化されたログが出力されることを確認"""
    result = subprocess.run(
        [PYTHON, 'vessel_structured.py'],
        input='raise ValueError("Test error")',
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    
    # stderrがJSON形式であることを確認
    try:
        error_log = json.loads(result.stderr.strip())
        assert error_log['level'] == 'error'
        assert error_log['message'] == 'Script execution failed'
        assert 'error' in error_log
        assert 'Test error' in error_log['error']
    except json.JSONDecodeError:
        assert False, f"Expected JSON log, got: {result.stderr}"
    
    print("✓ Structured error log test passed")

def test_vessel_debug_mode():
    """デバッグモードで追加情報が出力されることを確認"""
    import os
    env = os.environ.copy()
    env['VESSEL_DEBUG'] = '1'
    
    result = subprocess.run(
        [PYTHON, 'vessel_structured.py'],
        input='print("Hello")',
        capture_output=True,
        text=True,
        env=env
    )
    
    # デバッグログがstderrに出力される
    debug_logs = result.stderr.strip().split('\n')
    assert any('debug' in log for log in debug_logs if log)
    
    # 通常の出力はstdoutに
    assert result.stdout.strip() == "Hello"
    
    print("✓ Debug mode test passed")

def test_vessel_data_structured_log():
    """vessel_dataも構造化ログを使用することを確認"""
    result = subprocess.run(
        [PYTHON, 'vessel_data_structured.py', 'invalid_syntax('],
        input='test data',
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    
    try:
        error_log = json.loads(result.stderr.strip())
        assert error_log['level'] == 'error'
        assert 'vessel_type' in error_log
        assert error_log['vessel_type'] == 'data'
    except json.JSONDecodeError:
        assert False, f"Expected JSON log, got: {result.stderr}"
    
    print("✓ vessel_data structured log test passed")

if __name__ == "__main__":
    print("Testing structured logging for vessels...")
    test_vessel_structured_error_log()
    test_vessel_debug_mode()
    test_vessel_data_structured_log()
    print("\n✅ All structured logging tests passed!")