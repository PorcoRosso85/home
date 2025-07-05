#!/usr/bin/env python3
"""
テストランナー - conventionに準拠したテスト実行
"""

import sys
import os

# 親ディレクトリをパスに追加してパッケージとしてインポート
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# 作業ディレクトリを設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# テストモジュールをインポート
import test_search_convention

# 各テスト関数を実行
test_functions = [
    test_search_convention.test_search_symbols_directory_returns_success_dict,
    test_search_convention.test_search_symbols_nonexistent_path_returns_error_dict,
    test_search_convention.test_search_symbols_empty_directory_returns_empty_success,
    test_search_convention.test_search_symbols_invalid_url_scheme_returns_error_dict,
    test_search_convention.test_search_symbols_file_url_returns_success_dict,
    test_search_convention.test_search_symbols_never_raises_exception,
]

print("Running convention-compliant tests...\n")

passed = 0
failed = 0

for test_func in test_functions:
    try:
        print(f"Running {test_func.__name__}...", end=" ")
        test_func()
        print("✓ PASSED")
        passed += 1
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {e}")
        failed += 1

print(f"\n{'='*50}")
print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")

if failed == 0:
    print("\n✅ All tests passed! (TDD Green phase complete)")
    sys.exit(0)
else:
    print("\n❌ Some tests failed")
    sys.exit(1)