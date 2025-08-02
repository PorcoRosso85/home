"""
型エラーをJSONで取得して解析する例
"""
import subprocess
import json

# pyrightを実行してJSON出力を取得
result = subprocess.run(
    ["pyright", "--outputjson", "."],
    capture_output=True,
    text=True
)

if result.returncode != 0 and result.stdout:
    # JSON結果をパース
    data = json.loads(result.stdout)
    
    # サマリー情報
    summary = data.get('summary', {})
    print(f"Files analyzed: {summary.get('filesAnalyzed', 0)}")
    print(f"Errors: {summary.get('errorCount', 0)}")
    print(f"Warnings: {summary.get('warningCount', 0)}")
    
    # エラーの詳細を表示
    diagnostics = data.get('generalDiagnostics', [])
    for diag in diagnostics[:5]:  # 最初の5件のみ
        print(f"\n{diag.get('file')}:{diag.get('range', {}).get('start', {}).get('line', 0)}")
        print(f"  {diag.get('severity')}: {diag.get('message')}")
else:
    print("No type errors found!")