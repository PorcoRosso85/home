#!/usr/bin/env python3
"""最小限のテスト"""
import subprocess

# 直接vesselを実行
result = subprocess.run(
    ['python3', 'vessel.py'],
    input='print(5)',
    capture_output=True,
    text=True
)

print(f"stdout: '{result.stdout}'")
print(f"stderr: '{result.stderr}'")
print(f"returncode: {result.returncode}")

# 期待値の確認
assert result.stdout.strip() == '5', f"Expected '5', got '{result.stdout.strip()}'"
print("✓ Simple test passed")