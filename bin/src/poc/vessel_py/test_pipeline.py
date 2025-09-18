#!/usr/bin/env python3
"""
script | script | result パイプラインのテスト
"""
import subprocess
import sys

def test_basic_pipeline():
    """基本的なパイプライン: script1の出力をscript2で使う"""
    # Step 1: 数値を生成
    # Step 2: その数値を2倍にする
    pipeline = """
echo 'print(5)' | python3 vessel.py | \
python3 vessel.py << 'EOF'
import sys
n = int(sys.stdin.read().strip())
print(n * 2)
EOF
"""
    
    result = subprocess.run(pipeline, shell=True, capture_output=True, text=True)
    assert result.stdout.strip() == "10", f"Expected 10, got {result.stdout.strip()}"

def test_json_pipeline():
    """JSONデータのパイプライン処理"""
    pipeline = """
echo 'import json; print(json.dumps({"value": 42}))' | python3 vessel.py | \
python3 vessel.py << 'EOF'
import sys, json
data = json.loads(sys.stdin.read())
print(data["value"] * 2)
EOF
"""
    
    result = subprocess.run(pipeline, shell=True, capture_output=True, text=True)
    assert result.stdout.strip() == "84", f"Expected 84, got {result.stdout.strip()}"

def test_three_stage_pipeline():
    """3段階パイプライン: 生成→変換→集計"""
    pipeline = """
echo 'print(",".join(map(str, range(5))))' | python3 vessel.py | \
python3 vessel.py << 'EOF'
import sys
numbers = sys.stdin.read().strip().split(",")
doubled = [int(n) * 2 for n in numbers]
print(",".join(map(str, doubled)))
EOF | \
python3 vessel.py << 'EOF'
import sys
numbers = sys.stdin.read().strip().split(",")
total = sum(int(n) for n in numbers)
print(f"Sum: {total}")
EOF
"""
    
    result = subprocess.run(pipeline, shell=True, capture_output=True, text=True)
    assert result.stdout.strip() == "Sum: 20", f"Expected 'Sum: 20', got {result.stdout.strip()}"