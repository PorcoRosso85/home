#!/usr/bin/env python3
"""
pyright/ruffのネイティブ機能を直接使用する例

LSPツールの素の機能をそのまま使い、Pythonはその結果を解釈するだけです。
"""

import subprocess
import json
import os
from pathlib import Path


def show_raw_pyright_usage():
    """pyrightの生のコマンドライン使用例"""
    print("=== pyright の素の使い方 ===\n")
    
    # 1. 基本的な型チェック
    print("1️⃣ 基本的な型チェック:")
    print("$ pyright main.py")
    subprocess.run(["pyright", "--help"], capture_output=True)  # ヘルプ表示
    
    # 2. JSON出力で詳細な情報を取得
    print("\n2️⃣ JSON形式で詳細情報を取得:")
    print("$ pyright --outputjson main.py")
    print("結果をパイプで処理: $ pyright --outputjson main.py | jq '.generalDiagnostics'")
    
    # 3. 設定ファイルの使用
    print("\n3️⃣ pyrightconfig.json の例:")
    config_example = {
        "include": ["src"],
        "exclude": ["**/node_modules", "**/__pycache__"],
        "reportMissingImports": true,
        "reportGeneralTypeIssues": true,
        "pythonVersion": "3.12"
    }
    print(json.dumps(config_example, indent=2))
    
    # 4. ウォッチモード
    print("\n4️⃣ ファイル監視モード:")
    print("$ pyright --watch")
    print("ファイルを編集すると自動的に再チェックされます")


def show_raw_ruff_usage():
    """ruffの生のコマンドライン使用例"""
    print("\n\n=== ruff の素の使い方 ===\n")
    
    # 1. 基本チェック
    print("1️⃣ 基本的なリンティング:")
    print("$ ruff check .")
    print("$ ruff check --select I  # インポート関連のみ")
    
    # 2. 自動修正
    print("\n2️⃣ 自動修正機能:")
    print("$ ruff check --fix .")
    print("$ ruff check --fix --unsafe-fixes  # より積極的な修正")
    
    # 3. 差分表示
    print("\n3️⃣ 修正内容を事前確認:")
    print("$ ruff check --fix --diff .")
    
    # 4. フォーマット
    print("\n4️⃣ コードフォーマット:")
    print("$ ruff format .")
    print("$ ruff format --check  # チェックのみ（変更なし）")
    
    # 5. 設定ファイル
    print("\n5️⃣ pyproject.toml の例:")
    toml_example = """
[tool.ruff]
select = ["E", "F", "I"]  # I = isort (インポート順序)
line-length = 88

[tool.ruff.isort]
known-first-party = ["myproject"]
    """
    print(toml_example)


def demonstrate_import_analysis():
    """インポート分析の実演"""
    print("\n\n=== 実際のインポート分析 ===\n")
    
    # サンプルファイルを作成
    sample_file = Path("temp_import_test.py")
    sample_content = '''
import os
import sys
from typing import List
from examples.domain.user import User
from examples.application.service import UserService
import json

def main():
    user = User("test")
    service = UserService()
'''
    
    sample_file.write_text(sample_content)
    
    try:
        # pyrightで分析
        print("🔍 pyrightの出力:")
        result = subprocess.run(
            ["pyright", "--outputjson", str(sample_file)],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            print(f"分析完了: {data.get('summary', {}).get('filesAnalyzed', 0)} ファイル")
            
            # 診断結果を表示
            for diag in data.get('generalDiagnostics', [])[:3]:
                print(f"  - {diag.get('message', '')}")
        
        # ruffでインポート順序をチェック
        print("\n🔍 ruffのインポート関連チェック:")
        result = subprocess.run(
            ["ruff", "check", "--select", "I", str(sample_file)],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        else:
            print("✅ インポート順序は正しいです")
        
        # ruffの修正提案
        print("\n🔧 ruffの修正提案:")
        result = subprocess.run(
            ["ruff", "check", "--select", "I", "--fix", "--diff", str(sample_file)],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print("差分:")
            print(result.stdout)
        else:
            print("修正の必要はありません")
            
    finally:
        # クリーンアップ
        if sample_file.exists():
            sample_file.unlink()


def create_lsp_wrapper_script():
    """LSPツールのラッパースクリプト例"""
    print("\n\n=== LSPツールのシンプルなラッパー ===\n")
    
    wrapper_script = '''#!/bin/bash
# import_checker.sh - pyright/ruffを組み合わせたインポートチェッカー

FILE=$1

echo "🔍 Checking imports in $FILE"
echo "================================"

# pyrightで型とインポートをチェック
echo -e "\\n📘 Pyright analysis:"
pyright --outputjson "$FILE" | jq -r '.generalDiagnostics[] | 
    select(.message | contains("import")) | 
    "Line \\(.range.start.line): \\(.message)"'

# ruffでインポート順序をチェック
echo -e "\\n📙 Ruff import ordering:"
ruff check --select I "$FILE"

# 修正可能な場合は提案
if ruff check --select I --quiet "$FILE"; then
    echo "✅ No import issues found"
else
    echo -e "\\n💡 Suggested fixes:"
    ruff check --select I --fix --diff "$FILE"
fi
'''
    
    print("import_checker.sh:")
    print(wrapper_script)
    
    print("\n使い方:")
    print("$ chmod +x import_checker.sh")
    print("$ ./import_checker.sh main.py")


def show_vscode_integration():
    """VSCode統合の例"""
    print("\n\n=== VSCode/エディタ統合 ===\n")
    
    print("1️⃣ pyright LSP設定 (settings.json):")
    vscode_settings = {
        "python.analysis.typeCheckingMode": "strict",
        "python.analysis.autoImportCompletions": true,
        "python.analysis.diagnosticMode": "workspace",
        "python.analysis.inlayHints.functionReturnTypes": true
    }
    print(json.dumps(vscode_settings, indent=2))
    
    print("\n2️⃣ ruff LSP設定:")
    print("$ ruff serve")
    print("デフォルトでポート4797で起動")
    
    print("\n3️⃣ LSPクライアント設定例:")
    lsp_config = {
        "ruff": {
            "command": ["ruff", "serve"],
            "filetypes": ["python"],
            "rootPatterns": ["pyproject.toml", "ruff.toml", ".git"]
        }
    }
    print(json.dumps(lsp_config, indent=2))


if __name__ == "__main__":
    print("🛠️ pyright/ruff ネイティブ機能ガイド\n")
    print("このガイドは、各ツールの素の機能をそのまま使用する方法を示します。")
    print("=" * 60)
    
    # 各セクションを実行
    show_raw_pyright_usage()
    show_raw_ruff_usage()
    demonstrate_import_analysis()
    create_lsp_wrapper_script()
    show_vscode_integration()
    
    print("\n\n💡 まとめ:")
    print("- pyrightとruffは独立したツールとして動作")
    print("- 各ツールの出力をパイプやJSONで処理")
    print("- シェルスクリプトやエディタ統合で組み合わせ")
    print("- Pythonは結果の解釈と表示のみを担当")