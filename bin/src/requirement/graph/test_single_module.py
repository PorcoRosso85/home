#!/usr/bin/env python3
"""
単一モジュールのin-sourceテストを実行するヘルパースクリプト

使い方:
    python test_single_module.py <module_path>
    
例:
    python test_single_module.py infrastructure/hierarchy_validator.py
    python test_single_module.py domain/constraints.py
"""
import os
import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_single_module.py <module_path>")
        print("\nExamples:")
        print("  python test_single_module.py infrastructure/hierarchy_validator.py")
        print("  python test_single_module.py domain/constraints.py")
        return 1
    
    module_path = Path(sys.argv[1])
    
    # 絶対パスに変換
    if not module_path.is_absolute():
        module_path = Path(__file__).parent / module_path
    
    if not module_path.exists():
        print(f"Error: Module not found: {module_path}")
        return 1
    
    # 環境変数を設定
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
    env['RGL_DB_PATH'] = str(Path(__file__).parent / 'rgl_db')
    
    print(f"Testing {module_path.name}...")
    print("-" * 80)
    
    # プロジェクトルートディレクトリを取得
    project_root = Path(__file__).parent.parent.parent  # /home/nixos/bin/src
    
    # 特殊なケース: hierarchy_validator.pyは引数"test"が必要
    if module_path.name == "hierarchy_validator.py":
        cmd = [sys.executable, str(module_path), "test"]
        result = subprocess.run(cmd, env=env)
    else:
        # モジュールパスを計算
        relative_path = module_path.relative_to(project_root)
        module_name = str(relative_path.with_suffix('')).replace('/', '.')
        
        # モジュールとして実行
        cmd = [sys.executable, "-m", module_name]
        result = subprocess.run(cmd, cwd=str(project_root), env=env)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())