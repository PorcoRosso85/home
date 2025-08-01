#!/usr/bin/env python3
"""
Vessel テストフレームワーク
器の品質保証と再利用性を担保
"""
import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List

class VesselTester:
    """器のテスト基盤"""
    
    def test_vessel(self, vessel_path: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """器の動作をテスト"""
        results = {
            'vessel': vessel_path,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        for case in test_cases:
            try:
                # 器を実行
                result = subprocess.run(
                    ['python', vessel_path] if vessel_path.endswith('.py') else ['bun', vessel_path],
                    input=case['input'].encode(),
                    capture_output=True,
                    text=True
                )
                
                # 結果を検証
                if case.get('expected_output'):
                    if result.stdout.strip() == case['expected_output'].strip():
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'case': case['name'],
                            'expected': case['expected_output'],
                            'actual': result.stdout
                        })
                
                # エラーチェック
                if case.get('should_fail', False):
                    if result.returncode != 0:
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'case': case.get('name', 'unknown'),
                    'error': str(e)
                })
        
        return results

    def test_pipeline(self, vessels: List[str], input_data: str, expected_output: str) -> bool:
        """器のパイプラインをテスト"""
        data = input_data
        
        for vessel in vessels:
            result = subprocess.run(
                ['python', vessel] if vessel.endswith('.py') else ['bun', vessel],
                input=data.encode(),
                capture_output=True,
                text=True
            )
            data = result.stdout
        
        return data.strip() == expected_output.strip()

# 使用例
if __name__ == "__main__":
    tester = VesselTester()
    
    # 基本vessel.pyのテスト
    basic_tests = [
        {
            'name': 'simple_print',
            'input': 'print("Hello, Vessel!")',
            'expected_output': 'Hello, Vessel!'
        },
        {
            'name': 'calculation',
            'input': 'print(2 + 2)',
            'expected_output': '4'
        },
        {
            'name': 'error_handling',
            'input': 'raise ValueError("test")',
            'should_fail': True
        }
    ]
    
    results = tester.test_vessel('vessel.py', basic_tests)
    print(json.dumps(results, indent=2))