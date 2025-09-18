#!/usr/bin/env python3
"""
LSPを使った実践的なリファクタリング例

絶対パスから相対パスへの変換を支援するツール
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional


def find_python_files(directory: str) -> List[Path]:
    """Pythonファイルを再帰的に検索"""
    return list(Path(directory).rglob("*.py"))


def extract_imports(file_path: Path) -> List[Tuple[int, str]]:
    """ファイルからインポート文を抽出"""
    imports = []
    with open(file_path, 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip().startswith(('import ', 'from ')):
                imports.append((i, line.strip()))
    return imports


def check_with_pyright(file_path: Path) -> dict:
    """pyrightで型チェックを実行"""
    result = subprocess.run(
        ["pyright", "--outputjson", str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        return json.loads(result.stdout)
    return {"error": result.stderr}


def suggest_relative_import(absolute_import: str, current_file: Path) -> Optional[str]:
    """絶対インポートを相対インポートに変換する提案"""
    # "from package.module import something" のパターン
    match = re.match(r'from\s+(\S+)\s+import\s+(.+)', absolute_import)
    if not match:
        return None
    
    module_path = match.group(1)
    import_items = match.group(2)
    
    # 現在のファイルのパッケージパス
    current_parts = current_file.parts[:-1]  # ファイル名を除く
    
    # プロジェクトルートからの相対位置を計算
    # ここでは簡単な例として、同じプロジェクト内の相対パスを提案
    if module_path.startswith("examples."):
        # パッケージ階層を解析
        module_parts = module_path.split('.')
        
        # 共通の親を見つける
        common_parent_depth = 0
        for i, part in enumerate(current_parts):
            if i < len(module_parts) and part == module_parts[i]:
                common_parent_depth = i + 1
        
        # 相対パスを構築
        up_levels = len(current_parts) - common_parent_depth
        if up_levels > 0:
            relative_path = '.' * (up_levels + 1) + '.'.join(module_parts[common_parent_depth:])
        else:
            relative_path = '.' + '.'.join(module_parts[common_parent_depth:])
        
        return f"from {relative_path} import {import_items}"
    
    return None


def analyze_project(directory: str):
    """プロジェクト全体を解析してリファクタリング提案を生成"""
    print(f"🔍 プロジェクトを解析中: {directory}\n")
    
    python_files = find_python_files(directory)
    suggestions = []
    
    for file_path in python_files:
        print(f"📄 {file_path}")
        
        # インポート文を抽出
        imports = extract_imports(file_path)
        
        # pyrightでチェック
        pyright_result = check_with_pyright(file_path)
        errors = pyright_result.get('generalDiagnostics', [])
        
        # インポートエラーを確認
        import_errors = [e for e in errors if 'import' in e.get('message', '').lower()]
        
        if import_errors:
            print(f"   ⚠️  {len(import_errors)} 個のインポートエラー")
        
        # リファクタリング提案
        for line_num, import_stmt in imports:
            if import_stmt.startswith('from examples.'):
                suggestion = suggest_relative_import(import_stmt, file_path)
                if suggestion:
                    suggestions.append({
                        'file': str(file_path),
                        'line': line_num,
                        'original': import_stmt,
                        'suggested': suggestion
                    })
                    print(f"   💡 行 {line_num}: 相対インポートへの変換を提案")
    
    return suggestions


def apply_refactoring(suggestions: List[dict], dry_run: bool = True):
    """リファクタリング提案を適用"""
    print(f"\n📝 リファクタリング提案 (dry_run={dry_run}):\n")
    
    for s in suggestions:
        print(f"ファイル: {s['file']}")
        print(f"  行 {s['line']}:")
        print(f"    - 変更前: {s['original']}")
        print(f"    + 変更後: {s['suggested']}")
        print()
    
    if not dry_run:
        # 実際の変更を適用するコード
        # ここでは安全のため実装を省略
        print("⚠️  実際の変更は手動で行ってください")


def main():
    """メイン処理"""
    # 絶対インポートのプロジェクトを解析
    print("=== 絶対インポートプロジェクトの解析 ===")
    abs_suggestions = analyze_project("examples/absolute_imports")
    
    if abs_suggestions:
        apply_refactoring(abs_suggestions, dry_run=True)
    
    # 相対インポートのプロジェクトも確認
    print("\n=== 相対インポートプロジェクトの確認 ===")
    rel_suggestions = analyze_project("examples/relative_imports")
    
    if not rel_suggestions:
        print("✅ 相対インポートプロジェクトには提案はありません")


if __name__ == "__main__":
    main()