#!/usr/bin/env python3
"""
統合テストスイート - pytest版
すべての器の動作を検証
"""
import subprocess
import json
import sys
import pytest
from pathlib import Path


class TestBasicVessel:
    """基本vessel.pyのテスト"""
    
    @pytest.mark.parametrize("script,expected", [
        ('print("hello")', "hello\n"),
        ('print(1 + 1)', "2\n"),
        ('for i in range(3): print(i)', "0\n1\n2\n"),
    ])
    def test_basic_execution(self, script, expected):
        """基本的なスクリプト実行のテスト"""
        result = subprocess.run(
            ['python', 'vessel.py'],
            input=script,
            capture_output=True,
            text=True
        )
        assert result.stdout == expected
        assert result.returncode == 0


class TestJsonFilter:
    """JSONフィルターvesselのテスト"""
    
    def test_extract_field(self):
        """JSONフィールド抽出のテスト"""
        test_data = {"name": "test", "value": 42}
        
        result = subprocess.run(
            ['python', 'vessels/json_filter.py', '.value'],
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        
        assert result.stdout.strip() == '42'
        assert result.returncode == 0
    
    def test_nested_field(self):
        """ネストされたフィールドの抽出"""
        test_data = {"user": {"name": "Alice", "age": 30}}
        
        result = subprocess.run(
            ['python', 'vessels/json_filter.py', '.user.name'],
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        
        assert result.stdout.strip() == '"Alice"'
        assert result.returncode == 0


class TestPipeline:
    """パイプライン機能のテスト"""
    
    def test_vessel_to_vessel_pipeline(self):
        """vessel間のパイプライン"""
        # 最初のvessel: リストを生成
        script1 = '''
import json
data = [1, 2, 3, 4, 5]
print(json.dumps(data))
'''
        
        # vesselを実行してJSONを生成
        result1 = subprocess.run(
            ['python', 'vessel.py'],
            input=script1,
            capture_output=True,
            text=True
        )
        
        # vessel_dataでデータを処理
        script2 = '''
import json
nums = json.loads(data)
print(sum(nums))
'''
        
        result2 = subprocess.run(
            ['python', 'vessel_data.py'] + script2.split('\n'),
            input=result1.stdout,
            capture_output=True,
            text=True
        )
        
        assert result2.stdout.strip() == '15'
        assert result2.returncode == 0


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_syntax_error(self):
        """構文エラーの処理"""
        result = subprocess.run(
            ['python', 'vessel.py'],
            input='print("unclosed',
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        # 構造化ログがstderrに出力されることを確認
        assert 'error' in result.stderr.lower()
    
    def test_runtime_error(self):
        """実行時エラーの処理"""
        result = subprocess.run(
            ['python', 'vessel.py'],
            input='1/0',
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert 'error' in result.stderr.lower()