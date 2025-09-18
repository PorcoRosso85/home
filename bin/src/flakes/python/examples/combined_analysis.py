"""
複数のツールを組み合わせた総合的な品質チェック例
"""
import subprocess
import json

print("=== Python Code Quality Analysis ===\n")

# 利用可能なツールをチェック（vesselから提供される）
tools = available_tools  # vessel_python.pyから注入される

results = {}

# 1. Type checking with pyright
if 'pyright' in tools:
    print("1. Type Checking...")
    pyright_result = subprocess.run(
        ["pyright", "--outputjson"],
        capture_output=True,
        text=True
    )
    if pyright_result.stdout:
        pyright_data = json.loads(pyright_result.stdout)
        results['types'] = {
            'errors': pyright_data.get('summary', {}).get('errorCount', 0),
            'warnings': pyright_data.get('summary', {}).get('warningCount', 0)
        }
        print(f"   Errors: {results['types']['errors']}")
        print(f"   Warnings: {results['types']['warnings']}")

# 2. Linting with ruff
if 'ruff' in tools:
    print("\n2. Linting...")
    ruff_result = subprocess.run(
        ["ruff", "check", ".", "--exit-zero"],
        capture_output=True,
        text=True
    )
    issue_count = len(ruff_result.stdout.strip().split('\n')) if ruff_result.stdout.strip() else 0
    results['lint'] = {'issues': issue_count}
    print(f"   Issues found: {issue_count}")

# 3. Test execution
if 'pytest' in tools:
    print("\n3. Running Tests...")
    pytest_result = subprocess.run(
        ["pytest", "--tb=no", "-q"],
        capture_output=True,
        text=True
    )
    # Simple parsing of pytest output
    output_lines = pytest_result.stdout.strip().split('\n')
    for line in output_lines:
        if 'passed' in line or 'failed' in line:
            print(f"   {line}")

# Summary
print("\n=== Summary ===")
total_issues = sum([
    results.get('types', {}).get('errors', 0),
    results.get('types', {}).get('warnings', 0),
    results.get('lint', {}).get('issues', 0)
])

if total_issues == 0:
    print("✅ All checks passed! Code quality looks good.")
else:
    print(f"⚠️  Total issues found: {total_issues}")
    print("Run individual tools for detailed information.")