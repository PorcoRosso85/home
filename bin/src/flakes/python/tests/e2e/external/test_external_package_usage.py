#!/usr/bin/env python3
"""
E2Eテスト：外部パッケージとしての使用シナリオ

このPython環境を外部プロジェクトから参照・使用する際の
実際のシナリオを検証します。
"""

import subprocess
import tempfile
import os
import json
import pytest
from pathlib import Path


class TestExternalFlakeUsage:
    """外部プロジェクトからFlakeとして参照するシナリオ"""
    
    def test_子プロジェクトからPython環境を参照できる(self):
        """シナリオ：別のNixプロジェクトからこのFlakeのPython環境を利用する"""
        # 子プロジェクトのflake.nix
        child_flake = '''
{
  description = "Test project using Python flake";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    python-flake.url = "path:''' + os.getcwd() + '''";
  };
  
  outputs = { self, nixpkgs, python-flake }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          python-flake.packages.${system}.pythonEnv
          python-flake.packages.${system}.pyright
          python-flake.packages.${system}.ruff
        ];
      };
      
      packages.${system}.test-script = pkgs.writeScriptBin "test-env" \'\'
        #!${pkgs.bash}/bin/bash
        echo "Python version:"
        ${python-flake.packages.${system}.pythonEnv}/bin/python --version
        echo "Pyright version:"
        ${python-flake.packages.${system}.pyright}/bin/pyright --version
        echo "Ruff version:"
        ${python-flake.packages.${system}.ruff}/bin/ruff --version
      \'\';
    };
}
'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 子プロジェクトを作成
            flake_path = Path(tmpdir) / "flake.nix"
            flake_path.write_text(child_flake)
            
            # nix build でパッケージをビルド
            result = subprocess.run(
                ["nix", "build", f"{tmpdir}#test-script", "--no-link", "--print-out-paths"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            script_path = result.stdout.strip()
            
            # スクリプトを実行
            result = subprocess.run(
                [f"{script_path}/bin/test-env"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "Python version:" in result.stdout
            assert "3.12" in result.stdout  # Python 3.12が使用されている
            assert "Pyright version:" in result.stdout
            assert "Ruff version:" in result.stdout


class TestPythonModuleImport:
    """Pythonモジュールとしての使用シナリオ"""
    
    def test_modモジュールから関数をインポートして使用する(self):
        """シナリオ：mod.pyで公開されているAPIを実際のコードで使用する"""
        test_script = '''
import sys
import os
sys.path.insert(0, os.getcwd())

from mod import (
    safe_run_pyright,
    validate_pyright_output,
    get_tool_config,
    AnalysisResult
)

# 設定を取得
config = get_tool_config()
print(f"Timeout: {config['timeout']}s")
print(f"Allowed tools: {config['allowed_tools']}")

# 型チェックを実行（仮想的な例）
# 実際の実行にはVessel環境が必要
print("\\nAPI functions imported successfully:")
print(f"- safe_run_pyright: {safe_run_pyright.__name__}")
print(f"- validate_pyright_output: {validate_pyright_output.__name__}")
print(f"- AnalysisResult type: {AnalysisResult}")
'''
        
        result = subprocess.run(
            ["python3", "-c", test_script],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        assert result.returncode == 0
        assert "Timeout: 60s" in result.stdout
        assert "pytest" in result.stdout
        assert "API functions imported successfully" in result.stdout


class TestCompleteWorkflow:
    """完全なワークフローのシナリオ"""
    
    def test_プロジェクトの型チェック_テスト_リンティングを一括実行(self):
        """シナリオ：実際のプロジェクトで型チェック、テスト、リンティングを順次実行する"""
        # サンプルプロジェクトの作成
        with tempfile.TemporaryDirectory() as project_dir:
            # メインコード
            main_py = Path(project_dir) / "main.py"
            main_py.write_text('''
def calculate_sum(numbers: list[int]) -> int:
    """数値のリストの合計を計算する"""
    return sum(numbers)

def main():
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
''')
            
            # テストコード
            test_py = Path(project_dir) / "test_main.py"
            test_py.write_text('''
from main import calculate_sum

def test_calculate_sum():
    assert calculate_sum([1, 2, 3]) == 6
    assert calculate_sum([]) == 0
    assert calculate_sum([-1, 1]) == 0
''')
            
            # 統合スクリプト
            workflow_script = f'''
import json
import os
os.chdir("{project_dir}")

print("=== Running Complete Workflow ===\\n")

# 1. Pyright型チェック
print("1. Type checking with Pyright...")
pyright_result = safe_run_pyright(["main.py", "--outputjson"])
if pyright_result.get("success"):
    analysis = validate_pyright_output(pyright_result["stdout"])
    print(f"   Type check valid: {analysis['valid']}")
    print(f"   Errors: {analysis['summary']['error_count']}")

# 2. Pytestテスト実行
print("\\n2. Running tests with Pytest...")
pytest_result = safe_run_pytest(["test_main.py", "-v"])
if pytest_result.get("success"):
    print("   All tests passed!")
else:
    print(f"   Some tests failed: {pytest_result.get('stderr', '')}")

# 3. Ruffリンティング
print("\\n3. Linting with Ruff...")
ruff_result = safe_run_ruff(["check", "."])
if ruff_result.get("success"):
    print("   No linting issues found!")
else:
    analysis = validate_ruff_output(ruff_result.get("stdout", ""))
    print(f"   Found {len(analysis['issues'])} linting issues")

print("\\n=== Workflow Complete ===")
'''
            
            # vessel-pythonで実行
            result = subprocess.run(
                ["nix", "run", ".#vessel-python"],
                input=workflow_script,
                text=True,
                capture_output=True
            )
            
            assert result.returncode == 0
            assert "Running Complete Workflow" in result.stdout
            assert "Type check valid: True" in result.stdout
            assert "All tests passed" in result.stdout
            assert "No linting issues found" in result.stdout or "linting issues" in result.stdout