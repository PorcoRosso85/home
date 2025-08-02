"""
テストを実行してJSON形式でレポートを生成する例
"""
import subprocess
import json
import os

# テストをJSON形式で実行
result = subprocess.run(
    ["pytest", "--json-report", "--json-report-file=report.json", "-v"],
    capture_output=True,
    text=True
)

print("=== Test Output ===")
print(result.stdout)

# JSONレポートを読み込んで解析
if os.path.exists("report.json"):
    with open("report.json", "r") as f:
        report = json.load(f)
    
    print("\n=== Test Summary ===")
    summary = report.get("summary", {})
    print(f"Total: {summary.get('total', 0)}")
    print(f"Passed: {summary.get('passed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Skipped: {summary.get('skipped', 0)}")
    
    # 失敗したテストの詳細
    if summary.get('failed', 0) > 0:
        print("\n=== Failed Tests ===")
        for test in report.get("tests", []):
            if test.get("outcome") == "failed":
                print(f"- {test.get('nodeid')}")
                if 'call' in test and 'longrepr' in test['call']:
                    print(f"  {test['call']['longrepr'][:100]}...")
    
    # クリーンアップ
    os.remove("report.json")