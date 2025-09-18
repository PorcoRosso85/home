"""
ruffでコードをチェックし、自動修正可能な問題を表示する例
"""
import subprocess
import sys

# まずチェックのみ実行
print("=== Checking with ruff ===")
check_result = subprocess.run(
    ["ruff", "check", ".", "--output-format=concise"],
    capture_output=True,
    text=True
)

if check_result.returncode != 0:
    print("Issues found:")
    print(check_result.stdout)
    
    # 修正可能な問題があるか確認
    print("\n=== Checking fixable issues ===")
    fix_check = subprocess.run(
        ["ruff", "check", ".", "--fix", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    if "Would fix" in fix_check.stderr:
        print("Some issues can be automatically fixed.")
        print("Run 'ruff check . --fix' to apply fixes.")
else:
    print("No linting issues found!")

# フォーマットチェック
print("\n=== Format check ===")
format_result = subprocess.run(
    ["ruff", "format", ".", "--check"],
    capture_output=True,
    text=True
)

if format_result.returncode != 0:
    print("Formatting issues found.")
    print("Run 'ruff format .' to auto-format.")
else:
    print("Code is properly formatted!")