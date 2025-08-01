#!/usr/bin/env python3
"""
データ認識型vesselのテスト
"""
import subprocess
import sys
import pytest
from typing import Tuple

PYTHON = sys.executable


@pytest.fixture
def run_vessel():
    """vessel.pyを実行するためのヘルパー"""
    def _run(script: str, vessel_type: str = 'vessel.py') -> subprocess.CompletedProcess:
        return subprocess.run(
            [PYTHON, vessel_type],
            input=script,
            capture_output=True,
            text=True
        )
    return _run


@pytest.fixture
def run_data_vessel():
    """vessel_data.pyを実行するためのヘルパー"""
    def _run(script: str, input_data: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [PYTHON, 'vessel_data.py', script],
            input=input_data,
            capture_output=True,
            text=True
        )
    return _run


class TestDataVessel:
    """データ認識型vesselの基本機能テスト"""
    
    @pytest.mark.parametrize("input_data,script,expected", [
        ('5', 'print(int(data) * 2)', '10'),
        ('10', 'print(int(data) * 2)', '20'),
        ('Hello', 'print(data.upper())', 'HELLO'),
        ('world', 'print(data.capitalize())', 'World'),
    ])
    def test_simple_data_processing(self, run_data_vessel, input_data, script, expected):
        """シンプルなデータ処理のパラメトリックテスト"""
        result = run_data_vessel(script, input_data)
        assert result.stdout.strip() == expected
        assert result.returncode == 0
    
    def test_json_processing(self, run_data_vessel):
        """JSONデータの処理"""
        json_data = '{"values": [1, 2, 3, 4, 5]}'
        script = 'result = sum(json.loads(data)["values"]); print(result)'
        
        result = run_data_vessel(script, json_data)
        assert result.stdout.strip() == '15'
        assert result.returncode == 0
    
    @pytest.mark.parametrize("multiline_data,expected_count", [
        ("line1\nline2\nline3", 3),
        ("single line", 1),
        ("first\nsecond", 2),
        ("a\nb\nc\nd\ne", 5),
    ])
    def test_multiline_data(self, run_data_vessel, multiline_data, expected_count):
        """複数行データの処理"""
        script = 'lines = data.split("\\n"); print(f"Found {len(lines)} lines")'
        
        result = run_data_vessel(script, multiline_data)
        assert result.stdout.strip() == f'Found {expected_count} lines'
        assert result.returncode == 0


class TestPipeline:
    """パイプライン処理のテスト"""
    
    def test_vessel_to_data_vessel_pipeline(self, run_vessel, run_data_vessel):
        """vessel.py → vessel_data.py のパイプライン"""
        # Step 1: 通常のvesselで数値リストを生成
        step1 = run_vessel('print(",".join(map(str, range(5))))')
        assert step1.returncode == 0
        
        # Step 2: データ認識型vesselで合計を計算
        step2 = run_data_vessel(
            'nums = [int(x) for x in data.split(",")]; print(sum(nums))',
            step1.stdout
        )
        assert step2.stdout.strip() == '10'
        assert step2.returncode == 0
    
    @pytest.mark.parametrize("range_size,expected_sum", [
        (5, 10),   # 0+1+2+3+4 = 10
        (10, 45),  # 0+1+...+9 = 45
        (3, 3),    # 0+1+2 = 3
    ])
    def test_parametrized_pipeline(self, run_vessel, run_data_vessel, range_size, expected_sum):
        """パラメトリックなパイプラインテスト"""
        # Step 1: 数値リストを生成
        step1 = run_vessel(f'print(",".join(map(str, range({range_size}))))')
        assert step1.returncode == 0
        
        # Step 2: 合計を計算
        step2 = run_data_vessel(
            'nums = [int(x) for x in data.split(",")]; print(sum(nums))',
            step1.stdout
        )
        assert step2.stdout.strip() == str(expected_sum)
        assert step2.returncode == 0


class TestRealWorldScenarios:
    """実用的なシナリオのテスト"""
    
    @pytest.fixture
    def csv_data(self):
        """テスト用CSVデータ"""
        return """name,age,city
Alice,25,Tokyo
Bob,30,New York
Charlie,35,London"""
    
    def test_csv_processing_pipeline(self, run_vessel, run_data_vessel):
        """CSV処理パイプライン"""
        # Step 1: CSVデータを生成
        csv_gen_script = '''
headers = ["name", "age", "city"]
rows = [
    ["Alice", "25", "Tokyo"],
    ["Bob", "30", "New York"],
    ["Charlie", "35", "London"]
]
print(",".join(headers))
for row in rows:
    print(",".join(row))
'''
        csv_result = run_vessel(csv_gen_script)
        assert csv_result.returncode == 0
        
        # Step 2: 年齢の平均を計算
        avg_age_script = '''
lines = data.strip().split("\\n")
headers = lines[0].split(",")
age_idx = headers.index("age")
ages = [int(line.split(",")[age_idx]) for line in lines[1:]]
print(f"Average age: {sum(ages) / len(ages)}")
'''
        avg_result = run_data_vessel(avg_age_script, csv_result.stdout)
        assert "Average age: 30" in avg_result.stdout
        assert avg_result.returncode == 0
    
    @pytest.mark.parametrize("operation,expected", [
        ('age_idx = headers.index("age"); ages = [int(line.split(",")[age_idx]) for line in lines[1:]]; print(min(ages))', '25'),
        ('age_idx = headers.index("age"); ages = [int(line.split(",")[age_idx]) for line in lines[1:]]; print(max(ages))', '35'),
        ('print(len(lines) - 1)', '3'),  # データ行数
    ])
    def test_csv_operations(self, run_data_vessel, csv_data, operation, expected):
        """CSVデータに対する各種操作"""
        script = f'''
lines = data.strip().split("\\n")
headers = lines[0].split(",")
{operation}
'''
        result = run_data_vessel(script, csv_data)
        assert expected in result.stdout
        assert result.returncode == 0