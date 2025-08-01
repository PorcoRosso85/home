#!/usr/bin/env python3
"""
データ認識型vesselのテスト
"""
import subprocess
import sys

PYTHON = sys.executable

def test_data_as_argument():
    """コマンドライン引数でスクリプトを渡すパターン"""
    # データを送信してその2倍を計算
    result = subprocess.run(
        [PYTHON, 'vessel_data.py', 'print(int(data) * 2)'],
        input='5',
        capture_output=True,
        text=True
    )
    
    assert result.stdout.strip() == '10', f"Expected 10, got {result.stdout.strip()}"
    print("✓ Data as argument test passed")

def test_json_processing():
    """JSONデータの処理"""
    json_data = '{"values": [1, 2, 3, 4, 5]}'
    script = 'result = sum(json.loads(data)["values"]); print(result)'
    
    result = subprocess.run(
        [PYTHON, 'vessel_data.py', script],
        input=json_data,
        capture_output=True,
        text=True
    )
    
    assert result.stdout.strip() == '15', f"Expected 15, got {result.stdout.strip()}"
    print("✓ JSON processing test passed")

def test_pipeline_with_data_vessel():
    """vessel.py → vessel_data.py のパイプライン"""
    # Step 1: 通常のvesselで数値リストを生成
    step1 = subprocess.run(
        [PYTHON, 'vessel.py'],
        input='print(",".join(map(str, range(5))))',
        capture_output=True,
        text=True
    )
    
    # Step 2: データ認識型vesselで合計を計算
    step2 = subprocess.run(
        [PYTHON, 'vessel_data.py', 'nums = [int(x) for x in data.split(",")]; print(sum(nums))'],
        input=step1.stdout,
        capture_output=True,
        text=True
    )
    
    assert step2.stdout.strip() == '10', f"Expected 10, got {step2.stdout.strip()}"
    print("✓ Pipeline with data vessel test passed")

def test_multiline_data():
    """複数行データの処理"""
    multiline_data = """line1
line2
line3"""
    
    script = 'lines = data.split("\\n"); print(f"Found {len(lines)} lines")'
    
    result = subprocess.run(
        [PYTHON, 'vessel_data.py', script],
        input=multiline_data,
        capture_output=True,
        text=True
    )
    
    assert result.stdout.strip() == 'Found 3 lines', f"Got {result.stdout.strip()}"
    print("✓ Multiline data test passed")

def test_real_world_pipeline():
    """実用的なパイプライン例：CSV処理"""
    # Step 1: CSVデータを生成
    csv_gen = subprocess.run(
        [PYTHON, 'vessel.py'],
        input='''
headers = ["name", "age", "city"]
rows = [
    ["Alice", "25", "Tokyo"],
    ["Bob", "30", "New York"],
    ["Charlie", "35", "London"]
]
print(",".join(headers))
for row in rows:
    print(",".join(row))
''',
        capture_output=True,
        text=True
    )
    
    # Step 2: 年齢の平均を計算
    avg_age = subprocess.run(
        [PYTHON, 'vessel_data.py', '''
lines = data.strip().split("\\n")
headers = lines[0].split(",")
age_idx = headers.index("age")
ages = [int(line.split(",")[age_idx]) for line in lines[1:]]
print(f"Average age: {sum(ages) / len(ages)}")
'''],
        input=csv_gen.stdout,
        capture_output=True,
        text=True
    )
    
    assert "Average age: 30" in avg_age.stdout, f"Got {avg_age.stdout}"
    print("✓ Real-world pipeline test passed")

if __name__ == "__main__":
    print(f"Using Python: {PYTHON}")
    test_data_as_argument()
    test_json_processing()
    test_pipeline_with_data_vessel()
    test_multiline_data()
    test_real_world_pipeline()
    print("\n✅ All data vessel tests passed!")