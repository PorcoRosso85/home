#!/usr/bin/env python3
"""
最小限のパイプラインテスト
"""
import subprocess
import sys
import tempfile
import os

PYTHON = sys.executable

def test_with_files():
    """一時ファイルを使ったパイプラインテスト"""
    
    # Step 1: 数値を生成してファイルに保存
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        script1 = 'print(5)'
        result1 = subprocess.run(
            [PYTHON, 'vessel.py'],
            input=script1,
            capture_output=True,
            text=True
        )
        f.write(result1.stdout)
        temp_file = f.name
    
    # Step 2: ファイルから読んで2倍にする
    with open(temp_file, 'r') as f:
        value = f.read().strip()
    
    script2 = f'print({value} * 2)'
    result2 = subprocess.run(
        [PYTHON, 'vessel.py'],
        input=script2,
        capture_output=True,
        text=True
    )
    
    os.unlink(temp_file)
    
    print(f"Step 1 output: '{result1.stdout.strip()}'")
    print(f"Step 2 output: '{result2.stdout.strip()}'")
    
    assert result2.stdout.strip() == "10", f"Expected 10, got {result2.stdout.strip()}"
    print("✓ File-based pipeline test passed")

def test_direct_composition():
    """直接的な関数合成スタイル"""
    
    # vessel関数をシミュレート
    def run_vessel(script):
        result = subprocess.run(
            [PYTHON, 'vessel.py'],
            input=script,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"Vessel error: {result.stderr}")
        return result.stdout.strip()
    
    # パイプライン: 5を生成 → 2倍 → 結果
    step1 = run_vessel('print(5)')
    step2 = run_vessel(f'print({step1} * 2)')
    
    print(f"Pipeline result: {step1} -> {step2}")
    assert step2 == "10", f"Expected 10, got {step2}"
    print("✓ Direct composition test passed")

def test_unix_style_pipeline():
    """本物のUnixパイプラインを使用"""
    if os.name == 'nt':
        print("⚠️  Skipping Unix pipeline test on Windows")
        return
    
    # シェルで実際のパイプを使う
    cmd = f"""echo 'print(5)' | {PYTHON} vessel.py | {{
        read value
        echo "print($value * 2)"
    }} | {PYTHON} vessel.py"""
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        executable='/bin/bash'
    )
    
    print(f"Unix pipeline output: '{result.stdout.strip()}'")
    assert result.stdout.strip() == "10", f"Expected 10, got {result.stdout.strip()}"
    print("✓ Unix pipeline test passed")

if __name__ == "__main__":
    print(f"Using Python: {PYTHON}")
    test_with_files()
    test_direct_composition()
    test_unix_style_pipeline()
    print("\n✅ All minimal pipeline tests passed!")