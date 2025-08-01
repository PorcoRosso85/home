#!/usr/bin/env python3
"""
Vessel テストフレームワーク
器の品質保証と再利用性を担保
"""
import subprocess
import tempfile
import os
import pytest
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

class TestVesselFramework:
    """Vessel framework test cases"""
    
    @pytest.fixture
    def tester(self):
        """Provide VesselTester instance"""
        return VesselTester()
    
    @pytest.fixture
    def basic_test_cases(self):
        """Basic test cases for vessel.py"""
        return [
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
    
    def test_vessel_basic_functionality(self, tester, basic_test_cases):
        """Test basic vessel.py functionality"""
        results = tester.test_vessel('vessel.py', basic_test_cases)
        
        assert results['vessel'] == 'vessel.py'
        assert results['failed'] == 0
        assert results['passed'] == len(basic_test_cases)
        assert len(results['errors']) == 0
    
    def test_vessel_simple_print(self, tester):
        """Test simple print functionality"""
        test_case = [{
            'name': 'simple_print',
            'input': 'print("Hello, Vessel!")',
            'expected_output': 'Hello, Vessel!'
        }]
        
        results = tester.test_vessel('vessel.py', test_case)
        assert results['passed'] == 1
        assert results['failed'] == 0
    
    def test_vessel_calculation(self, tester):
        """Test calculation functionality"""
        test_case = [{
            'name': 'calculation',
            'input': 'print(2 + 2)',
            'expected_output': '4'
        }]
        
        results = tester.test_vessel('vessel.py', test_case)
        assert results['passed'] == 1
        assert results['failed'] == 0
    
    def test_vessel_error_handling(self, tester):
        """Test error handling"""
        test_case = [{
            'name': 'error_handling',
            'input': 'raise ValueError("test")',
            'should_fail': True
        }]
        
        results = tester.test_vessel('vessel.py', test_case)
        assert results['passed'] == 1
        assert results['failed'] == 0
    
    def test_vessel_pipeline_simple(self, tester):
        """Test simple pipeline functionality"""
        # Create a temporary vessel that just passes through input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('import sys\nprint(sys.stdin.read().strip())')
            temp_vessel = f.name
        
        try:
            result = tester.test_pipeline(
                [temp_vessel, temp_vessel],  # Two pass-through vessels
                'test data',
                'test data'
            )
            assert result is True
        finally:
            os.unlink(temp_vessel)
    
    def test_vessel_pipeline_transformation(self, tester):
        """Test pipeline with transformation"""
        # Create vessels for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
            f1.write('import sys\nprint(sys.stdin.read().strip().upper())')
            upper_vessel = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
            f2.write('import sys\nprint(sys.stdin.read().strip().lower())')
            lower_vessel = f2.name
        
        try:
            # Test upper -> lower pipeline
            result = tester.test_pipeline(
                [upper_vessel, lower_vessel],
                'Hello World',
                'hello world'
            )
            assert result is True
        finally:
            os.unlink(upper_vessel)
            os.unlink(lower_vessel)