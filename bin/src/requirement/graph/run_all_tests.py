#!/usr/bin/env python3
"""
requirement/graphディレクトリ内のすべてのin-sourceテストを一括実行するスクリプト

使い方:
    python run_all_tests.py
    
注意:
    - pytestがインストールされていない環境でも動作します
    - 各モジュールのif __name__ == "__main__"ブロックを利用します
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict


def find_test_modules() -> List[Path]:
    """in-sourceテストを含むPythonファイルを探す"""
    test_files = []
    base_dir = Path(__file__).parent
    
    # if __name__ == "__main__"を含むファイルを探す
    for py_file in base_dir.rglob("*.py"):
        if py_file.name == "run_all_tests.py":
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'if __name__ == "__main__"' in content:
                    test_files.append(py_file)
        except Exception:
            pass
    
    return sorted(test_files)


def run_module_test(module_path: Path) -> Tuple[bool, str, float]:
    """
    モジュールのテストを実行
    
    Returns:
        (success: bool, output: str, elapsed_time: float)
    """
    # プロジェクトルートディレクトリを取得
    project_root = Path(__file__).parent.parent.parent  # /home/nixos/bin/src
    
    # モジュールパスを計算
    relative_path = module_path.relative_to(project_root)
    module_name = str(relative_path.with_suffix('')).replace('/', '.')
    
    start_time = time.time()
    
    # 特殊なケース: hierarchy_validator.pyは引数"test"が必要
    if module_path.name == "hierarchy_validator.py":
        cmd = [sys.executable, str(module_path), "test"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(module_path.parent)
            )
            elapsed = time.time() - start_time
            return result.returncode == 0, result.stdout + result.stderr, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            return False, f"Error running {module_path}: {str(e)}", elapsed
    
    # 通常のケース: モジュールとして実行
    try:
        cmd = [sys.executable, "-m", module_name]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        elapsed = time.time() - start_time
        
        # 出力がない場合も成功とみなす（テストがない場合）
        if result.returncode == 0:
            output = result.stdout + result.stderr
            if not output.strip():
                output = "No tests found or module executed successfully"
            return True, output, elapsed
        else:
            return False, result.stdout + result.stderr, elapsed
            
    except Exception as e:
        elapsed = time.time() - start_time
        return False, f"Error running {module_name}: {str(e)}", elapsed


def print_summary(results: Dict[Path, Tuple[bool, str, float]]):
    """テスト結果のサマリーを表示"""
    total = len(results)
    passed = sum(1 for success, _, _ in results.values() if success)
    failed = total - passed
    total_time = sum(elapsed for _, _, elapsed in results.values())
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total modules tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.2f}s")
    print("=" * 80)
    
    if failed > 0:
        print("\nFailed modules:")
        for module, (success, output, elapsed) in results.items():
            if not success:
                print(f"  - {module.relative_to(Path(__file__).parent)}")
                # エラーの最初の数行を表示
                error_lines = output.strip().split('\n')
                for line in error_lines[-5:]:  # 最後の5行を表示
                    print(f"    {line}")


def main():
    """メイン処理"""
    print("requirement/graph In-Source Test Runner")
    print("=" * 80)
    print("Searching for test modules...")
    
    # テストモジュールを探す
    test_modules = find_test_modules()
    
    if not test_modules:
        print("No test modules found!")
        return 1
    
    print(f"Found {len(test_modules)} modules with tests:")
    for module in test_modules:
        print(f"  - {module.relative_to(Path(__file__).parent)}")
    
    print("\nRunning tests...")
    print("-" * 80)
    
    # 各モジュールのテストを実行
    results = {}
    for module in test_modules:
        relative_path = module.relative_to(Path(__file__).parent)
        print(f"\nTesting {relative_path}...", end=' ', flush=True)
        
        success, output, elapsed = run_module_test(module)
        results[module] = (success, output, elapsed)
        
        if success:
            print(f"✓ PASSED ({elapsed:.2f}s)")
            # 成功時も出力があれば表示（unittest出力など）
            if "test" in output.lower() and "ok" in output.lower():
                print(output.strip())
        else:
            print(f"✗ FAILED ({elapsed:.2f}s)")
            print(output.strip())
    
    # サマリーを表示
    print_summary(results)
    
    # 終了コード: 失敗があれば1、すべて成功なら0
    return 0 if all(success for success, _, _ in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())