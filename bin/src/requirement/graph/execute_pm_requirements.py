#!/usr/bin/env python3
"""
PM視点の要件を実行するスクリプト

実行方法:
    cd /home/nixos/bin/src/requirement/graph
    python execute_pm_requirements.py
"""
import json
import subprocess

def execute_requirement(query_data):
    """要件クエリを実行"""
    # JSONをechoコマンドで渡す
    json_str = json.dumps(query_data)
    cmd = f"echo '{json_str}' | LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ RGL_DB_PATH=./rgl_db python run.py"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            return json.loads(result.stdout)
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """メイン処理"""
    # PM要件ファイルを読み込む
    with open('pm_requirements_formatted.json', 'r', encoding='utf-8') as f:
        pm_data = json.load(f)

    results = []

    print("=== PM視点の要件追加を開始します ===\n")

    for _category_key, category_data in pm_data["pm_requirements"]["categories"].items():
        print(f"\n## {category_data['title']}")
        print("-" * 50)

        for req in category_data["requirements"]:
            print(f"\n実行: {req['name']}")
            print(f"期待結果: {req['expected']}")

            # クエリを実行
            result = execute_requirement(req["query"])

            # 結果を表示
            if result.get("status") == "success":
                print(f"✓ 成功: {result.get('message', 'クエリが正常に実行されました')}")
                if result.get("data"):
                    print(f"  データ: {result['data']}")
            else:
                print(f"✗ エラー: {result.get('message', '不明なエラー')}")
                if result.get("details"):
                    print(f"  詳細: {result['details']}")
                if result.get("suggestion"):
                    print(f"  提案: {result['suggestion']}")

            # 結果を記録
            results.append({
                "name": req['name'],
                "expected": req['expected'],
                "actual": result.get("status", "error"),
                "result": result
            })

    # サマリーを表示
    print("\n\n=== 実行サマリー ===")
    print("-" * 50)

    success_count = sum(1 for r in results if r["actual"] == "success")
    error_count = sum(1 for r in results if r["actual"] == "error")

    print(f"成功: {success_count}")
    print(f"エラー: {error_count}")
    print(f"合計: {len(results)}")

    # 期待通りでない結果を表示
    print("\n## 期待と異なる結果:")
    unexpected = [r for r in results if r["expected"] != r["actual"]]
    if unexpected:
        for r in unexpected:
            print(f"- {r['name']}: 期待={r['expected']}, 実際={r['actual']}")
    else:
        print("なし（すべて期待通り）")

    # 結果をJSONファイルに保存
    with open('pm_requirements_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n結果を pm_requirements_results.json に保存しました。")

if __name__ == "__main__":
    main()
