#!/usr/bin/env python3
"""
pyright/ruffの素の機能を使った絶対→相対インポート変換ツール

このツールは、pyright LSPとruffの実際のコマンドを直接使用して、
インポートの問題を検出し、修正を提案します。
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def run_pyright_lsp(file_path: Path) -> Dict:
    """
    pyrightのLSP機能を使用してファイルを解析
    
    素のpyrightコマンドをそのまま使用します。
    """
    print(f"🔍 pyright --outputjson {file_path}")
    
    result = subprocess.run(
        ["pyright", "--outputjson", str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        return json.loads(result.stdout)
    return {"error": result.stderr}


def run_ruff_check(file_path: Path) -> List[Dict]:
    """
    ruffの素のチェック機能を使用
    
    ruffのJSONフォーマット出力をそのまま使用します。
    """
    print(f"🔍 ruff check --output-format json {file_path}")
    
    result = subprocess.run(
        ["ruff", "check", "--output-format", "json", str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        return json.loads(result.stdout)
    return []


def run_ruff_fix_diff(file_path: Path) -> str:
    """
    ruffの--diffオプションで修正案を取得
    
    実際にファイルを変更せずに、どのような修正が可能か確認します。
    """
    print(f"🔧 ruff check --fix --diff {file_path}")
    
    result = subprocess.run(
        ["ruff", "check", "--fix", "--diff", str(file_path)],
        capture_output=True,
        text=True
    )
    
    return result.stdout


def analyze_imports_with_pyright(file_path: Path) -> List[Dict]:
    """
    pyrightの診断結果からインポート関連の問題を抽出
    """
    pyright_result = run_pyright_lsp(file_path)
    
    import_diagnostics = []
    
    # 診断結果から抽出
    for diag in pyright_result.get("generalDiagnostics", []):
        message = diag.get("message", "")
        
        # インポート関連のメッセージを探す
        if any(keyword in message.lower() for keyword in ["import", "module", "cannot find"]):
            import_diagnostics.append({
                "file": diag.get("file", ""),
                "line": diag.get("range", {}).get("start", {}).get("line", 0),
                "message": message,
                "severity": diag.get("severity", "error")
            })
    
    return import_diagnostics


def demonstrate_lsp_refactoring():
    """
    LSPを使用したリファクタリングのデモンストレーション
    """
    print("=== pyright/ruff LSP リファクタリングデモ ===\n")
    
    # テスト用の絶対インポートファイル
    test_file = Path("absolute_imports/main.py")
    
    if not test_file.exists():
        print(f"❌ ファイルが見つかりません: {test_file}")
        return
    
    # 1. pyrightで現在の状態を分析
    print("\n1️⃣ pyrightで現在のインポートを分析")
    print("-" * 50)
    
    pyright_result = run_pyright_lsp(test_file)
    print(f"分析したファイル数: {pyright_result.get('summary', {}).get('filesAnalyzed', 0)}")
    print(f"エラー数: {pyright_result.get('summary', {}).get('errorCount', 0)}")
    print(f"警告数: {pyright_result.get('summary', {}).get('warningCount', 0)}")
    
    # インポート診断を表示
    import_issues = analyze_imports_with_pyright(test_file)
    if import_issues:
        print("\n📋 インポート関連の診断:")
        for issue in import_issues:
            print(f"  L{issue['line']}: {issue['message']}")
    
    # 2. ruffでスタイルチェック
    print("\n\n2️⃣ ruffでインポートスタイルをチェック")
    print("-" * 50)
    
    ruff_issues = run_ruff_check(test_file)
    if ruff_issues:
        print(f"\n見つかった問題: {len(ruff_issues)}件")
        for issue in ruff_issues[:5]:  # 最初の5件のみ表示
            print(f"  L{issue.get('location', {}).get('row', 0)}: "
                  f"{issue.get('code', '')} - {issue.get('message', '')}")
    else:
        print("✅ ruffの問題は見つかりませんでした")
    
    # 3. ruffの修正提案を表示
    print("\n\n3️⃣ ruffの自動修正提案")
    print("-" * 50)
    
    diff_output = run_ruff_fix_diff(test_file)
    if diff_output:
        print("修正案:")
        print(diff_output)
    else:
        print("自動修正可能な問題はありません")


def interactive_converter():
    """
    インタラクティブな変換ツール
    """
    print("\n=== インタラクティブ インポート変換 ===")
    print("pyrightとruffの素の機能を使用します\n")
    
    while True:
        file_path = input("\nファイルパス (qで終了): ").strip()
        if file_path.lower() == 'q':
            break
            
        path = Path(file_path)
        if not path.exists():
            print(f"❌ ファイルが見つかりません: {path}")
            continue
        
        # pyrightで分析
        print("\n--- pyright分析 ---")
        pyright_result = run_pyright_lsp(path)
        
        diagnostics = pyright_result.get("generalDiagnostics", [])
        if diagnostics:
            print(f"診断結果: {len(diagnostics)}件")
            for diag in diagnostics[:3]:
                print(f"  {diag.get('message', '')[:80]}...")
        else:
            print("✅ エラーなし")
        
        # ruffでチェック
        print("\n--- ruffチェック ---")
        ruff_issues = run_ruff_check(path)
        
        if ruff_issues:
            print(f"問題: {len(ruff_issues)}件")
            
            # 修正を提案
            response = input("\nruffの修正提案を見ますか? (y/N): ")
            if response.lower() == 'y':
                diff = run_ruff_fix_diff(path)
                if diff:
                    print("\n修正案:")
                    print(diff)
                    
                    apply = input("\n実際に適用しますか? (y/N): ")
                    if apply.lower() == 'y':
                        subprocess.run(["ruff", "check", "--fix", str(path)])
                        print("✅ 修正を適用しました")
        else:
            print("✅ 問題なし")


def show_lsp_capabilities():
    """
    LSPの機能を表示
    """
    print("=== pyright/ruff LSP機能の説明 ===\n")
    
    print("🔷 pyright LSPの素の機能:")
    print("  - pyright --outputjson <file>    # JSON形式の診断結果")
    print("  - pyright --version              # バージョン確認")
    print("  - pyright --stats                # 統計情報付き")
    print("  - pyright --watch                # ファイル監視モード")
    
    print("\n🔷 ruff の素の機能:")
    print("  - ruff check <file>              # 基本チェック")
    print("  - ruff check --fix <file>        # 自動修正")
    print("  - ruff check --diff <file>       # 修正内容の差分表示")
    print("  - ruff check --output-format json # JSON出力")
    print("  - ruff format <file>             # フォーマット")
    
    print("\n💡 これらのコマンドを直接使用することで、")
    print("   各ツールの生の機能を活用できます。")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="pyright/ruffの素の機能を使ったインポート分析ツール"
    )
    parser.add_argument("--demo", action="store_true",
                       help="デモンストレーションを実行")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="インタラクティブモード")
    parser.add_argument("--capabilities", "-c", action="store_true",
                       help="LSP機能の説明を表示")
    parser.add_argument("file", nargs="?",
                       help="分析するファイル")
    
    args = parser.parse_args()
    
    if args.capabilities:
        show_lsp_capabilities()
    elif args.demo:
        demonstrate_lsp_refactoring()
    elif args.interactive:
        interactive_converter()
    elif args.file:
        # 単一ファイルの分析
        path = Path(args.file)
        print(f"=== {path} の分析 ===\n")
        
        # pyright
        print("pyright:")
        pyright_result = run_pyright_lsp(path)
        summary = pyright_result.get("summary", {})
        print(f"  エラー: {summary.get('errorCount', 0)}")
        print(f"  警告: {summary.get('warningCount', 0)}")
        
        # ruff
        print("\nruff:")
        ruff_issues = run_ruff_check(path)
        print(f"  問題: {len(ruff_issues)}件")
        
        if ruff_issues:
            print("\n修正可能な問題があります。")
            print("--interactive オプションで対話的に修正できます。")
    else:
        parser.print_help()