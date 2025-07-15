#!/usr/bin/env python3
"""
READMEの使用例が実際に動作することを確認する統合テスト
"""
import subprocess
import sys
import json


def test_basic_usage():
    """READMEの基本的な使用例が動作することを確認"""
    code = '''
import sys
sys.path.insert(0, '.')
from __init__ import log, to_jsonl, LogData

# ログ出力（uri, messageは必須）
log("INFO", {
    "uri": "/api/v1/payment/process",
    "message": "Payment processed",
    "amount": 1000,
    "currency": "JPY",
    "user_id": "user123"
})
'''
    
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="."
    )
    
    assert result.returncode == 0, f"Failed: {result.stderr}"
    output = json.loads(result.stdout.strip())
    assert output["level"] == "INFO"
    assert output["uri"] == "/api/v1/payment/process"
    assert output["message"] == "Payment processed"
    print("✓ Basic usage example works")


def test_extended_type():
    """READMEの型定義拡張例が動作することを確認"""
    code = '''
import sys
sys.path.insert(0, '.')
from __init__ import log, LogData

# アプリケーション固有の型定義（LogDataを継承）
class MyLogData(LogData):
    request_id: str
    latency_ms: int

# カスタムレベルも使用可能
log("METRIC", {
    "uri": "/api/health",
    "message": "Health check",
    "request_id": "req-123",
    "latency_ms": 42
})
'''
    
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="."
    )
    
    assert result.returncode == 0, f"Failed: {result.stderr}"
    output = json.loads(result.stdout.strip())
    assert output["level"] == "METRIC"
    assert output["latency_ms"] == 42
    print("✓ Type extension example works")


def test_to_jsonl():
    """to_jsonl関数が期待通り動作することを確認"""
    code = '''
import sys
sys.path.insert(0, '.')
from __init__ import to_jsonl
data = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "test"}
print(to_jsonl(data))
'''
    
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="."
    )
    
    assert result.returncode == 0, f"Failed: {result.stderr}"
    # JSONとしてパース可能であることを確認
    output = json.loads(result.stdout.strip())
    assert output["message"] == "test"
    print("✓ to_jsonl function works")


if __name__ == "__main__":
    print("=== README Integration Tests ===")
    test_basic_usage()
    test_extended_type()
    test_to_jsonl()
    print("\nAll README examples are working correctly! ✅")