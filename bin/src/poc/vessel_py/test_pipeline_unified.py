#!/usr/bin/env python3
"""
統合パイプラインテスト - pytest版
すべてのパイプライン機能を統合的にテスト
"""
import subprocess
import sys
import os
import pytest
import json
from pathlib import Path


@pytest.fixture
def python_exec():
    """Python実行パスを提供"""
    return sys.executable


class TestBasicPipeline:
    """基本的なパイプライン機能のテスト"""
    
    def test_simple_numeric_pipeline(self, python_exec):
        """数値を生成して2倍にする基本パイプライン"""
        # Step 1: vesselで5を出力
        result1 = subprocess.run(
            [python_exec, 'vessel.py'],
            input='print(5)',
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0
        
        # Step 2: 出力を2倍にする
        script2 = f"""
import sys
n = int(sys.stdin.read().strip())
print(n * 2)
"""
        result2 = subprocess.run(
            [python_exec, 'vessel.py'],
            input=script2,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 手動でパイプラインを実行
        result2 = subprocess.run(
            [python_exec, 'vessel.py'],
            input=script2,
            capture_output=True,
            text=True
        )
        result2.stdin = result1.stdout
        
        # 実際のパイプライン実行
        p1 = subprocess.Popen(
            [python_exec, 'vessel.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        p2 = subprocess.Popen(
            [python_exec, 'vessel.py'],
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            text=True
        )
        
        stdout1, _ = p1.communicate('print(5)')
        p2.stdin.write(f"""
import sys
n = int('{stdout1.strip()}')
print(n * 2)""")
        p2.stdin.close()
        stdout2, _ = p2.communicate()
        
        assert stdout2.strip() == '10'
    
    @pytest.mark.parametrize("input_value,expected", [
        (5, "10"),
        (3, "6"),
        (7, "14"),
    ])
    def test_parametrized_pipeline(self, python_exec, input_value, expected):
        """パラメータ化されたパイプラインテスト"""
        # vessel_dataを使用したシンプルなテスト
        result1 = subprocess.run(
            [python_exec, 'vessel.py'],
            input=f'print({input_value})',
            capture_output=True,
            text=True
        )
        
        result2 = subprocess.run(
            [python_exec, 'vessel_data.py', f'print(int(data) * 2)'],
            input=result1.stdout,
            capture_output=True,
            text=True
        )
        
        assert result2.stdout.strip() == expected
        assert result2.returncode == 0


class TestJsonPipeline:
    """JSON処理パイプラインのテスト"""
    
    def test_json_generation_and_processing(self, python_exec):
        """JSONデータの生成と処理"""
        # JSONを生成
        result1 = subprocess.run(
            [python_exec, 'vessel.py'],
            input='import json; print(json.dumps({"value": 42}))',
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0
        
        # JSONを処理
        result2 = subprocess.run(
            [python_exec, 'vessel_data.py', 'import json; d = json.loads(data); print(d["value"] * 2)'],
            input=result1.stdout,
            capture_output=True,
            text=True
        )
        
        assert result2.stdout.strip() == "84"
        assert result2.returncode == 0
    
    def test_json_filter_vessel(self, python_exec):
        """JSONフィルターvesselのテスト"""
        test_data = {"name": "test", "value": 42, "nested": {"key": "data"}}
        
        # .value抽出
        result = subprocess.run(
            [python_exec, 'vessels/json_filter.py', '.value'],
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == '42'
        
        # .nested.key抽出
        result = subprocess.run(
            [python_exec, 'vessels/json_filter.py', '.nested.key'],
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == '"data"'


class TestComplexPipeline:
    """複雑なパイプラインのテスト"""
    
    def test_three_stage_pipeline(self, python_exec):
        """3段階のパイプライン処理"""
        # Stage 1: リストを生成
        stage1 = subprocess.run(
            [python_exec, 'vessel.py'],
            input='print(",".join(map(str, range(5))))',
            capture_output=True,
            text=True
        )
        assert stage1.stdout.strip() == "0,1,2,3,4"
        
        # Stage 2: 各要素を2倍
        stage2_script = '''
nums = [int(x) for x in data.split(",")]
doubled = [x * 2 for x in nums]
print(",".join(map(str, doubled)))
'''
        stage2 = subprocess.run(
            [python_exec, 'vessel_data.py', stage2_script],
            input=stage1.stdout,
            capture_output=True,
            text=True
        )
        assert stage2.stdout.strip() == "0,2,4,6,8"
        
        # Stage 3: 合計を計算
        stage3_script = '''
nums = [int(x) for x in data.split(",")]
total = sum(nums)
print(f"Sum: {total}")
'''
        stage3 = subprocess.run(
            [python_exec, 'vessel_data.py', stage3_script],
            input=stage2.stdout,
            capture_output=True,
            text=True
        )
        assert stage3.stdout.strip() == "Sum: 20"
    
    def test_error_in_pipeline(self, python_exec):
        """パイプライン中のエラー処理"""
        # エラーを発生させる
        result1 = subprocess.run(
            [python_exec, 'vessel.py'],
            input='raise ValueError("Test error")',
            capture_output=True,
            text=True
        )
        assert result1.returncode != 0
        
        # 次のステージは実行されない（エラーを検知）
        result2 = subprocess.run(
            [python_exec, 'vessel_data.py', 'print("Should not run")'],
            input=result1.stdout,  # 空の出力
            capture_output=True,
            text=True
        )
        # vessel_dataは空の入力でも実行される
        assert result2.stdout.strip() == "Should not run"


class TestRealWorldPipeline:
    """実用的なパイプラインのテスト"""
    
    def test_csv_processing_pipeline(self, python_exec):
        """CSV風データの処理パイプライン"""
        # CSVデータを生成
        csv_data = '''name,age,city
Alice,30,Tokyo
Bob,25,Osaka
Charlie,35,Kyoto'''
        
        result1 = subprocess.run(
            [python_exec, 'vessel.py'],
            input=f'print("""{csv_data}""")',
            capture_output=True,
            text=True
        )
        
        # ヘッダーを抽出
        header_script = '''
lines = data.strip().split("\\n")
headers = lines[0].split(",")
print(",".join(headers))
'''
        result2 = subprocess.run(
            [python_exec, 'vessel_data.py', header_script],
            input=result1.stdout,
            capture_output=True,
            text=True
        )
        assert result2.stdout.strip() == "name,age,city"
        
        # 年齢の平均を計算
        avg_age_script = '''
lines = data.strip().split("\\n")
ages = []
for line in lines[1:]:  # ヘッダーをスキップ
    parts = line.split(",")
    if len(parts) >= 2:
        ages.append(int(parts[1]))
if ages:
    print(f"Average age: {sum(ages) / len(ages)}")
'''
        result3 = subprocess.run(
            [python_exec, 'vessel_data.py', avg_age_script],
            input=result1.stdout,
            capture_output=True,
            text=True
        )
        assert result3.stdout.strip() == "Average age: 30.0"