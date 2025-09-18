#!/usr/bin/env python3
"""
統合テストスイート
すべての器の動作を検証
"""
import subprocess
import json

def test_basic_vessel():
    """基本vessel.pyのテスト"""
    tests = [
        ('print("hello")', "hello\n"),
        ('print(1 + 1)', "2\n"),
        ('for i in range(3): print(i)', "0\n1\n2\n"),
    ]
    
    for script, expected in tests:
        result = subprocess.run(
            ['python', 'vessel.py'],
            input=script,
            capture_output=True,
            text=True
        )
        assert result.stdout == expected, f"Failed: {script}"
    

def test_json_filter():
    """json_filter.pyのテスト"""
    test_data = {
        "users": [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30}
        ]
    }
    
    tests = [
        (".users[0].name", '"Alice"'),
        (".users[1].age", '30'),
        (".users", json.dumps(test_data["users"])),
    ]
    
    for path, expected in tests:
        result = subprocess.run(
            ['python', 'vessels/json_filter.py', path],
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == expected, f"Failed: {path}"
    

def test_pipeline():
    """器のパイプラインテスト"""
    # データ生成 → フィルタ → 変換
    pipeline = """
echo '{"data": [1,2,3,4,5]}' | \
python vessels/json_filter.py .data | \
python vessel.py << 'EOF'
import json
import sys
data = json.loads(sys.stdin.read())
print(sum(data))
EOF
"""
    
    result = subprocess.run(pipeline, shell=True, capture_output=True, text=True)
    assert result.stdout.strip() == "15", "Pipeline test failed"
    

def test_error_handling():
    """エラーハンドリングのテスト"""
    # 無効なパス
    result = subprocess.run(
        ['python', 'vessels/json_filter.py', '.invalid.path'],
        input='{"valid": "data"}',
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "Should fail on invalid path"
    
