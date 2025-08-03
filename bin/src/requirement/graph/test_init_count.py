#!/usr/bin/env python3
"""
VSS/FTS初期化回数の測定スクリプト
単一のテストを実行して初期化がどのように行われているか確認
"""

import subprocess
import sys
import re

def run_test_and_count_inits():
    """テストを実行して初期化回数をカウント"""
    cmd = [
        "nix", "run", ".#test", "--",
        "e2e/internal/test_e2e_duplicate_detection.py::test_duplicate_simple",
        "-v", "-s", "--tb=short"
    ]
    
    print("Running test...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 初期化ログをカウント
    output = result.stdout + result.stderr
    
    search_adapter_count = len(re.findall(r"SearchAdapter initialization #(\d+)", output))
    vss_adapter_count = len(re.findall(r"VSSSearchAdapter initialization #(\d+)", output))
    fts_adapter_count = len(re.findall(r"FTSSearchAdapter initialization #(\d+)", output))
    
    print(f"\n=== Initialization Count ===")
    print(f"SearchAdapter: {search_adapter_count}")
    print(f"VSSSearchAdapter: {vss_adapter_count}")
    print(f"FTSSearchAdapter: {fts_adapter_count}")
    
    # 実際の初期化番号も表示
    search_nums = re.findall(r"SearchAdapter initialization #(\d+)", output)
    if search_nums:
        print(f"SearchAdapter init numbers: {search_nums}")
    
    return output

if __name__ == "__main__":
    output = run_test_and_count_inits()
    
    # デバッグ用: 全出力を保存
    with open("init_count_output.txt", "w") as f:
        f.write(output)
    print("\nFull output saved to init_count_output.txt")