#!/usr/bin/env python3
"""
E2Eテスト：Vesselツールの統合シナリオ

Vesselツール（vessel-pyright, vessel-python）の実際の使用シナリオを検証します。
これらのテストは、ユーザーがツールをどのように使用するかを仕様として定義します。
"""

import subprocess
import json
import pytest
import tempfile
import os
from pathlib import Path


class TestVesselPyrightIntegration:
    """vessel-pyrightツールの統合シナリオ"""
    
    def test_型エラーを含むPythonコードの分析を実行する(self):
        """シナリオ：型エラーを含むコードをpyrightで分析し、エラー情報を構造化して取得する"""
        # 型エラーを含むPythonコード
        code_with_type_error = '''
def greet(name: str) -> str:
    return f"Hello, {name}"

# 型エラー：数値を文字列引数に渡している
result = greet(123)
'''
        
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_with_type_error)
            temp_file = f.name
        
        try:
            # Vesselスクリプトを作成
            vessel_script = f'''
result = safe_run_pyright(["{temp_file}", "--outputjson"])
if result.get("success"):
    analysis = validate_pyright_output(result["stdout"])
    print(json.dumps(analysis, indent=2))
else:
    print(json.dumps(result, indent=2))
'''
            
            # vessel-pyrightを実行
            process = subprocess.run(
                ["nix", "run", ".#vessel-pyright"],
                input=vessel_script,
                text=True,
                capture_output=True
            )
            
            # 実行が成功することを確認
            assert process.returncode == 0
            
            # 結果をパース
            result = json.loads(process.stdout)
            
            # 型エラーが検出されることを確認
            assert result['valid'] is False
            assert result['summary']['error_count'] > 0
            assert len(result['issues']) > 0
            
            # エラーメッセージが適切であることを確認
            error_found = any(
                'Argument of type' in issue['message'] 
                for issue in result['issues']
            )
            assert error_found
            
        finally:
            # 一時ファイルをクリーンアップ
            os.unlink(temp_file)
    
    def test_正しいコードの分析で問題なしと報告する(self):
        """シナリオ：型的に正しいコードを分析し、問題なしと報告する"""
        # 型的に正しいコード
        correct_code = '''
def add(a: int, b: int) -> int:
    return a + b

result = add(1, 2)
print(f"Result: {result}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(correct_code)
            temp_file = f.name
        
        try:
            vessel_script = f'''
result = safe_run_pyright(["{temp_file}", "--outputjson"])
if result.get("success"):
    analysis = validate_pyright_output(result["stdout"])
    print(json.dumps(analysis, indent=2))
'''
            
            process = subprocess.run(
                ["nix", "run", ".#vessel-pyright"],
                input=vessel_script,
                text=True,
                capture_output=True
            )
            
            assert process.returncode == 0
            result = json.loads(process.stdout)
            
            # エラーがないことを確認
            assert result['valid'] is True
            assert result['summary']['error_count'] == 0
            assert len(result['issues']) == 0
            
        finally:
            os.unlink(temp_file)


class TestVesselPythonIntegration:
    """vessel-pythonツールの統合シナリオ"""
    
    def test_pytestでテストを実行し結果を構造化して取得する(self):
        """シナリオ：pytestでテストスイートを実行し、結果をJSON形式で取得する"""
        # テストコード
        test_code = '''
def test_success():
    assert 1 + 1 == 2

def test_failure():
    assert 1 + 1 == 3

def test_skip():
    import pytest
    pytest.skip("Skipping for demonstration")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        try:
            vessel_script = f'''
result = safe_run_pytest(["{temp_file}", "--json-report", "--json-report-file=-"])
if result.get("success") or "failed" in result.get("stdout", ""):
    # pytestは失敗テストがある場合もstdoutにJSONを出力する
    analysis = validate_pytest_output(result["stdout"], result.get("json_output", ""))
    print(json.dumps(analysis, indent=2))
'''
            
            process = subprocess.run(
                ["nix", "run", ".#vessel-python"],
                input=vessel_script,
                text=True,
                capture_output=True
            )
            
            assert process.returncode == 0
            result = json.loads(process.stdout)
            
            # テスト結果の検証
            assert result['valid'] is False  # 失敗したテストがあるため
            assert result['summary']['passed'] == 1
            assert result['summary']['failed'] == 1
            assert result['summary']['skipped'] == 1
            
        finally:
            os.unlink(temp_file)
    
    def test_ruffでコード品質をチェックし自動修正を提案する(self):
        """シナリオ：ruffでコード品質の問題を検出し、修正可能な問題を特定する"""
        # 品質問題を含むコード
        problematic_code = '''
import os
import sys
from typing import List

def process_data(data):
    # 未使用のインポート（os）
    # 型アノテーションの欠落
    result = []
    for   item   in   data:  # 余分なスペース
        result.append(item * 2)
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(problematic_code)
            temp_file = f.name
        
        try:
            vessel_script = f'''
# まず問題を検出
check_result = safe_run_ruff(["check", "{temp_file}"])
if check_result.get("success") or check_result.get("stdout"):
    analysis = validate_ruff_output(check_result.get("stdout", ""))
    print(json.dumps({{
        "analysis": analysis,
        "fixable": "--fix" in check_result.get("stdout", "")
    }}, indent=2))
'''
            
            process = subprocess.run(
                ["nix", "run", ".#vessel-python"],
                input=vessel_script,
                text=True,
                capture_output=True
            )
            
            assert process.returncode == 0
            result = json.loads(process.stdout)
            
            # リンティング問題が検出されることを確認
            assert result['analysis']['valid'] is False
            assert len(result['analysis']['issues']) > 0
            
            # 未使用インポートが検出されることを確認
            import_issue_found = any(
                'imported but unused' in issue.get('message', '')
                for issue in result['analysis']['issues']
            )
            assert import_issue_found
            
        finally:
            os.unlink(temp_file)


class TestVesselSecurityFeatures:
    """Vesselツールのセキュリティ機能の検証"""
    
    def test_危険な操作をブロックする(self):
        """シナリオ：eval, exec, os.systemなどの危険な操作がブロックされることを確認"""
        dangerous_scripts = [
            'eval("print(1 + 1)")',
            'exec("import os; os.system(\'ls\')")',
            '__import__("os").system("ls")',
            'open("/etc/passwd", "r")',
        ]
        
        for script in dangerous_scripts:
            process = subprocess.run(
                ["nix", "run", ".#vessel-python"],
                input=script,
                text=True,
                capture_output=True
            )
            
            # セキュリティエラーで終了することを確認
            assert process.returncode != 0
            assert "SecurityError" in process.stderr or "Security violation" in process.stderr
    
    def test_許可されたツールのみ実行可能(self):
        """シナリオ：環境変数で許可されていないツールの実行がブロックされる"""
        # 環境変数を設定して許可ツールを制限
        env = os.environ.copy()
        env['PYTHON_ALLOWED_TOOLS'] = 'pytest'  # ruffは許可しない
        
        vessel_script = '''
result = safe_run_ruff(["--version"])
print(result)
'''
        
        process = subprocess.run(
            ["nix", "run", ".#vessel-python"],
            input=vessel_script,
            text=True,
            capture_output=True,
            env=env
        )
        
        # ツールが許可されていないためエラーになることを確認
        assert process.returncode != 0
        assert "not allowed" in process.stderr or "SecurityError" in process.stderr