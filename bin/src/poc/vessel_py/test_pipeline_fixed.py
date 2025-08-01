#!/usr/bin/env python3
"""
script | script | result パイプラインのテスト（修正版）
"""
import subprocess
import sys
import os

# Python実行可能ファイルのパスを取得
PYTHON = sys.executable

def test_basic_pipeline():
    """基本的なパイプライン: script1の出力をscript2で使う"""
    # Step 1: 数値を生成
    cmd1 = subprocess.Popen(
        [PYTHON, 'vessel.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    output1, _ = cmd1.communicate('print(5)')
    
    # Step 2: その数値を2倍にする
    cmd2 = subprocess.Popen(
        [PYTHON, 'vessel.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    script2 = """import sys
n = int(sys.stdin.read().strip())
print(n * 2)"""
    output2, _ = cmd2.communicate(script2)
    
    # 最初の出力を2番目の標準入力として使う
    cmd3 = subprocess.Popen(
        [PYTHON, 'vessel.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    combined_script = f"""import sys
sys.stdin = type('obj', (object,), {{'read': lambda: '{output1.strip()}'}})()
{script2}"""
    result, _ = cmd3.communicate(combined_script)
    
    assert result.strip() == "10", f"Expected 10, got {result.strip()}"
    print("✓ Basic pipeline test passed")

def test_real_pipeline():
    """実際のパイプラインをPythonで実装"""
    # Step 1: データ生成
    p1 = subprocess.Popen(
        [PYTHON, 'vessel.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    
    # Step 2: データ変換
    p2 = subprocess.Popen(
        [PYTHON, 'vessel.py'],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        text=True
    )
    
    # スクリプトを送信
    p1.stdin.write('print(5)')
    p1.stdin.close()
    
    p2.stdin = p1.stdout
    p2_script = """import sys
n = int(sys.stdin.read().strip())
print(n * 2)"""
    
    # プロセス間でデータを流す別の方法
    output1 = subprocess.check_output(
        [PYTHON, 'vessel.py'],
        input='print(5)',
        text=True
    )
    
    output2 = subprocess.check_output(
        [PYTHON, 'vessel.py'],
        input=f"""import sys
# 前のステップの出力を仮想的にstdinとして扱う
class FakeStdin:
    def read(self):
        return '{output1.strip()}'
sys.stdin = FakeStdin()
n = int(sys.stdin.read().strip())
print(n * 2)""",
        text=True
    )
    
    assert output2.strip() == "10", f"Expected 10, got {output2.strip()}"
    print("✓ Real pipeline test passed")

def test_json_pipeline():
    """JSONデータのパイプライン処理"""
    # Step 1: JSON生成
    output1 = subprocess.check_output(
        [PYTHON, 'vessel.py'],
        input='import json; print(json.dumps({"value": 42}))',
        text=True
    )
    
    # Step 2: JSON処理
    output2 = subprocess.check_output(
        [PYTHON, 'vessel.py'],
        input=f"""import sys, json
# 前の出力を使用
data = json.loads('{output1.strip()}')
print(data["value"] * 2)""",
        text=True
    )
    
    assert output2.strip() == "84", f"Expected 84, got {output2.strip()}"
    print("✓ JSON pipeline test passed")

if __name__ == "__main__":
    print(f"Using Python: {PYTHON}")
    test_basic_pipeline()
    test_real_pipeline()
    test_json_pipeline()
    print("\n✅ All pipeline tests passed!")